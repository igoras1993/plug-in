from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass
from enum import StrEnum
import inspect
import logging
from typing import Any, Awaitable, Callable, Literal, Self, cast, get_type_hints
from plug_in.core.host import CoreHost
from plug_in.exc import (
    EmptyHostAnnotationError,
    ObjectNotSupported,
    SyncPluginExpected,
    UnexpectedForwardRefError,
)
from plug_in.ioc.hosted_mark import HostedMark
from plug_in.tools.introspect import contains_forward_refs, is_coroutine_callable
from plug_in.types.proto.core_host import CoreHostProtocol
from plug_in.types.proto.core_plugin import CorePluginProtocol
from plug_in.types.proto.hosted_mark import HostedMarkProtocol
from plug_in.types.proto.joint import Joint
from plug_in.types.proto.parameter import (
    FinalParamStageProtocol,
    FinalParamsProtocol,
    ParamsStateMachineProtocol,
)


class ParamsStateType(StrEnum):
    NOTHING_READY = "NOTHING_READY"
    DEFAULT_READY = "DEFAULT_READY"
    HOST_READY = "HOST_READY"
    PLUGIN_READY = "PLUGIN_READY"


@dataclass
class PluginParamStage[T: HostedMarkProtocol, JointType: Joint, MetaDataType](
    FinalParamStageProtocol[T, JointType, MetaDataType]
):
    _name: str
    _default: T
    _host: CoreHostProtocol[JointType]
    _plugin: CorePluginProtocol[JointType, MetaDataType]

    @property
    def name(self) -> str:
        return self._name

    @property
    def default(self) -> T:
        return self._default

    @property
    def host(self) -> CoreHostProtocol[JointType]:
        return self._host

    @property
    def plugin(self) -> CorePluginProtocol[JointType, MetaDataType]:
        return self._plugin


@dataclass
class HostParamStage[T: HostedMarkProtocol, JointType: Joint]:
    _name: str
    _default: T
    _host: CoreHostProtocol[JointType]

    @property
    def name(self) -> str:
        return self._name

    @property
    def default(self) -> T:
        return self._default

    @property
    def host(self) -> CoreHostProtocol[JointType]:
        return self._host


@dataclass
class DefaultParamStage[T: HostedMarkProtocol]:
    """
    Annotation is available and validated
    """

    _name: str
    _default: T

    @property
    def name(self) -> str:
        return self._name

    @property
    def default(self) -> T:
        return self._default


@dataclass
class NothingParamStage:
    pass


class ParamsStateMachine(ABC, ParamsStateMachineProtocol):

    @property
    @abstractmethod
    def callable(self) -> Callable: ...

    @property
    @abstractmethod
    def state_type(self) -> ParamsStateType: ...

    @abstractmethod
    def advance(self) -> "ParamsStateMachine": ...

    def is_final(self) -> bool:
        return self.state_type == ParamsStateType.PLUGIN_READY

    def assert_final(self) -> "PluginParams":
        """
        Return self if it is a final state, or raise ValueError.
        """
        if self.is_final():
            return cast(PluginParams, self)
        else:
            raise AssertionError("This is not a final state.")

    def finalize(self) -> "PluginParams":
        """
        Advance to the final state or raise any of the advancing stage exceptions.
        """
        state = self

        while not state.is_final():
            state = state.advance()

        return state.assert_final()


