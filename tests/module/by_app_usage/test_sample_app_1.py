import importlib


def test_sample_app_1_runs():
    importlib.import_module("tests.module.by_app_usage.sample_app_1")
