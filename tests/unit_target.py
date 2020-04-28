#!/usr/bin/env python3
import unittest
import os

from unit_shared import *

from dactyl.target import DactylTarget


class TestDactylPage(unittest.TestCase):
    def test_target_from_pages(self):
        files=["../examples/content/filter-examples/badges.md","../examples/content/filter-examples/buttonize.md"]
        t = DactylTarget(config=mockconfig, inpages=files)
        t.load_pages()



if __name__ == '__main__':
    unittest.main()
