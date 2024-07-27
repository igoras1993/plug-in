from dataclasses import dataclass
from typing import Callable, Literal, cast, overload

from plug_in.core.enum import PluginPolicy
from plug_in.core.plug import CorePlug
from plug_in.core.host import CoreHost
from plug_in.proto.core_plugin import (
    BindingCorePluginProtocol,
    ProvidingCorePluginProtocol,
)

from plug_in.proto.joint import Joint


@dataclass(frozen=True)
class DirectCorePlugin[JointType: Joint](BindingCorePluginProtocol[JointType]):
    plug: CorePlug[JointType]
    host: CoreHost[JointType]
    policy: Literal[PluginPolicy.DIRECT] = PluginPolicy.DIRECT

    def provide(self) -> JointType:
        return self.plug.provider


@dataclass(frozen=True)
class LazyCorePlugin[JointType: Joint](ProvidingCorePluginProtocol[JointType]):
    plug: CorePlug[Callable[[], JointType]]
    host: CoreHost[JointType]
    policy: Literal[PluginPolicy.LAZY] = PluginPolicy.LAZY

    def provide(self) -> JointType:
        try:
            return getattr(self, "_provided")
        except AttributeError:
            _provided = self.plug.provider()
            setattr(self, "_provided", _provided)
            return _provided


@dataclass(frozen=True)
class FactoryCorePlugin[JointType: Joint](ProvidingCorePluginProtocol[JointType]):
    plug: CorePlug[Callable[[], JointType]]
    host: CoreHost[JointType]
    policy: Literal[PluginPolicy.FACTORY] = PluginPolicy.FACTORY

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
                plug=cast(CorePlug[JointType], plug),
                host=host,
                policy=policy,
            )

        case PluginPolicy.LAZY:
            return LazyCorePlugin(
                plug=cast(CorePlug[Callable[[], JointType]], plug),
                host=host,
                policy=policy,
            )
        case PluginPolicy.FACTORY:
            return FactoryCorePlugin(
                plug=cast(CorePlug[Callable[[], JointType]], plug),
                host=host,
                policy=policy,
            )
        case _:
            raise RuntimeError(f"Unsupported plugin policy: {policy}")
