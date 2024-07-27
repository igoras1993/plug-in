class PlugInException(Exception):
    """
    Base class for all plug-in exceptions
    """


class MissingPluginError(PlugInException):
    pass


class AmbiguousHostError(PlugInException):
    pass
