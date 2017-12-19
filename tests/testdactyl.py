import os
import subprocess
import sys
import unittest

from pathlib import Path

class TestDactyl(unittest.TestCase):

	def setUp(self):
		#Before each test is run, remonve the existing files in out subdirectory.
		output_path = "out"
		output_file_list = os.listdir(output_path)
		for output_file_name in output_file_list:
			os.remove(output_path+"/"+output_file_name)
	
	def test_list(self):
		subprocess.check_output(["dactyl_build","-l"])
	
	def test_generate_html(self):
		subprocess.call(["dactyl_build","--pages","content/gfm-compat.md"])
		assert os.path.isfile("out/index.html")
		assert os.path.isfile("out/gfm-compat.html")
		
	def test_generate_html_from_multiple(self):
		subprocess.call(["dactyl_build","--pages","content/lists-and-codeblocks.md","content/gfm-compat.md"])
		assert os.path.isfile("out/index.html")
		assert os.path.isfile("out/gfm-compat.html")
		assert os.path.isfile("out/lists-and-codeblocks.html")
		
	def test_generate_html_from_config(self):
		subprocess.call(["dactyl_build","-c","dactyl-config.yml","--pages","content/gfm-compat.md"])
		assert os.path.isfile("out/index.html")
		assert os.path.isfile("out/gfm-compat.html")
		
	def test_generate_html_only_one_page(self):
		subprocess.call(["dactyl_build","--only","gfm-compat.html"])
		assert os.path.isfile("out/gfm-compat.html")
		
	def test_generate_pdf(self):
		subprocess.call(["dactyl_build","--pages","content/gfm-compat.md","--pdf","output.pdf"])
		assert os.path.isfile("out/output.pdf")
		
	def test_generate_pdf_from_multiple(self):
		subprocess.call(["dactyl_build","--pages","content/lists-and-codeblocks.md","content/gfm-compat.md","--pdf","output.pdf"])
		assert os.path.isfile("out/output.pdf")
		
	def test_generate_pdf_from_config(self):
		subprocess.call(["dactyl_build","--pdf"])
		assert os.path.isfile("out/Target_with_ALL_THE_EXAMPLES.pdf")
		
	def test_generate_pdf_only_one_page(self):
		subprocess.call(["dactyl_build","-c","dactyl-config.yml","--only","gfm-compat.md","--pdf"])
		assert os.path.isfile("out/Target_with_ALL_THE_EXAMPLES.pdf")
		
	def test_build_from_target(self):
		subprocess.call(["dactyl_build","-t","filter_demos"])
		
if __name__ == '__main__':
	unittest.main()
