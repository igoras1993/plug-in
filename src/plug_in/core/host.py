from dataclasses import dataclass
from typing import Hashable
from plug_in.proto.core_host import CoreHostProtocol


@dataclass(frozen=True)
class CoreHost[Subject](CoreHostProtocol[Subject]):
    _subject: type[Subject]
    _mark: Hashable = None

    @property
    def subject(self) -> type[Subject]:
        return self._subject

    @property
    def mark(self) -> Hashable:
        return self._mark

    def __hash__(self) -> int:
        return hash((self.subject, self.mark))
