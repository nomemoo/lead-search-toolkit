# Lead Search Toolkit

Config-driven lead search toolkit that finds potential customers across multiple data sources. Define your product, target segments, and keywords in a single YAML file — the toolkit generates search queries and collects leads into ready-to-use CSV files.

## Quick Start

```bash
git clone https://github.com/nomemoo/lead-search-toolkit.git
cd lead-search-toolkit
pip install -e .
cp config.yaml.example config.yaml   # Edit with your product + segments
lead-search                           # Runs google + gov_il engines
```

## Engines

| Engine | Auth Required | Risk Level | Data | Region |
|--------|:------------:|:----------:|------|--------|
| **Google Dorks** | None | None | LinkedIn profile URLs, names, titles | Global |
| **Gov IL** | None | None | NGO names, IDs, categories, addresses | Israel only |
| **LinkedIn API** | Yes | High (ToS) | Rich profiles, locations, headlines | Global |

By default, only **Google Dorks** and **Gov IL** run. The LinkedIn engine must be explicitly requested with `--engine linkedin` (see [LinkedIn Engine](#linkedin-engine) for safety guidance).

## Usage

```bash
# Run default engines (google + gov_il)
lead-search

# Use a different config file
lead-search --config my-product.yaml

# Run a specific engine
lead-search --engine google
lead-search --engine gov_il
lead-search --engine linkedin   # Requires credentials, see below
```

## Configuration Reference

All search parameters live in `config.yaml`. Copy `config.yaml.example` to get started.

### `product`

Your product details — used to contextualize search queries.

```yaml
product:
  name: "Moderatos"
  description: "AI-powered meeting moderator"
  url: "https://moderatos.com"
```

### `country`

Affects query language and LinkedIn geo-targeting. Supported: `"Israel"`, `"United States"`, `"United Kingdom"`.

```yaml
country: "Israel"
```

### `segments`

Each segment represents a target persona. The Google engine builds `site:linkedin.com/in` queries from `persona_titles`, while the LinkedIn engine searches using `keywords`.

```yaml
segments:
  - name: "HR Directors"
    persona_titles:
      hebrew: ["מנהל משאבי אנוש"]
      english: ["HR Director", "VP People"]
    keywords: ["HR", "people operations"]
```

Add as many segments as you need — no code changes required.

### `org_keywords`

Keywords for the Israeli NGO Registry engine (`gov_il`). Searches the official nonprofit registry at data.gov.il.

```yaml
org_keywords:
  hebrew:
    - "ייעוץ ארגוני"
    - "קואצ'ינג"
  english:
    - "coaching"
```

### `settings`

```yaml
settings:
  max_results_per_query: 20    # Results per search query
  sleep_between_queries: 2     # Seconds between queries (rate limiting)
  output_dir: "output"         # Where CSV files are saved
```

### `linkedin`

LinkedIn-specific settings (only used with `--engine linkedin`).

```yaml
linkedin:
  max_per_session: 50          # Stop after N results to reduce ban risk
  sleep_base: 3                # Base seconds between API calls
  sleep_jitter: 2              # Random 0-N extra seconds added for jitter
  network_depths: ["S", "O"]   # F=1st, S=2nd, O=3rd+ degree connections
```

## LinkedIn Engine

> **This engine uses an unofficial API that violates LinkedIn's Terms of Service. Understand the risks before using it.**

### Risks

- LinkedIn uses **ML-based behavioral analysis** to detect automation. Non-browser fingerprints are flagged.
- Accounts can be **restricted or permanently banned**. LinkedIn may request government ID verification.
- **Datacenter IPs** (cloud VMs, VPNs) are flagged aggressively — use a residential IP.
- The underlying `linkedin-api` library has **write capabilities** (messages, connection requests). Our code only uses `search_people()` (read), but the library itself can modify your account.

### Safety Recommendations

- **Use a dedicated account** — never your primary professional LinkedIn profile
- Stay under **~50 profile views/day** and **~300 searches/month** on free accounts
- Use **cookie auth** instead of email/password (avoids triggering login-flow detection)
- Keep the default `sleep_jitter` to randomize request timing
- Run during business hours to blend with normal usage patterns

### Authentication

**Option 1 — Cookie auth (recommended):**

Extract cookies from your browser after logging into LinkedIn:

```bash
export LINKEDIN_LI_AT="your_li_at_cookie_value"
export LINKEDIN_JSESSIONID="your_jsessionid_cookie_value"
lead-search --engine linkedin
```

To find these cookies: open LinkedIn in your browser → DevTools → Application → Cookies → `linkedin.com` → copy `li_at` and `JSESSIONID` values.

**Option 2 — Email/password:**

```bash
export LINKEDIN_EMAIL="you@example.com"
export LINKEDIN_PASSWORD="your-password"
lead-search --engine linkedin
```

### Installation

The LinkedIn engine requires an extra dependency:

```bash
pip install -e ".[linkedin]"
```

## Output

Results are saved to the `output/` directory (configurable via `settings.output_dir`):

| File | Contents | Source Engines |
|------|----------|----------------|
| `leads_combined.csv` | Person leads (name, LinkedIn URL, title, location, segment) | Google, LinkedIn |
| `leads_orgs.csv` | Organization leads (name, ID, category, address, goal) | Gov IL |

Leads are automatically deduplicated by LinkedIn URL.

## Adding Your Own Engine

Create a new file in `src/lead_search/engines/` that exports a `run(config: dict) -> list[dict]` function. Each dict should include at minimum: `name`, `segment`, `engine`, and `found_at`. Then register it in `cli.py`'s `ENGINE_MAP`.

## Using with Claude Code

This project includes a `CLAUDE.md` for AI-assisted development with [Claude Code](https://claude.ai/code).

Instead of editing YAML files manually, you can set up your entire config conversationally. Clone the repo, open it in Claude Code, and paste this prompt:

<details>
<summary><strong>Copy this setup prompt</strong></summary>

```
I just cloned lead-search-toolkit. Help me set up my config.yaml by asking me about:
1. What product/service am I searching leads for? (name, one-line description, URL)
2. What country am I targeting?
3. Who are my target personas? (ask me for 2-3 audience segments with job titles in relevant languages)
4. Do I want to search the Israeli NGO registry? If so, what keywords?

After collecting my answers, generate a complete config.yaml and save it. Then run `lead-search` and show me the results.
```

</details>

Claude Code will ask you the right questions, generate your config, and run the search — no YAML editing needed.

## Author

Built by [Sergei Benkovitch](https://nomemoo.com).

## License

[MIT](LICENSE)
