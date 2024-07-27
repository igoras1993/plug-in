from typing import Protocol
from plug_in.proto.pluggable import Pluggable


class CorePlugProtocol[T: Pluggable](Protocol):
    provider: T