@dataclass
class PluginParams[T: HostedMarkProtocol](ParamsStateMachine, FinalParamsProtocol):
    _params: list[PluginParamStage[T, Joint, Any]]
    _type_hints: dict[str, Any]
    _sig: inspect.Signature
    _callable: Callable
    _plugin_lookup: Callable[[CoreHostProtocol[Any]], CorePluginProtocol[Joint, Any]]
    _state_type: Literal[ParamsStateType.PLUGIN_READY] = ParamsStateType.PLUGIN_READY

    @property
    def params(self) -> list[PluginParamStage[T, Joint, Any]]:
        return self._params

    @property
    def type_hints(self) -> dict[str, Any]:
        return self._type_hints

    @property
    def sig(self) -> inspect.Signature:
        return self._sig

    @property
    def callable(self) -> Callable:
        return self._callable

    @property
    def plugin_lookup(self) -> Callable[[CoreHostProtocol], CorePluginProtocol]:
        return self._plugin_lookup

    @property
    def state_type(self) -> Literal[ParamsStateType.PLUGIN_READY]:
        return self._state_type

    def is_callable_a_coro_callable(self) -> bool:
        """
        Returns `True` if callable returns a coroutine.
        """
        return is_coroutine_callable(self.callable)

    def advance(self) -> Self:
        return self

    def _get_resolver_map_cache(
        self,
    ) -> tuple[
        dict[str, Callable[[], Joint]],
        dict[str, Callable[[], Awaitable[Joint]]],
    ]:
        """
        Return tuple of both sync and async resolver mappings or raise AttributeError
        when cache is empty.
        """
        return getattr(self, "_resolver_cache")

    def _build_resolver_map_cache(
        self,
    ) -> tuple[
        dict[str, Callable[[], Joint]],
        dict[str, Callable[[], Awaitable[Joint]]],
    ]:
        """
        Calculate both resolver mappings (sync and async), store it in cache and return
        tuple of them (sync_map, async_map)
        """
        sync_map: dict[str, Callable[[], Joint]] = {}
        async_map: dict[str, Callable[[], Awaitable[Joint]]] = {}

        for param in self.params:
            try:
                sync_plugin = param.plugin.assert_sync()
            except AssertionError:
                try:
                    async_plugin = param.plugin.assert_async()
                except AssertionError as e:
                    raise RuntimeError(
                        f"{param.plugin=} is neither sync or async, panic."
                    ) from e
                else:
                    # Async path
                    async_map[param.name] = async_plugin.provide
            else:
                # Sync path
                sync_map[param.name] = sync_plugin.provide

        both = (sync_map, async_map)
        setattr(self, "_resolver_cache", both)
        return both

    def sync_resolver_map(
        self,
    ) -> dict[str, Callable[[], Joint]]:
        """
        Returns prepared map of parameter names to their synchronous resolvers.
        """
        try:
            sync_map, _ = self._get_resolver_map_cache()
        except AttributeError:
            sync_map, _ = self._build_resolver_map_cache()

        return copy(sync_map)

    def async_resolver_map(self) -> dict[str, Callable[[], Awaitable[Joint]]]:
        """
        Returns prepared map of parameter names to their asynchronous resolvers.
        """
        try:
            _, async_map = self._get_resolver_map_cache()
        except AttributeError:
            _, async_map = self._build_resolver_map_cache()

        return copy(async_map)


