from typing import Callable, overload

from plug_in.boot.builder.facade import (
    PlugFacade,
    PlugFacadeProtocol,
    ProvidingPlugFacade,
    ProvidingPlugFacadeProtocol,
)


@overload
def plug[T](provider: Callable[[], T]) -> ProvidingPlugFacadeProtocol[T]: ...


@overload
def plug[T](provider: T) -> PlugFacadeProtocol[T]: ...


def plug[
    T
](provider: Callable[[], T] | T) -> (
    ProvidingPlugFacadeProtocol[T] | PlugFacadeProtocol[T]
):
    if callable(provider):
        return ProvidingPlugFacade(provider)
    else:
        return PlugFacade(provider)
