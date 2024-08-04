from dataclasses import dataclass
import threading
from typing import Callable, Literal, cast, overload

from plug_in.core.enum import PluginPolicy
from plug_in.core.plug import CorePlug
from plug_in.core.host import CoreHost
from plug_in.exc import UnexpectedForwardRefError
from plug_in.tools.introspect import contains_forward_refs
from plug_in.types.proto.core_plugin import (
    BindingCorePluginProtocol,
    ProvidingCorePluginProtocol,
)

from plug_in.types.proto.joint import Joint


@dataclass(frozen=True)
class DirectCorePlugin[JointType: Joint](BindingCorePluginProtocol[JointType]):
    _plug: CorePlug[JointType]
    _host: CoreHost[JointType]
    _policy: Literal[PluginPolicy.DIRECT] = PluginPolicy.DIRECT

    def __post_init__(self):
        """
        Raises:
            [.UnexpectedForwardRefError][]: When provided host has forward references.
        """
        if contains_forward_refs(self._host.subject):
            raise UnexpectedForwardRefError(
                f"Given host {self._host} contains forward references, which are not "
                f"allowed at plugin creation time."
            )

    @property
    def plug(self) -> CorePlug[JointType]:
        return self._plug

    @property
    def host(self) -> CoreHost[JointType]:
        return self._host

    @property
    def policy(self) -> Literal[PluginPolicy.DIRECT]:
        return self._policy

    def provide(self) -> JointType:
        return self.plug.provider


@dataclass(frozen=True)
class LazyCorePlugin[JointType: Joint](ProvidingCorePluginProtocol[JointType]):
    _plug: CorePlug[Callable[[], JointType]]
    _host: CoreHost[JointType]
    _policy: Literal[PluginPolicy.LAZY] = PluginPolicy.LAZY

    def __post_init__(self):
        """
        Raises:
            [.UnexpectedForwardRefError][]: When provided host has forward references.
        """
        if contains_forward_refs(self._host.subject):
            raise UnexpectedForwardRefError(
                f"Given host {self._host} contains forward references, which are not "
                f"allowed at plugin creation time."
            )

    @property
    def plug(self) -> CorePlug[Callable[[], JointType]]:
        return self._plug

    @property
    def host(self) -> CoreHost[JointType]:
        return self._host

    def provide(self) -> JointType:
        with threading.Lock():
            try:
                return getattr(self, "_provided")
            except AttributeError:
                _provided = self.plug.provider()
                object.__setattr__(self, "_provided", _provided)

        return _provided


@dataclass(frozen=True)
class FactoryCorePlugin[JointType: Joint](ProvidingCorePluginProtocol[JointType]):
    _plug: CorePlug[Callable[[], JointType]]
    _host: CoreHost[JointType]
    _policy: Literal[PluginPolicy.FACTORY] = PluginPolicy.FACTORY

    def __post_init__(self):
        """
        Raises:
            [.UnexpectedForwardRefError][]: When provided host has forward references.
        """
        if contains_forward_refs(self._host.subject):
            raise UnexpectedForwardRefError(
                f"Given host {self._host} contains forward references, which are not "
                f"allowed at plugin creation time."
            )

    @property
    def plug(self) -> CorePlug[Callable[[], JointType]]:
        return self._plug

    @property
    def host(self) -> CoreHost[JointType]:
        return self._host

    def provide(self) -> JointType:
        return self.plug.provider()


@overload
def create_core_plugin[
    JointType: Joint
](
    plug: CorePlug[JointType],
    host: CoreHost[JointType],
    policy: Literal[PluginPolicy.DIRECT],
) -> DirectCorePlugin[JointType]: ...


@overload
def create_core_plugin[
    JointType: Joint
](
    plug: CorePlug[Callable[[], JointType]],
    host: CoreHost[JointType],
    policy: Literal[PluginPolicy.LAZY],
) -> LazyCorePlugin[JointType]: ...


@overload
def create_core_plugin[
    JointType: Joint
](
    plug: CorePlug[Callable[[], JointType]],
    host: CoreHost[JointType],
    policy: Literal[PluginPolicy.FACTORY],
) -> FactoryCorePlugin[JointType]: ...


def create_core_plugin[
    JointType: Joint
](
    plug: CorePlug[Callable[[], JointType]] | CorePlug[JointType],
    host: CoreHost[JointType],
    policy: Literal[PluginPolicy.DIRECT, PluginPolicy.LAZY, PluginPolicy.FACTORY],
) -> (
    DirectCorePlugin[JointType]
    | LazyCorePlugin[JointType]
    | FactoryCorePlugin[JointType]
):
    match policy:
        case PluginPolicy.DIRECT:
            return DirectCorePlugin(
                _plug=cast(CorePlug[JointType], plug),
                _host=host,
                _policy=policy,
            )

        case PluginPolicy.LAZY:
            return LazyCorePlugin(
                _plug=cast(CorePlug[Callable[[], JointType]], plug),
                _host=host,
                _policy=policy,
            )
        case PluginPolicy.FACTORY:
            return FactoryCorePlugin(
                _plug=cast(CorePlug[Callable[[], JointType]], plug),
                _host=host,
                _policy=policy,
            )
        case _:
            raise RuntimeError(f"Unsupported plugin policy: {policy}")
