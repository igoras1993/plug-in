from dataclasses import dataclass
from typing import Hashable
from plug_in.proto.core_host import CoreHostProtocol


@dataclass(frozen=True)
class CoreHost[Subject](CoreHostProtocol[Subject]):
    subject: type[Subject]
    mark: Hashable = None

    def __hash__(self) -> int:
        return hash((self.subject, self.mark))
