"""Builders for test data. Every test creates its own users and products so tests can run in parallel."""
import itertools
import time
import uuid
from dataclasses import dataclass

from framework import db
from framework.client import ApiClient
from framework.config import PASSWORD

_counter = itertools.count()


def unique_email(prefix: str = "py") -> str:
    return f"{prefix}_{int(time.time() * 1000)}_{next(_counter)}_{uuid.uuid4().hex[:4]}@example.com"


@dataclass
class User:
    api: ApiClient
    id: int
    email: str
    password: str = PASSWORD


def register(prefix: str = "user") -> User:
    api = ApiClient()
    email = unique_email(prefix)
    res = api.post("auth/register", json={"email": email, "password": PASSWORD})
    assert res.status_code == 201, f"setup: registration failed: {res.status_code} {res.text}"
    return User(api, res.json()["user"]["id"], email)


def register_admin() -> User:
    """Promote through SQL (there is no API for it), then log in again: the role is stored in the session."""
    user = register("admin")
    db.sql("UPDATE users SET role = 'admin' WHERE id = %s", (user.id,))
    res = user.api.post("auth/login", json={"email": user.email, "password": user.password})
    assert res.status_code == 200, f"setup: admin login failed: {res.status_code}"
    return user


def create_product(admin: User, **overrides) -> dict:
    body = {
        "name": f"QA Product {uuid.uuid4().hex[:8]}",
        "description": "Created by the pytest suite",
        "price": 19.99,
        "stock": 10,
        "imageUrl": None,
        "categoryId": 1,
        **overrides,
    }
    res = admin.api.post("products", json=body)
    assert res.status_code == 201, f"setup: product creation failed: {res.status_code} {res.text}"
    return res.json()


def delete_product(admin: User, product_id: int) -> None:
    db.sql("DELETE FROM order_items WHERE product_id = %s", (product_id,))
    admin.api.delete(f"products/{product_id}")


def order_body(product: dict, quantity: int, price: float | None = None) -> dict:
    price = float(product["price"]) if price is None else price
    return {
        "totalAmount": round(price * quantity, 2),
        "items": [{"productId": product["id"], "quantity": quantity, "price": price}],
    }
