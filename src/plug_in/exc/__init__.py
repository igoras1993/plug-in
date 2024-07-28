class PlugInError(Exception):
    """
    Base class for all plug-in exceptions
    """

    pass


class CoreError(PlugInError):
    """
    Base class for all exceptions raised in core
    """

    pass


class MissingPluginError(CoreError):
    pass


class AmbiguousHostError(CoreError):
    pass


class IoCError(PlugInError):
    """
    Base class for all exceptions raised by ioc module
    """

    pass


class RouterAlreadyMountedError(IoCError):
    pass


class MissingMountError(IoCError):
    pass
