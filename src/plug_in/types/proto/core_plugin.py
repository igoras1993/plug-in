from abc import abstractmethod
from typing import Awaitable, Callable, Protocol, Self

from plug_in.types.proto.core_host import CoreHostProtocol
from plug_in.types.proto.core_plug import CorePlugProtocol
from plug_in.types.proto.joint import Joint


class BindingCorePluginProtocol[JointType: Joint, MetaDataType](Protocol):

    @property
    @abstractmethod
    def plug(self) -> CorePlugProtocol[JointType]: ...

    @property
    @abstractmethod
    def host(self) -> CoreHostProtocol[JointType]: ...

    @property
    @abstractmethod
    def metadata(self) -> MetaDataType: ...

    @abstractmethod
    def provide(self) -> JointType: ...

    @abstractmethod
    def assert_sync(
        self,
    ) -> Self: ...

    @abstractmethod
    def assert_async(self) -> "AsyncCorePluginProtocol[JointType, MetaDataType]": ...


# TODO: Consider allowing for passing host data into
#   providing plug callable.
class ProvidingCorePluginProtocol[JointType: Joint, MetaDataType](Protocol):

    @property
    @abstractmethod
    def plug(self) -> CorePlugProtocol[Callable[[], JointType]]: ...

    @property
    @abstractmethod
    def host(self) -> CoreHostProtocol[JointType]: ...

    @property
    @abstractmethod
    def metadata(self) -> MetaDataType: ...

    @abstractmethod
    def provide(self) -> JointType: ...

    @abstractmethod
    def assert_sync(
        self,
    ) -> Self: ...

    @abstractmethod
    def assert_async(self) -> "AsyncCorePluginProtocol[JointType, MetaDataType]": ...


class AsyncCorePluginProtocol[JointType: Joint, MetaDataType](Protocol):
    @property
    @abstractmethod
    def plug(self) -> CorePlugProtocol[Callable[[], Awaitable[JointType]]]: ...

    @property
    @abstractmethod
    def host(self) -> CoreHostProtocol[JointType]: ...

    @property
    @abstractmethod
    def metadata(self) -> MetaDataType: ...

    @abstractmethod
    def provide(self) -> Awaitable[JointType]: ...

    @abstractmethod
    def assert_sync(
        self,
    ) -> (
        BindingCorePluginProtocol[JointType, MetaDataType]
        | ProvidingCorePluginProtocol[JointType, MetaDataType]
    ): ...

    @abstractmethod
    def assert_async(self) -> Self: ...


class CorePluginProtocol[JointType: Joint, MetaDataType](Protocol):

    @property
    @abstractmethod
    def metadata(self) -> MetaDataType: ...

    @abstractmethod
    def provide(self) -> JointType | Awaitable[JointType]: ...

    @property
    @abstractmethod
    def host(self) -> CoreHostProtocol[JointType]: ...

    @abstractmethod
    def assert_sync(
        self,
    ) -> (
        BindingCorePluginProtocol[JointType, MetaDataType]
        | ProvidingCorePluginProtocol[JointType, MetaDataType]
    ):
        """
        Return one of the synchronous plugin protocols or raise `AssertionError`
        """

    @abstractmethod
    def assert_async(self) -> AsyncCorePluginProtocol[JointType, MetaDataType]:
        """
        Return one of the async plugin protocols or raise `AssertionError`
        """

    # TODO: Consider adding verify_joint method
    # @abstractmethod
    # def verify_joint(self) -> bool: ...
