from abc import abstractmethod
from typing import Callable, Protocol

from plug_in.types.proto.core_host import CoreHostProtocol
from plug_in.types.proto.core_registry import CoreRegistryProtocol
from plug_in.types.proto.joint import Joint
from plug_in.types.alias import Manageable


class RouterProtocol(Protocol):

    @abstractmethod
    def mount(self, registry: CoreRegistryProtocol) -> None:
        """
        Raises:
            [plug_in.exc.RouterAlreadyMountedError][]: ...
        """
        ...

    @abstractmethod
    def get_registry(self) -> CoreRegistryProtocol:
        """
        Raises:
            [plug_in.exc.MissingMountError][]: ...
        """

    @abstractmethod
    def resolve[JointType: Joint](self, host: CoreHostProtocol[JointType]) -> JointType:
        """
        Raises:
            [plug_in.exc.MissingMountError][]: ...
            [plug_in.exc.MissingPluginError][]: ...
        """
        ...

    @abstractmethod
    def manage[
        T: Manageable
    ](self, eager_forward_resolve: bool = True) -> Callable[[T], T]: ...
