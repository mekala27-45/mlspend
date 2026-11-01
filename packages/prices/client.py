from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from packages.core.io import digest, read_json, write_json


class SourceClient:
    """Cache HTTP evidence by exact URL; retry rate limits without losing completed pages."""

    def __init__(self, cache: Path, headers: dict[str, str] | None = None) -> None:
        self.cache = cache
        self.client = httpx.Client(headers=headers, timeout=60, follow_redirects=True)
        self.visited: list[str] = []

    def get(self, url: str) -> Any:
        if urlparse(url).scheme != "https":
            raise ValueError("Sources must use HTTPS")
        path = self.cache / (digest(url) + ".json")
        prior = read_json(path) if path.exists() else {}
        headers = {"If-None-Match": prior["etag"]} if prior.get("etag") else {}
        for attempt in range(6):
            response = self.client.get(url, headers=headers)
            if response.status_code == 304:
                self.visited.append(url)
                return prior["body"]
            if response.status_code in (429, 403) and (
                response.headers.get("Retry-After")
                or response.headers.get("X-RateLimit-Remaining") == "0"
            ):
                wait = float(response.headers.get("Retry-After", "0"))
                wait = max(
                    wait, float(response.headers.get("X-RateLimit-Reset", "0")) - time.time()
                )
                if wait > 60:
                    raise RuntimeError(
                        "Rate limit exceeded; resume after reset using the same cache"
                    )
                time.sleep(max(1, wait))
                continue
            if response.status_code >= 500 and attempt < 5:
                time.sleep(min(2**attempt, 8))
                continue
            response.raise_for_status()
            body = response.json()
            write_json(
                path,
                {
                    "url": url,
                    "etag": response.headers.get("ETag"),
                    "body": body,
                    "response_digest": __import__("hashlib").sha256(response.content).hexdigest(),
                },
            )
            self.visited.append(url)
            return body
        raise RuntimeError("Source retries exhausted")

    def github_pages(self, url: str, key: str | None = None) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        for page in range(1, 10001):
            separator = "&" if "?" in url else "?"
            body = self.get(f"{url}{separator}per_page=100&page={page}")
            rows = body[key] if key else body
            output.extend(rows)
            if len(rows) < 100:
                return output
        raise RuntimeError("Pagination limit reached; refusing an incomplete dataset")
