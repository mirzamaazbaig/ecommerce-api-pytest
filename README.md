# E-Commerce API Tests: Python and pytest

A pytest framework for the REST API of a React, Express and PostgreSQL shop ([application under test](https://github.com/mirzamaazbaig/Ecom)). 82 test cases for authentication, products, access control, orders, wishlist and reviews. They run in GitHub Actions against a PostgreSQL service container.

This is the Python counterpart to the Playwright API tests in the application repository; both exercise the same endpoints.

## What it shows

- **Layered framework:** `framework/` holds the HTTP client, test-data factories, SQL helper and JSON schemas; `tests/` holds only test logic.
- **Isolated data:** each test registers its own users and creates its own product, so tests run in parallel (`pytest -n 4`) and assertions on stock and totals are exact.
- **Contract checks:** response bodies are validated against JSON schemas, not just status codes.
- **Business rules:** server-side stock check (409), server-side pricing that ignores client prices, all-or-nothing orders, and a concurrency test (five buyers, stock for two, exactly two succeed).
- **Security checks (`-m security`):** 401 vs 403 on every protected endpoint, SQL metacharacters, an unsupported sort column, a login that does not reveal whether an email exists.
- **Database checks (`-m db`):** persisted rows are verified with SQL. These tests, and anything that needs an admin, are skipped when `DATABASE_URL` is not set.
- **Parametrised negative cases:** invalid ids, ratings, quantities and registration bodies.

## Run it

```bash
# 1. Start the application's API and database (see the Ecom README), then:
pip install -r requirements.txt
export API_URL=http://localhost:5000/api                       # default
export DATABASE_URL=postgresql://postgres:password@localhost:5432/ecom_db   # enables admin and db tests
pytest -n 4                    # everything
pytest -m smoke                # quick check
pytest -m security             # security checks only
```

The HTML report is written to `reports/report.html`.

## Verification

- All 82 pass in three consecutive runs, each from a freshly created and seeded database.
- Run against the application code from before the order fixes, 10 of the order tests fail (overselling, client-controlled prices, missing validation). They pass on the fixed code.

## Observation, not a failing test

`POST /orders` accepts a quantity sent as a numeric string (`"2"`) and treats it as 2. It rejects `"abc"`, `0`, negatives and decimals. I treat this as lenient input handling rather than a defect, so there is no test for it. A stricter contract would reject any non-integer type.

## Structure

```
framework/   client.py  config.py  db.py  factories.py  schemas.py
tests/       test_auth  test_products  test_access_control  test_admin  test_orders  test_wishlist_reviews
conftest.py  fixtures: anon, user, admin, product
.github/workflows/api-tests.yml
```
