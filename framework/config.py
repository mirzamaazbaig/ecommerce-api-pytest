import os

BASE_URL = os.environ.get("API_URL", "http://localhost:5000/api").rstrip("/")
DATABASE_URL = os.environ.get("DATABASE_URL")  # optional: enables the `db` tests
PASSWORD = "TestPass123!"
TIMEOUT = 10
