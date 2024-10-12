import threading
from typing import Any, Awaitable, Iterable

from plug_in.exc import AmbiguousHostError, MissingPluginError
from plug_in.types.proto.core_host import CoreHostProtocol
from plug_in.types.proto.core_plugin import (
    AsyncCorePluginProtocol,
    BindingCorePluginProtocol,
    CorePluginProtocol,
    ProvidingCorePluginProtocol,
)
from plug_in.types.proto.core_registry import (
    AsyncCoreRegistryProtocol,
    CoreRegistryProtocol,
)
from plug_in.types.proto.joint import Joint


# TODO: This class has potential to utilize TypeVarTuple, but only if
#   some kind of TypeVarTuple transformations will be implemented in python
#   type system. See e.g. this proposal:
#   https://discuss.python.org/t/pre-pep-considerations-and-feedback-type-transformations-on-variadic-generics/50605
class CoreRegistry(CoreRegistryProtocol):
    """
    Holds collection of plugins. Registry object is immutable.

    Raises:
        [.AmbiguousHostError][]: When host collision occurs.
    """

    def __init__(
        self,
        plugins: Iterable[CorePluginProtocol[Any, Any]],
        #  TODO: Consider adding verify_joints param
        #  verify_joints: bool = True,
    ) -> None:
        self._original_plugins = plugins

        # TODO: Verify if this is indeed needed for multithreading.
        #   Asyncio tasks are safe as this never will be an async method
        with threading.Lock():
            self._hash_to_sync_plugin_map: dict[
                int,
                BindingCorePluginProtocol[Any, Any]
                | ProvidingCorePluginProtocol[Any, Any],
            ] = {}

            self._hash_to_async_plugin_map: dict[
                int,
                AsyncCorePluginProtocol[Any, Any],
            ] = {}

            for plugin in plugins:
                host_hash = hash(plugin.host)

                if host_hash in self._hash_to_sync_plugin_map:
                    raise AmbiguousHostError(
                        f"Host {plugin.host} of plugin {plugin} is ambiguous in "
                        f"context of this registry. There is already a plugin "
                        f"registered on that host: "
                        f"{self._hash_to_sync_plugin_map[host_hash]} "
                        "Try using mark parameter ["
                        f"{plugin.host.__class__.__name__}(..., mark='some_mark') ]"
                        "to remove ambiguity, or register this plugin with sync metadata."
                    )

                if host_hash in self._hash_to_async_plugin_map:
                    raise AmbiguousHostError(
                        f"Host {plugin.host} of plugin {plugin} is ambiguous in "
                        f"context of this registry. There is already a plugin "
                        f"registered on that host: "
                        f"{self._hash_to_async_plugin_map[host_hash]} "
                        "Try using mark parameter ["
                        f"{plugin.host.__class__.__name__}(..., mark='some_mark') ]"
                        "to remove ambiguity, or register this plugin with sync metadata."
                    )

                try:
                    sync_plugin = plugin.assert_sync()
                except AssertionError:
                    try:
                        async_plugin = plugin.assert_sync()
                    except AssertionError as e:
                        raise RuntimeError(
                            "This should never happen, report an issue"
                        ) from e
                    else:
                        self._hash_to_async_plugin_map[host_hash] = async_plugin
                else:
                    self._hash_to_sync_plugin_map[host_hash] = sync_plugin

        self._hash_val: int = hash(
            (
                *tuple(self._hash_to_sync_plugin_map.keys()),
                *tuple(self._hash_to_async_plugin_map.keys()),
            )
        )

    def plugin[
        JointType: Joint
    ](self, host: CoreHostProtocol[JointType]) -> CorePluginProtocol[Any, Any]:
        """
        Raises:
            [plug_in.exc.MissingPluginError][]

        """
        try:
            return self._hash_to_sync_plugin_map[hash(host)]
        except KeyError:
            try:
                return self._hash_to_async_plugin_map[hash(host)]
            except KeyError:
                raise MissingPluginError(
                    f"Missing plugin for {host} in registry {self}"
                )

    def resolve[
        JointType: Joint
    ](self, host: CoreHostProtocol[JointType]) -> JointType | Awaitable[JointType]:
        """
        Resolve host into its provided value, or awaitable of provided value
        in case of async plugin.

        Raises:
            [plug_in.exc.MissingPluginError][] if plugin does not exit

        """
        return self.plugin(host=host).provide()

    async def async_resolve[
        JointType: Joint
    ](self, host: CoreHostProtocol[JointType]) -> JointType:
        """
        Resolve host into provided value. This will always resolve into
        provided value, both for sync and async plugins.

        Raises:
            [plug_in.exc.MissingPluginError][] if plugin does not exist
        """

        try:
            sync_plugin = self.plugin(host=host).assert_sync()
        except AssertionError:
            try:
                async_plugin = self.plugin(host=host).assert_async()
            except AssertionError as e:
                raise RuntimeError("This should never happen, report an issue") from e
            else:
                return await async_plugin.provide()
        else:
            return sync_plugin.provide()

    def sync_resolve[
        JointType: Joint
    ](self, host: CoreHostProtocol[JointType]) -> JointType:
        """
        Resolve host into provided value. Will search only for synchronous plugins.
        Will raise [plug_in.exc.MissingPluginError][] even when async plugin exists.

        Raises:
            [plug_in.exc.MissingPluginError][] if plugin does not exist
        """

        try:
            sync_plugin = self.plugin(host=host).assert_sync()
        except AssertionError as e:
            raise MissingPluginError(
                f"Missing plugin for {host} in registry {self}"
            ) from e
        else:
            return sync_plugin.provide()

    # Implemented it for trial. Do not know if it will be needed
    def __hash__(self) -> int:
        return self._hash_val

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(\n\t{self._original_plugins}"


class AsyncCoreRegistry(CoreRegistry, AsyncCoreRegistryProtocol):

    async def resolve[
        JointType: Joint
    ](self, host: CoreHostProtocol[JointType]) -> JointType:
        """
        Resolve host into its provided value.

        Raises:
            [plug_in.exc.MissingPluginError][] if plugin does not exit

        """
        return await self.async_resolve(host=host)
