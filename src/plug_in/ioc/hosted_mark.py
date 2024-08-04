from typing import Hashable
from plug_in.types.proto.hosted_mark import HostedMarkProtocol


class HostedMark(HostedMarkProtocol):
    """
    Marker for a hosted callable argument. You can provide additional marks
    to distinguish mark further. By default, mark is composed from the annotation.
    """

    def __init__(self, *marks: Hashable) -> None:
        self._marks = marks

    @property
    def marks(self) -> tuple[Hashable, ...]:
        return self._marks
