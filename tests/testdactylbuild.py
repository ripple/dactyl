#!/usr/bin/env python3

import unittest

from dactyl import dactyl_build

class TestDactylBuild(unittest.TestCase):
    dactyl_build.config = {"pdf_filename_fields": ["display_name"], 
	                       "pdf_filename_separator": "\'-\'",
                           "default_filters": ["this_is_a_default"],						   
                           "targets": [{"name": "test_target"}, {"name": "filters_target", "filters": ["target_filter"]}, {"name": "conditionals", "display_name": "Conditional Text Target"}],
                           "pages": [{"name": "filters_page", "filters": ["page_filter"]}]}

    def test_default_pdf_name(self):
        test_result = dactyl_build.default_pdf_name("conditionals")
        assert test_result == "Conditional_Text_Target.pdf"

    def test_get_target(self):
        assert dactyl_build.get_target(None) == {"name": "test_target"}
        assert dactyl_build.get_target("conditionals") == {"name": "conditionals", "display_name": "Conditional Text Target"}
        assert dactyl_build.get_target({"name": "runtime_target"}) == {"name": "runtime_target"}
    
    def test_get_filters_for_page(self):
        assert dactyl_build.get_filters_for_page(dactyl_build.config["pages"][0], dactyl_build.get_target("filters_target")) == {"this_is_a_default", "page_filter", "target_filter"}
    
    

if __name__ == '__main__':
    unittest.main()