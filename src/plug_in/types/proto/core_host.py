from abc import abstractmethod
from typing import Hashable, Protocol


class CoreHostProtocol[T](Protocol):

    @property
    @abstractmethod
    def subject(self) -> Hashable | type[T]: ...

    @abstractmethod
    def __hash__(self) -> int: ...
