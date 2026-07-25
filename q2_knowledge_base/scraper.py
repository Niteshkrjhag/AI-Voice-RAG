"""
q2_knowledge_base/scraper.py — Web content extraction using Crawl4AI

Crawl4AI v0.9.x API:
  - AsyncWebCrawler with BrowserConfig + CrawlerRunConfig
  - Returns CrawlResult with .markdown property
  - Requires `crawl4ai-setup` post-install for Playwright browser
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from shared.config import config
from shared.logger import get_logger

log = get_logger("q2.scraper")


# ── Browser configuration (reused across all crawls) ───────────
# headless=True: no visible browser window (required for CI/server)
# verbose=False: suppress Crawl4AI's internal logging noise
BROWSER_CONFIG = BrowserConfig(
    headless=True,
    verbose=False,
)


async def scrape_url(
    url: str,
    cache_mode: CacheMode = CacheMode.BYPASS,
) -> Optional[dict]:
    """
    Scrape a single URL and return structured content.

    Args:
        url: Target URL to scrape
        cache_mode: CacheMode.BYPASS skips cache (fresh fetch every time)

    Returns:
        Dict with url, markdown content, title, and success flag.
        None if the crawl fails entirely.
    """
    # CrawlerRunConfig controls per-crawl behavior (caching, extraction)
    run_config = CrawlerRunConfig(cache_mode=cache_mode)

    # AsyncWebCrawler as context manager ensures browser process cleanup
    async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
        try:
            result = await crawler.arun(url=url, config=run_config)

            if not result.success:
                log.warning("crawl_failed", url=url, error=result.error_message)
                return None

            log.info("crawl_success", url=url, content_length=len(result.markdown or ""))

            return {
                "url": url,
                "markdown": result.markdown,  # LLM-ready markdown output
                "title": result.metadata.get("title", "") if result.metadata else "",
                "success": True,
            }

        except Exception as e:
            log.error("crawl_exception", url=url, error=str(e))
            return None


async def scrape_urls(urls: list[str]) -> list[dict]:
    """
    Scrape multiple URLs concurrently using a shared browser instance.

    Uses arun_many() for efficient batch crawling — single browser
    process handles all URLs instead of spawning one per URL.

    Args:
        urls: List of target URLs

    Returns:
        List of successfully scraped content dicts
    """
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    results = []

    async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
        # arun_many handles concurrent crawling with connection pooling
        crawl_results = await crawler.arun_many(
            urls=urls,
            config=run_config,
        )

        for result in crawl_results:
            if result.success:
                results.append({
                    "url": result.url,
                    "markdown": result.markdown,
                    "title": result.metadata.get("title", "") if result.metadata else "",
                    "success": True,
                })
                log.info("batch_crawl_success", url=result.url)
            else:
                log.warning("batch_crawl_failed", url=result.url, error=result.error_message)

    log.info("batch_crawl_complete", total=len(urls), success=len(results))
    return results


def save_raw_content(content: dict, output_dir: Optional[Path] = None) -> Path:
    """
    Persist raw scraped content to disk for traceability.

    Assessment requires source tracking — every KB record must
    trace back to its raw extraction. Saved as JSON for schema consistency.

    Args:
        content: Scraped content dict from scrape_url()
        output_dir: Target directory (defaults to config.DATA_RAW_DIR)

    Returns:
        Path to the saved file
    """
    output_dir = output_dir or config.DATA_RAW_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize URL to create a safe filename
    safe_name = content["url"].replace("https://", "").replace("http://", "")
    safe_name = safe_name.replace("/", "_").replace(".", "_")[:100]
    filepath = output_dir / f"{safe_name}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)

    log.info("raw_content_saved", path=str(filepath))
    return filepath


# ── CLI entry point for standalone scraping ─────────────────────
if __name__ == "__main__":
    import sys

    # Usage: python -m q2_knowledge_base.scraper <url1> <url2> ...
    urls = sys.argv[1:] or ["https://example.com"]

    async def main():
        results = await scrape_urls(urls)
        for r in results:
            save_raw_content(r)
            print(f"✓ {r['url']} ({len(r['markdown'])} chars)")

    asyncio.run(main())
