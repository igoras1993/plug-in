import pytest
from plug_in import plug


def f() -> int:
    return 10


@pytest.mark.skip("Implement a selector toto")
def test_plugin_creation_with_mismatched_types_fail():
    with pytest.raises(TypeError):
        plug(f).into(int).directly()

    with pytest.raises(TypeError):
        plug(lambda: 10).into(int).directly()
