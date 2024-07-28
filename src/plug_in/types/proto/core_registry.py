from abc import abstractmethod
from typing import Protocol
from plug_in.types.proto.core_host import CoreHostProtocol
from plug_in.types.proto.core_plugin import (
    CorePluginProtocol,
)
from plug_in.types.proto.joint import Joint


class CoreRegistryProtocol(Protocol):

    @abstractmethod
    def resolve[JointType: Joint](self, host: CoreHostProtocol[JointType]) -> JointType:
        """
        Raises:
            [plug_in.exc.MissingPluginError][]

        """
        ...

    @abstractmethod
    def plugin[
        JointType: Joint
    ](self, host: CoreHostProtocol[JointType]) -> CorePluginProtocol[JointType]:
        """
        Raises:
            [plug_in.exc.MissingPluginError][]

        """
        ...
