################################################################################
# Dactyl config-loading module
################################################################################
from dactyl.common import *

# Used to import filters.
from importlib import import_module
# import importlib.util
from importlib.machinery import SourceFileLoader

# Used for pulling in the default config file
from pkg_resources import resource_stream

# Not the file containing defaults, but the default name of user-specified conf
DEFAULT_CONFIG_FILE = "dactyl-config.yml"

class DactylConfig:
    def __init__(self, config_file=DEFAULT_CONFIG_FILE, bypass_errors=False):
        """Reload config from a YAML file."""

        # Start with the default config, then overwrite later
        self.config = yaml.load(resource_stream(__name__, "default-config.yml"))
        self.filters = {}
        self.load_config_from_file(config_file, bypass_errors)
        self.load_filters()

    def load_config_from_file(self, config_file, bypass_errors=False):
        logger.debug("loading config file %s..." % config_file)
        try:
            with open(config_file, "r") as f:
                loaded_config = yaml.load(f)
        except FileNotFoundError as e:
            if config_file == DEFAULT_CONFIG_FILE:
                logger.info("Couldn't read a config file; using generic config")
                loaded_config = {}
            else:
                traceback.print_tb(e.__traceback__)
                exit("Fatal: Config file '%s' not found"%config_file)
        except yaml.parser.ParserError as e:
            traceback.print_tb(e.__traceback__)
            exit("Fatal: Error parsing config file: %s"%e)

        # Migrate legacy config fields
        if "pdf_template" in loaded_config:
            if "default_pdf_template" in loaded_config:
                recoverable_error("Ignoring redundant global config option "+
                               "pdf_template in favor of default_pdf_template",
                               bypass_errors)
            else:
                loaded_config["default_pdf_template"] = loaded_config["pdf_template"]
                logger.warning("Deprecation warning: Global field pdf_template has "
                              +"been renamed default_pdf_template")

        self.config.update(loaded_config)

        targetnames = set()
        for t in self.config["targets"]:
            if "name" not in t:
                logger.error("Target does not have required 'name' field: %s" % t)
                exit(1)
            elif t["name"] in targetnames:
                recoverable_error("Duplicate target name in config file: '%s'" %
                    t["name"], bypass_errors)
            targetnames.add(t["name"])

        # Check page list for consistency and provide default values
        for page in self.config["pages"]:
            if "targets" not in page:
                if "name" in page:
                    logger.warning("Page %s is not part of any targets." %
                                 page["name"])
                else:
                    logger.warning("Page %s is not part of any targets." % page)
            elif type(page["targets"]) != list:
                recoverable_error(("targets parameter specified incorrectly; "+
                                  "must be a list. Page: %s") % page, bypass_errors)
            elif set(page["targets"]).difference(targetnames):
                recoverable_error("Page '%s' contains undefined targets: %s" %
                            (page, set(page["targets"]).difference(targetnames)),
                            bypass_errors)
            if "md" in page and "name" not in page:
                logger.debug("Guessing page name for page %s" % page)
                page_path = os.path.join(self.config["content_path"], page["md"])
                page["name"] = guess_title_from_md_file(page_path)

            if "html" not in page:
                page["html"] = self.html_filename_from(page)


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
            filter_loaded = False
            loading_errors = []
            if "filter_paths" in self.config:
                for filter_path in self.config["filter_paths"]:
                    try:
                        f_filepath = os.path.join(filter_path, "filter_"+filter_name+".py")

                        ## Requires Python 3.5+
                        # spec = importlib.util.spec_from_file_location(
                        #             "dactyl_filters."+filter_name, f_filepath)
                        # self.filters[filter_name] = importlib.util.module_from_spec(spec)
                        # spec.loader.exec_module(self.filters[filter_name])

                        ## Compatible with Python 3.4 and 3.3, probably
                        loader = SourceFileLoader("dactyl_filters", f_filepath)
                        self.filters[filter_name] = loader.load_module()

                        filter_loaded = True
                        break
                    except Exception as e:
                        loading_errors.append(e)
                        logger.debug("Filter %s isn't in path %s\nErr:%s" %
                                    (filter_name, filter_path, e))

            if not filter_loaded:
                # Load from the Dactyl module
                try:
                    self.filters[filter_name] = import_module("dactyl.filter_"+filter_name)
                except Exception as e:
                    loading_errors.append(e)
                    logger.debug("Failed to load filter %s. Errors: %s" %
                        (filter_name, loading_errors))


    def html_filename_from(self, page):
        """Take a page definition and choose a reasonable HTML filename for it."""
        if "md" in page:
            new_filename = re.sub(r"[.]md$", ".html", page["md"])
            if self.config.get("flatten_default_html_paths", True):
                return new_filename.replace(os.sep, "-")
            else:
                return new_filename
        elif "name" in page:
            return slugify(page["name"]).lower()+".html"
        else:
            new_filename = str(time.time()).replace(".", "-")+".html"
            logger.debug("Generated filename '%s' for page: %s" %
                        (new_filename, page))
            return new_filename


    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value

    def __contains__(self, key):
        return self.config.__contains__(key)

    def get(self, key, default=None):
        return self.config.get(key, default)
