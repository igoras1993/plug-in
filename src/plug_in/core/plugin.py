from dataclasses import dataclass
import threading
from typing import Any, Awaitable, Callable, Literal, Self, cast, overload

from plug_in.core.enum import PluginPolicy
from plug_in.core.plug import CorePlug
from plug_in.core.host import CoreHost
from plug_in.exc import UnexpectedForwardRefError
from plug_in.tools.introspect import contains_forward_refs
from plug_in.types.proto.core_plugin import (
    AsyncCorePluginProtocol,
    BindingCorePluginProtocol,
    ProvidingCorePluginProtocol,
)
from plug_in.core.asyncio.plugin import LazyAsyncCorePlugin, FactoryAsyncCorePlugin

from plug_in.types.proto.joint import Joint


@dataclass(frozen=True)
class DirectCorePlugin[JointType: Joint, MetaDataType](
    BindingCorePluginProtocol[JointType, MetaDataType]
):
    _plug: CorePlug[JointType]
    _host: CoreHost[JointType]
    _metadata: MetaDataType
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
    def metadata(self) -> MetaDataType:
        return self._metadata

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

    def assert_sync(
        self,
    ) -> Self:
        return self

    def assert_async(self) -> AsyncCorePluginProtocol[JointType, MetaDataType]:
        """
        Always raises `AssertionError`.
        """
        raise AssertionError("DirectCorePlugin is not asynchronous")


@dataclass(frozen=True)
class LazyCorePlugin[JointType: Joint, MetaDataType](
    ProvidingCorePluginProtocol[JointType, MetaDataType]
):
    _plug: CorePlug[Callable[[], JointType]]
    _host: CoreHost[JointType]
    _metadata: MetaDataType
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
    def metadata(self) -> MetaDataType:
        return self._metadata

    @property
    def plug(self) -> CorePlug[Callable[[], JointType]]:
        return self._plug

    @property
    def host(self) -> CoreHost[JointType]:
        return self._host

    def _get_lock(self) -> threading.Lock:
        try:
            return getattr(self, "_lock")
        except AttributeError:
            _lock = threading.Lock()
            object.__setattr__(self, "_lock", _lock)

        return _lock

    def provide(self) -> JointType:
        # TODO: Lock should be instantiated
        with self._get_lock():
            try:
                return getattr(self, "_provided")
            except AttributeError:
                _provided = self.plug.provider()
                object.__setattr__(self, "_provided", _provided)

        return _provided

    def assert_sync(
        self,
    ) -> Self:
        return self

    def assert_async(self) -> AsyncCorePluginProtocol[JointType, MetaDataType]:
        """
        Always raises `FactoryCorePlugin`.
        """
        raise AssertionError("LazyCorePlugin is not asynchronous")


@dataclass(frozen=True)
class FactoryCorePlugin[JointType: Joint, MetaDataType](
    ProvidingCorePluginProtocol[JointType, MetaDataType]
):
    _plug: CorePlug[Callable[[], JointType]]
    _host: CoreHost[JointType]
    _metadata: MetaDataType
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
    def metadata(self) -> MetaDataType:
        return self._metadata

    @property
    def plug(self) -> CorePlug[Callable[[], JointType]]:
        return self._plug

    @property
    def host(self) -> CoreHost[JointType]:
        return self._host

    def provide(self) -> JointType:
        return self.plug.provider()

    def assert_sync(
        self,
    ) -> Self:
        return self

    def assert_async(self) -> AsyncCorePluginProtocol[JointType, MetaDataType]:
        """
        Always raises `AssertionError`.
        """
        raise AssertionError("FactoryCorePlugin is not asynchronous")


@overload
def create_core_plugin[
    JointType: Joint, MetaDataType: Any
](
    plug: CorePlug[JointType],
    host: CoreHost[JointType],
    policy: Literal[PluginPolicy.DIRECT],
    meta: MetaDataType = None,
) -> DirectCorePlugin[JointType, MetaDataType]: ...


@overload
def create_core_plugin[
    JointType: Joint, MetaDataType: Any
](
    plug: CorePlug[Callable[[], JointType]],
    host: CoreHost[JointType],
    policy: Literal[PluginPolicy.LAZY],
    meta: MetaDataType = None,
) -> LazyCorePlugin[JointType, MetaDataType]: ...


@overload
def create_core_plugin[
    JointType: Joint, MetaDataType: Any
](
    plug: CorePlug[Callable[[], JointType]],
    host: CoreHost[JointType],
    policy: Literal[PluginPolicy.FACTORY],
    meta: MetaDataType = None,
) -> FactoryCorePlugin[JointType, MetaDataType]: ...


@overload
def create_core_plugin[
    JointType: Joint, MetaDataType: Any
](
    plug: CorePlug[Callable[[], Awaitable[JointType]]],
    host: CoreHost[JointType],
    policy: Literal[PluginPolicy.LAZY_ASYNC],
    meta: MetaDataType = None,
) -> LazyAsyncCorePlugin[JointType, MetaDataType]: ...


@overload
def create_core_plugin[
    JointType: Joint, MetaDataType: Any
](
    plug: CorePlug[Callable[[], Awaitable[JointType]]],
    host: CoreHost[JointType],
    policy: Literal[PluginPolicy.FACTORY_ASYNC],
    meta: MetaDataType = None,
) -> FactoryAsyncCorePlugin[JointType, MetaDataType]: ...


def create_core_plugin[
    JointType: Joint,
    MetaDataType: Any,
](
    plug: (
        CorePlug[Callable[[], JointType]]
        | CorePlug[JointType]
        | CorePlug[Callable[[], Awaitable[JointType]]]
    ),
    host: CoreHost[JointType],
    policy: Literal[
        PluginPolicy.DIRECT,
        PluginPolicy.LAZY,
        PluginPolicy.FACTORY,
        PluginPolicy.LAZY_ASYNC,
        PluginPolicy.FACTORY_ASYNC,
    ],
    meta: MetaDataType = None,
) -> (
    DirectCorePlugin[JointType, MetaDataType]
    | LazyCorePlugin[JointType, MetaDataType]
    | FactoryCorePlugin[JointType, MetaDataType]
    | LazyAsyncCorePlugin[JointType, MetaDataType]
    | FactoryAsyncCorePlugin[JointType, MetaDataType]
):
    match policy:
        case PluginPolicy.DIRECT:
            return DirectCorePlugin(
                _plug=cast(CorePlug[JointType], plug),
                _host=host,
                _metadata=meta,
                _policy=policy,
            )

        case PluginPolicy.LAZY:
            return LazyCorePlugin(
                _plug=cast(CorePlug[Callable[[], JointType]], plug),
                _host=host,
                _metadata=meta,
                _policy=policy,
            )
        case PluginPolicy.FACTORY:
            return FactoryCorePlugin(
                _plug=cast(CorePlug[Callable[[], JointType]], plug),
                _host=host,
                _metadata=meta,
                _policy=policy,
            )
        case PluginPolicy.LAZY_ASYNC:
            return LazyAsyncCorePlugin(
                _plug=cast(CorePlug[Callable[[], Awaitable[JointType]]], plug),
                _host=host,
                _metadata=meta,
                _policy=policy,
            )
        case PluginPolicy.FACTORY_ASYNC:
            return FactoryAsyncCorePlugin(
                _plug=cast(CorePlug[Callable[[], Awaitable[JointType]]], plug),
                _host=host,
                _metadata=meta,
                _policy=policy,
            )

        case _:
            raise RuntimeError(f"Unsupported plugin policy: {policy}")
