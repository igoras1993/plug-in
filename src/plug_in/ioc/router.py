from dataclasses import dataclass
from functools import partial
from typing import Callable, cast
from plug_in.exc import MissingMountError, RouterAlreadyMountedError
from plug_in.types.proto.core_host import CoreHostProtocol
from plug_in.types.proto.core_registry import CoreRegistryProtocol
from plug_in.types.proto.router import RouterProtocol
from plug_in.types.proto.joint import Joint
from plug_in.types.alias import Manageable
from plug_in.ioc.resolve import callable_route_factory


@dataclass
class Router(RouterProtocol):

    def __init__(self) -> None:
        self._reg: CoreRegistryProtocol | None = None

    def mount(self, registry: CoreRegistryProtocol) -> None:
        """
        Raises:
            [plug_in.exc.RouterAlreadyMountedError][]: ...
        """
        if self._reg is not None:
            raise RouterAlreadyMountedError(
                f"This router {self} is already mounted ({self._reg})"
            )

        self._reg = registry

    def get_registry(self) -> CoreRegistryProtocol:
        """
        Raises:
            [plug_in.exc.MissingMountError][]: ...
        """
        if self._reg is None:
            raise MissingMountError(f"Mount is missing for this router ({self})")

        return self._reg

    def resolve[JointType: Joint](self, host: CoreHostProtocol[JointType]) -> Joint:
        """
        Raises:
            [plug_in.exc.MissingMountError][]: ...
            [plug_in.exc.MissingPluginError][]: ...
        """
        reg = self.get_registry()
        return reg.resolve(host=host)

    def _callable_manager_factory[
        T: Manageable
    ](self, eager_forward_resolve: bool, callable: T) -> T:
        # TODO: Consider adding runtime check for being callable
        return cast(T, callable_route_factory(callable, self, eager_forward_resolve))

    def manage[
        T: Manageable
    ](self, eager_forward_resolve: bool = True) -> Callable[[T], T]:
        """
        Decorator maker for marking callables to be managed by plug_in IoC system.

        plug_in IoC system applies modification to the runtime of decorated
        callable, but does not changes its type hints. Default values of
        host type are just replaces with resolved default values. No further
        modification is applied to the marked callable.

        Args:
            eager_forward_resolve: Set this to `False` when You are using hosts
                with subjects being generic classes parametrized with forward
                references. Defaults to `True`. Default behavior slightly improves
                call-time performance.

        Returns:
            Decorator that makes your callable a manageable entity

        """
        return partial(self._callable_manager_factory, eager_forward_resolve)
