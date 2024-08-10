from typing import Callable
from plug_in.core.enum import PluginPolicy
from plug_in.core.host import CoreHost
from plug_in.core.plug import CorePlug
from plug_in.core.plugin import create_core_plugin
from plug_in.core.registry import CoreRegistry
from plug_in.ioc.router import Router
from plug_in.types.alias import Manageable


type RootRegistry = CoreRegistry
type RootRouter = Router


def get_root_registry() -> RootRegistry:
    return BootstrapWizard().root_registry


def get_root_router() -> RootRouter:
    return BootstrapWizard().root_router


def manage[T: Manageable]() -> Callable[[T], T]:
    return get_root_router().manage()


class _Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# I want some syntactic sugar for globals
class BootstrapWizard(metaclass=_Singleton):
    """
    A singleton class for global plug_in initialization. Create wizard Yourself
    if You want to posses it, or leave it alone and plugin boot methods will
    work anyway.
    """

    def __init__(self) -> None:
        self._router = Router()
        self._registry = self.create_registry(self._router)

    def get_root_registry(self) -> RootRegistry:
        return self._registry

    @property
    def root_registry(self) -> RootRegistry:
        return self.get_root_registry()

    def get_root_router(self) -> RootRouter:
        return self._router

    @property
    def root_router(self) -> RootRouter:
        return self.get_root_router()

    def create_registry(self, router: RootRouter) -> RootRegistry:
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

        reg = CoreRegistry([reg_plugin, router_plugin])

        router.mount(reg)

        return reg
