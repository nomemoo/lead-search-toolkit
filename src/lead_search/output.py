"""CSV writer with deduplication and merge support."""

import csv
from pathlib import Path


# Shared fields across all lead types
PERSON_FIELDS = [
    "name", "linkedin_url", "handle", "title", "snippet", "location",
    "source_query", "segment", "engine", "status", "contacted",
    "response", "email", "notes", "found_at",
]

ORG_FIELDS = [
    "name_hebrew", "name_english", "org_number", "category", "city",
    "status", "guidestar_url", "source_keyword", "segment",
    "lead_status", "contact_name", "contact_linkedin",
    "email", "notes", "found_at",
]


def deduplicate_leads(leads: list[dict], key: str = "linkedin_url") -> list[dict]:
    """Remove duplicate leads by a key field."""
    seen = set()
    unique = []
    for lead in leads:
        val = lead.get(key, "")
        if not val or val in seen:
            continue
        seen.add(val)
        unique.append(lead)
    return unique


def save_csv(leads: list[dict], filepath: str, fieldnames: list[str] | None = None):
    """Write leads to CSV. Auto-detects fields if not provided."""
    if not leads:
        print("No leads to save.")
        return

    if fieldnames is None:
        fieldnames = list(leads[0].keys())

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)

    print(f"Saved {len(leads)} records to {filepath}")
