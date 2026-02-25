# Lead Search Toolkit

## Profile
- **Stack:** static-site
- **Git User:** hello@nomemoo.com

## What This Is
Config-driven lead search toolkit. Finds potential customers via Google dorks (DuckDuckGo), LinkedIn API, and Israeli government data. All search parameters come from `config.yaml`.

## Quick Start for Claude Code

When the user says "search for leads", "find leads", or "run lead search":

1. Check if `config.yaml` exists
   - If not: `cp config.yaml.example config.yaml` and ask the user to fill in product details
   - If `product.name` is still "Your Product": ask targeted questions to fill it in
2. Run: `lead-search` (or `python -m lead_search.cli` if not pip-installed)
3. Present results summary from terminal output
4. Ask: "Want to review the CSV, filter results, or try the LinkedIn API engine too?"

## Engines

| Engine | Command | Auth Required | Notes |
|--------|---------|---------------|-------|
| Google Dorks | `lead-search --engine google` | No | DuckDuckGo `site:linkedin.com/in` queries |
| LinkedIn API | `lead-search --engine linkedin` | Yes: `LINKEDIN_EMAIL` + `LINKEDIN_PASSWORD` env vars | Richer data, needs `pip install -e ".[linkedin]"` |
| Israeli NGOs | `lead-search --engine gov_il` | No | Only runs if `country: Israel` in config |

## Key Files

| File | Purpose |
|------|---------|
| `config.yaml` | All search parameters — product, segments, keywords |
| `config.yaml.example` | Template to copy from |
| `src/lead_search/cli.py` | CLI entry point |
| `src/lead_search/engines/` | One module per search engine |
| `output/` | CSV results land here (gitignored) |

## Config-Driven Architecture

Everything is in `config.yaml`:
- `product.*` — what you're selling
- `segments[]` — who you're looking for (titles in Hebrew + English, keywords)
- `org_keywords` — keywords for Israeli NGO registry
- `settings` — rate limits, output directory

To add a new segment: add an entry to `segments[]` in config.yaml. No code changes needed.

## Installation

```bash
pip install -e .                    # basic (google + gov_il engines)
pip install -e ".[linkedin]"        # include LinkedIn API support
```
