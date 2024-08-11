import inspect
from types import NotImplementedType
from typing import Callable, Hashable, Literal, get_origin, overload
from plug_in.boot.builder.proto import (
    PluginSelectorProtocol,
    ProvidingPluginSelectorProtocol,
    TypedPluginSelectorProtocol,
    TypedProvidingPluginSelectorProtocol,
)
from plug_in.core.host import CoreHost
from plug_in.core.plug import CorePlug
from plug_in.core.plugin import DirectCorePlugin, FactoryCorePlugin, LazyCorePlugin


class PluginSelector[P](PluginSelectorProtocol, TypedPluginSelectorProtocol):
    def __init__(self, provider: P, sub: type[P] | Hashable, *marks: Hashable):
        self._provider = provider
        self._sub = sub
        self._marks = marks

    def directly(self) -> DirectCorePlugin[P]:
        """
        Create [.DirectCorePlugin][]. This method implements both protocols.
        """
        return DirectCorePlugin(
            CorePlug(self._provider), CoreHost(self._sub, self._marks)
        )


class ProvidingPluginSelector[P](
    ProvidingPluginSelectorProtocol, TypedProvidingPluginSelectorProtocol
):
    def __init__(
        self, provider: Callable[[], P], sub: Hashable | type[P], *marks: Hashable
    ):
        self._provider = provider
        self._sub = sub
        self._marks = marks

    def directly(self) -> DirectCorePlugin[Callable[[], P]] | NotImplementedType:
        """
        Create [.DirectCorePlugin][] or fail for not allowed policy. This
        method implements both protocols.

        Raises NotImplementedError() when attempt on creating typed plugin
        directly with mismatched types.
        """
        # TODO: This implementation does not work. Make it fail at least for some cases

        # Checking for one and only not allowed case. Both are callables, but
        # subject return type does not match provider return type
        provider_sig = inspect.signature(self._provider, eval_str=True)
        if isinstance(self._sub, type):
            # Callable as provider and typed subject. This is not an error
            # only for directly plugging a callable to the "factory like"
            # type.
            # I am not a type checker developer, so here I will be permissive and
            # narrow the failing scenario only to matching return types of
            # both callables.

            # Getting a __call__ through hasattr to also address metaclass slots
            call_of_sub = getattr(self._sub, "__call__")
            sig_of_sub = inspect.signature(call_of_sub, eval_str=True)

            # Get rid of type parametrization if any exists
            provider_return_origin = get_origin(provider_sig.return_annotation)
            sub_return_origin = get_origin(sig_of_sub.return_annotation)
            if (
                isinstance(provider_return_origin, type)
                and isinstance(sub_return_origin, type)
                and not issubclass(provider_return_origin, sub_return_origin)
            ):
                # Return type of provider is subtype of host return type
                raise TypeError(
                    f"Signature of provider {provider_sig} does not match "
                    f"the signature of host subject {sig_of_sub}"
                )

        return DirectCorePlugin(
            CorePlug(self._provider),
            CoreHost(self._sub, self._marks),
        )

    @overload
    def via_provider(self, policy: Literal["lazy"]) -> LazyCorePlugin[P]:
        """
        Create [.LazyCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked once host subject is requested in runtime,
        and then the result from this callable will be always used in place
        of host subject.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    @overload
    def via_provider(self, policy: Literal["factory"]) -> FactoryCorePlugin[P]:
        """
        Create [.FactoryCorePlugin][] for non-obvious host type. Your plug
        callable will be invoked every time host subject is requested in runtime.

        Always be careful about typing in non-obvious host subject type.
        """
        ...

    def via_provider(
        self, policy: Literal["lazy", "factory"]
    ) -> FactoryCorePlugin[P] | LazyCorePlugin[P]:

        match policy:
            case "lazy":
                return LazyCorePlugin(
                    CorePlug(self._provider), CoreHost(self._sub, self._marks)
                )
            case "factory":
                return FactoryCorePlugin(
                    CorePlug(self._provider), CoreHost(self._sub, self._marks)
                )
            case _:
                raise RuntimeError(f"{policy=} is not implemented")
