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


# TODO: To be removed
class InvalidHostSubject(CoreError):
    pass


class IoCError(PlugInError):
    """
    Base class for all exceptions raised by ioc module
    """

    pass


class ObjectNotSupported(IoCError):
    pass


class EmptyHostAnnotationError(IoCError):
    pass


class UnexpectedForwardRefError(IoCError):
    pass


class RouterAlreadyMountedError(IoCError):
    pass


class MissingMountError(IoCError):
    pass


class MissingRouteError(IoCError):
    pass


class BootError(PlugInError):
    """
    Base class for all exceptions raised in boot module
    """


class ConfigError(BootError):
    pass
