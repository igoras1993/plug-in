from abc import abstractmethod
from typing import Any, Callable, Protocol

from plug_in.types.proto.core_host import CoreHostProtocol
from plug_in.types.proto.core_registry import CoreRegistryProtocol
from plug_in.types.proto.joint import Joint
from plug_in.types.alias import Manageable
from plug_in.types.proto.resolver import ParameterResolverProtocol


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
        Resolve a host via mounted registry.

        Raises:
            [plug_in.exc.MissingMountError][]: ...
            [plug_in.exc.MissingPluginError][]: ...
        """

    # @abstractmethod
    # def resolve_at(self, callable: Callable, host_mark: HostedMarkProtocol) -> Joint:
    #     """
    #     Resolve given host mark in context of some callable.

    #     Raises:
    #         [plug_in.exc.MissingMountError][]: ...
    #         [plug_in.exc.MissingPluginError][]: ...
    #     """
    #     ...

    @abstractmethod
    def manage[T: Manageable](self, *args, **kwargs) -> Callable[[T], T]:
        """
        Decorator factory for marking a callable as managed
        """

    @abstractmethod
    def get_route_resolver[
        **CallParams
    ](self, callable: Callable[CallParams, Any]) -> ParameterResolverProtocol[
        CallParams
    ]: ...
