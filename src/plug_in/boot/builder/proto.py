from abc import abstractmethod
from types import NotImplementedType
from typing import Callable, Hashable, Literal, Protocol, overload

from plug_in.core.plugin import DirectCorePlugin, FactoryCorePlugin, LazyCorePlugin


class PluginSelectorProtocol[P, MetaData](Protocol):

    @abstractmethod
    def directly(self) -> DirectCorePlugin[P, MetaData]:
        """
        Create [.DirectCorePlugin][] for non-obvious host type. Please
        revise plugin configuration is such case.

        Always be careful about typing in non-obvious host subject type.
        """
        ...


class TypedPluginSelectorProtocol[P, MetaData](Protocol):

    @abstractmethod
    def directly(self) -> DirectCorePlugin[P, MetaData]:
        """
        Create [.DirectCorePlugin][] for host of well known subject type.
        """
        ...


class ProvidingPluginSelectorProtocol[P, MetaData](Protocol):

    @abstractmethod
    def directly(self) -> DirectCorePlugin[Callable[[], P], MetaData]:
        """
        Create [.DirectCorePlugin][] for non-obvious host type. Please
        revise plugin configuration is such case. This plugin routine is
        equivalent to [.PluginSelector.directly]. Revise Your configuration.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    @overload
    @abstractmethod
    def via_provider(self, policy: Literal["lazy"]) -> LazyCorePlugin[P, MetaData]:
        """
        Create [.LazyCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked once host subject is requested in runtime,
        and then the result from this callable will be always used in place
        of host subject.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    @overload
    @abstractmethod
    def via_provider(
        self, policy: Literal["factory"]
    ) -> FactoryCorePlugin[P, MetaData]:
        """
        Create [.FactoryCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked every time host subject is requested in runtime.

        Always be careful about typing in non-obvious host subject type.
        """
        ...


class TypedProvidingPluginSelectorProtocol[P, MetaData](Protocol):

    @abstractmethod
    def directly(self) -> NotImplementedType:
        """
        USAGE PROHIBITED.

        This method exists only for type-consistency purpose. It will
        raise TypeError every time. You cannot plug callable
        directly into typed host. Usage is allowed only for non-typed
        hosts.
        """
        raise TypeError()

    @overload
    @abstractmethod
    def via_provider(self, policy: Literal["lazy"]) -> LazyCorePlugin[P, MetaData]:
        """
        Create [.LazyCorePlugin][] for well-known host. Your plug
        callable will be invoked once host subject is requested in runtime,
        and then the result from this callable will be always used in place
        of host subject.

        """
        ...

    @overload
    @abstractmethod
    def via_provider(
        self, policy: Literal["factory"]
    ) -> FactoryCorePlugin[P, MetaData]:
        """
        Create [.FactoryCorePlugin][] for well-known host. Your plug
        callable will be invoked every time host subject is requested in runtime.
        """
        ...


class PlugFacadeProtocol[T, MetaData](Protocol):
    @overload
    @abstractmethod
    def into(
        self, subject: type[T], *marks: Hashable
    ) -> TypedPluginSelectorProtocol[T, MetaData]:
        """
        Plug Your instance into host of well-known type. Proceed with
        `.directly` / `.via_provider` to finish plugin creation.
        """
        ...

    @overload
    @abstractmethod
    def into(
        self, subject: Hashable, *marks: Hashable
    ) -> PluginSelectorProtocol[T, MetaData]:
        """
        Plug Your instance into host of NON-OBVIOUS type. Proceed with
        `.directly` / `.via_provider` to finish plugin creation, but be careful
        about plugin runtime type consistency.
        """
        ...


class ProvidingPlugFacadeProtocol[T, MetaData](Protocol):
    @overload
    @abstractmethod
    def into(
        self, subject: type[T], *marks: Hashable
    ) -> TypedProvidingPluginSelectorProtocol[T, MetaData]:
        """
        Plug the result of Your callable into well known host type.
        Proceed with `.via_provider` (or sometimes with `.directly`) to
        finish Your plugin creation.
        """
        ...

    @overload
    @abstractmethod
    def into(
        self, subject: Hashable, *marks: Hashable
    ) -> ProvidingPluginSelectorProtocol[T, MetaData]:
        """
        Plug the result of Your callable into NON-OBVIOUS host type.
        Proceed with `.via_provider` (or sometimes with `.directly`) to
        finish Your plugin creation, but be careful
        about plugin runtime type consistency.
        """
        ...
