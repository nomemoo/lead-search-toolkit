"""LinkedIn API engine — uses unofficial linkedin-api for richer profile search.

Requires: pip install lead-search-toolkit[linkedin]

Auth: LINKEDIN_EMAIL + LINKEDIN_PASSWORD env vars
      (see linkedin-api docs for additional auth methods)

NOTE: Uses an unofficial API. Review the linkedin-api project documentation
for risks and Terms of Service implications.
"""

import os
import random
import sys
import time
from datetime import datetime


def _available() -> bool:
    """Check if linkedin-api is installed."""
    try:
        import linkedin_api  # noqa: F401
        return True
    except ImportError:
        return False


def _get_credentials() -> dict | None:
    """Return auth dict: cookie-based or email/password, or None."""
    li_at = os.environ.get("LINKEDIN_LI_AT")
    jsessionid = os.environ.get("LINKEDIN_JSESSIONID")
    if li_at and jsessionid:
        return {"method": "cookie", "li_at": li_at, "jsessionid": jsessionid}

    email = os.environ.get("LINKEDIN_EMAIL")
    password = os.environ.get("LINKEDIN_PASSWORD")
    if email and password:
        return {"method": "login", "email": email, "password": password}

    return None


def _print_safety_warning():
    """Print a brief notice to stderr on engine startup."""
    warning = (
        "\n  LinkedIn Engine: Uses an unofficial API. "
        "Review linkedin-api docs for risks and ToS implications.\n"
    )
    print(warning, file=sys.stderr)


def _authenticate(creds: dict):
    """Create and return a Linkedin API instance."""
    from linkedin_api import Linkedin

    if creds["method"] == "cookie":
        print("  Authenticating with LinkedIn (cookie auth)...")
        cookies = {"li_at": creds["li_at"], "JSESSIONID": creds["jsessionid"]}
        return Linkedin("", "", cookies=cookies)
    else:
        print("  Authenticating with LinkedIn (email/password)...")
        return Linkedin(creds["email"], creds["password"])


def _extract_lead(person: dict, source_label: str, segment_name: str) -> dict:
    """Flatten a LinkedIn person result into a lead dict."""
    profile = person.get("memberIdentity", "")

    def _name(obj):
        if isinstance(obj, str):
            return obj
        if isinstance(obj, dict):
            return obj.get("text", "") or obj.get("value", "")
        return ""

    name = f"{_name(person.get('firstName', ''))} {_name(person.get('lastName', ''))}".strip()

    headline = person.get("headline", "")
    if isinstance(headline, dict):
        headline = headline.get("text", "")

    location = person.get("subline", "")
    if isinstance(location, dict):
        location = location.get("text", "")

    linkedin_url = f"https://www.linkedin.com/in/{profile}" if profile else ""

    return {
        "name": name,
        "linkedin_url": linkedin_url,
        "handle": profile,
        "title": headline,
        "snippet": "",
        "location": location,
        "source_query": source_label,
        "segment": segment_name,
        "engine": "linkedin_api",
        "status": "identified",
        "contacted": "",
        "response": "",
        "email": "",
        "notes": "",
        "found_at": datetime.now().strftime("%Y-%m-%d"),
    }


def run(config: dict) -> list[dict]:
    """Run LinkedIn API searches and return list of lead dicts."""
    if not _available():
        print("  linkedin-api not installed. Install with: pip install lead-search-toolkit[linkedin]")
        return []

    creds = _get_credentials()
    if not creds:
        print("  Set LinkedIn credentials to use this engine.")
        print("  Option 1 (safer): LINKEDIN_LI_AT + LINKEDIN_JSESSIONID")
        print("  Option 2: LINKEDIN_EMAIL + LINKEDIN_PASSWORD")
        return []

    _print_safety_warning()

    try:
        api = _authenticate(creds)
    except Exception as e:
        print(f"  LinkedIn auth failed: {e}")
        return []
    print("  Connected.")

    settings = config.get("settings", {})
    max_results = settings.get("max_results_per_query", 25)
    sleep_base = settings.get("sleep_between_queries", 3)

    linkedin_cfg = config.get("linkedin", {})
    max_per_session = linkedin_cfg.get("max_per_session", 50)
    sleep_jitter = linkedin_cfg.get("sleep_jitter", 2)
    network_depths = linkedin_cfg.get("network_depths", ["S", "O"])

    all_leads = []
    seen_handles = set()
    session_count = 0

    for segment in config.get("segments", []):
        seg_name = segment["name"]
        for keyword in segment.get("keywords", []):
            if session_count >= max_per_session:
                print(f"  Session limit reached ({max_per_session} results). Stopping.")
                return all_leads

            label = f"{seg_name}-li"
            print(f"  [{label}] '{keyword}'...")
            try:
                results = api.search_people(
                    keywords=keyword,
                    network_depths=network_depths,
                    limit=max_results,
                )
                count = 0
                for person in results:
                    if session_count >= max_per_session:
                        print(f"  Session limit reached ({max_per_session} results). Stopping.")
                        return all_leads

                    handle = person.get("memberIdentity", "")
                    if not handle or handle in seen_handles:
                        continue
                    seen_handles.add(handle)

                    lead = _extract_lead(person, label, seg_name)
                    all_leads.append(lead)
                    count += 1
                    session_count += 1
                    print(f"    {lead['name']} — {lead['title'][:60]}")

                print(f"    -> {count} new leads")
                delay = sleep_base + random.uniform(0, sleep_jitter)
                time.sleep(delay)

            except Exception as e:
                print(f"    Error on '{keyword}': {e}")
                time.sleep(10)

    return all_leads
