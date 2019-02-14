# -*- coding: utf-8 -*-

import os
import configparser
import logging
from ndexutil.exceptions import ConfigError


class NDExUtilConfig(object):
    """
    Instances provide configuration information
    stored for ndexutil package in user's home directory
    """
    CONFIG_FILE = '.ndexutils.conf'

    USER = 'user'
    PASSWORD = 'password'
    SERVER = 'server'

    def __init__(self, conf_file=None):
        """Constructor
        """
        self._conf_file = conf_file
        self._homedir = os.path.expanduser('~')

    def set_home_directory(self, path):
        """Sets alternate home directory
        :param path: Alternate home directory path
        """
        if path is not None and '~' in path:
            self._homedir = os.path.expanduser(path)
        else:
            self._homedir = path

    def get_home_directory(self):
        """
        Returns home directory path
        :returns: Path to home directory
        """
        return self._homedir

    def get_config_file(self):
        """
        Gets config file
        :return:
        """
        if self._conf_file is None:
            return os.path.join(self._homedir, NDExUtilConfig.CONFIG_FILE)
        return self._conf_file

    def get_config(self):
        """
        Gets configparser object loaded with data from
        :return:
        """
        if not os.path.isfile(self.get_config_file()):
            raise ConfigError('No configuration file found')

        parser = configparser.ConfigParser()
        parser.read(self.get_config_file())
        return parser