"""Google Dorks engine — uses DuckDuckGo to find LinkedIn profiles via site:linkedin.com/in queries."""

import logging
import re
import time
from datetime import datetime

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

# Safety limits
QUERY_TIMEOUT = 30  # seconds per query
MAX_TOTAL_TIME = 180  # 3 minutes total for all queries


def _extract_handle(url: str) -> str:
    match = re.search(r"linkedin\.com/in/([^/?]+)", url)
    return match.group(1) if match else ""


def _build_queries(config: dict) -> list[tuple[str, str, str]]:
    """Generate (segment_name, label, query) tuples from config segments."""
    country = config.get("country", "")
    queries = []

    for segment in config.get("segments", []):
        seg_name = segment["name"]

        # Hebrew titles — no country filter needed (inherently local)
        for title in segment.get("persona_titles", {}).get("hebrew", []):
            label = f"{seg_name}-he"
            query = f'site:linkedin.com/in "{title}"'
            queries.append((seg_name, label, query))

        # English titles — add country filter
        for title in segment.get("persona_titles", {}).get("english", []):
            label = f"{seg_name}-en"
            query = f'site:linkedin.com/in "{title}"'
            if country:
                query += f" {country}"
            queries.append((seg_name, label, query))

    return queries


def run(config: dict) -> list[dict]:
    """Run DuckDuckGo searches and return list of lead dicts."""
    queries = _build_queries(config)
    settings = config.get("settings", {})
    max_results = settings.get("max_results_per_query", 10)
    sleep_sec = settings.get("sleep_between_queries", 2)

    all_leads = []
    seen_urls = set()
    start_time = time.monotonic()

    with DDGS(timeout=QUERY_TIMEOUT) as ddgs:
        for seg_name, label, query in queries:
            # Total time budget check
            if time.monotonic() - start_time > MAX_TOTAL_TIME:
                logger.warning("Total time budget exceeded (%ds), stopping", MAX_TOTAL_TIME)
                break

            logger.info("[%s] %s", label, query[:80])
            try:
                results = list(ddgs.text(query, max_results=max_results))
                count = 0
                for r in results:
                    url = r.get("href", "")
                    if "linkedin.com/in/" not in url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    handle = _extract_handle(url)
                    all_leads.append({
                        "name": "",
                        "linkedin_url": url,
                        "handle": handle,
                        "title": r.get("title", ""),
                        "snippet": r.get("body", "")[:200],
                        "location": "",
                        "source_query": label,
                        "segment": seg_name,
                        "engine": "google_dorks",
                        "status": "identified",
                        "contacted": "",
                        "response": "",
                        "email": "",
                        "notes": "",
                        "found_at": datetime.now().strftime("%Y-%m-%d"),
                    })
                    count += 1
                    logger.debug("  %s — %s", handle, r.get("title", "")[:60])

                logger.info("  -> %d new leads from %s", count, label)
                time.sleep(sleep_sec)

            except Exception as e:
                logger.warning("  Query error for %s: %s", label, e)
                time.sleep(3)

    elapsed = time.monotonic() - start_time
    logger.info("Google dorks: %d leads in %.1fs from %d queries", len(all_leads), elapsed, len(queries))
    return all_leads
