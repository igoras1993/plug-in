from abc import abstractmethod
from typing import Protocol
from plug_in.proto.pluggable import Pluggable


class CorePlugProtocol[T: Pluggable](Protocol):

    @property
    @abstractmethod
    def provider(self) -> T: ...
