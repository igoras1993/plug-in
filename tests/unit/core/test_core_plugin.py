from typing import Any, Callable
import pytest
from plug_in.core.enum import PluginPolicy
from plug_in.core.host import CoreHost
from plug_in.core.plug import CorePlug
from plug_in.core.plugin import create_core_plugin
from plug_in.types.proto.core_plugin import CorePluginProtocol


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
def test_plugin_provide(plugin: CorePluginProtocol[Any, Any], expected: Any):
    """
    Check if [.CorePluginProtocol.provide][] call equals to the expected value.
    """
    assert plugin.assert_sync().provide() == expected
    assert plugin.provide() == expected


async def _async_plug() -> str:
    return "Dup"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "plugin, expected",
    [
        (
            create_core_plugin(
                CorePlug(_async_plug), CoreHost(str), PluginPolicy.LAZY_ASYNC
            ),
            "Dup",
        ),
        (
            create_core_plugin(
                CorePlug(_async_plug), CoreHost(str), PluginPolicy.FACTORY_ASYNC
            ),
            "Dup",
        ),
    ],
)
async def test_plugin_async_provide(
    plugin: CorePluginProtocol[Any, Any], expected: Any
):
    """
    Check if [.CorePluginProtocol.provide][] call equals to the expected value.
    """
    assert await plugin.assert_async().provide() == expected
    assert await plugin.provide() == expected


@pytest.mark.parametrize(
    "plug, expected_equal",
    [
        (CorePlug("Dupa"), "Dupa"),
        (CorePlug([1, 2, 3]), [1, 2, 3]),
    ],
)
def test_direct_plugin_provide(plug: CorePlug[Any], expected_equal: Any):
    """
    1. Constructs plugin
    2. Checks if [.CorePluginProtocol.provide][] call equals to the expected value.
    3. Checks if consecutive calls results in the same value (is check)
    """

    plugin = create_core_plugin(
        plug=plug, host=CoreHost(object), policy=PluginPolicy.DIRECT
    )

    value = plugin.provide()

    assert value == expected_equal
    assert value is plugin.provide()
    assert value is plugin.provide()
    assert value is plugin.provide()


@pytest.mark.parametrize(
    "plug, expected_equal",
    [
        (CorePlug(lambda: "Dupa"), "Dupa"),
        (CorePlug(dict), {}),
    ],
)
def test_lazy_plugin_provide(plug: CorePlug[Callable[[], Any]], expected_equal: Any):
    """
    1. Constructs plugin
    2. Checks if [.CorePluginProtocol.provide][] call equals to the expected value.
    3. Checks if consecutive calls results in the same value (is check)
    """

    plugin = create_core_plugin(
        plug=plug, host=CoreHost(object), policy=PluginPolicy.LAZY
    )

    value = plugin.provide()

    assert value == expected_equal
    assert value is plugin.provide()
    assert value is plugin.provide()
    assert value is plugin.provide()


@pytest.mark.parametrize(
    "plug, expected_equal, should_is_fail",
    [
        (CorePlug(lambda: "Dupa"), "Dupa", False),
        (CorePlug(dict), {}, True),
    ],
)
def test_factory_plugin_provide(
    plug: CorePlug[Callable[[], Any]], expected_equal: Any, should_is_fail: bool
):
    """
    1. Constructs plugin
    2. Checks if [.CorePluginProtocol.provide][] call equals to the expected value.
    3. Checks if consecutive calls results in a different instances (is comparison
        returns `False`), but only if it should.
    """

    plugin = create_core_plugin(
        plug=plug, host=CoreHost(object), policy=PluginPolicy.FACTORY
    )

    value = plugin.provide()

    assert value == expected_equal

    if should_is_fail:
        assert not (value is plugin.provide())
        assert not (value is plugin.provide())
        assert not (value is plugin.provide())
    else:
        assert value is plugin.provide()
        assert value is plugin.provide()
        assert value is plugin.provide()
