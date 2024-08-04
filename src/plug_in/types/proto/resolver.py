from abc import abstractmethod
import inspect
from typing import Protocol

from plug_in.types.proto.parameter import ParamsStateMachineProtocol


class ParameterResolverProtocol[**CallParams](Protocol):

    @property
    @abstractmethod
    def state(self) -> ParamsStateMachineProtocol: ...

    @abstractmethod
    def try_finalize_state(self, assert_resolver_ready: bool = False) -> None: ...

    def get_one_time_bind(
        self, *args: CallParams.args, **kwargs: CallParams.kwargs
    ) -> inspect.BoundArguments: ...
