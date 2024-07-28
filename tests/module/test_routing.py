from dataclasses import dataclass
from plug_in.core.enum import PluginPolicy
from plug_in.core.plug import CorePlug
from plug_in.core.plugin import create_core_plugin
from plug_in.core.registry import CoreRegistry
from plug_in.ioc.hosting import Host
from plug_in.ioc.router import Router


def test_routing_capabilities():

    # My code know nothing about plugins, only router is used
    router = Router()

    @dataclass
    class SomeClass[T]:
        value: T

    @router.manage()
    def some_function(x: str, some: SomeClass[int] = Host(SomeClass[int])) -> str:
        return some.value * x

    @router.manage()
    @dataclass
    class SomeManagedDataclass:
        x: str
        some: SomeClass[int] = Host(SomeClass[int])

        def run_some(self) -> str:
            return self.some.value * self.x

    # Now I create plugins and register it

    some_int_class_plugin = create_core_plugin(
        CorePlug(SomeClass(3)), Host(SomeClass[int]), policy=PluginPolicy.DIRECT
    )

    registry = CoreRegistry(plugins=[some_int_class_plugin])

    # I also mount router to the registry
    router.mount(registry)

    # Now moment of truth
    assert some_function("Dupa") == "DupaDupaDupa"
    assert some_function("Dupa", SomeClass(2)) == "DupaDupa"

    smd = SomeManagedDataclass("Kupa")
    assert smd.run_some() == "KupaKupaKupa"

    smd = SomeManagedDataclass("Kupa", SomeClass(2))
    assert smd.run_some() == "KupaKupa"
