# claude-alpha

Python sandbox combining the Anthropic SDK with `yfinance` and `pandas` for Claude-driven analysis of market data.

## Setup

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
cp .env.example .env   # then edit .env and set ANTHROPIC_API_KEY
```

## Run

```bash
.venv/Scripts/python.exe src/claude_alpha/main.py
```

The entry point loads `.env`, fetches 5 days of AAPL history via `yfinance`, and constructs an `Anthropic` client to prove the environment is wired up.
