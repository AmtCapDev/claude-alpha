import argparse
import json
import os
import re
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_ROOT / "output"

MODEL = "claude-opus-4-7"
MAX_TOKENS = 1500


def extract_json(text: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        return json.loads(brace.group(0))

    raise ValueError(f"Could not find JSON object in response:\n{text}")


def call_claude(system_prompt: str, user_prompt: str) -> dict:
    client = Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw_text = "".join(block.text for block in response.content if block.type == "text")
    return extract_json(raw_text)


def build_user_prompt(risk_profile: str, formatted_data: str, data_intro: str) -> str:
    return (
        f"Risk profile: {risk_profile}\n\n"
        f"{formatted_data}\n\n"
        f"{data_intro}, respond with ONLY a JSON object (no prose, no code "
        "fences) with exactly these fields:\n"
        '  - "recommendation": either "BUY" or "SELL"\n'
        '  - "confidence": one of "high", "medium", "low"\n'
        '  - "reasoning": 2-3 paragraph string explaining your analysis\n'
        '  - "key_factors": list of 3-5 short strings naming the drivers'
    )


def print_recommendation(label: str, ticker: str, result: dict) -> None:
    print(f"\n=== {label}: {ticker} ===")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Confidence:     {result['confidence']}")
    print("\nKey Factors:")
    for factor in result.get("key_factors", []):
        print(f"  - {factor}")
    print("\nReasoning:")
    print(result["reasoning"])


def build_arg_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("ticker", help="Stock ticker symbol, e.g. AAPL")
    parser.add_argument(
        "--risk-profile",
        default="risk-neutral",
        help="Risk profile to include in the prompt (default: risk-neutral)",
    )
    return parser


def load_env_or_exit() -> None:
    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in."
        )


def save_recommendation(ticker: str, role_suffix: str, result: dict) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{ticker}_{role_suffix}.json"
    output_path.write_text(json.dumps(result, indent=2))
    return output_path
