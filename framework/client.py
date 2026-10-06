"""Thin wrapper around requests.Session: base URL, timeout, cookie jar per instance."""
import requests

from framework.config import BASE_URL, TIMEOUT


class ApiClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", TIMEOUT)
        return self.session.request(method, f"{self.base_url}/{path.lstrip('/')}", **kwargs)

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, **kw):
        return self.request("POST", path, **kw)

    def put(self, path, **kw):
        return self.request("PUT", path, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)

    def close(self):
        self.session.close()
