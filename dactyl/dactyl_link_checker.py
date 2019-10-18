#!/usr/bin/env python3
from dactyl.common import *

import requests
from bs4 import BeautifulSoup
from time import time, sleep

from dactyl.config import DactylConfig
from dactyl.cli import DactylCLIParser

TIMEOUT_SECS = 9.1
CHECK_IN_INTERVAL = 30
FINAL_RETRY_DELAY = 4 * CHECK_IN_INTERVAL

soupsCache = {}
def getSoup(fullPath):
    if fullPath in soupsCache.keys():
        soup = soupsCache[fullPath]
    else:
        with open(fullPath, 'r', encoding="utf-8") as f:
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
        logger.warning("Error occurred: %s" % repr(e))
        code = 500
    if code == 405 or code == 404:
        #HEAD didn't work, maybe GET will?
        try:
            code = requests.get(endpoint, timeout=TIMEOUT_SECS).status_code
        except Exception as e:
          logger.warning("Error occurred: %s" % repr(e))
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
                        logger.warning("Skipping email link in %s to %s" %
                                (fullPath, endpoint))
                        continue

                    elif endpoint[0] == '/':
                        # Can't properly test absolute links without knowing where the
                        #   server root will be, so skip this
                        logger.warning("Skipping absolute link in %s to %s" %
                                (fullPath, endpoint))
                        continue

                    elif "://" in endpoint:
                        if offline:
                            logger.info("Offline - Skipping remote URL %s" % (endpoint))
                            continue

                        num_links_checked += 1
                        check_remote_url(endpoint, fullPath, broken_links, externalCache)


                    elif '#' in endpoint:
                        if fname in config["ignore_anchors_in"]:
                            logger.warning("Ignoring anchor %s in dynamic page %s" %
                                    (endpoint,fname))
                            continue
                        logger.info("Testing local link %s from %s" %
                                (endpoint, fullPath))
                        num_links_checked += 1
                        filename,anchor = endpoint.split("#",1)
                        # Strip query parameters
                        if "?" in filename:
                            filename, query = filename.split("?", 1)
                        if filename == "":
                            fullTargetPath = fullPath
                        else:
                            fullTargetPath = os.path.join(dirpath, filename)
                        if not os.path.exists(fullTargetPath):
                            logger.warning("Broken local link in %s to %s" %
                                    (fullPath, endpoint))
                            broken_links.append( (fullPath, endpoint) )

                        elif filename in config["ignore_anchors_in"]:
                            #Some pages are populated dynamically, so BeatifulSoup wouldn't
                            # be able to find anchors in them anyway
                            logger.info("Skipping anchor link in %s to ignored page %s" %
                                  (fullPath, endpoint))
                            continue

                        elif fullTargetPath != "../":
                            num_links_checked += 1
                            targetSoup = getSoup(fullTargetPath)
                            if not targetSoup.find(id=anchor) and not targetSoup.find(
                                        "a",attrs={"name":anchor}):
                                logger.warning("Broken anchor link in %s to %s" %
                                        (fullPath, endpoint))
                                broken_links.append( (fullPath, endpoint) )
                            else:
                                logger.info("...anchor found.")
                            continue

                    else:
                        num_links_checked += 1
                        if "?" in endpoint:
                            filename, query = endpoint.split("?", 1)
                        else:
                            filename = endpoint
                        if not os.path.exists(os.path.join(dirpath, filename)):
                            logger.warning("Broken local link in %s to %s" %
                                    (fullPath, filename))
                            broken_links.append( (fullPath, filename) )

                    #Now check images
                    imgs = soup.find_all('img')
                    for img in imgs:
                        num_links_checked += 1
                        if "src" not in img.attrs or not img["src"].strip():
                            logger.warning("Broken image with no src in %s" % fullPath)
                            broken_links.append( (fullPath, img["src"]) )
                            continue

                        src = img["src"]
                        if src[0] == "/":
                            logger.warning("Skipping absolute image path %s in %s" %
                                    (src, fullPath))
                        elif "://" in src:
                            if offline:
                                logger.info("Offline - Skipping remote image %s"%(endpoint))
                                continue

                            check_remote_url(src, fullPath, broken_links, externalCache, isImg=True)

                        else:
                            logger.info("Checking local image %s in %s" %
                                    (src, fullPath))
                            if os.path.exists(os.path.join(dirpath, src)):
                                logger.info("...success")
                            else:
                                logger.warning("Broken local image %s in %s" %
                                        (src, fullPath))
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



def main(cli_args):
    broken_links, num_links_checked = checkLinks(cli_args.offline)

    if not cli_args.no_final_retry and not cli_args.offline:
        final_retry_links(broken_links)
        #^ sleeps for FINAL_RETRY_DELAY and then retries remote links
        # Automatically removes from broken_links if they work now

    print("---------------------------------------")
    print("Link check report. %d links checked."%num_links_checked)

    if not cli_args.strict:
        unknown_broken_links = [ (page,link) for page,link in broken_links
                        if link not in config["known_broken_links"] ]

    if not broken_links:
        print("Success! No broken links found.")
    else:
        print("%d broken links found:"%(len(broken_links)))
        [print("File:",fname,"Link:",link) for fname,link in broken_links]

        if cli_args.strict or unknown_broken_links:
            exit(1)

        print("Success - all broken links are known problems.")


def dispatch_main():
    cli = DactylCLIParser(DactylCLIParser.UTIL_LINKS)
    global config
    config = DactylConfig(cli.cli_args)
    main(cli.cli_args)

if __name__ == "__main__":
    dispatch_main()
