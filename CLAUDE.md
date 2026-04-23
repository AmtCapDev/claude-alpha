# ClaudeAlpha

Multi-agent stock analysis system.

## Agent roles

Three specialist agents, each with a script in [src/claude_alpha/agents/](src/claude_alpha/agents/):

- **Valuation analyst** — [valuation_agent.py](src/claude_alpha/agents/valuation_agent.py). Analyzes historical price/volume, annualized return and volatility.
- **Sentiment analyst** — [sentiment_agent.py](src/claude_alpha/agents/sentiment_agent.py). Analyzes recent news and market sentiment.
- **Fundamental analyst** — [fundamental_agent.py](src/claude_alpha/agents/fundamental_agent.py). Analyzes financial statements, margins, growth, balance sheet.

Each script takes a ticker as its first argument and produces a JSON recommendation with these fields:

- `recommendation` — `"BUY"` or `"SELL"`
- `confidence` — `"high"`, `"medium"`, or `"low"`
- `reasoning` — string (2–3 paragraphs)
- `key_factors` — list of short strings naming the drivers

## Data and output

- Data helpers live in [src/claude_alpha/data/](src/claude_alpha/data/).
- All agent output is written to [output/](output/) as `<TICKER>_<role>.json`.

## Running as a team

When agents work together:

1. Each agent runs its own script to produce its JSON recommendation.
2. Agents share findings with teammates by name using `SendMessage`.
3. If recommendations disagree, agents debate until they reach consensus.

## Environment

`ANTHROPIC_API_KEY` is loaded from `.env` at the project root.
