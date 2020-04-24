#!/usr/bin/env python3
import unittest
import os

from unit_shared import *

from dactyl.page import DactylPage


class TestDactylPage(unittest.TestCase):
    def test_page_init(self):
        page = DactylPage(mockconfig, {})

    def test_default_filename(self):
        page = DactylPage(mockconfig, {"name":"TeSt1!"})
        assert page.data["html"] == "test1.html"

    def test_frontmatter(self):
        page = DactylPage(mockconfig, {"md":"with-frontmatter.md"})
        assert page.data["desc"] == "This file has Jekyll-style frontmatter"

    def test_preprocess(self):
        page = DactylPage(mockconfig, {"name": "Testpage"})
        page.pp_template = mocktemplate
        page.preprocess({"currentpage":page.data})
        print(page.md)
        assert page.md == "This page is Testpage."

    def test_get_filters_for_page(self):
        # Please note: due to the mock setup for unit testing, this function will always return an empty set.  Refactoring is recommended to verify the remaining functionality for this method.
        page = DactylPage(mockconfig, {})
        assert page.filters() == set()

if __name__ == '__main__':
    unittest.main()
