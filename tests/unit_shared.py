# Shared resources for unit testing purposes

class MockCliArgs:
    version=None
    bypass_errors=False
    config="test-config.yml"
    debug=False
    quiet=False
    out_dir=None
    skip_preprocessor=False

from dactyl.config import DactylConfig
from dactyl.target import DactylTarget

class MockDactylConfig(DactylConfig):
    def load_filters(self):
        pass

from jinja2 import Template
mocktemplate = Template("This page is {{ currentpage.name }}.")
mockconfig = MockDactylConfig(MockCliArgs)
mocktarget = DactylTarget(mockconfig, inpages={})
