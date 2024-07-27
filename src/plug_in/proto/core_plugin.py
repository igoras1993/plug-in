from abc import abstractmethod
from typing import Callable, Protocol

from plug_in.proto.core_host import CoreHostProtocol
from plug_in.proto.core_plug import CorePlugProtocol
from plug_in.proto.joint import Joint


class CorePluginProtocol[JointType: Joint](Protocol):

    @abstractmethod
    def provide(self) -> JointType: ...

    # TODO: Consider adding verify_joint method
    # @abstractmethod
    # def verify_joint(self) -> bool: ...


class BindingCorePluginProtocol[JointType: Joint](
    CorePluginProtocol[JointType], Protocol
):
    plug: CorePlugProtocol[JointType]
    host: CoreHostProtocol[JointType]


# TODO: Consider allowing for passing host data into
#   providing plug callable.
class ProvidingCorePluginProtocol[JointType: Joint](
    CorePluginProtocol[JointType], Protocol
):
    plug: CorePlugProtocol[Callable[[], JointType]]
    host: CoreHostProtocol[JointType]
