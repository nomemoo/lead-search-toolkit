"""Data models for lead search results."""

from dataclasses import dataclass, field


class ConfigError(Exception):
    """Raised when config validation fails."""
    pass


@dataclass
class SearchResult:
    """Result from a programmatic search run."""

    person_leads: list[dict] = field(default_factory=list)
    org_leads: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
