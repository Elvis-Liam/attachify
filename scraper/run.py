"""Scraper entry point. Run with: python run.py (from the scraper/ folder).

Adds both backend/ and this project's root to sys.path before any other
import in this file runs. backend/ is needed so every module under scraper/
can import the backend's models and db session as if they were part of the
same package, reusing the exact same schema rather than duplicating it. The
project root is needed so this file's own "from scraper.pipeline import ..."
style imports resolve regardless of which directory the script is actually
launched from, since Python only auto-adds a script's own directory to the
path, not that directory's parent. Both have to happen first, at module
import time, not inside a function, since Python resolves import statements
immediately as they're read.
"""
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "backend"))
sys.path.insert(0, str(_PROJECT_ROOT))

import asyncio  # noqa: E402
from typing import Callable  # noqa: E402

import httpx  # noqa: E402

from app.db.session import AsyncSessionLocal  # noqa: E402
from scraper.pipeline.fetch import fetch  # noqa: E402
from scraper.pipeline.normalize import normalize_opportunity  # noqa: E402
from scraper.pipeline.store import upsert_opportunity  # noqa: E402
from scraper.pipeline.validate import ValidationError, validate_opportunity  # noqa: E402
from scraper.sources import safaricom  # noqa: E402
from scraper.sources.base import SourceConfig  # noqa: E402

# Each entry: (config, list-page parser, detail-page parser or None if the
# source doesn't have one implemented yet). Adding a new source means adding
# one more tuple here, not touching this file's logic.
SOURCES: list[tuple[SourceConfig, Callable, Callable | None]] = [
    (safaricom.CONFIG, safaricom.parse_list, safaricom.parse_detail),
]


async def run_source(config: SourceConfig, parse_list: Callable, parse_detail: Callable | None, client: httpx.AsyncClient) -> None:
    print(f"[{config.company_slug}] fetching list page: {config.list_url}")
    try:
        list_html = await fetch(config.list_url, needs_js=config.needs_js, client=client)
        debug_path = Path(f"debug_{config.company_slug}_list.html")
        debug_path.write_text(list_html, encoding="utf-8")
        print(f"[{config.company_slug}] fetched {len(list_html)} characters, saved to {debug_path.resolve()}")
    except Exception as exc:
        print(f"[{config.company_slug}] failed to fetch list page: {exc!r}")
        return

    raw_items = parse_list(list_html)
    print(f"[{config.company_slug}] found {len(raw_items)} candidate listing(s)")

    stored, skipped = 0, 0
    async with AsyncSessionLocal() as db:
        for item in raw_items:
            title = item.get("title", "(untitled)")
            detail_url = item.get("detail_url")
            full_item = dict(item)

            if parse_detail is not None and detail_url:
                try:
                    detail_html = await fetch(detail_url, needs_js=config.needs_js, client=client)
                    full_item.update(parse_detail(detail_html))
                except NotImplementedError as exc:
                    print(f"[{config.company_slug}] skipping '{title}': {exc}\n    detail_url: {detail_url}")
                    skipped += 1
                    continue
                except Exception as exc:
                    print(f"[{config.company_slug}] skipping '{title}': failed to fetch/parse detail page: {exc!r}")
                    skipped += 1
                    continue

            source_url = detail_url or config.list_url
            record = normalize_opportunity(full_item, company_slug=config.company_slug, source_url=source_url)

            try:
                validate_opportunity(record)
            except ValidationError as exc:
                print(f"[{config.company_slug}] skipping '{title}': {exc.reason}")
                skipped += 1
                continue

            opportunity, created = await upsert_opportunity(db, record=record, company_name=config.company_name)
            stored += 1
            print(f"[{config.company_slug}] {'created' if created else 'updated'}: {opportunity.title}")

    print(f"[{config.company_slug}] done: {stored} stored, {skipped} skipped\n")


async def main() -> None:
    async with httpx.AsyncClient() as client:
        for config, parse_list, parse_detail in SOURCES:
            await run_source(config, parse_list, parse_detail, client)


if __name__ == "__main__":
    asyncio.run(main())
