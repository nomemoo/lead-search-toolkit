"""YAML config loader and validation."""

import sys
from pathlib import Path

import yaml


# LinkedIn GeoURN mapping
GEO_URNS = {
    "Israel": "urn:li:geo:101620260",
    "United States": "urn:li:geo:103644278",
    "United Kingdom": "urn:li:geo:101165590",
}


def load_config(path: str = "config.yaml") -> dict:
    """Load and validate config.yaml, returning the parsed dict."""
    config_path = Path(path)
    if not config_path.exists():
        print(f"Config not found: {config_path}")
        example = config_path.parent / "config.yaml.example"
        if example.exists():
            print(f"Copy the example and fill it in:\n  cp {example} {config_path}")
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    _validate(config, path)
    return config


def _validate(config: dict, path: str):
    """Check required fields exist."""
    if not config.get("product", {}).get("name"):
        _bail("product.name is required", path)
    if config["product"]["name"] == "Your Product":
        _bail("product.name is still the placeholder — fill in your real product name", path)
    if not config.get("segments"):
        _bail("at least one segment is required", path)


def _bail(msg: str, path: str):
    print(f"Config error in {path}: {msg}")
    sys.exit(1)


def get_geo_urn(config: dict) -> str | None:
    """Return LinkedIn GeoURN for the configured country, or None."""
    return GEO_URNS.get(config.get("country", ""))
