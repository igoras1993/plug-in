from abc import abstractmethod
from typing import Protocol


class CoreHostProtocol[T](Protocol):
    subject: type[T]

    @abstractmethod
    def __hash__(self) -> int: ...
