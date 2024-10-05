from types import NotImplementedType
from typing import Awaitable, Callable, Hashable, Literal, overload
from plug_in.boot.builder.proto import (
    CoroutinePluginSelectorProtocol,
    PluginSelectorProtocol,
    ProvidingPluginSelectorProtocol,
    TypedCoroutinePluginSelectorProtocol,
    TypedPluginSelectorProtocol,
    TypedProvidingPluginSelectorProtocol,
)
from plug_in.core.asyncio.plugin import FactoryAsyncCorePlugin, LazyAsyncCorePlugin
from plug_in.core.host import CoreHost
from plug_in.core.plug import CorePlug
from plug_in.core.plugin import DirectCorePlugin, FactoryCorePlugin, LazyCorePlugin


class PluginSelector[P, MetaData](
    PluginSelectorProtocol[P, MetaData], TypedPluginSelectorProtocol[P, MetaData]
):
    def __init__(
        self,
        provider: P,
        sub: type[P] | Hashable,
        *marks: Hashable,
        metadata: MetaData = None,
    ):
        self._provider = provider
        self._sub = sub
        self._marks = marks
        self._metadata = metadata

    def directly(self) -> DirectCorePlugin[P, MetaData]:
        """
        Create [.DirectCorePlugin][]. This method implements both protocols.
        """
        return DirectCorePlugin(
            CorePlug(self._provider),
            CoreHost(self._sub, self._marks),
            _metadata=self._metadata,
        )


