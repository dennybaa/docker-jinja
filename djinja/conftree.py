# -*- coding: utf-8 -*-

# python std lib
import os
import json
import logging
import sys
import yaml

Log = logging.getLogger(__name__)


class ConfTree(object):

    class LoadError(Exception):
        """Config file load error exception
        """

    def __init__(self, config_files=None):
        self.config_files = config_files if config_files else []
        if not isinstance(self.config_files, list):
            raise Exception("config_files must be a list of items that can be read from FS")
        self.tree = {}

    def load_config_files(self, **kwargs):
        """ Loads a bunch of config files, accepts onload_fail keyword argument.
            onload_fail can be used to skip failure during default config file load.
        """
        for config_file in self.config_files:
            onload_fail = kwargs.get('onload_fail')
            try:
                self.load_config_file(config_file)
            except ConfTree.LoadError as e:
                if not onload_fail:
                    continue
                Log.error("Config load failed - %s", config_file)
                Log.error("%s", e.args[0])
                sys.exit(1)

    def load_config_file(self, config_file):
        """ Load YAML or JSON from given config file and merge data tree
        """
        try:
            with open(config_file, "r") as stream:
                data = stream.read()
        except (OSError, IOError) as e:
            raise ConfTree.LoadError(e)

        # Determine file type by extension
        extension = os.path.splitext(config_file)[-1].lower()
        if extension in ('.yaml', '.yml'):
            load_function = yaml.load
        elif extension in ('.json'):
            load_function = json.loads
        else:
            Log.error("Unsupported config file type, please provide correct file "
                      "with one of the following extentions: .yml, .yaml, .json")
            sys.exit(1)

        # Generic exception catch because several exceptions are raised as
        # well as newer python raises different exception (at least py35)
        try:
            data_tree = load_function(data)
        except (yaml.YAMLError, Exception) as e:
            raise ConfTree.LoadError(e)

        Log.debug("Loading data from config file `%s'", config_file)

        # If data was loaded into python datastructure then load it into the config tree
        self.merge_data_tree(data_tree)

    def merge_data_tree(self, data_tree):
        if not isinstance(data_tree, dict):
            raise Exception("Data tree to merge must be of dict type")

        self.tree.update(data_tree)

    def get_tree(self):
        return self.tree

    def get(self, key, default=None):
        return self.tree.get(key, default)
