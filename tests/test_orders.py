"""Orders: server-side stock and price rules (see the Ecom defect log, D1 and D2)."""
import concurrent.futures

import pytest

from framework import db, factories
from framework.factories import order_body


def stock_of(anon, product):
    return anon.get(f"products/{product['id']}").json()["stock"]


@pytest.mark.smoke
def test_valid_order_is_created_pending_and_listed(user, product):
    res = user.api.post("orders", json=order_body(product, 2))
    assert res.status_code == 201
    assert res.json()["order"]["status"] == "pending"

    orders = user.api.get("orders/my-orders").json()
    assert len(orders) == 1
    assert float(orders[0]["total_amount"]) == pytest.approx(2 * 19.99)
    assert orders[0]["items"][0]["product_id"] == product["id"] and orders[0]["items"][0]["quantity"] == 2


@pytest.mark.parametrize("body", [{"items": []}, {}])
def test_empty_cart_is_400(user, body):
    res = user.api.post("orders", json=body)
    assert res.status_code == 400 and res.json()["message"] == "Cart is empty"


def test_ordering_reduces_stock_by_exactly_the_quantity(user, product, anon):
    user.api.post("orders", json=order_body(product, 4))
    assert stock_of(anon, product) == 6


def test_ordering_more_than_the_stock_is_409_and_changes_nothing(user, product, anon):
    res = user.api.post("orders", json=order_body(product, 11))
    assert res.status_code == 409
    assert stock_of(anon, product) == 10
    assert user.api.get("orders/my-orders").json() == []


def test_the_whole_order_fails_if_one_line_is_short(user, admin, product, anon):
    other = factories.create_product(admin, stock=1)
    try:
        body = {"items": [
            {"productId": product["id"], "quantity": 1, "price": 1},
            {"productId": other["id"], "quantity": 5, "price": 1},
        ]}
        assert user.api.post("orders", json=body).status_code == 409
        assert stock_of(anon, product) == 10, "all-or-nothing: the valid line must not be applied"
    finally:
        factories.delete_product(admin, other["id"])


@pytest.mark.security
def test_client_supplied_price_and_total_are_ignored(user, product):
    body = {"totalAmount": 0.01, "items": [{"productId": product["id"], "quantity": 3, "price": 0.01}]}
    assert user.api.post("orders", json=body).status_code == 201
    order = user.api.get("orders/my-orders").json()[0]
    assert float(order["total_amount"]) == pytest.approx(3 * 19.99)
    assert float(order["items"][0]["price"]) == pytest.approx(19.99)


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "abc", None])
def test_invalid_quantities_are_400(user, product, quantity):
    body = {"items": [{"productId": product["id"], "quantity": quantity, "price": 1}]}
    assert user.api.post("orders", json=body).status_code == 400


def test_unknown_product_is_404(user):
    body = {"items": [{"productId": 99999999, "quantity": 1, "price": 1}]}
    assert user.api.post("orders", json=body).status_code == 404


def test_orders_are_private_to_their_owner(user, product):
    user.api.post("orders", json=order_body(product, 1))
    other = factories.register()
    try:
        assert other.api.get("orders/my-orders").json() == []
    finally:
        other.api.close()


@pytest.mark.db
def test_order_is_persisted_in_the_database(user, product):
    user.api.post("orders", json=order_body(product, 2))
    rows = db.sql(
        "SELECT o.status, oi.quantity FROM orders o JOIN order_items oi ON oi.order_id = o.id WHERE o.user_id = %s",
        (user.id,),
    )
    assert rows == [("pending", 2)]


def test_concurrent_orders_never_oversell(admin, product, anon):
    """Five customers each try to buy 4 of a product with 10 in stock: at most two can succeed."""
    shoppers = [factories.register() for _ in range(5)]
    try:
        with concurrent.futures.ThreadPoolExecutor(5) as pool:
            codes = list(pool.map(lambda s: s.api.post("orders", json=order_body(product, 4)).status_code, shoppers))
        assert sorted(codes) == [201, 201, 409, 409, 409]
        assert stock_of(anon, product) == 2
    finally:
        for s in shoppers:
            s.api.close()