@dataclass
class HostParams[T: HostedMarkProtocol](ParamsStateMachine):
    _params: list[HostParamStage[T, Joint]]
    _type_hints: dict[str, Any]
    _sig: inspect.Signature
    _callable: Callable
    _plugin_lookup: Callable[[CoreHostProtocol[Any]], CorePluginProtocol[Joint, Any]]
    _state_type: Literal[ParamsStateType.HOST_READY] = ParamsStateType.HOST_READY

    @property
    def params(self) -> list[HostParamStage[T, Joint]]:
        return self._params

    @property
    def type_hints(self) -> dict[str, Any]:
        return self._type_hints

    @property
    def sig(self) -> inspect.Signature:
        return self._sig

    @property
    def callable(self) -> Callable:
        return self._callable

    @property
    def plugin_lookup(self) -> Callable[[CoreHostProtocol], CorePluginProtocol]:
        return self._plugin_lookup

    @property
    def state_type(self) -> Literal[ParamsStateType.HOST_READY]:
        return self._state_type

    def is_callable_a_coro_callable(self) -> bool:
        """
        Returns `True` if callable returns a coroutine.
        """
        return is_coroutine_callable(self.callable)

    def advance(self) -> PluginParams:
        """
        Advancing this stage can raise plugin-lookup related exceptions.

        Raises:
            [plug_in.exc.MissingMountError][]: ...
            [plug_in.exc.MissingPluginError][]: ...
            [plug_in.exc.SyncPluginExpected][]: ...
        """

        plugin_ready_stages: list[PluginParamStage] = []
        will_resolve_in_coro = self.is_callable_a_coro_callable()

        if not will_resolve_in_coro:
            for staged_host_param in self.params:
                # Every plugin must be synchronous
                plugin = self.plugin_lookup(staged_host_param.host)
                try:
                    plugin = plugin.assert_sync()
                except AssertionError as e:
                    raise SyncPluginExpected(
                        "Parameter state machine encountered a non-sync plugin for a "
                        "mark hosted in synchronous callable. This is not possible to "
                        "resolve async plugin in scope of sync callable. Use synchronous "
                        "plugin for this mark instead.\n"
                        f"mark={staged_host_param.default}\n"
                        f"{plugin=}\n"
                        f"{staged_host_param.name=}\n"
                        f"{staged_host_param.host=}\n"
                        f"{self.callable=}\n"
                        f"{self.sig=}"
                    ) from e

                param_stage = PluginParamStage(
                    _name=staged_host_param.name,
                    _default=staged_host_param.default,
                    _host=staged_host_param.host,
                    _plugin=plugin,
                )
                plugin_ready_stages.append(param_stage)

        else:
            for staged_host_param in self.params:
                # Can be sync and async
                param_stage = PluginParamStage(
                    _name=staged_host_param.name,
                    _default=staged_host_param.default,
                    _host=staged_host_param.host,
                    _plugin=self.plugin_lookup(staged_host_param.host),
                )
                plugin_ready_stages.append(param_stage)

        return PluginParams(
            _callable=self.callable,
            _plugin_lookup=self.plugin_lookup,
            _state_type=ParamsStateType.PLUGIN_READY,
            _params=plugin_ready_stages,
            _type_hints=self.type_hints,
            _sig=self.sig,
        )


@dataclass
class DefaultParams[T: HostedMarkProtocol](ParamsStateMachine):
    _params: list[DefaultParamStage[T]]
    _sig: inspect.Signature
    _callable: Callable
    _plugin_lookup: Callable[[CoreHostProtocol[Any]], CorePluginProtocol[Joint, Any]]
    _state_type: Literal[ParamsStateType.DEFAULT_READY] = ParamsStateType.DEFAULT_READY

    @property
    def params(self) -> list[DefaultParamStage[T]]:
        return self._params

    @property
    def sig(self) -> inspect.Signature:
        return self._sig

    @property
    def callable(self) -> Callable:
        return self._callable

    @property
    def plugin_lookup(self) -> Callable[[CoreHostProtocol], CorePluginProtocol]:
        return self._plugin_lookup

    @property
    def state_type(self) -> Literal[ParamsStateType.DEFAULT_READY]:
        return self._state_type

    def is_callable_a_coro_callable(self) -> bool:
        """
        Returns `True` if callable returns a coroutine.
        """
        return is_coroutine_callable(self.callable)

    def advance(self) -> HostParams:
        """
        Advancing this stage can still raise forward reference or annotation
        based exception

        Raises:
            [.EmptyHostAnnotationError][]: ...

        """

        try:
            hints = get_type_hints(self.callable)
        except NameError as e:
            raise UnexpectedForwardRefError(
                f"Given {self.callable=} contains params that cannot be evaluated now"
            ) from e

        except Exception as e:

            logging.warning(
                "Unhandled exception ocurred during retrieval of callable type hints. "
                "Info:"
                "\n\n%s"
                "\n\n%s"
                "\n\n%s",
                self.sig,
                self.callable,
                self.plugin_lookup,
            )

            raise RuntimeError(
                "Either You have used wrong kind of object for an annotation, "
                "or this case is not supported by a plug_in. If You are sure "
                "that annotations in Your callable are correct, please report "
                "an issue posting logger output"
            ) from e

        host_ready_stages: list[HostParamStage] = []

        for staged_default_param in self.params:
            # If get_type_hits call did not raise NameError, now we should be
            # able to retrieve everything without errors
            # However, I am leaving sanity check here
            if contains_forward_refs(staged_default_param.default):
                logging.warning(
                    "Unhandled exception ocurred during retrieval of callable type "
                    "hints. Info:"
                    "\n\n%s"
                    "\n\n%s"
                    "\n\n%s"
                    "\n\n%s",
                    hints,
                    self.sig,
                    self.callable,
                    self.plugin_lookup,
                )
                raise RuntimeError(
                    "Forward references still present on type hints. Please report "
                    "an issue posting logger output"
                )

            # One more validity check involves checking if annotation exists
            # on marked param

            # Annotation not present
            try:
                annotation = hints[staged_default_param.name]
            except KeyError as e:
                raise EmptyHostAnnotationError(
                    f"Parameter {staged_default_param.name} of {self.callable=} has been "
                    "marked as a hosted param, but no annotation is present on "
                    f"callable signature {self.sig}"
                ) from e

            host = CoreHost(annotation, staged_default_param.default.marks)

            # Sanity check done, prepare next stage
            host_ready_stages.append(
                HostParamStage(
                    _name=staged_default_param.name,
                    _default=staged_default_param.default,
                    _host=host,
                )
            )

        return HostParams(
            _callable=self.callable,
            _plugin_lookup=self.plugin_lookup,
            _state_type=ParamsStateType.HOST_READY,
            _params=host_ready_stages,
            _type_hints=hints,
            _sig=self.sig,
        )


