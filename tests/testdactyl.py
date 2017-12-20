#!/usr/bin/env python3

import os
import subprocess
import sys
import unittest

from distutils.dir_util import remove_tree
from pathlib import Path

class TestDactyl(unittest.TestCase):

    def setUp(self):
        #Before each test is run, remonve the existing files in out subdirectory.
        try:
	        remove_tree("out")
        except FileNotFoundError:
            print("No out/ dir to remove")

    #P1 tests defined below

    def test_list(self):
        subprocess.check_output(["dactyl_build","-l"])

    def test_generate_html(self):
        subprocess.check_call(["dactyl_build","--pages","content/gfm-compat.md"])
        assert os.path.isfile("out/index.html")
        assert os.path.isfile("out/gfm-compat.html")

    def test_generate_html_from_multiple(self):
        subprocess.check_call(["dactyl_build","--pages","content/lists-and-codeblocks.md","content/gfm-compat.md"])
        assert os.path.isfile("out/index.html")
        assert os.path.isfile("out/gfm-compat.html")
        assert os.path.isfile("out/lists-and-codeblocks.html")

    def test_generate_html_from_config(self):
        subprocess.check_call(["dactyl_build","-c","dactyl-config.yml","--pages","content/gfm-compat.md"])
        assert os.path.isfile("out/index.html")
        assert os.path.isfile("out/gfm-compat.html")

    def test_generate_only_one_page_using_html_extension(self):
        subprocess.check_call(["dactyl_build","--only","gfm-compat.html"])
        assert os.path.isfile("out/gfm-compat.html")

    def test_generate_pdf(self):
        subprocess.check_call(["dactyl_build","--pages","content/gfm-compat.md","--pdf","output.pdf"])
        assert os.path.isfile("out/output.pdf")

    def test_generate_pdf_from_multiple(self):
        subprocess.check_call(["dactyl_build","--pages","content/lists-and-codeblocks.md","content/gfm-compat.md","--pdf","output.pdf"])
        assert os.path.isfile("out/output.pdf")

    def test_generate_pdf_from_config(self):
        subprocess.check_call(["dactyl_build","--pdf"])
        assert os.path.isfile("out/Target_with_ALL_THE_EXAMPLES.pdf")

    def test_generate_pdf_only_one_page(self):
        subprocess.check_call(["dactyl_build","-c","dactyl-config.yml","--only","gfm-compat.md","--pdf"])
        assert os.path.isfile("out/Target_with_ALL_THE_EXAMPLES.pdf")

    def test_build_from_target(self):
        subprocess.check_call(["dactyl_build","-t","filterdemos"])
        assert os.path.isfile("out/filter-examples-callouts.html")
        assert os.path.isfile("out/filter-examples-xrefs.html")
        assert os.path.isfile("out/filter-examples-buttonize.html")
        assert os.path.isfile("out/filter-examples-badges.html")
        assert os.path.isfile("out/filter-examples-include_code.html")
        assert os.path.isfile("out/filter-examples-multicode_tabs.html")

    #P2 tests defined below

    def test_generate_markdown(self):
        subprocess.check_call(["dactyl_build","--md"])
        assert os.path.isfile("out/includes.md")
        assert os.path.isfile("out/conditionals.md")
        assert os.path.isfile("out/lists-and-codeblocks.md")
        assert os.path.isfile("out/gfm-compat.md")
        assert os.path.isfile("out/filter-examples/callouts.md")
        assert os.path.isfile("out/filter-examples/xrefs.md")
        assert os.path.isfile("out/filter-examples/buttonize.md")
        assert os.path.isfile("out/filter-examples/badges.md")
        assert os.path.isfile("out/filter-examples/include_code.md")
        assert os.path.isfile("out/filter-examples/multicode_tabs.md")

    def test_generate_markdown_only_one_page(self):
        subprocess.check_call(["dactyl_build","-c","dactyl-config.yml","--only","gfm-compat.md","--md"])
        assert os.path.isfile("out/gfm-compat.md")

    def test_generate_only_one_page_using_md_extension(self):
        subprocess.check_call(["dactyl_build","--only","gfm-compat.md"])
        assert os.path.isfile("out/gfm-compat.html")

    def test_preprocessing_command_line(self):
        subprocess.check_call(["dactyl_build","--vars","{\"target\":\"filterdemos\"}"])
        assert os.path.isfile("out/filter-examples-callouts.html")
        assert os.path.isfile("out/filter-examples-xrefs.html")
        assert os.path.isfile("out/filter-examples-buttonize.html")
        assert os.path.isfile("out/filter-examples-badges.html")
        assert os.path.isfile("out/filter-examples-include_code.html")
        assert os.path.isfile("out/filter-examples-multicode_tabs.html")

    def test_preprocessing_json(self):
        subprocess.check_call(["dactyl_build","--vars","../tests/test_preprocessing.json"])
        assert os.path.isfile("out/filter-examples-callouts.html")
        assert os.path.isfile("out/filter-examples-xrefs.html")
        assert os.path.isfile("out/filter-examples-buttonize.html")
        assert os.path.isfile("out/filter-examples-badges.html")
        assert os.path.isfile("out/filter-examples-include_code.html")
        assert os.path.isfile("out/filter-examples-multicode_tabs.html")

if __name__ == '__main__':
    if os.path.basename(os.getcwd())=="dactyl":
        os.chdir("examples")
    elif os.path.split(os.getcwd())=="tests":
        os.chdir("../examples")
    unittest.main()
