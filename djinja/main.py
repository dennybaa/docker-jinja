# -*- coding: utf-8 -*-

# python std lib
import os
import sys
import logging

from jinja2 import Template

from djinja import contrib, FileProcessingError
from djinja.conftree import ConfTree

Log = logging.getLogger(__name__)


class Core(object):

    def __init__(self, cli_args):
        """
        :param cli_args: Arguments structure from docopt.
        """
        self.args = cli_args
        # Context hash to store context for template environment
        self.environment_vars = {
            "globals": {},
            "filters": {},
        }
        Log.debug("Cli args: %s", self.args)

        self.default_config_files = [
            os.path.expanduser("~/.dj.yaml"),
            os.path.expanduser("~/.dj.json"),
            os.path.join(os.getcwd(), ".dj.yaml"),
            os.path.join(os.getcwd(), ".dj.json"),
        ]

        Log.debug("DEFAULT_CONFIG_FILES: %s", self.default_config_files)

        # Load all config files into unified config tree, don't fail on load since
        # default config files might not exist.
        Log.debug("Building config...")
        self.config = ConfTree()
        self.config.load_config_files(self.default_config_files, onload_fail=False)
        Log.debug("Config building is done")

    def parse_env_vars(self):
        """
        Parse all variables inputed from cli and add them to global config
        """
        _vars = {}
        for var in self.args.get("--env", []):
            s = var.split("=")
            if len(s) != 2 or (len(s[0]) == 0 or len(s[1]) == 0):
                raise Exception("var '{0}' is not of format 'key=value'".format(var))
            _vars[s[0]] = s[1]
        self.config.merge_data_tree(_vars)

    def load_user_specefied_config_file(self):
        """
        Loads any config file specefied by user from commandline.

        It should only be possible to load one user specefied config file.
        """
        user_specefied_config_files = self.args.get("--config", [])
        self.config.load_config_files(user_specefied_config_files)

    def handle_data_sources(self):
        """
        Take all specefied datasources from cli and merge with any in config then
        try to import all datasources and raise exception if it fails.
        """
        ds = self.args.get("--datasource", [])
        ds.extend(self.config.tree.get("datasources", []))

        # Find all contrib files and add them to datasources to load
        ds.extend([getattr(contrib, c).__file__ for c in dir(contrib) if not c.startswith("_")])

        # Load all specefied datasource files
        for datasource_file in ds:
            p = os.path.dirname(datasource_file)
            try:
                # Append to sys path so we can import the python file
                sys.path.insert(0, p)
                datasource_path = os.path.splitext(os.path.basename(datasource_file))[0]
                Log.debug("%s", datasource_path)

                # Import python file but do nothing with it because all datasources should
                #  handle and register themself to jinja.
                i = __import__(datasource_path)

                # Auto load all filters and global functions if they follow name pattern
                for method in dir(i):
                    if method.lower().startswith("_filter_"):
                        method_name = method.replace("_filter_", "")
                        self.attach_function("filters", getattr(i, method), method_name)
                    elif method.lower().startswith("_global_"):
                        method_name = method.replace("_global_", "")
                        self.attach_function("globals", getattr(i, method), method_name)
            except ImportError as ie:
                Log.error("Unable to import - %s", datasource_file)
                Log.error("%s", ie)
                sys.exit(1)
            finally:
                # Clean out path to avoid issue
                sys.path.remove(p)

    def handle_dockerfile(self):
        """
        Handle errors and pass the invocation to process_dockerfile.
        """
        try:
            self.process_dockerfile()
        except FileProcessingError as e:
            Log.error("Couldn't process - %s", e.args[1])
            Log.error("%s", e.args[0])
            sys.exit(1)

    def process_dockerfile(self):
        """
        Read source dockerfile --> Render with jinja --> Write to outfile
        """
        source_dockerfile = self.args["--dockerfile"]
        outputfile = self.args["--outfile"]

        try:
            with open(source_dockerfile, "r") as stream:
                Log.info("Reading source file...")
                # we'll render a file, so we should preserve newlines as they are
                template = Template(stream.read(), keep_trailing_newline=True)
        except (OSError, IOError) as e:
            raise FileProcessingError(e, source_dockerfile)

        # Update the jinja environment with all custom functions & filters
        self.update_template_env(template.environment)

        context = self.config.get_tree()
        Log.debug("context: %s", context)

        Log.info("rendering Dockerfile...")
        out_data = template.render(**context)

        Log.debug("Data to be written to the output file\n*****\n%s*****", out_data)

        try:
            with open(outputfile, "w") as stream:
                Log.info("Writing to outfile...")
                stream.write(out_data)
        except (OSError, IOError) as e:
            raise FileProcessingError(e, outputfile)

    def attach_function(self, attr, func, name):
        """
        Add function to environment context hash so it can be used within Jinja
        """
        Log.debug("Attaching function to jinja : %s : %s : %s", attr, func.__name__, name)
        self.environment_vars[attr][name] = func
        return func

    def update_template_env(self, template_env):
        """
        Given a jinja environment, update it with third party
        collected environment extensions.
        """
        for n in ('globals', 'filters'):
            env_vars = getattr(template_env, n)
            env_vars.update(self.environment_vars[n])

    def main(self):
        """
        Runs all logic in application
        """
        self.load_user_specefied_config_file()

        self.parse_env_vars()

        self.handle_data_sources()

        self.handle_dockerfile()

        Log.info("Done... Bye :]")
