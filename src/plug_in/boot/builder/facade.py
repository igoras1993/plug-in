from typing import (
    Callable,
    Hashable,
    Union,
    overload,
)
from plug_in.boot.builder.proto import (
    PlugFacadeProtocol,
    PluginSelectorProtocol,
    ProvidingPlugFacadeProtocol,
    ProvidingPluginSelectorProtocol,
    TypedPluginSelectorProtocol,
    TypedProvidingPluginSelectorProtocol,
)
from plug_in.boot.builder.selector import (
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
