import threading
from typing import Any, Callable, Concatenate, Iterable, Union
from plug_in.boot.builder.builder import plug
from plug_in.core.registry import CoreRegistry
from plug_in.exc import BootConfigError
from plug_in.ioc.router import Router
from plug_in.types.alias import Manageable
from plug_in.types.proto.core_plugin import (
    CorePluginProtocol,
)
from plug_in.types.proto.core_registry import (
    CoreRegistryProtocol,
)
from plug_in.types.proto.router import RouterProtocol


type RootRegistry = CoreRegistryProtocol
type RootRouter = RouterProtocol

_boot_lock: threading.RLock = threading.RLock()
_root_config: Union["RootConfig[Any, Any]", None] = None


class _RootCfgMeta(type):

    def __call__(cls, *args, **kwargs):
        global _root_config

        with _boot_lock:
            if _root_config is not None:
                raise BootConfigError(
                    f"RootConfig is already present: {_root_config} and initialized. "
                    "You cannot override root config once root is initialized"
                )
            cfg = super(_RootCfgMeta, cls).__call__(*args, **kwargs)
            _root_config = cfg
            return cfg


class RootConfig[RegCls: CoreRegistryProtocol, RouterCls: RouterProtocol](
    metaclass=_RootCfgMeta
):
    """
    A configuration class for "root" things in bootstrap module. This is just
    simplification of plug-in library setup for most of the use-cases.

    Root config allows You to define factories for router and registry classes.

    When root registry is initialized (`[.RootRegistry.init_root_registry][]`
    was invoked) - You can start using `[.get_root_registry][]`.

    `[.get_root_router][]` and `[.get_root_config][]` functions operate on
    existing RootConfig and if no config found - they are creating a new default one.

    You can pass setup params for already created RootConfig by calling
    `[.RootConfig.set_registry_config][]`.

    Root config is a singleton class. Moreover, You can have only one
    instance of it ever created in one process. It should be thread safe.

    Attempt to creating more than one RootConfig results in `[.BootConfigError][]`.

    You can get already created RootConfig instance by calling [.get_root_config][]`.
    """

    def __init__(
        self,
        reg_class: Callable[
            Concatenate[Iterable[CorePluginProtocol[Any, Any]], ...], RegCls
        ] = CoreRegistry,
        router_class: Callable[..., RouterCls] = Router,
        reg_default_kwargs: dict[str, Any] | None = None,
        router_default_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self._reg_class = reg_class
        self._router_class = router_class
        self._reg_default_kwargs: dict[str, Any] = (
            reg_default_kwargs if reg_default_kwargs is not None else dict()
        )
        self._router_default_kwargs: dict[str, Any] = (
            router_default_kwargs if router_default_kwargs is not None else dict()
        )

        # Simple lazy loading done here
        self._router: RouterCls | None = None

        # Registry will be delayed
        self._is_reg_initialized: bool = False
        self._registry: RegCls | None = None

    def set_registry_config(
        self,
        reg_class: Callable[
            Concatenate[Iterable[CorePluginProtocol[Any, Any]], ...], RegCls
        ] = CoreRegistry,
        reg_default_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """
        Overwrite registry configuration passed in __init__. This method can be
        called only when root registry was not yet initialized. Otherwise
        `[.BootConfigError][]` will be raised.
        """
        with _boot_lock:
            if self._is_root_initialized:
                raise BootConfigError(
                    "Cannot set registry config when registry is already initialized"
                )
            else:
                self._reg_class = reg_class
                self._reg_default_kwargs: dict[str, Any] = (
                    reg_default_kwargs if reg_default_kwargs is not None else dict()
                )

    @property
    def is_root_registry_initialized(self) -> bool:
        return self._is_root_initialized

    def get_registry(self) -> RegCls:
        """
        Get root registry. If it is not initialized, raises `[.BootConfigError][]`
        """
        if self._registry is None:
            raise BootConfigError(
                "Root is not initialized, use `.init_root_registry` first."
            )

        return self._registry

    def get_router(self) -> RouterCls:
        with _boot_lock:
            if self._router is None:
                router = self._make_router()
                self._router = router
            else:
                router = self._router

        return router

    def _make_registry(
        self,
        plugins: Iterable[CorePluginProtocol],
        **kwargs: dict[str, Any],
    ) -> RegCls:
        """
        Create registry instance from config
        """
        return self._reg_class(plugins, **{**self._reg_default_kwargs, **kwargs})

    def _make_router(self, **kwargs: dict[str, Any]) -> RouterCls:
        """
        Create registry instance from config
        """
        return self._router_class(**{**self._router_default_kwargs, **kwargs})

    def _root_registry_provider(self) -> Callable[[], RootRegistry]:
        return self.get_registry

    def _root_router_provider(self) -> Callable[[], RootRouter]:
        return self.get_router

    def init_root_registry(
        self,
        plugins: Iterable[CorePluginProtocol],
        include_default_plugins: bool = True,
        reg_kwargs: dict[str, Any] | None = None,
    ) -> None:
        """
        Creates root registry with provided plugins. Mounts root router to newly
        created registry.

        Args:
            plugins: List of plugins to be included in root registry
            include_default_plugins: If `True` (default), three additional plugins
                will be automatically included in root registry:
                - for `RootRouter` - provides root router from config
                - for `RootRegistry` - provides root registry itself
                - for `RootConfig` - provides root config
            reg_kwargs: Additional keyword arguments that will be passed to registry
                factory
        """
        with _boot_lock:
            if self._is_reg_initialized:
                raise BootConfigError(f"Root already initialized with config: {self}")

            use_reg_kwargs = reg_kwargs if reg_kwargs is not None else dict()

            if include_default_plugins:
                use_plugins = [
                    *plugins,
                    plug(self._root_registry_provider())
                    .into(RootRegistry)
                    .via_provider(policy="lazy"),
                    plug(self._root_router_provider())
                    .into(RootRouter)
                    .via_provider(policy="lazy"),
                    plug(self).into(RootConfig).directly(),
                ]
            else:
                use_plugins = plugins

            self._registry = self._make_registry(
                use_plugins,
                **use_reg_kwargs,
            )
            self.get_router().mount(self._registry)

            self._is_root_initialized = True


def get_root_config() -> RootConfig[CoreRegistryProtocol, RouterProtocol]:
    """
    Returns already created `RootConfig` or new one if no root config exists
    in application process.
    """
    with _boot_lock:
        is_root_cfg_none = _root_config is None

    if is_root_cfg_none:
        return RootConfig()

    else:
        assert _root_config is not None
        return _root_config


def get_root_registry() -> RootRegistry:
    return get_root_config().get_registry()


def get_root_router() -> RootRouter:
    return get_root_config().get_router()


def manage[T: Manageable]() -> Callable[[T], T]:
    return get_root_router().manage()
