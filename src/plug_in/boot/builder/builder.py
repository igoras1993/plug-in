from typing import Callable, overload

from plug_in.boot.builder.facade import (
    PlugFacade,
    PlugFacadeProtocol,
    ProvidingPlugFacade,
    ProvidingPlugFacadeProtocol,
)


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
](provider: Callable[[], T] | T, metadata: MetaData = None) -> (
    ProvidingPlugFacadeProtocol[T, MetaData] | PlugFacadeProtocol[T, MetaData]
):
    if callable(provider):
        return ProvidingPlugFacade(provider, metadata)
    else:
        return PlugFacade(provider, metadata)
