from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass
from enum import StrEnum
import inspect
import logging
from typing import Any, Callable, Literal, Self, cast, get_type_hints
from plug_in.core.host import CoreHost
from plug_in.exc import (
    EmptyHostAnnotationError,
    ObjectNotSupported,
    UnexpectedForwardRefError,
)
from plug_in.ioc.hosted_mark import HostedMark
from plug_in.tools.introspect import contains_forward_refs
from plug_in.types.proto.core_host import CoreHostProtocol
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
    RESOLVER_READY = "RESOLVER_READY"


@dataclass
class ResolverParamStage[T: HostedMarkProtocol, JointType: Joint](
    FinalParamStageProtocol[T, JointType]
):
    _name: str
    _default: T
    _host: CoreHostProtocol[JointType]
    _resolver: Callable[[], JointType]

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
    def resolver(self) -> Callable[[], JointType]:
        return self._resolver


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
    def resolve_provider(self) -> Callable[[CoreHostProtocol], Callable[[], Joint]]: ...

    @property
    @abstractmethod
    def state_type(self) -> ParamsStateType: ...

    @abstractmethod
    def advance(self) -> "ParamsStateMachine": ...

    def is_final(self) -> bool:
        return self.state_type == ParamsStateType.RESOLVER_READY

    def assert_final(self) -> "ResolverParams":
        """
        Return self if it is a final state, or raise ValueError.
        """
        if self.is_final():
            return cast(ResolverParams, self)
        else:
            raise ValueError("This is not a final state.")

    def finalize(self) -> "ResolverParams":
        """
        Advance to the final state or raise any of the advancing stage exceptions.
        """
        state = self

        while not state.is_final():
            state.advance()

        return state.assert_final()


@dataclass
class ResolverParams[T: HostedMarkProtocol, JointType: Joint](
    ParamsStateMachine, FinalParamsProtocol
):
    _params: list[ResolverParamStage[T, JointType]]
    _type_hints: dict[str, Any]
    _sig: inspect.Signature
    _callable: Callable
    _resolve_provider: Callable[[CoreHostProtocol], Callable[[], Joint]]
    _state_type: Literal[ParamsStateType.RESOLVER_READY] = (
        ParamsStateType.RESOLVER_READY
    )

    @property
    def params(self) -> list[ResolverParamStage[T, JointType]]:
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
    def resolve_provider(self) -> Callable[[CoreHostProtocol], Callable[[], Joint]]:
        return self._resolve_provider

    @property
    def state_type(self) -> Literal[ParamsStateType.RESOLVER_READY]:
        return self._state_type

    def advance(self) -> Self:
        return self

    def resolver_map(self) -> dict[str, Callable[[], JointType]]:
        """
        Returns prepared map of parameter names to their resolvers.
        """
        try:
            _resolver_map = getattr(self, "_resolver_map_cache")
        except AttributeError:
            _resolver_map = {param.name: param.resolver for param in self.params}
            setattr(self, "_resolver_map_cache", _resolver_map)

        return copy(_resolver_map)


@dataclass
class HostParams[T: HostedMarkProtocol, JointType: Joint](ParamsStateMachine):
    _params: list[HostParamStage[T, JointType]]
    _type_hints: dict[str, Any]
    _sig: inspect.Signature
    _callable: Callable
    _resolve_provider: Callable[[CoreHostProtocol], Callable[[], Joint]]
    _state_type: Literal[ParamsStateType.HOST_READY] = ParamsStateType.HOST_READY

    @property
    def params(self) -> list[HostParamStage[T, JointType]]:
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
    def resolve_provider(self) -> Callable[[CoreHostProtocol], Callable[[], Joint]]:
        return self._resolve_provider

    @property
    def state_type(self) -> Literal[ParamsStateType.HOST_READY]:
        return self._state_type

    def advance(self) -> ResolverParams:
        """
        Advancing this stage can raise plugin-lookup related exceptions.

        Raises:
            [plug_in.exc.MissingMountError][]: ...
            [plug_in.exc.MissingPluginError][]: ...
        """

        resolver_ready_stages = [
            ResolverParamStage(
                _name=staged_host_param.name,
                _default=staged_host_param.default,
                _host=staged_host_param.host,
                _resolver=self.resolve_provider(staged_host_param.host),
            )
            for staged_host_param in self.params
        ]

        return ResolverParams(
            _callable=self.callable,
            _resolve_provider=self.resolve_provider,
            _state_type=ParamsStateType.RESOLVER_READY,
            _params=resolver_ready_stages,
            _type_hints=self.type_hints,
            _sig=self.sig,
        )


@dataclass
class DefaultParams[T: HostedMarkProtocol](ParamsStateMachine):
    _params: list[DefaultParamStage[T]]
    _sig: inspect.Signature
    _callable: Callable
    _resolve_provider: Callable[[CoreHostProtocol], Callable[[], Joint]]
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
    def resolve_provider(self) -> Callable[[CoreHostProtocol], Callable[[], Joint]]:
        return self._resolve_provider

    @property
    def state_type(self) -> Literal[ParamsStateType.DEFAULT_READY]:
        return self._state_type

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
                self.resolve_provider,
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
                    self.resolve_provider,
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
            _resolve_provider=self.resolve_provider,
            _state_type=ParamsStateType.HOST_READY,
            _params=host_ready_stages,
            _type_hints=hints,
            _sig=self.sig,
        )


@dataclass
class NothingParams(ParamsStateMachine):
    _callable: Callable
    _resolve_provider: Callable[[CoreHostProtocol], Callable[[], Joint]]
    _state_type: Literal[ParamsStateType.NOTHING_READY] = ParamsStateType.NOTHING_READY

    @property
    def callable(self) -> Callable:
        return self._callable

    @property
    def resolve_provider(self) -> Callable[[CoreHostProtocol], Callable[[], Joint]]:
        return self._resolve_provider

    @property
    def state_type(self) -> Literal[ParamsStateType.NOTHING_READY]:
        return self._state_type

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
                self.resolve_provider,
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
            _resolve_provider=self.resolve_provider,
            _state_type=ParamsStateType.DEFAULT_READY,
            _params=default_ready_stages,
            _sig=sig,
        )
