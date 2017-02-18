#!/usr/bin/env python3
import requests
import os
import yaml
import argparse
import logging
import re
from bs4 import BeautifulSoup
from time import time, sleep

# Used for pulling in the default config file
from pkg_resources import resource_stream

DEFAULT_CONFIG_FILE = "dactyl-config.yml"
TIMEOUT_SECS = 9.1
CHECK_IN_INTERVAL = 30
FINAL_RETRY_DELAY = 4 * CHECK_IN_INTERVAL

# The log level is configurable at runtime (see __main__ below)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

soupsCache = {}
def getSoup(fullPath):
  if fullPath in soupsCache.keys():
    soup = soupsCache[fullPath]
  else:
    with open(fullPath, 'r') as f:
      soup = BeautifulSoup(f.read(), "html.parser")
      soupsCache[fullPath] = soup
  return soup


def check_for_unparsed_reference_links(soup):
    #unmatched_reflink_regex = re.compile(r"\[[^\]]+\]\[(\w| )*\]")
    unmatched_reflink_regex = re.compile(r"(\[[^\]]+)?\]\[(\w| )*\]")
    unparsed_links = []
    for s in soup.strings:
        m = re.search(unmatched_reflink_regex, s)
        if m:
            unparsed_links.append(m.group(0))
    return unparsed_links


def check_remote_url(endpoint, fullPath, broken_links, externalCache, isImg=False):
    if isImg:
        linkword = "image"
    else:
        linkword = "link"
    if endpoint in [v for k,v in broken_links]:
        # We already confirmed this was broken, so just add another instance
        logger.warning("Broken %s %s appears again in %s" % (linkword, endpoint, fullPath))
        broken_links.append( (fullPath, endpoint) )
        return False
    if endpoint in externalCache:
        logger.debug("Skipping cached %s %s" % (linkword, endpoint))
        return True
    if endpoint in config["known_broken_links"]:
        logger.warning("Skipping known broken %s %s in %s" % (linkword, endpoint, fullPath))
        return True

    logger.info("Testing remote %s URL %s"%(linkword, endpoint))
    try:
        code = requests.head(endpoint, timeout=TIMEOUT_SECS).status_code
    except Exception as e:
        logger.warning("Error occurred: %s" % e)
        code = 500
    if code == 405 or code == 404:
        #HEAD didn't work, maybe GET will?
        try:
            code = requests.get(endpoint, timeout=TIMEOUT_SECS).status_code
        except Exception as e:
          logger.warning("Error occurred: %s" % e)
          code = 500

    if code < 200 or code >= 400:
        logger.warning("Broken remote %s in %s to %s"%(linkword, fullPath, endpoint))
        broken_links.append( (fullPath, endpoint) )
        return False
    else:
        logger.info("...success.")
        externalCache.append(endpoint)
        return True


def checkLinks(offline=False):
    externalCache = []
    broken_links = []
    num_links_checked = 0
    last_checkin = time()
    for dirpath, dirnames, filenames in os.walk(config["out_path"]):
      if time() - last_checkin > CHECK_IN_INTERVAL:
        ## Print output periodically so Jenkins/etc. don't kill the job
        last_checkin = time()
        print("... still working (dirpath: %s) ..." % dirpath)
      if "template_path" in config and \
         os.path.abspath(dirpath) == os.path.abspath(config["template_path"]):
        # don't try to parse and linkcheck the templates
        logger.warning("Skipping link checking for template path %s" % dirpath)
        continue
      for fname in filenames:
        if time() - last_checkin > CHECK_IN_INTERVAL:
          last_checkin = time()
          print("... still working (file: %s) ..." % fname)
        fullPath = os.path.join(dirpath, fname)
        if "/node_modules/" in fullPath or ".git" in fullPath:
          logger.debug("skipping ignored dir: %s" % fullPath)
          continue
        if fullPath.endswith(".html"):
          soup = getSoup(fullPath)
          unparsed_links = check_for_unparsed_reference_links(soup)
          if unparsed_links:
            logger.warning("Found %d unparsed Markdown reference links: %s" %
                        (len(unparsed_links), "\n... ".join(unparsed_links)))
            [broken_links.append( (fullPath, u) ) for u in unparsed_links]
          links = soup.find_all('a')
          for link in links:
            if time() - last_checkin > CHECK_IN_INTERVAL:
              last_checkin = time()
              print("... still working (link: %s) ..." % link)
            if "href" not in link.attrs:
              #probably an <a name> type anchor, skip
              continue

            endpoint = link['href']
            if not endpoint.strip():
              logger.warning("Empty link in %s" % fullPath)
              broken_links.append( (fullPath, endpoint) )
              num_links_checked += 1

            elif endpoint == "#":
              continue

            elif "mailto:" in endpoint:
              logger.info("Skipping email link in %s to %s"%(fullPath, endpoint))
              continue

            elif "://" in endpoint:
              if offline:
                logger.info("Offline - Skipping remote URL %s"%(endpoint))
                continue

              num_links_checked += 1
              check_remote_url(endpoint, fullPath, broken_links, externalCache)


            elif '#' in endpoint:
              if fname in config["ignore_anchors_in"]:
                logger.info("Ignoring anchor %s in dynamic page %s"%(endpoint,fname))
                continue
              logger.info("Testing local link %s from %s"%(endpoint, fullPath))
              num_links_checked += 1
              filename,anchor = endpoint.split("#",1)
              if filename == "":
                fullTargetPath = fullPath
              else:
                fullTargetPath = os.path.join(dirpath, filename)
              if not os.path.exists(fullTargetPath):
                logger.warning("Broken local link in %s to %s"%(fullPath, endpoint))
                broken_links.append( (fullPath, endpoint) )

              elif filename in config["ignore_anchors_in"]:
                  #Some pages are populated dynamically, so BeatifulSoup wouldn't
                  # be able to find anchors in them anyway
                  logger.info("Skipping anchor link in %s to dynamic page %s" %
                        (fullPath, endpoint))
                  continue

              elif fullTargetPath != "../":
                num_links_checked += 1
                targetSoup = getSoup(fullTargetPath)
                if not targetSoup.find(id=anchor) and not targetSoup.find(
                        "a",attrs={"name":anchor}):
                  logger.warning("Broken anchor link in %s to %s"%(fullPath, endpoint))
                  broken_links.append( (fullPath, endpoint) )
                else:
                  logger.info("...anchor found.")
                continue

            elif endpoint[0] == '/':
              #can't really test links out of the local field
              logger.info("Skipping absolute link in %s to %s"%(fullPath, endpoint))
              continue

            else:
              num_links_checked += 1
              if not os.path.exists(os.path.join(dirpath, endpoint)):
                logger.warning("Broken local link in %s to %s"%(fullPath, endpoint))
                broken_links.append( (fullPath, endpoint) )

          #Now check images
          imgs = soup.find_all('img')
          for img in imgs:
            num_links_checked += 1
            if "src" not in img.attrs or not img["src"].strip():
              logger.warning("Broken image with no src in %s" % fullPath)
              broken_links.append( (fullPath, img["src"]) )
              continue

            src = img["src"]
            if "://" in src:
              if offline:
                logger.info("Offline - Skipping remote image %s"%(endpoint))
                continue

              check_remote_url(src, fullPath, broken_links, externalCache, isImg=True)

            else:
              logger.info("Checking local image %s in %s" % (src, fullPath))
              if os.path.exists(os.path.join(dirpath, src)):
                logger.info("...success")
              else:
                logger.warning("Broken local image %s in %s" % (src, fullPath))
                broken_links.append( (fullPath, src) )
    return broken_links, num_links_checked


