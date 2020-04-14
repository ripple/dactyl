################################################################################
# Dactyl watch mode handler class
################################################################################
from watchdog.events import PatternMatchingEventHandler

from dactyl.common import *

class UpdaterHandler(PatternMatchingEventHandler):
    """Updates to pattern-matched files means rendering."""
    def __init__(self, builder):
        self.builder = builder
        patterns = ["*template-*.html",
                    "*.md",
                    "*code_samples/*"]
        PatternMatchingEventHandler.__init__(self, patterns)

    def on_any_event(self, event):
        logger.debug("watch: got event!")
        # Set builder to bypass errors, because a file temporarily not existing
        #  should not cause watch mode to fail
        self.builder.config.bypass_errors=True
        self.builder.build_all()
        logger.info("done rendering")
        builder.copy_static()
