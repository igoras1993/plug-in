from abc import abstractmethod
from typing import Protocol


class CoreHostProtocol[T](Protocol):

    @property
    @abstractmethod
    def subject(self) -> type[T]: ...

    @abstractmethod
    def __hash__(self) -> int: ...
