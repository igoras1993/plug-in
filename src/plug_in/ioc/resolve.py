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
    InvalidHostSubject,
    MissingMountError,
    MissingPluginError,
    ObjectNotSupported,
    UnexpectedForwardRefError,
)
from plug_in.ioc.hosted_mark import HostedMark
from plug_in.tools.introspect import contains_forward_refs
from plug_in.types.proto.core_host import CoreHostProtocol
from plug_in.types.proto.hosted_mark import HostedMarkProtocol
from plug_in.types.proto.joint import Joint


class ParamsStateType(StrEnum):
    NOTHING_READY = "NOTHING_READY"
    DEFAULT_READY = "DEFAULT_READY"
    HOST_READY = "HOST_READY"
    RESOLVER_READY = "RESOLVER_READY"


_NOT_GIVEN = object()


@dataclass
class ResolverParamStage[T: HostedMarkProtocol, JointType: Joint]:
    name: str
    default: T
    host: CoreHost[JointType]
    resolver: Callable[[], JointType]


@dataclass
class HostParamStage[T: HostedMarkProtocol, JointType: Joint]:
    name: str
    default: T
    host: CoreHost[JointType]


@dataclass
class DefaultParamStage[T: HostedMarkProtocol]:
    """
    Annotation is available and validated
    """

    name: str
    default: T


@dataclass
class NothingParamStage:
    pass


class ParamsStateMachine[
    Stage: NothingParamStage | DefaultParamStage | HostParamStage | ResolverParamStage
](ABC):

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
    ParamsStateMachine[ResolverParamStage[T, JointType]]
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
class HostParams[T: HostedMarkProtocol, JointType: Joint](
    ParamsStateMachine[HostParamStage[T, JointType]]
):
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
                name=staged_host_param.name,
                default=staged_host_param.default,
                host=staged_host_param.host,
                resolver=self.resolve_provider(staged_host_param.host),
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
class DefaultParams[T: HostedMarkProtocol](ParamsStateMachine[DefaultParamStage[T]]):
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
            [.InvalidHostSubject][]: ...

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
            # on parked param and it is a valid type

            # 1. Annotation not present
            try:
                annotation = hints[staged_default_param.name]
            except KeyError as e:
                raise EmptyHostAnnotationError(
                    f"Parameter {staged_default_param.name} of {self.callable=} has been "
                    "marked as a hosted param, but no annotation is present on "
                    f"callable signature {self.sig}"
                ) from e

            # 2. Invalid host subject - annotation is present but is not a type
            # This line will raise InvalidHostSubject
            host = CoreHost(annotation, staged_default_param.default.marks)

            # Sanity check done, prepare next stage
            host_ready_stages.append(
                HostParamStage(
                    name=staged_default_param.name,
                    default=staged_default_param.default,
                    host=host,
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
class NothingParams(ParamsStateMachine[NothingParamStage]):
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
            DefaultParamStage(name=param_name, default=param.default)
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


class ParameterResolver[**CallParams]:
    """
    Helper class for efficient callable signature replacement.

    Args:
        callable: A callable that will be managed
        resolve_callback: Function transforming a [.CoreHost][] instance into
            provided value.
        assert_no_forward_ref: If forward reference is present at the resolver
            construction time, setting this to `True` will result in
            [.UnexpectedForwardRefError][]. When it is `False` (default), resolver
            will take an attempt to evaluate forward refs at the first callable
            invocation.
    """

    def __init__(
        self,
        callable: Callable[CallParams, Any],
        resolve_callback: Callable[[CoreHostProtocol], Callable[[], Joint]],
        assert_resolver_ready: bool = False,
    ) -> None:
        self._state = NothingParams(
            _callable=callable, _resolve_provider=resolve_callback
        )

        # Try to advance
        self.try_finalize_state(assert_resolver_ready)

    def try_finalize_state(self, assert_resolver_ready: bool = False) -> None:
        """
        Advances internal resolver state to the point that no further advances
        are possible at this time. Keeping resolver in the most recent state
        improves call-time performance.

        You can safely use this method whenever you want. It is also a reasonable
        routine to [eventually] call this whenever all Your managed objects and
        managing subjects are ready.

        You can control the exception raising behavior with `assert_resolver_ready`.
        Setting it to `True` will raise one of three exceptions that should be
        cached by caller:

        - [.UnexpectedForwardRefError][]
        - [.MissingMountError][]
        - [.MissingPluginError][]

        When this flag is set to `False` (default), those exceptions are silenced
        and resolver is kept at the most possible recent state.
        Above exceptions are caused by not finished plugin setup and will likely
        vanish at the application startup time.

        If they are not vanishing, this means that `plug_in` is unable to resolve
        some symbols (e.g. when they are used via `if TYPE_CHECKING: import ...`)
        or `plug_in` registry/router configuration is incorrect.

        Raises:
            [.UnexpectedForwardRefError][]: Only of assert flag is set
            [.MissingMountError][]: Only of assert flag is set
            [.MissingPluginError][]: Only of assert flag is set
            [.ObjectNotSupported][]: Always when callable is not supported by
                a `plug_in`
            [.EmptyHostAnnotationError][]: Always when callable parameter marked
                by a [.HostedMark][] has no annotation.
            [.InvalidHostSubject][]: Always when callable parameter marked by a
                [.HostMark][] is annotated with object which is not a valid type.

        """
        while not self._state.is_final():
            try:
                self._state = self._state.advance()
            except (
                ObjectNotSupported,
                EmptyHostAnnotationError,
                InvalidHostSubject,
            ) as e:
                # Always reraise
                raise e
            except (
                UnexpectedForwardRefError,
                MissingMountError,
                MissingPluginError,
            ) as e:
                logging.debug(
                    "Halted resolver state at %s, with reason: %s", self._state, e
                )
                if assert_resolver_ready:
                    raise e
                else:
                    return

    def get_one_time_bind(
        self, *args: CallParams.args, **kwargs: CallParams.kwargs
    ) -> inspect.BoundArguments:
        """
        Get [inspect.BoundArguments][], with [.HosedMark][] default values
        replaced with its resolved value. Resolving happens by calling
        `replace_callback` given at initialization time. Default values are
        applied.

        Invoke this method with the same arguments that user invokes his `callable`.

        Args:
            args: The same positional arguments that original `callable` accepts
            kwargs: The same keyword arguments that original `callable` accepts

        Returns:
            [inspect.BoundArguments][] object with applied defaults.
        """
        # At this stage resolver must be ready
        self.try_finalize_state(assert_resolver_ready=True)
        resolver_params = self._state.assert_final()
        resolver_map = self._state.assert_final().resolver_map()
        sig = resolver_params.sig

        # https://github.com/python/cpython/issues/85542
        # Replace defaults filtering only hosts
        new_sig = sig.replace(
            parameters=[
                (
                    param.replace(default=resolver_map[param.name]())
                    if param.name in resolver_map
                    else param
                )
                for param in sig.parameters.values()
            ]
        )

        arg_bind = new_sig.bind(*args, **kwargs)
        arg_bind.apply_defaults()
        return arg_bind
