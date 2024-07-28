from abc import abstractmethod
from typing import Callable, Protocol

from plug_in.types.proto.core_host import CoreHostProtocol
from plug_in.types.proto.core_plug import CorePlugProtocol
from plug_in.types.proto.joint import Joint


class CorePluginProtocol[JointType: Joint](Protocol):

    @abstractmethod
    def provide(self) -> JointType: ...

    # TODO: Consider adding verify_joint method
    # @abstractmethod
    # def verify_joint(self) -> bool: ...


class BindingCorePluginProtocol[JointType: Joint](
    CorePluginProtocol[JointType], Protocol
):
    @property
    def plug(self) -> CorePlugProtocol[JointType]: ...

    @property
    def host(self) -> CoreHostProtocol[JointType]: ...


# TODO: Consider allowing for passing host data into
#   providing plug callable.
class ProvidingCorePluginProtocol[JointType: Joint](
    CorePluginProtocol[JointType], Protocol
):
    @property
    def plug(self) -> CorePlugProtocol[Callable[[], JointType]]: ...

    @property
    def host(self) -> CoreHostProtocol[JointType]: ...
