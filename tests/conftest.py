import os

import pytest


def pytest_addoption(parser):
    parser.addoption("--e2e", action="store_true", default=False, help="run e2e tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: mark test as e2e to run")


def pytest_collection_modifyitems(config, items):
    is_e2e = config.getoption("--e2e")

    def should_skip(item):
        return "e2e" in item.keywords if not is_e2e else "e2e" not in item.keywords

    skip = pytest.mark.skip(reason=f"--e2e was {'not ' if is_e2e else ''}passed")
    for item in items:
        if should_skip(item):
            item.add_marker(skip)


@pytest.fixture(scope="session")
def api_key():
    _api_key = os.environ.get("CONFSEC_API_KEY")
    assert _api_key is not None
    return _api_key


@pytest.fixture(scope="session")
def env():
    _env = os.environ.get("CONFSEC_ENV")
    if _env is None:
        _env = "prod"
    return _env