class ProvidingPluginSelector[P, MetaData](
    ProvidingPluginSelectorProtocol[P, MetaData],
    TypedProvidingPluginSelectorProtocol[P, MetaData],
):
    def __init__(
        self,
        provider: Callable[[], P],
        sub: Hashable | type[P],
        *marks: Hashable,
        metadata: MetaData = None,
    ):
        self._provider = provider
        self._sub = sub
        self._marks = marks
        self._metadata = metadata

    def directly(
        self,
    ) -> DirectCorePlugin[Callable[[], P], MetaData] | NotImplementedType:
        """
        Create [.DirectCorePlugin][] or fail for not allowed policy. This
        method implements both protocols.

        Raises NotImplementedError() when attempt on creating typed plugin
        directly with mismatched types.
        """
        # TODO: This implementation does not work. Make it fail at least for some cases

        # # Checking for one and only not allowed case. Both are callables, but
        # # subject return type does not match provider return type
        # provider_sig = inspect.signature(self._provider, eval_str=True)
        # if isinstance(self._sub, type):
        #     # Callable as provider and typed subject. This is not an error
        #     # only for directly plugging a callable to the "factory like"
        #     # type.
        #     # I am not a type checker developer, so here I will be permissive and
        #     # narrow the failing scenario only to matching return types of
        #     # both callables.

        #     # Getting a __call__ through hasattr to also address metaclass slots
        #     call_of_sub = getattr(self._sub, "__call__")
        #     sig_of_sub = inspect.signature(call_of_sub, eval_str=True)

        #     # Get rid of type parametrization if any exists
        #     provider_return_origin = get_origin(provider_sig.return_annotation)
        #     sub_return_origin = get_origin(sig_of_sub.return_annotation)
        #     if (
        #         isinstance(provider_return_origin, type)
        #         and isinstance(sub_return_origin, type)
        #         and not issubclass(provider_return_origin, sub_return_origin)
        #     ):
        #         # Return type of provider is subtype of host return type
        #         raise TypeError(
        #             f"Signature of provider {provider_sig} does not match "
        #             f"the signature of host subject {sig_of_sub}"
        #         )

        return DirectCorePlugin(
            CorePlug(self._provider),
            CoreHost(self._sub, self._marks),
            _metadata=self._metadata,
        )

    @overload
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
    def via_provider(
        self, policy: Literal["factory"]
    ) -> FactoryCorePlugin[P, MetaData]:
        """
        Create [.FactoryCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked every time host subject is requested in runtime.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    def via_provider(
        self, policy: Literal["lazy", "factory"]
    ) -> FactoryCorePlugin[P, MetaData] | LazyCorePlugin[P, MetaData]:

        match policy:
            case "lazy":
                return LazyCorePlugin(
                    CorePlug(self._provider),
                    CoreHost(self._sub, self._marks),
                    _metadata=self._metadata,
                )
            case "factory":
                return FactoryCorePlugin(
                    CorePlug(self._provider),
                    CoreHost(self._sub, self._marks),
                    _metadata=self._metadata,
                )
            case _:
                raise RuntimeError(f"{policy=} is not implemented")


class CoroutinePluginSelector[P, MetaData](
    CoroutinePluginSelectorProtocol[P, MetaData],
    TypedCoroutinePluginSelectorProtocol[P, MetaData],
):
    def __init__(
        self,
        provider: Callable[[], Awaitable[P]],
        sub: Hashable | type[P],
        *marks: Hashable,
        metadata: MetaData = None,
    ):
        self._provider = provider
        self._sub = sub
        self._marks = marks
        self._metadata = metadata

    def directly(
        self,
    ) -> DirectCorePlugin[Callable[[], Awaitable[P]], MetaData] | NotImplementedType:
        """
        Create [.DirectCorePlugin][] or fail for not allowed policy. This
        method implements both protocols.

        Raises NotImplementedError() when attempt on creating typed plugin
        directly with mismatched types.
        """
        # TODO: Make it fail at least for some cases

        return DirectCorePlugin(
            CorePlug(self._provider),
            CoreHost(self._sub, self._marks),
            _metadata=self._metadata,
        )

    @overload
    def via_provider(
        self, policy: Literal["lazy"]
    ) -> LazyCorePlugin[Awaitable[P], MetaData] | NotImplementedType:
        """
        Create [.LazyCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked once host subject is requested in runtime,
        and then the result from this callable will be always used in place
        of host subject.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    @overload
    def via_provider(
        self, policy: Literal["factory"]
    ) -> FactoryCorePlugin[Awaitable[P], MetaData] | NotImplementedType:
        """
        Create [.FactoryCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked every time host subject is requested in runtime.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    @overload
    def via_provider(
        self, policy: Literal["lazy_async"]
    ) -> LazyAsyncCorePlugin[P, MetaData]:
        """
        Create [.LazyAsyncCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked and awaited once host subject is requested in
        runtime, and then the result from this callable will be always used in
        place of host subject.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    @overload
    def via_provider(
        self, policy: Literal["factory_async"]
    ) -> FactoryAsyncCorePlugin[P, MetaData]:
        """
        Create [.FactoryAsyncCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked and awaited every time host subject is
        requested in runtime.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    @overload
    def via_async_provider(
        self, policy: Literal["lazy"]
    ) -> LazyAsyncCorePlugin[P, MetaData]:
        """
        Alias on `.via_provider(policy="lazy_async")`

        Create [.LazyAsyncCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked and awaited once host subject is requested in
        runtime, and then the result from this callable will be always used in
        place of host subject.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    @overload
    def via_async_provider(
        self, policy: Literal["factory"]
    ) -> FactoryAsyncCorePlugin[P, MetaData]:
        """
        Alias on `.via_provider(policy="factory_async")`

        Create [.FactoryAsyncCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked and awaited every time host subject is
        requested in runtime.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    def via_provider(
        self, policy: Literal["lazy_async", "factory_async", "lazy", "factory"]
    ) -> (
        FactoryAsyncCorePlugin[P, MetaData]
        | LazyAsyncCorePlugin[P, MetaData]
        | FactoryCorePlugin[Awaitable[P], MetaData]
        | LazyCorePlugin[Awaitable[P], MetaData]
    ):

        match policy:
            case "lazy_async":
                return LazyCorePlugin(
                    CorePlug(self._provider),
                    CoreHost(self._sub, self._marks),
                    _metadata=self._metadata,
                )
            case "factory_async":
                return FactoryCorePlugin(
                    CorePlug(self._provider),
                    CoreHost(self._sub, self._marks),
                    _metadata=self._metadata,
                )
            case "lazy":
                return LazyAsyncCorePlugin(
                    CorePlug(self._provider),
                    CoreHost(self._sub, self._marks),
                    _metadata=self._metadata,
                )
            case "factory":
                return FactoryAsyncCorePlugin(
                    CorePlug(self._provider),
                    CoreHost(self._sub, self._marks),
                    _metadata=self._metadata,
                )
            case _:
                raise RuntimeError(f"{policy=} is not implemented")

    def via_async_provider(
        self, policy: Literal["lazy", "factory"]
    ) -> LazyAsyncCorePlugin[P, MetaData] | FactoryAsyncCorePlugin[P, MetaData]:
        match policy:
            case "lazy":
                return self.via_provider(policy="lazy_async")
            case "factory":
                return self.via_provider(policy="factory_async")
            case _:
                raise RuntimeError(f"{policy=} is not implemented")
