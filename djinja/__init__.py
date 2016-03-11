# -*- coding: utf-8 -*-

""" dj - Docker-Jinja """

# import sys
import os

# init python std logging
import logging
import logging.config

__version__ = "14.07-dev"
__author__ = 'Grokzen <Grokzen@gmail.com>'

# Set to True to have revision from Version Control System in version string
__devel__ = True

log_level_to_string_map = {
    5: "DEBUG",
    4: "INFO",
    3: "WARNING",
    2: "ERROR",
    1: "CRITICAL",
    0: "INFO"
}


def init_logging(log_level):
    """
    Init logging settings with default set to INFO
    """
    level = log_level_to_string_map[log_level]
    message = "%(levelname)s:"

    if level == 'DEBUG':
        message = ' '.join((message, "at %(name)s:%(lineno)s\t"))

    message = ' '.join((message, "%(message)s"))

    logging_conf = {
        "version": 1,
        "root": {
            "level": level,
            "handlers": ["console"]
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            }
        },
        "formatters": {
            "simple": {
                "format": "{}".format(message)
            }
        }
    }

    logging.config.dictConfig(logging_conf)


class FileProcessingError(Exception):
    """
    FileProcessingError exception throwed when file couldn't be read/write
    or its processing fails.
    """


class ExitError(Exception):
    """
    Custom exit error
    """

    def __init__(self, message):
        super(ExitError, self).__init__()
        self.message = message
