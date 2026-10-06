import pytest

from framework import factories


def test_new_user_has_an_empty_wishlist(user):
    assert user.api.get("wishlist").json() == []


def test_add_list_and_remove_a_wishlist_item(user):
    assert user.api.post("wishlist", json={"product_id": 1}).status_code == 201
    items = user.api.get("wishlist").json()
    assert [i["product_id"] for i in items] == [1]
    assert user.api.delete("wishlist/1").status_code == 200
    assert user.api.get("wishlist").json() == []


def test_adding_twice_is_idempotent(user):
    user.api.post("wishlist", json={"product_id": 1})
    again = user.api.post("wishlist", json={"product_id": 1})
    assert again.status_code == 200 and again.json()["message"] == "Item already in wishlist"
    assert len(user.api.get("wishlist").json()) == 1


def test_wishlists_are_private(user):
    other = factories.register()
    try:
        user.api.post("wishlist", json={"product_id": 1})
        assert other.api.get("wishlist").json() == []
    finally:
        other.api.close()


@pytest.mark.parametrize("product_id,status", [(99999999, 404), ("abc", 400), (-1, 400), (None, 400)])
def test_invalid_wishlist_product_is_rejected(user, product_id, status):
    assert user.api.post("wishlist", json={"product_id": product_id}).status_code == status


def test_review_is_public_and_shows_the_author(user, product, anon):
    res = user.api.post("reviews", json={"product_id": product["id"], "rating": 4, "comment": "Solid"})
    assert res.status_code == 201
    reviews = anon.get(f"reviews/{product['id']}").json()
    assert len(reviews) == 1
    assert (reviews[0]["rating"], reviews[0]["comment"], reviews[0]["email"]) == (4, "Solid", user.email)


@pytest.mark.parametrize("rating", [0, 6, -1, 3.5, "5", None])
def test_invalid_ratings_are_rejected_and_not_stored(user, product, anon, rating):
    res = user.api.post("reviews", json={"product_id": product["id"], "rating": rating, "comment": "x"})
    assert res.status_code == 400
    assert anon.get(f"reviews/{product['id']}").json() == []


def test_reviewing_an_unknown_product_is_404(user):
    assert user.api.post("reviews", json={"product_id": 99999999, "rating": 3, "comment": "x"}).status_code == 404
