from typing import Any
import pytest
from plug_in.core.enum import PluginPolicy
from plug_in.core.host import CoreHost
from plug_in.core.plug import CorePlug
from plug_in.core.plugin import create_core_plugin
from plug_in.proto.core_plugin import CorePluginProtocol


@pytest.mark.parametrize(
    "plugin, expected",
    [
        (
            create_core_plugin(CorePlug("Dupa"), CoreHost(str), PluginPolicy.DIRECT),
            "Dupa",
        ),
        (
            create_core_plugin(
                CorePlug(lambda: "Dup"), CoreHost(str), PluginPolicy.LAZY
            ),
            "Dup",
        ),
        (
            create_core_plugin(
                CorePlug(lambda: "Dup"), CoreHost(str), PluginPolicy.FACTORY
            ),
            "Dup",
        ),
    ],
)
def test_plugin_provide(plugin: CorePluginProtocol[Any], expected: Any):
    assert plugin.provide() == expected
