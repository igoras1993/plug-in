import importlib
import sys

from logging import getLogger
from pathlib import Path
import pytest


logger = getLogger(__name__)


@pytest.fixture(scope="module")
def sample_app_package_path(request: pytest.FixtureRequest):
    app_dir_name: str = request.param
    assert isinstance(
        app_dir_name, str
    ), "Expecting string in fixture request parameter"

    path = str(
        Path(__file__)
        .parent.parent.parent.parent.joinpath("sample")
        .joinpath(app_dir_name)
        .absolute()
    )

    sys.path.insert(0, path)
    logger.info(
        "Inserted path:\n\t" "--> %s\n\t" "-- At position 0 of the sys.path", path
    )

    yield

    try:
        idx = sys.path.index(path)
    except ValueError:
        logger.warning(
            "Previously inserted path:\n\t"
            "--> %s\n\t"
            "-- Not found in sys.path; Skipping cleanup.",
            path,
        )
    else:
        sys.path.pop(idx)
        logger.info(
            "Removing previously inserted path:\n\t"
            "--> %s\n\t"
            "-- It was found at position: %s",
            path,
            idx,
        )


@pytest.mark.parametrize("sample_app_package_path", ["sample_app_1"], indirect=True)
def test_sample_app_1_runs_and_injects(sample_app_package_path):

    config = importlib.import_module("config")
    config.configure()

    api = importlib.import_module("api")
    assert api.get_user("user1").id == "user1"
    assert api.get_user_session_data("user1") == "some_data"

    # Destroy import
    del api
    del config
