import inspect
import logging
from typing import Any, Callable
from plug_in.exc import (
    EmptyHostAnnotationError,
    MissingMountError,
    MissingPluginError,
    ObjectNotSupported,
    UnexpectedForwardRefError,
)
from plug_in.ioc.parameter import NothingParams, ParamsStateMachine
from plug_in.types.proto.core_host import CoreHostProtocol
from plug_in.types.proto.joint import Joint
from plug_in.types.proto.resolver import ParameterResolverProtocol


class ParameterResolver[**CallParams](ParameterResolverProtocol):
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
        self._state: ParamsStateMachine = NothingParams(
            _callable=callable, _resolve_provider=resolve_callback
        )

        # Try to advance
        self.try_finalize_state(assert_resolver_ready)

    @property
    def state(self) -> ParamsStateMachine:
        return self._state

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

        """
        while not self._state.is_final():
            try:
                self._state = self._state.advance()
            except (
                ObjectNotSupported,
                EmptyHostAnnotationError,
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
