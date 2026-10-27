"""Fail browser tests when a page requests an external address.

Test-specific routes run before this catch-all route. Unhandled requests are
therefore the only requests recorded here.
"""

import sys
from typing import Any
from urllib.parse import urlsplit

from playwright.sync_api import Browser, BrowserContext, Route

LOCAL_HOSTS = {"127.0.0.1", "localhost"}

external: list[str] = []


def refuse(route: Route) -> None:
    url = route.request.url
    if urlsplit(url).hostname in LOCAL_HOSTS:
        route.fallback()
        return
    external.append(url)
    print(f"✗ request to an external host: {url}", file=sys.stderr)
    route.abort()


def new_context(browser: Browser, **options: Any) -> BrowserContext:
    context = browser.new_context(**options)
    context.route("**/*", refuse)
    return context


def verify() -> None:
    if external:
        urls = "\n".join(f"  {url}" for url in sorted(set(external)))
        sys.exit(f"The tests requested external addresses:\n{urls}")