@dataclass
class NothingParams(ParamsStateMachine):
    _callable: Callable
    _plugin_lookup: Callable[[CoreHostProtocol], CorePluginProtocol]
    _state_type: Literal[ParamsStateType.NOTHING_READY] = ParamsStateType.NOTHING_READY

    @property
    def callable(self) -> Callable:
        return self._callable

    @property
    def plugin_lookup(self) -> Callable[[CoreHostProtocol], CorePluginProtocol]:
        return self._plugin_lookup

    @property
    def state_type(self) -> Literal[ParamsStateType.NOTHING_READY]:
        return self._state_type

    def is_callable_a_coro_callable(self) -> bool:
        """
        Returns `True` if callable returns a coroutine.
        """
        return is_coroutine_callable(self.callable)

    def advance(self) -> DefaultParams:
        """
        Advancing this stage can raise errors on signature inspection.
        Rather minority of plug_in exceptions comes from this stage. If You,
        however, are trying to manage some exotic python internal object -
        beware that this is the stage that will probably not advance.

        Raises:
            [.ObjectNotSupported][]: ...
            [.UnexpectedForwardRefError][]: ...
        """

        try:
            sig = inspect.signature(self.callable)

        except TypeError as e:
            raise ObjectNotSupported(
                f"Given {self.callable=} is not supported by inspect.signature"
            ) from e

        except ValueError as e:
            raise ObjectNotSupported(
                f"Given {self.callable=} is not supported by inspect.signature"
            ) from e

        except NameError as e:
            # User wants to communicate this by exception
            raise UnexpectedForwardRefError(
                f"Given {self.callable=} contains params that cannot be evaluated now"
            ) from e

        except Exception as orig_e:
            try:
                _debug_sig = inspect.signature(self.callable, eval_str=False)
            except Exception as e:
                _debug_sig = e

            logging.warning(
                "Unhandled exception ocurred during signature retrieval. Info:"
                "\n\n%s"
                "\n\n%s"
                "\n\n%s",
                _debug_sig,
                self.callable,
                self.plugin_lookup,
            )

            raise RuntimeError(
                "Either You have used wrong kind of object for an annotation, "
                "or this case is not supported by a plug_in. If You are sure "
                "that annotations in Your callable are correct, please report "
                "an issue posting logger output"
            ) from orig_e

        default_ready_stages: list[DefaultParamStage] = [
            DefaultParamStage(_name=param_name, _default=param.default)
            for param_name, param in sig.parameters.items()
            if isinstance(param.default, HostedMark)
        ]

        return DefaultParams(
            _callable=self.callable,
            _plugin_lookup=self.plugin_lookup,
            _state_type=ParamsStateType.DEFAULT_READY,
            _params=default_ready_stages,
            _sig=sig,
        )
