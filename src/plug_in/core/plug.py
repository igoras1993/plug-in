from dataclasses import dataclass

from plug_in.types.proto.core_plug import CorePlugProtocol
from plug_in.types.proto.pluggable import Pluggable


@dataclass(frozen=True)
class CorePlug[T: Pluggable](CorePlugProtocol):
    _provider: T

    @property
    def provider(self) -> T:
        return self._provider
