"""CLI entry point for lead-search command."""

import argparse
import sys

from lead_search.api import search
from lead_search.models import ConfigError


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
        "--engine", choices=["google", "linkedin", "gov_il"],
        help="Run only a specific engine (default: all applicable)",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Don't save results to CSV",
    )
    args = parser.parse_args()

    engines = [args.engine] if args.engine else None

    try:
        result = search(config=args.config, engines=engines, save=not args.no_save)
    except ConfigError as e:
        print(str(e))
        sys.exit(1)

    product = result.stats.get("product", "unknown")
    print(f"Lead Search Toolkit — {product}")
    print("=" * 60)

    if result.person_leads:
        print(f"\nPerson leads by segment:")
        for seg, n in (result.stats.get("persons_by_segment") or {}).items():
            print(f"  {seg}: {n}")

    if result.org_leads:
        print(f"\nOrg leads: {len(result.org_leads)}")

    if result.errors:
        print(f"\nWarnings:")
        for err in result.errors:
            print(f"  ⚠ {err}")

    if not result.person_leads and not result.org_leads:
        print("\nNo leads found across any engine.")
    else:
        total = result.stats["total_persons"] + result.stats["total_orgs"]
        print(f"\nTotal: {total} leads ({result.stats['total_persons']} people, {result.stats['total_orgs']} orgs)")


if __name__ == "__main__":
    main()
