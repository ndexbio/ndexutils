# -*- coding: utf-8 -*-


class NDExUtilError(Exception):
    """
    Base exception for all errors originating from ndexutil
    """
    pass


class NDExUtilSaveNetworkError(Exception):
    """
    Error saving network to NDEx
    """
    pass

class ConfigError(NDExUtilError):
    """
    Raised if there is an error with configuration file
    """
    pass
