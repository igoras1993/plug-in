from dataclasses import dataclass
from typing import Hashable
from plug_in.types.proto.core_host import CoreHostProtocol


@dataclass(frozen=True)
class CoreHost[Subject](CoreHostProtocol[Subject]):
    """
    Create a host object. Hosts are used as a keys to lookup plugins in
    registries.

    """

    _subject: Hashable | type[Subject]
    _marks: tuple[Hashable, ...] = ()

    # This was a wrong decision
    # def __post_init__(self):
    #     """
    #     Check for subject type
    #     """
    #     # TODO: Is limiting a subject to a Type is really necessary?
    #     #   Users will then be allowed to annotate their things with e.g. x: 10
    #     #   But maybe this is good?

    #     # If generic, check origin, if not, check directly
    #     origin = get_origin(self._subject)
    #     origin = origin if origin is not None else self._subject

    #     if not isinstance(origin, type):
    #         raise InvalidHostSubject(
    #             f"Host subject is invalid. Expecting a type, not a {self._subject}"
    #         )

    @property
    def subject(
        self,
    ) -> Hashable | type[Subject]:
        return self._subject

    @property
    def marks(self) -> tuple[Hashable, ...]:
        return self._marks

    def __hash__(self) -> int:
        return hash((self.subject, *self.marks))
