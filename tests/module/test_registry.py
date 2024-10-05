from dataclasses import dataclass

from plug_in.core.enum import PluginPolicy
from plug_in.core.host import CoreHost
from plug_in.core.plug import CorePlug
from plug_in.core.plugin import create_core_plugin
from plug_in.core.registry import CoreRegistry


def test_registry():

    @dataclass
    class SampleClass[T]:
        sample_field: T

    def sample_int_class_factory() -> SampleClass[int]:
        return SampleClass(10)

    def sample_str_class_factory() -> SampleClass[str]:
        return SampleClass("abc")

    reg = CoreRegistry(
        [
            create_core_plugin(
                plug=CorePlug(_provider=sample_int_class_factory),
                host=CoreHost(SampleClass[int]),
                policy=PluginPolicy.LAZY,
            ),
            create_core_plugin(
                plug=CorePlug(_provider=sample_str_class_factory),
                host=CoreHost(SampleClass[str]),
                policy=PluginPolicy.FACTORY,
            ),
        ]
    )

    ten = reg.resolve(CoreHost(SampleClass[int]))
    abc = reg.resolve(CoreHost(SampleClass[str]))

    assert ten == SampleClass(10)
    assert abc == SampleClass("abc")

    # Additional lazy checks, ten should be singleton
    assert ten == reg.resolve(CoreHost(SampleClass[int]))
    assert ten == reg.resolve(CoreHost(SampleClass[int]))


def test_registry_can_be_hosted():
    """
    This is a meat. Registry should be ordinarily hosted. Two registries also.
    """

    # ############ #
    # ### REG1 ### #

    @dataclass
    class SampleClass[T]:
        sample_field: T

    def sample_int_class_factory() -> SampleClass[int]:
        return SampleClass(10)

    def sample_str_class_factory() -> SampleClass[str]:
        return SampleClass("abc")

    reg1 = CoreRegistry(
        [
            create_core_plugin(
                plug=CorePlug(_provider=sample_int_class_factory),
                host=CoreHost(SampleClass[int]),
                policy=PluginPolicy.LAZY,
            ),
            create_core_plugin(
                plug=CorePlug(_provider=sample_str_class_factory),
                host=CoreHost(SampleClass[str]),
                policy=PluginPolicy.FACTORY,
            ),
        ]
    )

    # ############ #
    # ### REG2 ### #

    reg2 = CoreRegistry(
        [
            create_core_plugin(
                plug=CorePlug(reg1),
                host=CoreHost(CoreRegistry, _marks=("reg1",)),
                policy=PluginPolicy.DIRECT,
            ),
            # In here, for the same types as before, we plug different providers
            create_core_plugin(
                plug=CorePlug(SampleClass(100)),
                host=CoreHost(SampleClass[int]),
                policy=PluginPolicy.DIRECT,
            ),
            create_core_plugin(
                plug=CorePlug(SampleClass("abcdef")),
                host=CoreHost(SampleClass[str]),
                policy=PluginPolicy.DIRECT,
            ),
            create_core_plugin(
                plug=CorePlug("Scott"),
                host=CoreHost(str, _marks=("FIRST_NAME",)),
                policy=PluginPolicy.DIRECT,
            ),
            create_core_plugin(
                plug=CorePlug("Tiger"),
                host=CoreHost(str, _marks=("LAST_NAME",)),
                policy=PluginPolicy.DIRECT,
            ),
        ]
    )

    assert reg2.sync_resolve(CoreHost(str, ("FIRST_NAME",))) == "Scott"
    assert reg2.sync_resolve(CoreHost(str, ("LAST_NAME",))) == "Tiger"
    assert reg2.sync_resolve(CoreHost(SampleClass[int])) == SampleClass(100)
    assert reg2.sync_resolve(CoreHost(SampleClass[str])) == SampleClass("abcdef")

    assert reg2.sync_resolve(CoreHost(CoreRegistry, ("reg1",))) == reg1

    assert reg2.sync_resolve(CoreHost(CoreRegistry, ("reg1",))).sync_resolve(
        CoreHost(SampleClass[int])
    ) == SampleClass(10)
    assert reg2.sync_resolve(CoreHost(CoreRegistry, ("reg1",))).sync_resolve(
        CoreHost(SampleClass[str])
    ) == SampleClass("abc")
