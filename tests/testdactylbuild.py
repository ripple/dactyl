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
    out_dir=None # might need to customize this? Not sure
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

from mockfilter import MockFilter

#test_filter = MockFilter()
#dactyl_build.config["filters"] = {}
#dactyl_build.config["filters"]["mock_filter"] = test_filter

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
        assert dactyl_build.get_pages(dactyl_build.get_target("test_target"), False) == [{"name": "test_page", "html": "test.html", "targets": ["test_target"]}]
    
    def test_get_filters_for_page(self):
        assert dactyl_build.get_filters_for_page(dactyl_build.config["pages"][0], dactyl_build.get_target("filters_target")) == {"mock_filter"}
 
    def test_parse_markdown(self):
        print(dactyl_build.config)
        output = dactyl_build.parse_markdown(dactyl_build.config["pages"][2], "filters_target", dactyl_build.config["pages"], [], "html", "", False)

    def test_render_page(self):
        output = dactyl_build.render_page(dactyl_build.config["pages"][2], "filters_target", dactyl_build.config["pages"], "html", "", [], mocktemplate, False)

    #P2 tests listed below


if __name__ == '__main__':
    unittest.main()