from typing import Awaitable, Callable, cast, overload

from plug_in.boot.builder.facade import (
    CoroutinePlugFacade,
    PlugFacade,
    PlugFacadeProtocol,
    ProvidingPlugFacade,
    ProvidingPlugFacadeProtocol,
)
from plug_in.boot.builder.proto import CoroutinePlugFacadeProtocol
from plug_in.tools.introspect import is_coroutine_callable


@overload
def plug[
    T, MetaData
](
    provider: Callable[[], Awaitable[T]], metadata: MetaData = None
) -> CoroutinePlugFacadeProtocol[T, MetaData]: ...


@overload
def plug[
    T, MetaData
](provider: Callable[[], T], metadata: MetaData = None) -> ProvidingPlugFacadeProtocol[
    T, MetaData
]: ...


@overload
def plug[
    T, MetaData
](provider: T, metadata: MetaData = None) -> PlugFacadeProtocol[T, MetaData]: ...


def plug[
    T, MetaData
](
    provider: Callable[[], Awaitable[T]] | Callable[[], T] | T,
    metadata: MetaData = None,
) -> (
    CoroutinePlugFacadeProtocol[T, MetaData]
    | ProvidingPlugFacadeProtocol[T, MetaData]
    | PlugFacadeProtocol[T, MetaData]
):
    if is_coroutine_callable(provider):
        return CoroutinePlugFacade(provider, metadata)
    elif callable(provider):
        return ProvidingPlugFacade(cast(Callable[[], T], provider), metadata)
    else:
        return PlugFacade(provider, metadata)
