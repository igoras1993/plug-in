from typing import Any, Hashable

from plug_in.core.host import CoreHost


def Host[T](subject: type[T], mark: Hashable = None) -> Any:
    return CoreHost(subject, mark)
