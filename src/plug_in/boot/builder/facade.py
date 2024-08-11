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


class PlugFacade[T](PlugFacadeProtocol[T]):

    def __init__(self, provider: T):
        self._provider = provider

    @overload
    def into(
        self, subject: type[T], *marks: Hashable
    ) -> TypedPluginSelectorProtocol[T]:
        """
        Plug Your instance into host of well-known type. Proceed with
        `.directly` / `.via_provider` to finish plugin creation.
        """
        ...

    @overload
    def into(self, subject: Hashable, *marks: Hashable) -> PluginSelectorProtocol[T]:
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
        PluginSelectorProtocol[T],
        TypedPluginSelectorProtocol[T],
    ]:
        return PluginSelector(self._provider, subject, *marks)


class ProvidingPlugFacade[T](ProvidingPlugFacadeProtocol[T]):

    def __init__(self, provider: Callable[[], T]):
        self._provider = provider

    @overload
    def into(
        self, subject: type[T], *marks: Hashable
    ) -> TypedProvidingPluginSelectorProtocol[T]:
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
    ) -> ProvidingPluginSelectorProtocol[T]:
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
        ProvidingPluginSelectorProtocol[T],
        TypedProvidingPluginSelectorProtocol[T],
    ]:
        return ProvidingPluginSelector(self._provider, subject, *marks)
