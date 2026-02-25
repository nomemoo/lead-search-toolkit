"""CLI entry point for lead-search command."""

import argparse
from collections import Counter
from pathlib import Path

from lead_search.config import load_config
from lead_search.output import deduplicate_leads, save_csv, PERSON_FIELDS, ORG_FIELDS
from lead_search.engines import google_dorks, linkedin_api, gov_il_orgs


ENGINE_MAP = {
    "google": google_dorks,
    "linkedin": linkedin_api,
    "gov_il": gov_il_orgs,
}


def main():
    parser = argparse.ArgumentParser(
        prog="lead-search",
        description="Config-driven lead search across multiple engines",
    )
    parser.add_argument(
        "--config", default="config.yaml",
        help="Path to config YAML (default: ./config.yaml)",
    )
    parser.add_argument(
        "--engine", choices=list(ENGINE_MAP.keys()),
        help="Run only a specific engine (default: all applicable)",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    output_dir = config.get("settings", {}).get("output_dir", "output")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    product = config["product"]["name"]
    print(f"Lead Search Toolkit — {product}")
    print("=" * 60)

    engines_to_run = [args.engine] if args.engine else ["google", "gov_il"]

    person_leads = []
    org_leads = []

    for engine_name in engines_to_run:
        engine = ENGINE_MAP[engine_name]
        print(f"\n--- Engine: {engine_name} ---")
        results = engine.run(config)

        if engine_name == "gov_il":
            org_leads.extend(results)
        else:
            person_leads.extend(results)

    # Save person leads (google + linkedin)
    if person_leads:
        person_leads = deduplicate_leads(person_leads, key="linkedin_url")
        combined_path = f"{output_dir}/leads_combined.csv"
        save_csv(person_leads, combined_path, PERSON_FIELDS)

        print(f"\nPerson leads by segment:")
        for seg, n in Counter(l["segment"] for l in person_leads).most_common():
            print(f"  {seg}: {n}")

    # Save org leads separately
    if org_leads:
        org_path = f"{output_dir}/leads_orgs.csv"
        save_csv(org_leads, org_path, ORG_FIELDS)

        print(f"\nOrg leads by category:")
        for cat, n in Counter(r["category"] for r in org_leads).most_common(10):
            print(f"  {cat or '(uncategorized)'}: {n}")

    if not person_leads and not org_leads:
        print("\nNo leads found across any engine.")
    else:
        total = len(person_leads) + len(org_leads)
        print(f"\nTotal: {total} leads ({len(person_leads)} people, {len(org_leads)} orgs)")


if __name__ == "__main__":
    main()
