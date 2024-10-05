from dataclasses import dataclass
from typing import Awaitable, Callable, Literal, Self
import asyncio

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

from plug_in.types.proto.joint import Joint


@dataclass(frozen=True)
class LazyAsyncCorePlugin[JointType: Joint, MetaDataType](
    AsyncCorePluginProtocol[JointType, MetaDataType]
):
    _plug: CorePlug[Callable[[], Awaitable[JointType]]]
    _host: CoreHost[JointType]
    _metadata: MetaDataType
    _policy: Literal[PluginPolicy.LAZY_ASYNC] = PluginPolicy.LAZY_ASYNC

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
    def plug(self) -> CorePlug[Callable[[], Awaitable[JointType]]]:
        return self._plug

    @property
    def host(self) -> CoreHost[JointType]:
        return self._host

    def _get_lock(self) -> asyncio.Lock:
        try:
            return getattr(self, "_lock")
        except AttributeError:
            _lock = asyncio.Lock()
            object.__setattr__(self, "_lock", _lock)

        return _lock

    async def provide(self) -> JointType:
        async with self._get_lock():
            try:
                return getattr(self, "_provided")
            except AttributeError:
                _provided = await self.plug.provider()
                object.__setattr__(self, "_provided", _provided)

        return _provided

    def assert_sync(
        self,
    ) -> (
        BindingCorePluginProtocol[JointType, MetaDataType]
        | ProvidingCorePluginProtocol[JointType, MetaDataType]
    ):
        """
        Always raises `AssertionError`.
        """
        raise AssertionError("LazyAsyncCorePlugin is not synchronous.")

    def assert_async(self) -> Self:
        return self


@dataclass(frozen=True)
class FactoryAsyncCorePlugin[JointType: Joint, MetaDataType](
    AsyncCorePluginProtocol[JointType, MetaDataType]
):
    _plug: CorePlug[Callable[[], Awaitable[JointType]]]
    _host: CoreHost[JointType]
    _metadata: MetaDataType
    _policy: Literal[PluginPolicy.FACTORY_ASYNC] = PluginPolicy.FACTORY_ASYNC

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
    def plug(self) -> CorePlug[Callable[[], Awaitable[JointType]]]:
        return self._plug

    @property
    def host(self) -> CoreHost[JointType]:
        return self._host

    async def provide(self) -> JointType:
        return await self.plug.provider()

    def assert_sync(
        self,
    ) -> (
        BindingCorePluginProtocol[JointType, MetaDataType]
        | ProvidingCorePluginProtocol[JointType, MetaDataType]
    ):
        """
        Always raises `AssertionError`.
        """
        raise AssertionError("LazyAsyncCorePlugin is not synchronous.")

    def assert_async(self) -> Self:
        return self
