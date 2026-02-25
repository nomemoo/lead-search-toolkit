"""Google Dorks engine — uses DuckDuckGo to find LinkedIn profiles via site:linkedin.com/in queries."""

import re
import time
from datetime import datetime

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS


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
    max_results = settings.get("max_results_per_query", 20)
    sleep_sec = settings.get("sleep_between_queries", 2)

    all_leads = []
    seen_urls = set()

    with DDGS() as ddgs:
        for seg_name, label, query in queries:
            print(f"  [{label}] {query[:80]}...")
            try:
                results = ddgs.text(query, max_results=max_results)
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
                    print(f"    {handle} — {r.get('title', '')[:60]}")

                print(f"    -> {count} new leads")
                time.sleep(sleep_sec)

            except Exception as e:
                print(f"    Error: {e}")
                time.sleep(5)

    return all_leads
