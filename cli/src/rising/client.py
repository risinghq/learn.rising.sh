"""The HTTP calls to the Rising site. The site answers errors as {"error", "reason"}."""

import json
import urllib.error
import urllib.parse
import urllib.request
from importlib.metadata import version
from typing import Any

TIMEOUT = 15
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


class ApiError(Exception):
    def __init__(self, status: int, reason: str, message: str, retry_after: int = 0) -> None:
        super().__init__(message)
        self.status = status
        self.reason = reason
        self.retry_after = retry_after


class Client:
    def __init__(self, url: str, token: str | None = None) -> None:
        parts = urllib.parse.urlsplit(url)
        # Credentials may leave the machine only over HTTPS, except on loopback.
        if parts.scheme != "https" and not (
            parts.scheme == "http" and parts.hostname in LOCAL_HOSTS
        ):
            raise ApiError(0, "bad_url", f"La dirección {url} debe empezar con https://.")
        self.url = url.rstrip("/")
        self.token = token

    def request(self, method: str, path: str, body: Any = None) -> Any:
        headers = {"User-Agent": f"rising-cli/{version('rising')}", "Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(self.url + path, data, headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                raw = response.read()
        except urllib.error.HTTPError as e:
            raise self._failure(e) from None
        except urllib.error.URLError as e:
            raise ApiError(
                0, "unreachable", f"No se pudo conectar con {self.url}: {e.reason}"
            ) from None
        return json.loads(raw) if raw else None

    @staticmethod
    def _failure(e: urllib.error.HTTPError) -> ApiError:
        try:
            body = json.loads(e.read())
            reason, message = body["reason"], body["error"]
        except ValueError, KeyError, TypeError:
            reason, message = "http", f"El sitio respondió {e.code}."
        retry = e.headers.get("Retry-After", "")
        return ApiError(e.code, reason, message, int(retry) if retry.isdecimal() else 0)
