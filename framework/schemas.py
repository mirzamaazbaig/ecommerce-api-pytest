"""JSON schemas for response contracts."""
PRODUCT = {
    "type": "object",
    "required": ["id", "name", "price", "stock", "category_name", "avg_rating", "review_count"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "price": {"type": "string", "pattern": r"^\d+\.\d{2}$"},  # pg serialises DECIMAL as a string
        "stock": {"type": "integer", "minimum": 0},
        "category_name": {"type": "string"},
        "avg_rating": {"type": "number"},
        "review_count": {"type": "integer"},
    },
}
PRODUCT_LIST = {"type": "array", "items": PRODUCT}

USER = {
    "type": "object",
    "required": ["id", "email", "role"],
    "properties": {"id": {"type": "integer"}, "email": {"type": "string"}, "role": {"enum": ["user", "admin"]}},
}
