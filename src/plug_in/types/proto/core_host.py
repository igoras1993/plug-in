from abc import abstractmethod
from typing import Any, Protocol


class CoreHostProtocol[T](Protocol):

    @property
    @abstractmethod
    def subject(self) -> type[T] | Any: ...

    @abstractmethod
    def __hash__(self) -> int: ...
