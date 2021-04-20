################################################################################
# Dactyl config-loading module
################################################################################
from dactyl.common import *
from dactyl.version import __version__
from dactyl.page import DactylPage

# Used to import filters.
from importlib import import_module
import importlib.util

# Not the file containing defaults, but the default name of user-specified conf
DEFAULT_CONFIG_FILE = "dactyl-config.yml"

class DactylConfig:
    def __init__(self, cli_args):
        """Load config from commandline arguments"""
        self.cli_args = cli_args
        self.set_logging()

        # Don't even bother loading the config file if it's just a version query
        if cli_args.version:
            print("Dactyl version %s" % __version__)
            exit(0)

        self.bypass_errors = cli_args.bypass_errors
        if self.bypass_errors:
            yaml.allow_duplicate_keys = True

        # Start with the default config, then overwrite later
        self.config = yaml.load(resource_stream(__name__, "default-config.yml"))
        self.filters = {}
        if cli_args.config:
            self.load_config_from_file(cli_args.config)
        else:
            logger.debug("No config file specified, trying ./dactyl-config.yml")
            self.load_config_from_file(DEFAULT_CONFIG_FILE)
        self.check_consistency()
        self.load_filters()

        self.page_cache = []


    def set_logging(self):
        if self.cli_args.debug:
            logger.setLevel(logging.DEBUG)
        elif not self.cli_args.quiet:
            logger.setLevel(logging.INFO)


    def load_config_from_file(self, config_file):
        logger.debug("loading config file %s..." % config_file)
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                loaded_config = yaml.load(f)
        except FileNotFoundError as e:
            if config_file == DEFAULT_CONFIG_FILE:
                logger.info("Couldn't read a config file; using generic config")
                loaded_config = {}
            else:
                traceback.print_tb(e.__traceback__)
                exit("Fatal: Config file '%s' not found"%config_file)
        except ruamel.yaml.parser.ParserError as e:
            traceback.print_tb(e.__traceback__)
            exit("Fatal: Error parsing config file: %s"%e)

        # Migrate legacy config fields
        if "pdf_template" in loaded_config:
            if "default_pdf_template" in loaded_config:
                recoverable_error("Ignoring redundant global config option "+
                               "pdf_template in favor of default_pdf_template",
                               self.bypass_errors)
            else:
                loaded_config["default_pdf_template"] = loaded_config["pdf_template"]
                logger.warning("Deprecation warning: Global field pdf_template has "
                              +"been renamed default_pdf_template")

        self.config.update(loaded_config)

    def check_consistency(self):
        """
        Check a loaded config for common errors, such as unused pages,
        references to non-existing targets, duplicate target names, etc.
        """

        # Look for poorly or redundantly defined targets
        targetnames = set()
        for t in self.config["targets"]:
            if "name" not in t:
                logger.error("Target does not have required 'name' field: %s" % t)
                exit(1)
            elif t["name"] in targetnames:
                recoverable_error("Duplicate target name in config file: '%s'" %
                    t["name"], self.bypass_errors)
            targetnames.add(t["name"])

        # Check page list for consistency
        for page in self.config["pages"]:
            if "targets" not in page:
                if "name" in page:
                    logger.warning("Page %s is not part of any targets." %
                                 page["name"])
                else:
                    logger.warning("Page %s is not part of any targets." % page)
            elif type(page["targets"]) != list:
                recoverable_error(("targets parameter specified incorrectly; "+
                                  "must be a list. Page: %s") % page,
                                  self.bypass_errors)
            elif set(page["targets"]).difference(targetnames):
                recoverable_error("Page '%s' contains undefined targets: %s" %
                            (page, set(page["targets"]).difference(targetnames)),
                            self.bypass_errors)

    def load_pages(self):
        """
        Preload all config'd pages, not just target pages, to get them
        default name values.
        """

        self.page_cache = []
        skip_pp = self.config.get("skip_preprocessor", False)
        for page_data in self.config["pages"]:
            if OPENAPI_SPEC_KEY not in page_data:
                # Try loading page now; but if it fails, that might be OK
                # depending on whether we need the file later.
                try:
                    self.page_cache.append(DactylPage(self, page_data, skip_pp))
                except Exception as e:
                    logger.warning("Couldn't load page '%s': %s"%(page_data,e))
                    self.page_cache.append(NOT_LOADED_PLACEHOLDER)
            else:
                # OpenAPI specs are too much work to load at this time
                self.page_cache.append(OPENAPI_SPEC_PLACEHOLDER)

    def load_filters(self):
        # Figure out which filters we need
        filternames = set(self.config["default_filters"])
        for target in self.config["targets"]:
            if "filters" in target:
                filternames.update(target["filters"])
        for page in self.config["pages"]:
            if "filters" in page:
                filternames.update(page["filters"])

        # Try loading from custom filter paths in order, fall back to built-ins
        for filter_name in filternames:
            self.load_filter(filter_name)

    def load_filter(self, filter_name):
        """
        Load a specific filter, if possible. Can be called "late" when parsing
        frontmatter.
        """
        if filter_name in self.filters.keys():
            return True

        loading_errors = []
        if "filter_paths" in self.config:
            for filter_path in self.config["filter_paths"]:
                try:
                    f_filepath = os.path.join(filter_path, "filter_"+filter_name+".py")

                    ## Requires Python 3.5+
                    spec = importlib.util.spec_from_file_location(
                                "dactyl_filters."+filter_name, f_filepath)
                    self.filters[filter_name] = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(self.filters[filter_name])

                    return True

                except FileNotFoundError as e:
                    loading_errors.append({"Path": filter_path, "Error": repr(e)})
                    logger.debug("Filter %s isn't in path %s\nErr:%s" %
                                (filter_name, filter_path, repr(e)))
                except Exception as e:
                    loading_errors.append({"Path": filter_path, "Error": repr(e)})
                    recoverable_error("Failed to load filter '%s', with error: %s" %
                            (filter_name, repr(e)), self.bypass_errors)

        # Didn't find it yet; try loading it from the Dactyl module
        try:
            self.filters[filter_name] = import_module("dactyl.filter_"+filter_name)
            return True
        except Exception as e:
            loading_errors.append({"Path": "(Dactyl Built-ins)", "Error": repr(e)})
            #logger.debug("Failed to load filter %s. Errors: %s" %
            #    (filter_name, loading_errors))
            recoverable_error("Failed to load filter %s. Errors:\n%s" %
                (filter_name, "\n".join(
                    ["  %s: %s" % (le["Path"], le["Error"])
                        for le in loading_errors])
                ), self.bypass_errors)



    def load_build_options(self):
        """Overwrites some build-specific options based on the CLI params"""
        if self.cli_args.out_dir:
            self.config["out_path"] = self.cli_args.out_dir

        self.config["skip_preprocessor"] = self.cli_args.skip_preprocessor

        if self.cli_args.template_strict_undefined:
            self.config["template_allow_undefined"] = False
        if self.cli_args.pp_strict_undefined:
            self.config["preprocessor_allow_undefined"] = False
        if self.cli_args.legacy_prince:
            self.config["legacy_prince"] = True


    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value

    def __contains__(self, key):
        return self.config.__contains__(key)

    def get(self, key, default=None):
        return self.config.get(key, default)
