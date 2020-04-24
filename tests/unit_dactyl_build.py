#!/usr/bin/env python3

import argparse
import sys
import unittest

from unit_shared import *

from dactyl.dactyl_build import DactylBuilder



class TestDactylBuild(unittest.TestCase):
    def test_init(self):
        d = DactylBuilder(mocktarget, mockconfig)

    def test_default_copy_static(self):
        d = DactylBuilder(mocktarget, mockconfig)
        assert d.copy_content_static == True
        assert d.copy_template_static == True

    ## TODO: a bunch of these tests are for things that have moved to page.py or target.py
    #### Tests to refactor below here.
    ## TODO: this functionality was moved to target.py
    # def test_default_pdf_name(self):
    #     test_result = dactyl_build.default_pdf_name("conditionals")
    #     assert test_result == "Conditional_Text_Target.pdf"
    #
    # def test_get_target(self):
    #     assert dactyl_build.get_target(None) == {"name": "test_target"}
    #     assert dactyl_build.get_target("conditionals") == {"name": "conditionals", "display_name": "Conditional Text Target"}
    #     assert dactyl_build.get_target({"name": "runtime_target"}) == {"name": "runtime_target"}
    #
    # def test_get_pages(self):
    #     assert dactyl_build.get_pages(dactyl_build.get_target("test_target"), False) == [{'name': 'filters_page', 'category': 'Filters', 'filters': ['mock_filter'], 'targets': ['test_target'], 'html': 'filters_page.html'}, {'name': 'test_page', 'category': 'Tests', 'html': 'test.html', 'targets': ['test_target']}]
    #
    #
    #
    # def test_parse_markdown(self):
    #     output = dactyl_build.parse_markdown(dactyl_build.config["pages"][2], "filters_target", dactyl_build.config["pages"], [], "html", "", False)
    #
    # def test_render_page(self):
    #     output = dactyl_build.render_page(dactyl_build.config["pages"][2], "filters_target", dactyl_build.config["pages"], "html", "", [], mocktemplate, False)
    #     assert output == "This page is md_test."
    #
    # def test_target_slug_name(self):
    #     print("target_slug_name is", dactyl_build.target_slug_name("conditionals"))
    #     fields_to_use = ["display_name"]
    #     sep = ","
    #     assert dactyl_build.target_slug_name("conditionals", fields_to_use, sep) == "Conditional_Text_Target"
    #
    # def test_es_index_name(self):
    #     test_target = dactyl_build.get_target("es_index_test_target")
    #     dactyl_build.config["es_index_fields"] = ["foo1", "foo2"]
    #     dactyl_build.config["es_index_separator"] = "--"
    #     assert dactyl_build.es_index_name(test_target) == "Foo_Value_1--Foo_Value_TWOOOO"
    #
    # def test_make_adhoc_target(self):
    #     assert dactyl_build.make_adhoc_target(["gfm-compat.md"]) == {'name': '__ADHOC__', 'display_name': 'GitHub Markdown Compatibility'}
    #
    # def test_get_categories(self):
    #     assert dactyl_build.get_categories(dactyl_build.config["pages"]) == ['Filters', 'Tests', 'Markdown']

if __name__ == '__main__':
    unittest.main()
