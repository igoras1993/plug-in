from typing import (
    Awaitable,
    Callable,
    Hashable,
    Union,
    overload,
)
from plug_in.boot.builder.proto import (
    CoroutinePlugFacadeProtocol,
    CoroutinePluginSelectorProtocol,
    PlugFacadeProtocol,
    PluginSelectorProtocol,
    ProvidingPlugFacadeProtocol,
    ProvidingPluginSelectorProtocol,
    TypedCoroutinePluginSelectorProtocol,
    TypedPluginSelectorProtocol,
    TypedProvidingPluginSelectorProtocol,
)
from plug_in.boot.builder.selector import (
    CoroutinePluginSelector,
    PluginSelector,
    ProvidingPluginSelector,
)


class PlugFacade[T, MetaData](PlugFacadeProtocol[T, MetaData]):

    def __init__(self, provider: T, metadata: MetaData = None):
        self._provider = provider
        self._metadata = metadata

    @overload
    def into(
        self, subject: type[T], *marks: Hashable
    ) -> TypedPluginSelectorProtocol[T, MetaData]:
        """
        Plug Your instance into host of well-known type. Proceed with
        `.directly` / `.via_provider` to finish plugin creation.
        """
        ...

    @overload
    def into(
        self, subject: Hashable, *marks: Hashable
    ) -> PluginSelectorProtocol[T, MetaData]:
        """
        Plug Your instance into host of NON-OBVIOUS type. Proceed with
        `.directly` / `.via_provider` to finish plugin creation, but be careful
        about plugin runtime type consistency.
        """
        ...

    def into(
        self,
        subject: Union[Hashable, type[T]],
        *marks: Hashable,
    ) -> Union[
        PluginSelectorProtocol[T, MetaData],
        TypedPluginSelectorProtocol[T, MetaData],
    ]:
        return PluginSelector(self._provider, subject, *marks, metadata=self._metadata)


class ProvidingPlugFacade[T, MetaData](ProvidingPlugFacadeProtocol[T, MetaData]):

    def __init__(self, provider: Callable[[], T], metadata: MetaData = None):
        self._provider = provider
        self._metadata = metadata

    @overload
    def into(
        self, subject: type[T], *marks: Hashable
    ) -> TypedProvidingPluginSelectorProtocol[T, MetaData]:
        """
        Plug the result of Your callable into well known host type.
        Proceed with `.via_provider` (or sometimes with `.directly`) to
        finish Your plugin creation.

        This will fail with RuntimeError if subject is a type and provider ...
        """
        ...

    @overload
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

    def into(
        self,
        subject: Union[Hashable, type[T]],
        *marks: Hashable,
    ) -> Union[
        ProvidingPluginSelectorProtocol[T, MetaData],
        TypedProvidingPluginSelectorProtocol[T, MetaData],
    ]:
        return ProvidingPluginSelector(
            self._provider, subject, *marks, metadata=self._metadata
        )


class CoroutinePlugFacade[T, MetaData](CoroutinePlugFacadeProtocol[T, MetaData]):

    def __init__(self, provider: Callable[[], Awaitable[T]], metadata: MetaData = None):
        self._provider = provider
        self._metadata = metadata

    @overload
    def into(
        self, subject: type[T], *marks: Hashable
    ) -> TypedCoroutinePluginSelectorProtocol[T, MetaData]:
        """
        Plug the result of Your callable into well known host type.
        Proceed with `.via_async_provider` to
        finish Your plugin creation.
        """
        ...

    @overload
    def into(
        self, subject: Hashable, *marks: Hashable
    ) -> CoroutinePluginSelectorProtocol[T, MetaData]:
        """
        Plug the result of Your callable into NON-OBVIOUS host type.
        Proceed with `.via_async_provider` (or sometimes with `.directly`) to
        finish Your plugin creation, but be careful
        about plugin runtime type consistency.
        """
        ...

    def into(
        self,
        subject: Union[Hashable, type[T]],
        *marks: Hashable,
    ) -> Union[
        CoroutinePluginSelectorProtocol[T, MetaData],
        TypedCoroutinePluginSelectorProtocol[T, MetaData],
    ]:
        return CoroutinePluginSelector(
            self._provider, subject, *marks, metadata=self._metadata
        )
