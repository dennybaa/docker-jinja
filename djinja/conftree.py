# -*- coding: utf-8 -*-

# python std lib
import os
import json
import logging
import sys
import yaml

from djinja import FileProcessingError

Log = logging.getLogger(__name__)


class ConfTree(object):

    def __init__(self):
        self.tree = {}

    def load_config_files(self, config_files, **kwargs):
        """
        Loads a bunch of config files, accepts onload_fail keyword argument.
        onload_fail can be used to skip failure during default config file load.
        """
        if not isinstance(config_files, list):
            raise TypeError("config_files must be a list")

        onload_fail = kwargs.get('onload_fail', True)
        for config_file in config_files:
            try:
                self.load_config_file(config_file)
            except FileProcessingError as e:
                if not onload_fail:
                    continue
                Log.error("Config load failed - %s", config_file)
                Log.error("%s", e.args[0])
                sys.exit("config not loaded")

    def load_config_file(self, config_file):
        """
        Load YAML or JSON from given config file and merge data tree
        """
        try:
            with open(config_file, "r") as stream:
                data = stream.read()
        except (OSError, IOError) as e:
            raise FileProcessingError(e)

        # JSON is a subset of YAML, so we iterate through load functions to read
        # the data rather than trying to probe data type.
        yaml_error = None
        for load_function in (yaml.load, json.loads):
            try:
                data_tree = load_function(data)
                break
            except yaml.YAMLError as e:
                # try to load using json loader
                yaml_error = e
                continue
            except Exception as e:
                # Both loaders have failed or other error occured,
                # raise more descriptive yaml error.
                raise FileProcessingError(yaml_error or e)

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
