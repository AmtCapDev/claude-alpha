# ClaudeAlpha

Multi-agent stock analysis system, inspired by the AlphaAgents paper.

## Analyst roles

Three analyst roles, each with a script in [src/claude_alpha/agents/](src/claude_alpha/agents/) that pulls data using the helpers in [src/claude_alpha/data/](src/claude_alpha/data/), calls the Claude API, and produces a JSON recommendation in [output/](output/):

- **ValuationAnalyst** — [valuation_agent.py](src/claude_alpha/agents/valuation_agent.py)
- **SentimentAnalyst** — [sentiment_agent.py](src/claude_alpha/agents/sentiment_agent.py)
- **FundamentalAnalyst** — [fundamental_agent.py](src/claude_alpha/agents/fundamental_agent.py)

## JSON output schema

Every per-stock recommendation (and every item in a final file) must have these fields:

| Field | Type | Values |
|---|---|---|
| `agent` | string | `"ValuationAnalyst"` / `"SentimentAnalyst"` / `"FundamentalAnalyst"` |
| `ticker` | string | e.g. `"AAPL"` |
| `recommendation` | string | `"BUY"` or `"SELL"` |
| `confidence` | string | `"high"`, `"medium"`, or `"low"` |
| `reasoning` | string | 2–3 paragraph rationale |
| `key_factors` | list of strings | 3–5 short drivers |
| `risk_profile` | string | e.g. `"risk-neutral"`, `"risk-averse"`, `"risk-seeking"` |

Per-stock files: `output/{TICKER}_{agent}.json`. Final files: `output/{agent}_final.json`.

## Team workflow

When the three analysts work as a team, execution happens in two phases. **Do not exit between phases.**

### Messaging setup

Before any teammate tries to use `SendMessage`, they must first call `ToolSearch('SendMessage')` to load the tool into their context. This is required because `SendMessage` is a deferred tool — its schema is not loaded by default and calling it without loading first will fail with `InputValidationError`.

If `SendMessage` is not found via `ToolSearch`, fall back to writing results to output files and notifying the lead.

### Phase 1 — Gather

Each teammate:

1. Runs their agent script for every stock in the universe.
2. Saves per-stock JSONs to `output/{TICKER}_{agent}.json`.
3. Sends one `SendMessage` to each of the other two teammates containing all per-stock recommendations (ticker, recommendation, confidence, short rationale).
4. **Waits** after sending. Do not exit.

### Phase 2 — Debate

Once a teammate has received recommendations from **both** other teammates:

1. Compare calls across the three lenses.
2. For any disagreement, `SendMessage` the others explaining your reasoning.
3. Consider their arguments and revise your call if convinced.
4. Up to **3 rounds** of debate per disagreement.
5. Save final recommendations to `output/{agent}_final.json` using the schema above.
6. **Do NOT exit until Phase 2 is complete.**

## Environment

- `ANTHROPIC_API_KEY` is loaded from `.env` at the project root.
- Run Python scripts from the **project root** (paths inside the scripts assume this, e.g. `PROJECT_ROOT / "output"`).
