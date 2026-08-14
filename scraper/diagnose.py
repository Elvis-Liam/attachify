"""One-off diagnostic, not part of the normal pipeline.

Renders a page with Playwright and saves a full-page screenshot plus the
rendered HTML locally, so a real page's actual structure can be inspected
instead of guessed at. This exists specifically because this environment has
no way to render JavaScript or see raw HTML itself; a screenshot is the most
direct way to close that gap.

Run with: python diagnose.py [url]
Defaults to the Safaricom Oracle HCM requisitions page if no URL is given.
Writes diagnostic_screenshot.png and diagnostic_page.html into this folder.
"""
import asyncio
import sys
from pathlib import Path

DEFAULT_URL = "https://egjd.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/requisitions"


async def diagnose(url: str) -> None:
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            page = await browser.new_page(viewport={"width": 1400, "height": 900})
            print(f"Loading {url} ...")
            await page.goto(url, timeout=30000, wait_until="networkidle")
            # A short extra wait on top of networkidle: some single-page apps
            # finish their last render just after network activity settles,
            # not exactly when it does.
            await page.wait_for_timeout(3000)

            html = await page.content()
            html_path = Path("diagnostic_page.html")
            html_path.write_text(html, encoding="utf-8")

            screenshot_path = Path("diagnostic_screenshot.png")
            await page.screenshot(path=str(screenshot_path), full_page=True)

            title = await page.title()
            link_count = await page.locator("a").count()
            job_link_count = await page.locator("a[href*='/job/']").count()

            print(f"\nPage title: {title!r}")
            print(f"Total <a> links found: {link_count}")
            print(f"Links matching '/job/': {job_link_count}")
            print(f"Saved screenshot to: {screenshot_path.resolve()}")
            print(f"Saved rendered HTML to: {html_path.resolve()} ({len(html)} characters)")
        finally:
            await browser.close()


if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    asyncio.run(diagnose(target_url))
