from types import NotImplementedType
from typing import Callable, Hashable, Literal, overload
from plug_in.boot.builder.proto import (
    PluginSelectorProtocol,
    ProvidingPluginSelectorProtocol,
    TypedPluginSelectorProtocol,
    TypedProvidingPluginSelectorProtocol,
)
from plug_in.core.host import CoreHost
from plug_in.core.plug import CorePlug
from plug_in.core.plugin import DirectCorePlugin, FactoryCorePlugin, LazyCorePlugin


# class PluginSelector[P](PluginSelectorProtocol):
#     def __init__(self, provider: P, sub: Hashable, *marks: Hashable):
#         self._provider = provider
#         self._sub = sub
#         self._marks = marks

#     def directly(self) -> DirectCorePlugin[P]:
#         """
#         Create [.DirectCorePlugin][] for non-obvious host type. Please
#         revise plugin configuration is such case.

#         Always be careful about typing in non-obvious host subject type.
#         """
#         return DirectCorePlugin(
#             CorePlug(self._provider), CoreHost(self._sub, self._marks)
#         )


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


class ProvidingPluginSelector[P](ProvidingPluginSelectorProtocol):
    def __init__(self, provider: Callable[[], P], sub: Hashable, *marks: Hashable):
        self._provider = provider
        self._sub = sub
        self._marks = marks

    def directly(self) -> DirectCorePlugin[Callable[[], P]]:
        """
        Create [.DirectCorePlugin][] for non-obvious host type. Please
        revise plugin configuration is such case. This plugin routine is
        equivalent to [.PluginSelector.directly]. Revise Your configuration.

        Always be careful about typing in non-obvious host subject type.
        """
        return DirectCorePlugin(
            CorePlug(self._provider), CoreHost(self._sub, self._marks)
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


class TypedProvidingPluginSelector[P](TypedProvidingPluginSelectorProtocol):
    def __init__(self, provider: Callable[[], P], sub: type[P], *marks: Hashable):
        self._provider = provider
        self._sub = sub
        self._marks = marks

    def directly(self) -> NotImplementedType:
        """
        USAGE PROHIBITED.

        This method exists only for type-consistency purpose. It will
        raise NotImplementedError every time. You cannot plug callable
        directly into typed host. Usage is allowed only for non-typed
        hosts, or use a `via_provider` instead.
        """
        raise NotImplementedError("Type mismatch between provider and host")

    @overload
    def via_provider(self, policy: Literal["lazy"]) -> LazyCorePlugin[P]:
        """
        Create [.LazyCorePlugin][] for well-known host. Your plug
        callable will be invoked once host subject is requested in runtime,
        and then the result from this callable will be always used in place
        of host subject.

        """
        ...

    @overload
    def via_provider(self, policy: Literal["factory"]) -> FactoryCorePlugin[P]:
        """
        Create [.FactoryCorePlugin][] for well-known host. Your plug
        callable will be invoked every time host subject is requested in runtime.
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
                return LazyCorePlugin(
                    CorePlug(self._provider), CoreHost(self._sub, self._marks)
                )
