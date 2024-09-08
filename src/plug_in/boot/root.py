import threading
from typing import Any, Callable, Sequence
from plug_in.core.enum import PluginPolicy
from plug_in.core.host import CoreHost
from plug_in.core.plug import CorePlug
from plug_in.core.plugin import create_core_plugin
from plug_in.core.registry import CoreRegistry
from plug_in.exc import ConfigError
from plug_in.ioc.router import Router
from plug_in.types.alias import Manageable
from plug_in.types.proto.core_plugin import (
    BindingCorePluginProtocol,
    ProvidingCorePluginProtocol,
)


type RootRegistry = CoreRegistry
type RootRouter = Router


def get_root_registry() -> RootRegistry:
    return BootstrapWizard().root_registry


def get_root_router() -> RootRouter:
    return BootstrapWizard().root_router


def manage[T: Manageable]() -> Callable[[T], T]:
    return get_root_router().manage()


class _NoArgSingleton(type):
    _instance = None

    def __call__(cls):
        if cls._instance is None:
            cls._instance = super(_NoArgSingleton, cls).__call__()
        return cls._instance


# I want some syntactic sugar for globals, so singleton
class BootstrapWizard(metaclass=_NoArgSingleton):
    """
    A singleton class for convenient global plug_in initialization.
    """

    def __init__(
        self,
    ) -> None:
        self._router = Router()
        self._registry: CoreRegistry | None = None
        self._lock = threading.RLock()

    def configure_root_registry(
        self,
        plugins: Sequence[
            BindingCorePluginProtocol[Any] | ProvidingCorePluginProtocol[Any]
        ] = (),
    ) -> None:
        """
        Creates and configures root registry. This method is intended to be called only
        once. Calling it second time will raise [plug_in.exc.ConfigError][]
        """
        with self._lock:
            if self._registry is not None:
                raise ConfigError("Root registry is already configured!")

            self._registry = self._create_registry(self._router, plugins)

    def get_root_registry(self) -> RootRegistry:
        """
        Get root registry. If root registry is not configured, then
        [plug_in.exc.ConfigError][] will be raised.
        """
        if self._registry is None:
            raise ConfigError(
                "Root registry is not yet configured. "
                f"Call `{self.__class__.__name__}().configure_root_registry(...)` first"
            )

        return self._registry

    @property
    def root_registry(self) -> RootRegistry:
        return self.get_root_registry()

    def get_root_router(self) -> RootRouter:
        return self._router

    @property
    def root_router(self) -> RootRouter:
        return self.get_root_router()

    def _create_registry(
        self,
        router: RootRouter,
        plugins: Sequence[
            BindingCorePluginProtocol[Any] | ProvidingCorePluginProtocol[Any]
        ],
    ) -> RootRegistry:
        """
        Returns registry with two plugins: one for itself and one for router
        """

        reg_plugin = create_core_plugin(
            plug=CorePlug(self.get_root_registry),
            host=CoreHost(RootRegistry),
            policy=PluginPolicy.LAZY,
        )

        router_plugin = create_core_plugin(
            CorePlug(router), CoreHost(RootRouter), PluginPolicy.DIRECT
        )

        reg = CoreRegistry([reg_plugin, router_plugin, *plugins])

        router.mount(reg)

        return reg
