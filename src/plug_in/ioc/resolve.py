from dataclasses import dataclass
from functools import wraps
import inspect
from typing import Any, Callable
from plug_in.core.host import CoreHost
from plug_in.types.proto.joint import Joint
from plug_in.types.proto.router import RouterProtocol


@dataclass
class PrecomputedParamState:
    signature: inspect.Signature
    params: list[inspect.Parameter]


class ParameterResolver[JointType: Joint, **CallParams]:
    """
    Helper class for efficient callable signature replacement.

    Args:
        callable: A callable that will be managed
        resolve_callback: Function transforming a [.CoreHost][] instance into
            provided value.
        eager_forward_resolve: Boolean flag. If `True` (default) - will attempt
            to retrieve a `callable` signature at initialization time. If
            You are using forward referenced generics to parametrize host,
            You should set this to `False`. Setting it to `False` slightly
            downgrades performance, as signature retrieval is deferred to the
            [.ParameterResolver.get_one_time_signature][] call time.
    """

    def __init__(
        self,
        callable: Callable[CallParams, Any],
        resolve_callback: Callable[[CoreHost[JointType]], JointType],
        eager_forward_resolve: bool = True,
    ) -> None:
        self._precomputed_params: PrecomputedParamState | None = None
        self._callable = callable
        self._replace_callback = resolve_callback

        if eager_forward_resolve:
            # List of params that have host default value
            host_defaults: list[inspect.Parameter] = []

            # Retrieve callable signature
            try:
                sig = inspect.signature(callable)
            except Exception as e:
                raise RuntimeError(
                    "Failure with signature inspection. Verify that You are trying to "
                    "manage a callable. If your Host is hosting a forward-referenced "
                    "type (e.g. `host(list['str'])` instead of `host(list[str])`) "
                    "try disabling `eager_forward_resolve` flag."
                ) from e

            # Detect parameters to be replaced in call time
            for param in sig.parameters.values():
                if isinstance(param.default, CoreHost):
                    host_defaults.append(param)

            # Save precomputed state
            self._precomputed_params = PrecomputedParamState(sig, host_defaults)

    def get_one_time_bind(
        self, *args: CallParams.args, **kwargs: CallParams.kwargs
    ) -> inspect.BoundArguments:
        """
        Get [inspect.BoundArguments][], with CoreHost defaults replaced with its
        resolved value. Resolving happens by calling `replace_callback` given at
        initialization time. Default values are applied.

        Invoke this method with arguments that user invokes his `callable`.

        Args:
            args: The same positional arguments that original `callable` accepts
            kwargs: The same keyword arguments that original `callable` accepts

        Returns:
            [inspect.BoundArguments][] object with applied defaults.
        """

        # TODO: Revisit need of eager_forward_resolve as it turns out that
        #   full loop is always needed
        if self._precomputed_params is not None:
            # Eager resolving was ordered, we can utilize existing list and signature
            new_sig = self._precomputed_params.signature.replace(
                parameters=[
                    (
                        param.replace(default=self._replace_callback(param.default))
                        if param in self._precomputed_params.params
                        else param
                    )
                    for param in self._precomputed_params.signature.parameters.values()
                ]
            )
        else:
            # Lazy resolving, resolving during call time:

            # Retrieve callable signature
            sig = inspect.signature(callable)

            # Replace defaults filtering only hosts
            new_sig = sig.replace(
                parameters=[
                    (
                        param.replace(default=self._replace_callback(param.default))
                        if isinstance(param.default, CoreHost)
                        else param
                    )
                    for param in sig.parameters.values()
                ]
            )

        arg_bind = new_sig.bind(*args, **kwargs)
        arg_bind.apply_defaults()
        return arg_bind


def callable_route_factory[
    R, **P
](
    callable: Callable[P, R], router: RouterProtocol, eager_forward_resolve: bool = True
) -> Callable[P, R]:
    """
    Create new callable that will have default values substituted by a plugin
    resolver.

    Args:
        callable: Subject callable.
        eager_forward_resolve: Boolean flag. If `True` (default) - will attempt
            to retrieve a `callable` signature at initialization time. If
            You are using forward referenced generics to parametrize host,
            You should set this to `False`. Setting it to `False` slightly
            downgrades performance, as signature retrieval is deferred to the
            [.ParameterResolver.get_one_time_signature][] call time.

    Returns:
        New callable with substituted `CoreHost` defaults. Nothing but default
        values to parameters change in new callable signature.
    """
    # Keep parameter resolver
    param_resolver = ParameterResolver(
        callable=callable,
        resolve_callback=router.resolve,
        eager_forward_resolve=eager_forward_resolve,
    )

    # Create wrapper for callable
    @wraps(callable)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # Get arg bind
        bind = param_resolver.get_one_time_bind(*args, **kwargs)

        # Proceed with call
        return callable(*bind.args, **bind.kwargs)

    return wrapper
