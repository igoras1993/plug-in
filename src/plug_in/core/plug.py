from dataclasses import dataclass

from plug_in.proto.pluggable import Pluggable


@dataclass(frozen=True)
class CorePlug[T: Pluggable]:
    provider: T
