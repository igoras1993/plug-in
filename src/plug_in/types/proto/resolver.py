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

    @property
    @abstractmethod
    def should_use_async_bind(self) -> bool: ...

    def get_one_time_bind_sync(
        self, *args: CallParams.args, **kwargs: CallParams.kwargs
    ) -> inspect.BoundArguments: ...

    async def get_one_time_bind_async(
        self, *args: CallParams.args, **kwargs: CallParams.kwargs
    ) -> inspect.BoundArguments: ...
