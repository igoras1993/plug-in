from typing import Any, Hashable

from plug_in.ioc.hosted_mark import HostedMark


def Hosted(*marks: Hashable) -> Any:
    return HostedMark(*marks)
