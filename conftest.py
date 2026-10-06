import pytest

from framework import db, factories
from framework.client import ApiClient


def pytest_collection_modifyitems(config, items):
    if not db.available():
        skip = pytest.mark.skip(reason="DATABASE_URL not set")
        for item in items:
            if "db" in item.keywords or "admin" in item.fixturenames:
                item.add_marker(skip)


@pytest.fixture
def anon():
    api = ApiClient()
    yield api
    api.close()


@pytest.fixture
def user():
    u = factories.register()
    yield u
    u.api.close()


@pytest.fixture
def admin():
    a = factories.register_admin()
    yield a
    a.api.close()


@pytest.fixture
def product(admin):
    """An isolated product (stock 10, price 19.99) removed after the test."""
    p = factories.create_product(admin)
    yield p
    factories.delete_product(admin, p["id"])
