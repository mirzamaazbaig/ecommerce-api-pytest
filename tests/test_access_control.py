import pytest

pytestmark = pytest.mark.security

ADMIN_CALLS = [
    ("POST", "products", {"json": {"name": "x", "price": 1, "stock": 1, "categoryId": 1}}),
    ("PUT", "products/1", {"json": {"price": 1}}),
    ("DELETE", "products/1", {}),
    ("GET", "orders", {}),
]


@pytest.mark.parametrize("method,path,kwargs", ADMIN_CALLS)
def test_anonymous_requests_to_admin_endpoints_are_401(anon, method, path, kwargs):
    assert anon.request(method, path, **kwargs).status_code == 401


@pytest.mark.parametrize("method,path,kwargs", ADMIN_CALLS)
def test_customers_get_403_on_admin_endpoints(user, method, path, kwargs):
    assert user.api.request(method, path, **kwargs).status_code == 403


@pytest.mark.parametrize("method,path", [
    ("GET", "orders/my-orders"), ("POST", "orders"), ("GET", "wishlist"), ("POST", "wishlist"), ("POST", "reviews"),
])
def test_customer_endpoints_require_a_session(anon, method, path):
    assert anon.request(method, path, json={}).status_code == 401


def test_a_customer_cannot_change_a_product(user, product, anon):
    before = anon.get(f"products/{product['id']}").json()
    assert user.api.put(f"products/{product['id']}", json={"price": 1}).status_code == 403
    assert anon.get(f"products/{product['id']}").json()["price"] == before["price"]
