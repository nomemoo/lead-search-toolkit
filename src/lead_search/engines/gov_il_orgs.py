"""Israeli NGO Registry engine — queries data.gov.il for registered organizations.

No authentication required. Official open data from Rasham Amutot (Ministry of Justice).
Only runs when country is set to "Israel" in config.
"""

import requests
from datetime import datetime

API_BASE = "https://data.gov.il/api/3/action/datastore_search"
AMUTOT_RESOURCE_ID = "be5b7935-3922-45d4-9638-08871b17ec95"
ACTIVE_STATUSES = ["רשומה", "פעילה"]


def _fetch_by_keyword(keyword: str, limit: int = 100) -> list[dict]:
    params = {
        "resource_id": AMUTOT_RESOURCE_ID,
        "q": keyword,
        "limit": limit,
    }
    try:
        r = requests.get(API_BASE, params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("result", {}).get("records", [])
    except Exception as e:
        print(f"    Error fetching '{keyword}': {e}")
        return []


def _is_active(record: dict) -> bool:
    status = record.get("סטטוס", "")
    return any(s in status for s in ACTIVE_STATUSES) or status == ""


def _flatten(record: dict, source_keyword: str) -> dict:
    name_he = record.get("שם עמותה בעברית", "").strip()
    name_en = record.get("שם עמותה באנגלית", "").strip()
    number = record.get("מספר עמותה", "")
    category = record.get("סיווג פעילות ענפי", "")
    city = record.get("כתובת - ישוב", "")
    status = record.get("סטטוס", "")

    guidestar_url = f"https://www.guidestar.org.il/organization/{number}" if number else ""

    return {
        "name_hebrew": name_he,
        "name_english": name_en,
        "org_number": number,
        "category": category,
        "city": city,
        "status": status,
        "guidestar_url": guidestar_url,
        "source_keyword": source_keyword,
        "segment": "Organization",
        "lead_status": "identified",
        "contact_name": "",
        "contact_linkedin": "",
        "email": "",
        "notes": "",
        "found_at": datetime.now().strftime("%Y-%m-%d"),
    }


def run(config: dict) -> list[dict]:
    """Run Israeli NGO registry search. Returns empty list if country != Israel."""
    if config.get("country", "") != "Israel":
        print("  Skipping gov_il engine (country is not Israel).")
        return []

    org_keywords = config.get("org_keywords", {})
    keywords = org_keywords.get("hebrew", []) + org_keywords.get("english", [])
    if not keywords:
        print("  No org_keywords configured.")
        return []

    all_records = []
    seen_numbers = set()

    for keyword in keywords:
        print(f"  Searching: '{keyword}'...")
        records = _fetch_by_keyword(keyword)
        added = 0
        for r in records:
            number = r.get("מספר עמותה", "")
            if number in seen_numbers or not _is_active(r):
                continue
            seen_numbers.add(number)
            all_records.append(_flatten(r, keyword))
            added += 1
        print(f"    -> {added} new orgs")

    return all_records
