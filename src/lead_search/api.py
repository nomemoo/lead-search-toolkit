"""Programmatic API for lead search.

Usage:
    from lead_search.api import search
    from lead_search.models import ConfigError, SearchResult

    result = search(config="config.yaml", save=False)
    print(result.person_leads)
    print(result.org_leads)
    print(result.stats)
"""

import logging
from collections import Counter
from pathlib import Path

from lead_search.config import load_config
from lead_search.engines import google_dorks, linkedin_api, gov_il_orgs
from lead_search.models import SearchResult
from lead_search.output import deduplicate_leads, save_csv, PERSON_FIELDS, ORG_FIELDS

logger = logging.getLogger(__name__)

ENGINE_MAP = {
    "google": google_dorks,
    "linkedin": linkedin_api,
    "gov_il": gov_il_orgs,
}


def search(
    config: str = "config.yaml",
    engines: list[str] | None = None,
    save: bool = True,
) -> SearchResult:
    """Run lead search programmatically.

    Args:
        config: Path to config YAML file.
        engines: List of engine names to run (default: ["google", "gov_il"]).
        save: Whether to save results to CSV files.

    Returns:
        SearchResult with person_leads, org_leads, stats, and errors.

    Raises:
        ConfigError: If config file is missing or invalid.
    """
    cfg = load_config(config)
    output_dir = cfg.get("settings", {}).get("output_dir", "output")
    product = cfg["product"]["name"]

    engines_to_run = engines or ["google", "gov_il"]

    person_leads: list[dict] = []
    org_leads: list[dict] = []
    errors: list[str] = []

    for engine_name in engines_to_run:
        if engine_name not in ENGINE_MAP:
            errors.append(f"Unknown engine: {engine_name}")
            continue

        engine = ENGINE_MAP[engine_name]
        logger.info("Running engine: %s", engine_name)
        try:
            results = engine.run(cfg)
            if engine_name == "gov_il":
                org_leads.extend(results)
            else:
                person_leads.extend(results)
        except Exception as e:
            logger.warning("Engine %s failed: %s", engine_name, e)
            errors.append(f"Engine {engine_name}: {e}")

    # Deduplicate
    if person_leads:
        person_leads = deduplicate_leads(person_leads, key="linkedin_url")

    # Save if requested
    if save and (person_leads or org_leads):
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        if person_leads:
            save_csv(person_leads, f"{output_dir}/leads_combined.csv", PERSON_FIELDS)
        if org_leads:
            save_csv(org_leads, f"{output_dir}/leads_orgs.csv", ORG_FIELDS)

    # Build stats
    stats = {
        "product": product,
        "total_persons": len(person_leads),
        "total_orgs": len(org_leads),
        "engines_run": engines_to_run,
    }
    if person_leads:
        stats["persons_by_segment"] = dict(
            Counter(l.get("segment", "") for l in person_leads).most_common()
        )

    return SearchResult(
        person_leads=person_leads,
        org_leads=org_leads,
        stats=stats,
        errors=errors,
    )
