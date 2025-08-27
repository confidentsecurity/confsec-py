import os

import pytest


def pytest_addoption(parser):
    parser.addoption("--e2e", action="store_true", default=False, help="run e2e tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: mark test as e2e to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--e2e"):
        return
    skip_e2e = pytest.mark.skip(reason="--e2e was not passed")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)


@pytest.fixture
def api_key():
    _api_key = os.environ.get("CONFSEC_API_KEY")
    assert _api_key is not None
    return _api_key


@pytest.fixture
def env():
    _env = os.environ.get("CONFSEC_ENV")
    if _env is None:
        _env = "prod"
    return _env
