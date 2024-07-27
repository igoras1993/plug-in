import threading
from typing import Any, Iterable

from plug_in.core.plugin import DirectCorePlugin, FactoryCorePlugin, LazyCorePlugin
from plug_in.exc import AmbiguousHostError, MissingPluginError
from plug_in.proto.core_host import CoreHostProtocol
from plug_in.proto.core_registry import CoreRegistryProtocol
from plug_in.proto.joint import Joint


# TODO: This class has potential to utilize TypeVarTuple, but only if
#   some kind of TypeVarTuple transformations will be implemented in python
#   type system. See e.g. this proposal:
#   https://discuss.python.org/t/pre-pep-considerations-and-feedback-type-transformations-on-variadic-generics/50605
class CoreRegistry(CoreRegistryProtocol):

    def __init__(
        self,
        plugins: Iterable[
            DirectCorePlugin[Any] | LazyCorePlugin[Any] | FactoryCorePlugin[Any]
        ],
        #  TODO: Consider adding verify_joints param
        #  verify_joints: bool = True,
    ) -> None:

        # TODO: Verify if this is indeed needed for multithreading.
        #   Asyncio tasks are safe as this never will be an async method
        with threading.Lock():
            self._hash_to_plugin_map: dict[
                int,
                DirectCorePlugin[Any] | LazyCorePlugin[Any] | FactoryCorePlugin[Any],
            ]

            for plugin in plugins:
                host_hash = hash(plugin.host)

                if host_hash not in self._hash_to_plugin_map:
                    self._hash_to_plugin_map[host_hash] = plugin

                else:
                    raise AmbiguousHostError(
                        f"Host {plugin.host} of plugin {plugin} is ambiguous in "
                        f"context of this registry. There is already a plugin "
                        f"registered on that host: {self._hash_to_plugin_map[host_hash]} "
                        "Try using mark parameter ["
                        f"{plugin.host.__class__.__name__}(..., mark='some_mark') ]"
                        "to remove ambiguity."
                    )

        self._hash_val: int = hash(tuple(self._hash_to_plugin_map.keys()))

    def plugin[
        JointType: Joint
    ](self, host: CoreHostProtocol[JointType]) -> (
        DirectCorePlugin[JointType]
        | LazyCorePlugin[JointType]
        | FactoryCorePlugin[JointType]
    ):
        """
        Raises:
            [plug_in.exc.MissingPluginError][]

        """
        try:
            return self._hash_to_plugin_map[hash(host)]
        except KeyError:
            raise MissingPluginError(f"Missing plugin for {host} in registry {self}")

    def resolve[JointType: Joint](self, host: CoreHostProtocol[JointType]) -> JointType:
        """
        Raises:
            [plug_in.exc.MissingPluginError][]

        """
        return self.plugin(host=host).provide()

    # Implemented it for trial. Do not know if it will be needed
    def __hash__(self) -> int:
        return self._hash_val
