from collections import defaultdict

import requests
from jinja2 import BaseLoader, FileSystemLoader, TemplateNotFound, Template
from urllib.parse import urlparse
from dactyl.common import *

class FrontMatterRemoteLoader(BaseLoader):
    def __init__(self):
        self.baseurl = None
        self.fm_map = defaultdict(dict) # Save frontmatter here, if any
        self.twolines = {} # Save first two lines so we can try guessing titles

    def get_source(self, environment, template):
        """Fetch a remote markdown file and return its contents"""
        parsed_url = urlparse(template)

        # save this base URL if it's new; that way we can try to let remote
        # templates inherit from other templates at related URLs
        if parsed_url.scheme or (self.baseurl is None):
            base_path = os.path.dirname(parsed_url.path)
            self.baseurl = (
                parsed_url[0],
                parsed_url[1],
                base_path,
                parsed_url[3],
                parsed_url[4],
                parsed_url[5],
            )
        # if we're at read_markdown_remote without a scheme, it's probably a remote
        # template trying to import another template, so let's assume it's from the
        # base path of the imported template
        if not parsed_url.scheme:
            url = os.path.join(self.baseurl, template)
        else:
            url = template

        response = requests.get(url)
        if response.status_code == 200:
            text, frontmatter = parse_frontmatter(response.text)
            self.fm_map[template] = frontmatter
            self.twolines[template] = text.split("\n", 2)[:2]
            return text, url, None
        else:
            raise TemplateNotFound(template)

class FrontMatterFSLoader(FileSystemLoader):
    def __init__(self, searchpath, encoding='utf-8', followlinks=False):
        super().__init__(searchpath, encoding, followlinks)
        self.fm_map = defaultdict(dict)

    def get_source(self, environment, template):
        text, filename, uptodate = super().get_source(environment, template)
        text, frontmatter = parse_frontmatter(text)
        self.fm_map[template] = frontmatter
        self.twolines[template] = text.split("\n", 2)[:2]
        return text, filename, uptodate
