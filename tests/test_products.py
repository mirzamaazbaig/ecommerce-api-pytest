import pytest
from jsonschema import validate

from framework import schemas


@pytest.mark.smoke
def test_list_matches_the_product_contract(anon):
    res = anon.get("products")
    assert res.status_code == 200
    assert "application/json" in res.headers["content-type"]
    products = res.json()
    assert products
    validate(products, schemas.PRODUCT_LIST)


def test_limit_restricts_the_result_size(anon):
    assert len(anon.get("products", params={"limit": 2}).json()) == 2


def test_paging_does_not_overlap(anon):
    q = {"limit": 3, "sort_by": "name", "order": "ASC"}
    first = {p["id"] for p in anon.get("products", params={**q, "offset": 0}).json()}
    second = {p["id"] for p in anon.get("products", params={**q, "offset": 3}).json()}
    assert second and not first & second


def test_category_filter_only_returns_that_category(anon):
    products = anon.get("products", params={"category_id": 1}).json()
    assert products
    assert {p["category_id"] for p in products} == {1}


def test_max_price_filter(anon):
    products = anon.get("products", params={"max_price": 30}).json()
    assert products
    assert all(float(p["price"]) <= 30 for p in products)


@pytest.mark.parametrize("order", ["ASC", "DESC"])
def test_sort_by_price(anon, order):
    prices = [float(p["price"]) for p in anon.get("products", params={"sort_by": "price", "order": order}).json()]
    assert len(prices) > 1
    assert prices == sorted(prices, reverse=(order == "DESC"))


def test_search_is_case_insensitive(anon):
    lower = {p["id"] for p in anon.get("products", params={"search": "t-shirt"}).json()}
    upper = {p["id"] for p in anon.get("products", params={"search": "T-SHIRT"}).json()}
    assert lower and lower == upper


def test_search_without_match_returns_an_empty_list(anon):
    res = anon.get("products", params={"search": "zzz-no-such-product-zzz"})
    assert res.status_code == 200 and res.json() == []


@pytest.mark.security
@pytest.mark.parametrize("payload", ["' OR 1=1; --", "'; DROP TABLE products; --", "\" OR \"\"=\""])
def test_sql_metacharacters_in_search_are_data(anon, payload):
    assert anon.get("products", params={"search": payload}).status_code == 200
    assert anon.get("products").json(), "the products table must still be intact"


@pytest.mark.security
def test_unsupported_sort_column_is_ignored(anon):
    res = anon.get("products", params={"sort_by": "password_hash; --"})
    assert res.status_code == 200 and res.json()


def test_get_by_id_matches_the_list(anon):
    first = anon.get("products", params={"limit": 1}).json()[0]
    res = anon.get(f"products/{first['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == first["id"] and res.json()["name"] == first["name"]


def test_unknown_product_is_404(anon):
    res = anon.get("products/99999999")
    assert res.status_code == 404 and res.json()["message"] == "Product not found"


@pytest.mark.parametrize("bad_id", ["abc", "-1", "0", "1.5", "99999999999"])
def test_invalid_id_is_400_not_a_server_error(anon, bad_id):
    assert anon.get(f"products/{bad_id}").status_code == 400
