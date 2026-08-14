"""Fetching. Two paths, matching each source's needs_js flag.

The httpx path is real, tested code (see tests/test_pipeline.py, which exercises
it against a mock transport rather than a live network call, since this
environment has no general internet access to test against). The Playwright
path follows Playwright's standard, documented async API, but this environment
cannot run a real browser, so it has not been executed here even once. Treat it
as correct-by-inspection, not verified, until it's actually run.
"""
import asyncio

import httpx

DEFAULT_TIMEOUT = 20.0
DEFAULT_HEADERS = {
    "User-Agent": "AttachifyBot/0.1 (+https://attachify.example; verified opportunity directory)"
}


async def fetch_static(url: str, client: httpx.AsyncClient) -> str:
    """Fetch a page that does not need JavaScript to render its content."""
    response = await client.get(url, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT, follow_redirects=True)
    response.raise_for_status()
    return response.text


async def fetch_rendered(url: str) -> str:
    """Fetch a page's fully rendered HTML after JavaScript execution.

    Requires the playwright package and its browser binaries to be installed
    (playwright install chromium), which is why this stays a separate,
    optional path rather than something every source pays for by default.
    Not executed in this environment; there is no browser available here to
    run it against.
    """
    from playwright.async_api import async_playwright  # imported lazily: only
    # needed for needs_js sources, so a plain httpx-only scraper run never
    # requires Playwright to even be installed.

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            # Deliberately NOT using DEFAULT_HEADERS here, unlike fetch_static.
            # A custom, obviously-a-bot User-Agent is honest practice for a
            # plain page fetch, but against an enterprise platform like Oracle
            # HCM it's a likely reason the app's own data-fetching calls got
            # silently blocked while the page shell still loaded: run.py found
            # 0 jobs with it, diagnose.py found the real 4 without it, using
            # Playwright's own default browser identity plus a larger
            # viewport. Matching that exactly now rather than guessing at one
            # variable at a time.
            page = await browser.new_page(viewport={"width": 1400, "height": 900})
            await page.goto(url, timeout=DEFAULT_TIMEOUT * 1000, wait_until="networkidle")
            # Some single-page apps finish their last render just after network
            # activity settles, not exactly when it does.
            await page.wait_for_timeout(3000)
            return await page.content()
        finally:
            await browser.close()


async def fetch(url: str, *, needs_js: bool, client: httpx.AsyncClient | None = None) -> str:
    """Dispatch to the right fetch path for a source."""
    if needs_js:
        return await fetch_rendered(url)
    if client is None:
        async with httpx.AsyncClient() as owned_client:
            return await fetch_static(url, owned_client)
    return await fetch_static(url, client)
