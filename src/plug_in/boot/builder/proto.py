from abc import abstractmethod
from types import NotImplementedType
from typing import Any, Awaitable, Callable, Hashable, Literal, Protocol, overload

from plug_in.core.asyncio.plugin import FactoryAsyncCorePlugin, LazyAsyncCorePlugin
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


class ProvidingPluginSelectorProtocol[P, MetaData](
    PluginSelectorProtocol[Callable[[], P], MetaData], Protocol
):

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


class TypedProvidingPluginSelectorProtocol[P, MetaData](
    TypedPluginSelectorProtocol[Callable[[], P], MetaData], Protocol
):

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


class CoroutinePluginSelectorProtocol[P, MetaData](
    ProvidingPluginSelectorProtocol[Awaitable[P], MetaData], Protocol
):

    @abstractmethod
    def directly(self) -> DirectCorePlugin[Callable[[], Awaitable[P]], MetaData]:
        """
        Create [.DirectCorePlugin][] for non-obvious host type. Please
        revise plugin configuration in such case. This plugin routine is
        equivalent to [.PluginSelector.directly].

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    @overload
    @abstractmethod
    def via_provider(
        self, policy: Literal["lazy"]
    ) -> LazyCorePlugin[Awaitable[P], MetaData]:
        """
        Create [.LazyCorePlugin][] for non-obvious host type.

        ## Caution

        Please revise plugin configuration. Your host type cannot be determined, assuming
        that Your plug is a callable that returns `Awaitable[T]`. This `Awaitable[T]`
        will be returned by plugin.provide().

        ## Notes

        This typically means that Your `subject` (i.e. `Hosted(subject)`) is not
        the type that the instance returning from awaiting and calling the plug.

        Use with care.
        """
        ...

    @overload
    @abstractmethod
    def via_provider(
        self, policy: Literal["factory"]
    ) -> FactoryCorePlugin[Awaitable[P], MetaData]:
        """
        Create [.FactoryCorePlugin][] for non-obvious host type.

        ## Caution

        Please revise plugin configuration. Your host type cannot be determined, assuming
        that Your plug is a callable that returns `Awaitable[T]`. This `Awaitable[T]`
        will be returned by plugin.provide().

        ## Notes

        This typically means that Your `subject` (i.e. `Hosted(subject)`) is not
        the type that the instance returning from awaiting and calling the plug.

        Use with care.
        """
        ...

    @overload
    @abstractmethod
    def via_provider(
        self, policy: Literal["lazy_async"]
    ) -> LazyAsyncCorePlugin[P, MetaData]:
        """
        Create [.AsyncLazyCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked and awaited once host subject is requested in
        runtime, and then the result from this callable will be always used in
        place of host subject.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    @overload
    @abstractmethod
    def via_provider(
        self, policy: Literal["factory_async"]
    ) -> FactoryAsyncCorePlugin[P, MetaData]:
        """
        Create [.AsyncFactoryCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked and awaited every time host subject is requested
        in runtime.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    @overload
    @abstractmethod
    def via_async_provider(
        self, policy: Literal["lazy"]
    ) -> LazyAsyncCorePlugin[P, MetaData]:
        """
        Alias on `.via_provider(policy="lazy_async")`

        Create [.AsyncLazyCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked and awaited once host subject is requested in
        runtime, and then the result from this callable will be always used in
        place of host subject.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    @overload
    @abstractmethod
    def via_async_provider(
        self, policy: Literal["factory"]
    ) -> FactoryAsyncCorePlugin[P, MetaData]:
        """
        Alias on `.via_provider(policy="factory_async")`

        Create [.AsyncFactoryCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked and awaited every time host subject is requested
        in runtime.

        Always be careful about typing in non-obvious host subject type.
        """
        ...


class TypedCoroutinePluginSelectorProtocol[P, MetaData](
    TypedProvidingPluginSelectorProtocol[Awaitable[P], MetaData], Protocol
):

    @abstractmethod
    def directly(self) -> NotImplementedType:
        """
        # !! USAGE PROHIBITED !!

        ## Not implemented for typed host subject.

        Your host subject indicates that provider action is done by calling and
        awaiting. Plugging it directly will result in receiving
        `Callable[[], Awaitable[T]]` instead of `T`. Use `.via_async_provider()`
        instead.
        """
        ...

    @overload
    @abstractmethod
    def via_provider(self, policy: Literal["lazy"]) -> NotImplementedType:
        """
        # !! USAGE PROHIBITED !!

        ## Not implemented for typed host subject.

        Your host subject indicates that provider action is done by calling and
        awaiting. Plugging it via sync provider will result in receiving
        `Awaitable[T]` instead of `T`. Use `.via_async_provider()`
        instead.
        """
        ...

    @overload
    @abstractmethod
    def via_provider(self, policy: Literal["factory"]) -> NotImplementedType:
        """
        # !! USAGE PROHIBITED !!

        ## Not implemented for typed host subject.

        Your host subject indicates that provider action is done by calling and
        awaiting. Plugging it via sync provider will result in receiving
        `Awaitable[T]` instead of `T`. Use `.via_async_provider()`
        instead.
        """
        ...

    @overload
    @abstractmethod
    def via_provider(
        self, policy: Literal["lazy_async"]
    ) -> LazyAsyncCorePlugin[P, MetaData]:
        """
        Create [.LazyAsyncCorePlugin][]. Your plug
        callable will be invoked and awaited on first request, and then
        the same result will be returned on every subsequent request.
        """
        ...

    @overload
    @abstractmethod
    def via_provider(
        self, policy: Literal["factory_async"]
    ) -> FactoryAsyncCorePlugin[P, MetaData]:
        """
        Create [.FactoryAsyncCorePlugin][]. Your plug
        callable will be invoked and awaited every time host
        subject is requested in runtime.
        """
        ...

    @overload
    @abstractmethod
    def via_async_provider(
        self, policy: Literal["lazy"]
    ) -> LazyAsyncCorePlugin[P, MetaData]:
        """
        Alias on `.via_provider(policy="factory_async")`

        Create [.LazyAsyncCorePlugin][]. Your plug
        callable will be invoked and awaited on first request, and then
        the same result will be returned on every subsequent request.
        """
        ...

    @overload
    @abstractmethod
    def via_async_provider(
        self, policy: Literal["factory"]
    ) -> FactoryAsyncCorePlugin[P, MetaData]:
        """
        Alias on `.via_provider(policy="factory_async")`

        Create [.FactoryAsyncCorePlugin][]. Your plug
        callable will be invoked and awaited every time host
        subject is requested in runtime.
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
    ) -> PluginSelectorProtocol[Any, MetaData]:
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
    ) -> ProvidingPluginSelectorProtocol[Any, MetaData]:
        """
        Plug the result of Your callable into NON-OBVIOUS host type.
        Proceed with `.via_provider` (or sometimes with `.directly`) to
        finish Your plugin creation, but be careful
        about plugin runtime type consistency.
        """
        ...


class CoroutinePlugFacadeProtocol[T, MetaData](Protocol):
    @overload
    @abstractmethod
    def into(
        self, subject: type[T], *marks: Hashable
    ) -> TypedCoroutinePluginSelectorProtocol[T, MetaData]:
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
    ) -> CoroutinePluginSelectorProtocol[Any, MetaData]:
        """
        Plug the result of Your callable into NON-OBVIOUS host type.
        Proceed with `.via_provider` (or sometimes with `.directly`) to
        finish Your plugin creation, but be careful
        about plugin runtime type consistency.
        """
        ...
