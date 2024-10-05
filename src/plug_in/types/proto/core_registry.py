from abc import abstractmethod
from typing import Any, Awaitable, Protocol
from plug_in.types.proto.core_host import CoreHostProtocol
from plug_in.types.proto.core_plugin import (
    CorePluginProtocol,
)
from plug_in.types.proto.joint import Joint


class CoreRegistryProtocol(Protocol):

    @abstractmethod
    def resolve[
        JointType: Joint
    ](self, host: CoreHostProtocol[JointType]) -> JointType | Awaitable[JointType]:
        """
        Raises:
            [plug_in.exc.MissingPluginError][]

        """
        ...

    async def async_resolve[
        JointType: Joint
    ](self, host: CoreHostProtocol[JointType]) -> JointType:
        """
        Resolve host into provided value. This will always resolve into
        provided value, both for sync and async plugins.

        Raises:
            [plug_in.exc.MissingPluginError][] if plugin does not exist
        """
        ...

    def sync_resolve[
        JointType: Joint
    ](self, host: CoreHostProtocol[JointType]) -> JointType:
        """
        Resolve host into provided value. Will search only for synchronous plugins.
        Will raise [plug_in.exc.MissingPluginError][] even when async plugin exists.

        Raises:
            [plug_in.exc.MissingPluginError][] if plugin does not exist
        """
        ...

    @abstractmethod
    def plugin[
        JointType: Joint
    ](self, host: CoreHostProtocol[JointType]) -> CorePluginProtocol[JointType, Any]:
        """
        Raises:
            [plug_in.exc.MissingPluginError][]

        """
        ...
