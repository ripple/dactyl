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

    def test_generate_html_only_one_page(self):
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

if __name__ == '__main__':
    unittest.main()