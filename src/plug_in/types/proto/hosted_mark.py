from abc import abstractmethod
from typing import Hashable, Protocol


class HostedMarkProtocol(Protocol):
    """
    Marker for a hosted callable argument. You can provide additional marks
    to distinguish mark further. By default, mark is composed from the annotation.
    """

    @property
    @abstractmethod
    def marks(self) -> tuple[Hashable, ...]: ...

    # def evaluate_corresponding_host(self, callable: Callable) -> CoreHostProtocol:
    #     """
    #     Given a callable, search for annotation for this mark in its signature,
    #     and return corresponding [.CoreHostProtocol][] object.

    #     Raises:
    #         `LookupError`: If parameter was not found in callable
    #         `TypeError`: if some type object is not supported
    #         `ValueError`: if no signature can be retrieved
    #         [.UnexpectedForwardRefError][]: When evaluation of postponed
    #             annotations cant be performed
    #         [.EmptyHostAnnotationError][]: When there is no annotation for that
    #             host marker

    #     """
    #     ...
