#!/usr/bin/env python3

import os
import subprocess
import sys
import unittest

from distutils.dir_util import remove_tree
from pathlib import Path

class TestDactyl(unittest.TestCase):

    def setUp(self):
        self.startdir = os.getcwd()
        # Before each test is run, remove the existing files in out subdirectory.
        try:
            remove_tree("out")
        except FileNotFoundError:
            print("No out/ dir to remove")

    def tearDown(self):
        # After running each test, reset the working directory.
        # (The link checker in particular might change it)
        os.chdir(self.startdir)

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
        assert os.path.isfile("out/Dactyl_A_Heroic_Doc_Tool.pdf")

    def test_generate_pdf_only_one_page(self):
        subprocess.check_call(["dactyl_build","-c","dactyl-config.yml","--only","gfm-compat.md","--pdf"])
        assert os.path.isfile("out/Dactyl_A_Heroic_Doc_Tool.pdf")

    def test_build_from_target(self):
        subprocess.check_call(["dactyl_build","-t","filterdemos"])
        assert os.path.isfile("out/callouts.html")
        assert os.path.isfile("out/xrefs.html")
        assert os.path.isfile("out/buttonize.html")
        assert os.path.isfile("out/badges.html")
        assert os.path.isfile("out/multicode_tabs.html")

    def test_dactyl_link_checker(self):
        # Build some docs to link-check
        subprocess.check_call(["dactyl_build","-t","filterdemos"])
        # exit code 0 means all links were validated successfully.
        subprocess.check_call(["dactyl_link_checker"])

    def test_dactyl_link_checker_with_broken_links(self):
        # Build a doc with a broken link
        subprocess.check_call(["dactyl_build", "--pages", "content/broken-link.md"])
        assert subprocess.call(["dactyl_link_checker"]) != 0

    def test_dactyl_style_checker(self):
        assert subprocess.check_call(["dactyl_style_checker","-t","conditionals"]) == 0

    def test_dactyl_style_checker_with_known_issues(self):
        # Assert that the style checker exits with a non-zero exit code, meaning it has found a styling error.
        assert subprocess.call(["dactyl_style_checker","-t","filterdemos"]) != 0

    def test_elastic_search_default(self):
        subprocess.check_call(["dactyl_build","--es"])
        assert os.path.isfile("out/includes.json")
        assert os.path.isfile("out/conditionals.json")
        assert os.path.isfile("out/lists-and-codeblocks.json")
        assert os.path.isfile("out/gfm-compat.json")
        assert os.path.isfile("out/callouts.json")
        assert os.path.isfile("out/xrefs.json")
        assert os.path.isfile("out/buttonize.json")
        assert os.path.isfile("out/badges.json")
        assert os.path.isfile("out/multicode_tabs.json")

    def test_elastic_search_single_page(self):
        subprocess.check_call(["dactyl_build","--es","--pages","content/gfm-compat.md"])
        assert os.path.isfile("out/gfm-compat.json")

    def test_generate_markdown(self):
        subprocess.check_call(["dactyl_build","--md"])
        assert os.path.isfile("out/includes.md")
        assert os.path.isfile("out/conditionals.md")
        assert os.path.isfile("out/lists-and-codeblocks.md")
        assert os.path.isfile("out/gfm-compat.md")
        assert os.path.isfile("out/filters/callouts.md")
        assert os.path.isfile("out/filters/xrefs.md")
        assert os.path.isfile("out/filters/buttonize.md")
        assert os.path.isfile("out/filters/badges.md")
        assert os.path.isfile("out/filters/multicode_tabs.md")

    def test_generate_markdown_only_one_page(self):
        subprocess.check_call(["dactyl_build","-c","dactyl-config.yml","--only","gfm-compat.md","--md"])
        assert os.path.isfile("out/gfm-compat.md")

    def test_generate_only_one_page_using_md_extension(self):
        subprocess.check_call(["dactyl_build","--only","gfm-compat.md"])
        assert os.path.isfile("out/gfm-compat.html")

    def test_no_vars(self):
        subprocess.check_call(["dactyl_build"])
        assert os.path.isfile("out/cli-vars.html")
        with open("out/cli-vars.html","r") as f:
            text = f.read()
        assert "fooooooo" in text
        assert "``" in text

    def test_vars_inlined(self):
        subprocess.check_call(["dactyl_build","--vars",'{"foo": "FOO VALUE", "bar": "BAR VAL"}'])
        assert os.path.isfile("out/cli-vars.html")
        with open("out/cli-vars.html","r") as f:
            text = f.read()
        assert "``" not in text
        assert "fooooooo" not in text


    def test_vars_file(self):
        subprocess.check_call(["dactyl_build","--vars","../tests/test_vars.json"])
        assert os.path.isfile("out/cli-vars.html")
        with open("out/cli-vars.html","r") as f:
            text = f.read()
        assert "``" not in text
        assert "fooooooo" not in text


    def test_codehilite(self):
        """
        Check that syntax highlighting runs by default.
        """
        subprocess.check_call(["dactyl_build"])
        assert os.path.isfile("out/code-highlighting.html")
        with open("out/code-highlighting.html","r") as f:
            text = f.read()
        assert '<span class="nf">slugify</span>' in text

    def test_nohilight(self):
        """
        Check that syntax highlighting does not run when disabled on a page.
        """
        subprocess.check_call(["dactyl_build"])
        assert os.path.isfile("out/debug.html")
        with open("out/debug.html","r") as f:
            text = f.read()
        assert '<div class="codehilite">' not in text




if __name__ == '__main__':
    if os.path.basename(os.getcwd())=="dactyl":
        os.chdir("examples")
    elif os.path.basename(os.getcwd())=="tests":
        os.chdir("../examples")
    unittest.main()
