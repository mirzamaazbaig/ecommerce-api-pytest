from framework import factories


def test_admin_creates_a_product_that_everyone_can_see(admin, anon):
    product = factories.create_product(admin, price=42.5, stock=7)
    try:
        seen = anon.get(f"products/{product['id']}").json()
        assert seen["name"] == product["name"] and float(seen["price"]) == 42.5 and seen["stock"] == 7
    finally:
        factories.delete_product(admin, product["id"])


def test_update_changes_only_the_supplied_fields(admin, anon, product):
    res = admin.api.put(f"products/{product['id']}", json={"price": 5})
    assert res.status_code == 200
    after = anon.get(f"products/{product['id']}").json()
    assert float(after["price"]) == 5
    assert after["name"] == product["name"] and after["stock"] == product["stock"]


def test_delete_removes_the_product(admin, anon):
    product = factories.create_product(admin)
    assert admin.api.delete(f"products/{product['id']}").status_code == 200
    assert anon.get(f"products/{product['id']}").status_code == 404


def test_unknown_product_update_and_delete_are_404(admin):
    assert admin.api.put("products/99999999", json={"price": 1}).status_code == 404
    assert admin.api.delete("products/99999999").status_code == 404
