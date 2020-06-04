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

TYPE_LINK = "link"
TYPE_IMAGE = "image"

soupsCache = {}
def getSoup(in_file):
    if in_file in soupsCache.keys():
        soup = soupsCache[in_file]
    else:
        with open(in_file, 'r', encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            soupsCache[in_file] = soup
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


remote_url_cache = {
    #str url: bool was_good
}
def check_remote_url(endpoint, in_file, hreftype=TYPE_LINK):
    if endpoint in remote_url_cache.keys():
        if remote_url_cache[endpoint]:
            logger.debug("Skipping cached %s %s" % (hreftype, endpoint))
            return (1, True)
        else:
            # We already confirmed this was broken, so just add another instance
            logger.warning("Broken %s '%s' appears again in %s" %
                    (hreftype, endpoint, in_file))
            return (1, False)

    logger.info("Testing remote %s '%s'" % (hreftype, endpoint))
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
          logger.warning("... Error occurred: %s" % repr(e))
          code = 500

    if code < 200 or code >= 400:
        logger.warning("... Broken remote %s in %s to '%s'" %
                (hreftype, in_file, endpoint))
        remote_url_cache[endpoint] = False
        return (1, False)
    else:
        logger.info("... success.")
        remote_url_cache[endpoint] = True
        return (1, True)


def check_href(endpoint, in_file, dirpath, top_dir, offline, hreftype=TYPE_LINK, site_prefix=None):
    """
    Check a given href to see if it's a working link (coming from )
    Use hreftype=TYPE_IMAGE for modified behavior/logging for images.
    Returns (int was_checked, bool was_good) where was_checked indicates how
        many links were actually checked (1 or 0) and was_good indicates
        whether the link was found if checked.
        If the link was not checked, was_good is False.
    """

    if not endpoint.strip():
        logger.warning("Empty %s in %s" % (hreftype,in_file))
        return (1, False)

    if endpoint in config["known_broken_links"]:
        logger.warning("Skipping known broken %s '%s' in %s" %
                (hreftype, endpoint, in_file))
        return (0, False)

    if endpoint == "#":
        if hreftype == TYPE_IMAGE:
            logger.warning("Invalid image URL: '#' in %s" % in_file)
            return (1, False)
        logger.debug("Skipping empty anchor link in %s" % in_file)
        return (0, False)

    if "mailto:" in endpoint:
        if hreftype == TYPE_IMAGE:
            logger.warning("Invalid image URL: '%s' in %s" % (endpoint, in_file))
            return (1, False)
        logger.warning("Skipping email link in %s to %s" %
                (in_file, endpoint))
        return (0, False)

    if "://" in endpoint or endpoint[:2] == "//":
        # Remote link.
        if offline:
            logger.info("Offline - Skipping remote URL %s" % (endpoint))
            return (0, False)

        return check_remote_url(endpoint, in_file, hreftype)
    else:
        # Local Anchor link; check presence of target file & anchor too.
        return check_local_file(endpoint, in_file, dirpath, top_dir, site_prefix)


def check_local_file(endpoint, in_file, dirpath, top_dir, site_prefix):
    # First, split the link up into parts
    if "#" in endpoint:
        filename, anchor = endpoint.split("#",1)
    else:
        filename, anchor = endpoint,""
    if "?" in filename:
        filename, query = filename.split("?", 1)
    else:
        filename, query = filename, ""

    if filename == "":
        # Anchor only; linked file is the current one.
        full_file_path = in_file
    elif filename[0] == "/":
        # Absolute path.
        if site_prefix and filename.startswith(site_prefix):
            logger.debug("Trimming site prefix (%s) from absolute link..." %
                    site_prefix)
            full_file_path = os.path.join(top_dir, filename[len(site_prefix):])
        else:
            # Can't properly test absolute links without knowing where the
            #   server root will be, so skip this
            logger.warning("Skipping absolute link in %s to '%s'" %
                    (in_file, endpoint))
            return (0, False)
    else:
        # Relative path.
        full_file_path = os.path.join(dirpath, filename)

    # Assume index.html if path is a directory.
    # This won't work for certain unusual server configurations or if you're
    # building PHP files or something weird like that
    if os.path.isdir(full_file_path):
        full_file_path = os.path.join(full_file_path, "index.html")

    logger.info("Testing local link in %s to '%s'" %
            (in_file, endpoint))

    # See if the file is even there...
    if not os.path.exists(full_file_path):
        logger.warning("... Broken local link in %s to '%s' (file not found)" %
                (in_file, endpoint))
        return (1, False)

    if not anchor:
        # No anchor to check? Then we're done.
        logger.info("... success.")
        return (1, True)

    # Skip the anchor if this is a configured "ignore anchors" file.
    # This is mostly useful if the linked page has its anchors dynamically
    # populated by JavaScript or something.
    if filename in config["ignore_anchors_in"]:
        logger.warning("Ignoring anchor '%s' in page %s" %
                (endpoint,filename))
        return (0, False)

    targetSoup = getSoup(full_file_path)
    if not targetSoup.find(id=anchor) and not targetSoup.find(
                "a",attrs={"name":anchor}):
        logger.warning("... Broken anchor link in %s to %s" %
                (in_file, endpoint))
        return (1, False)
    else:
        logger.info("... anchor found.")
        return (1, True)


def check_directory(top_dir, offline=False, site_prefix=None):
    """
    Walk the given out_path for .html files and check links in each of them.
    """
    externalCache = []
    broken_links = []
    num_links_checked = 0
    last_checkin = time()
    for dirpath, dirnames, filenames in os.walk(top_dir):
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

            in_file = os.path.join(dirpath, fname)
            if "/node_modules/" in in_file or ".git" in in_file:
                logger.debug("skipping ignored dir: %s" % in_file)
                continue
            if in_file.endswith(".html"):
                soup = getSoup(in_file)
                unparsed_links = check_for_unparsed_reference_links(soup)
                if unparsed_links:
                    logger.warning("Found %d unparsed Markdown reference links: %s" %
                            (len(unparsed_links), "\n... ".join(unparsed_links)))
                    [broken_links.append( (in_file, u) ) for u in unparsed_links]

                # Check <a> tags
                links = soup.find_all('a')
                for link in links:
                    if time() - last_checkin > CHECK_IN_INTERVAL:
                        last_checkin = time()
                        print("... still working (link: %s) ..." % link)
                    if "href" not in link.attrs:
                        #probably an <a name> type anchor, skip
                        continue

                    was_checked, was_good = check_href(link['href'],
                            in_file, dirpath, top_dir, offline,
                            site_prefix=site_prefix)
                    num_links_checked += was_checked
                    if was_checked and not was_good:
                        broken_links.append( (in_file, link['href']) )

                # Check <img> tags
                imgs = soup.find_all('img')
                for img in imgs:
                    if "src" not in img.attrs or not img["src"].strip():
                        logger.warning("Broken image with no src in %s" % in_file)
                        broken_links.append( (in_file, img["src"]) )
                        num_links_checked += 1
                        continue

                    was_checked, was_good = check_href(img["src"],
                            in_file, dirpath, top_dir, offline,
                            site_prefix=site_prefix, hreftype=TYPE_IMAGE)
                    num_links_checked += was_checked
                    if was_checked and not was_good:
                        broken_links.append( (in_file, img["src"]) )

    return broken_links, num_links_checked


def final_retry_links(broken_links):
    """Give the broken remote links a little while to recover in case they're just flaps"""
    broken_remote_links = [ (page,link) for page,link in broken_links
                           if re.match(r"^https?://", link) ]
    if not broken_remote_links:
        logger.info("(no http/https broken links to retry)")
        return

    print("Waiting %d seconds to retry %d broken remote links..."
                % (FINAL_RETRY_DELAY, len(broken_remote_links)))
    start_wait = time()
    elapsed = 0
    while elapsed < FINAL_RETRY_DELAY:
        sleep(CHECK_IN_INTERVAL)
        print("...")
        elapsed = time() - start_wait

    global remote_url_cache
    remote_url_cache = {}
    retry_broken = []
    for page, link in broken_remote_links:
        was_checked, was_good = check_remote_url(link, page)
        if was_good:
            logger.info("Link '%s' in page %s is back online" % (link, page))
            broken_links.remove( (page,link) )
        else:
            logger.info("Link '%s' in page %s is still down." % (link, page))



def main(cli_args):
    if cli_args.dir:
        out_path = cli_args.dir
        logger.debug("Chose top_dir '%s'" % out_path)
    else:
        out_path = config["out_path"]

    if cli_args.prefix:
        if cli_args.prefix[0] != "/":
            logger.error("Invalid --prefix value '%s'. Prefixes must start with '/'."
                    % cli_args.prefix)
            exit(1)
        site_prefix = cli_args.prefix
    elif cli_args.no_prefix:
        site_prefix = None

    broken_links, num_links_checked = check_directory(out_path, cli_args.offline, site_prefix)

    if not cli_args.no_final_retry and not cli_args.offline:
        final_retry_links(broken_links)
        #^ sleeps for FINAL_RETRY_DELAY and then retries remote links
        # Automatically removes from broken_links if they work now

    print("---------------------------------------")
    print("Link check report. %d links checked." % num_links_checked)

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
