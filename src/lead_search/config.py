"""YAML config loader and validation."""

import sys
from pathlib import Path

import yaml

from lead_search.models import ConfigError


# LinkedIn GeoURN mapping
GEO_URNS = {
    "Israel": "urn:li:geo:101620260",
    "United States": "urn:li:geo:103644278",
    "United Kingdom": "urn:li:geo:101165590",
}


def load_config(path: str = "config.yaml") -> dict:
    """Load and validate config.yaml, returning the parsed dict.

    Raises ConfigError on validation failures (for programmatic use).
    """
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _validate(config, path)
    return config


def _validate(config: dict, path: str):
    """Check required fields exist."""
    if not config.get("product", {}).get("name"):
        raise ConfigError(f"Config error in {path}: product.name is required")
    if config["product"]["name"] == "Your Product":
        raise ConfigError(f"Config error in {path}: product.name is still the placeholder — fill in your real product name")
    if not config.get("segments"):
        raise ConfigError(f"Config error in {path}: at least one segment is required")


def get_geo_urn(config: dict) -> str | None:
    """Return LinkedIn GeoURN for the configured country, or None."""
    return GEO_URNS.get(config.get("country", ""))