def final_retry_links(broken_links):
    """Give the broken remote links a little while to recover in case they're just flaps"""
    broken_remote_links = [ (page,link) for page,link in broken_links
                           if re.match(r"^https?://", link) ]
    if not broken_remote_links:
        logger.info("(no http/https broken links to retry)")
        return

    print("Waiting %d seconds to retry broken %d remote links..."
                % (FINAL_RETRY_DELAY, len(broken_remote_links)))
    start_wait = time()
    elapsed = 0
    while elapsed < FINAL_RETRY_DELAY:
        sleep(CHECK_IN_INTERVAL)
        print("...")
        elapsed = time() - start_wait

    retry_cache = []
    retry_broken = []
    for page, link in broken_remote_links:
        link_works = check_remote_url(link, page, retry_broken, retry_cache)
        if link_works:
            logger.info("Link %s in page %s is back online" % (link, page))
            broken_links.remove( (page,link) )
        else:
            logger.info("Link %s in page %s is still down." % (link, page))


config = yaml.load(resource_stream(__name__, "default-config.yml"))

def load_config(config_file=DEFAULT_CONFIG_FILE):
    """Reload config from a YAML file."""
    global config
    logger.info("loading config file %s..." % config_file)
    try:
        with open(config_file, "r") as f:
            loaded_config = yaml.load(f)
    except FileNotFoundError as e:
        if config_file == DEFAULT_CONFIG_FILE:
            logger.warning("Couldn't read a config file; using generic config")
            loaded_config = {}
        else:
            traceback.print_tb(e.__traceback__)
            exit("Fatal: Config file '%s' not found"%config_file)
    except yaml.parser.ParserError as e:
        traceback.print_tb(e.__traceback__)
        exit("Fatal: Error parsing config file: %s"%e)

    config.update(loaded_config)
    assert(config["out_path"])
    assert(type(config["known_broken_links"]) == list)


def main(args):
    if not args.quiet:
        logger.setLevel(logging.INFO)

    if args.config:
        load_config(args.config)
    else:
        load_config()

    broken_links, num_links_checked = checkLinks(args.offline)

    if not args.no_final_retry and not args.offline:
        final_retry_links(broken_links)
        #^ sleeps for FINAL_RETRY_DELAY and then retries remote links
        # Automatically removes from broken_links if they work now

    print("---------------------------------------")
    print("Link check report. %d links checked."%num_links_checked)

    if not args.strict:
      unknown_broken_links = [ (page,link) for page,link in broken_links
                        if link not in config["known_broken_links"] ]

    if not broken_links:
      print("Success! No broken links found.")
    else:
      print("%d broken links found:"%(len(broken_links)))
      [print("File:",fname,"Link:",link) for fname,link in broken_links]

      if args.strict or unknown_broken_links:
          exit(1)

      print("Success - all broken links are known problems.")


def dispatch_main():
    parser = argparse.ArgumentParser(
            description='Check files in this repository for broken links.')
    parser.add_argument("-o", "--offline", action="store_true",
                       help="Check local anchors only")
    parser.add_argument("-s", "--strict", action="store_true",
                        help="Exit with error even on known problems")
    parser.add_argument("--config", "-c", type=str,
                        help="Specify path to an alternate config file.")
    parser.add_argument("-n", "--no_final_retry", action="store_true",
                        help="Don't wait and retry failed remote links at the end.")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Reduce output to just failures and final report")
    args = parser.parse_args()
    main(args)


if __name__ == "__main__":
    dispatch_main()
