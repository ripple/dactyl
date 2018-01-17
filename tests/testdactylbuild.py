#!/usr/bin/env python3

import argparse
import sys
import unittest

from dactyl import dactyl_build

class MockCliArgs:
    version=None
    bypass_errors=False
    config="test-config.yml"
    debug=False
    quiet=False
    out_dir=None
    skip_preprocessor=False

from dactyl.config import DactylConfig

class MockDactylConfig(DactylConfig):
    def load_filters(self):
        pass

try:
    dc = MockDactylConfig(MockCliArgs)
    dactyl_build.config = dc
except ModuleNotFoundError:
    print("Oh no!  A module wasn't found, and this statement is extremely unhelpful!")

from jinja2 import Template
mocktemplate = Template("This page is {{ currentpage.name }}.")

class TestDactylBuild(unittest.TestCase):

    #P1 tests listed below

    def test_default_pdf_name(self):
        test_result = dactyl_build.default_pdf_name("conditionals")
        assert test_result == "Conditional_Text_Target.pdf"

    def test_get_target(self):
        assert dactyl_build.get_target(None) == {"name": "test_target"}
        assert dactyl_build.get_target("conditionals") == {"name": "conditionals", "display_name": "Conditional Text Target"}
        assert dactyl_build.get_target({"name": "runtime_target"}) == {"name": "runtime_target"}

    def test_get_pages(self):
        assert dactyl_build.get_pages(dactyl_build.get_target("test_target"), False) == [{'name': 'filters_page', 'category': 'Filters', 'filters': ['mock_filter'], 'targets': ['test_target'], 'html': 'filters_page.html'}, {'name': 'test_page', 'category': 'Tests', 'html': 'test.html', 'targets': ['test_target']}]
    
    def test_get_filters_for_page(self):
        # Please note: due to the mock setup for unit testing, this function will always return an empty set.  Refactoring is recommended to verify the remaining functionality for this method.
        assert dactyl_build.get_filters_for_page(dactyl_build.config["pages"][0], dactyl_build.get_target("filters_target")) == set()
 
    def test_parse_markdown(self):
        output = dactyl_build.parse_markdown(dactyl_build.config["pages"][2], "filters_target", dactyl_build.config["pages"], [], "html", "", False)

    def test_render_page(self):
        output = dactyl_build.render_page(dactyl_build.config["pages"][2], "filters_target", dactyl_build.config["pages"], "html", "", [], mocktemplate, False)
        assert output == "This page is md_test."

    #P2 tests listed below

    def test_target_slug_name(self):
        assert dactyl_build.target_slug_name("conditionals") == "Conditional_Text_Target"

    def test_make_adhoc_target(self):
        assert dactyl_build.make_adhoc_target(["gfm-compat.md"]) == {'name': '__ADHOC__', 'display_name': 'GitHub Markdown Compatibility'}

    def test_get_categories(self):
        assert dactyl_build.get_categories(dactyl_build.config["pages"]) == ['Filters', 'Tests', 'Markdown']

if __name__ == '__main__':
    unittest.main()