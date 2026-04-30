"""Build output/valuation_final.json from the Phase 1 summary, applying
the confidence revisions agreed in Phase 2 debate."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"

REVISIONS = {
    "AAPL":  {"confidence": "high",   "note": "Revised medium->high after debate. Fundamental case (31.97% op margin, $98.8B FCF, FCF~=NI) and Sentiment medium (CEO succession, AI re-rating, lagging Mag7) blend with constructive tape (recovery from $246 low, accumulation volume) to support higher conviction."},
    "MSFT":  {"confidence": "high",   "note": "Revised medium->high after debate. Fundamental case (14.93% rev growth, 45.62% op margin, D/E 0.18, $71.6B FCF) is elite, and the April 30 -5% flush appears to be a sentiment shock against intact franchise quality. Mean-reversion setup is strong."},
    "GOOGL": {"confidence": "high",   "note": "Revised medium->high after debate. Sentiment-high (Q1 beat, TPU external sales) and Fundamental-high (15% growth, 32% op margin, D/E 0.14, $73.3B FCF) outweigh near-term overextension after 40% rally; momentum + breakout volume confirm trend."},
    "META":  {"confidence": "medium", "note": "Held medium. Fundamentals strong (22.17% growth, 41.4% op margin, $46.1B FCF), Sentiment medium, but fresh April 30 -8.7% post-earnings flush on 2.4x volume is a real near-term overhang; mean-reversion setup attractive but not yet confirmed."},
    "NVDA":  {"confidence": "high",   "note": "Revised medium->high after debate. Fundamental-high (65% growth, 60% op margin, D/E 0.07, $96.7B FCF) and Sentiment-medium (hyperscaler capex tailwind, $9T narrative) align with a confirmed uptrend and breakout above $190-198."},
    "AMD":   {"confidence": "medium", "note": "Held medium. Fundamental (34% growth, $6.74B FCF) and Sentiment-high (hyperscaler AI capex tailwind, Nvidia-alternative thesis) are bullish, but the 402% trailing return / near-doubling in six weeks is technically extended; risk-neutral expected return positive but entry timing risk material."},
    "CRM":   {"confidence": "medium", "note": "Revised low->medium after debate. Fundamental case (9.58% growth, 21.5% op margin, $14.4B FCF / ~35% margin, D/E 0.29) plus Sentiment-medium (Slack/MSFT ruling, Benioff hiring 1,000) materially offset the technical damage. Tape remains bearish but basing above April $164 low is constructive enough for medium."},
    "ORCL":  {"confidence": "medium", "note": "Held medium. Three-way medium consensus. Fundamental flagged D/E 5.09 and FCF -$394M from cloud capex, validating the same balance-sheet caution that tempered my technical view."},
    "ADBE":  {"confidence": "medium", "note": "Held medium. Fundamental-high ($9.85B FCF > NI, 36.6% op margin) is genuinely strong, but the chart remains in a confirmed downtrend without a definitive reversal. Sentiment-medium (AI disruption overhang persists). Will revisit if support at $234-238 breaks decisively or stock reclaims $260."},
    "ZS":    {"confidence": "medium", "note": "Revised low->medium after Round 2 debate. Fundamental made a persuasive cash-quality case: the GAAP loss is overwhelmingly non-cash stock-based comp, while $727M FCF (27% margin) on 23% growth is durable and well-covers D/E 1.00. Sentiment-medium aligns. Tape remains broken but capitulation basing near $130 plus durable cash conversion now supports medium rather than low."},
    "CRWD":  {"confidence": "high",   "note": "Revised medium->high after debate. Fundamental-high (21.71% growth, $1.24B FCF / 26% margin) and Sentiment-high (Mizuho upgrade $520 PT, AI cybersec leadership) reinforce the higher-lows uptrend off Feb capitulation; consolidation near $467 high is continuation pattern."},
    "CSCO":  {"confidence": "high",   "note": "Revised medium->high after debate. Fundamental-high (5.3% growth, 22% op margin, $13.3B FCF > NI) and Sentiment-medium (Splunk/Qmulos deal, Nokia read-through) align with a strong uptrend, breakout above $89-90, and Sharpe-like ratio of 2.35."},
}


def main() -> None:
    phase1 = json.loads((OUTPUT_DIR / "_valuation_phase1_summary.json").read_text())

    finals = []
    for record in phase1:
        ticker = record["ticker"]
        rev = REVISIONS[ticker]
        new_conf = rev["confidence"]
        old_conf = record["confidence"]

        debate_paragraph = "\n\nPhase 2 debate update: " + rev["note"]
        new_reasoning = record["reasoning"] + debate_paragraph

        final = {
            "agent": "ValuationAnalyst",
            "ticker": ticker,
            "recommendation": "BUY",  # unchanged after debate
            "confidence": new_conf,
            "reasoning": new_reasoning,
            "key_factors": record["key_factors"],
            "risk_profile": "risk-neutral",
        }
        finals.append(final)
        print(f"{ticker}: {old_conf} -> {new_conf}")

        # Also overwrite the per-stock file with the final record
        per_stock = OUTPUT_DIR / f"{ticker}_ValuationAnalyst.json"
        per_stock.write_text(json.dumps(final, indent=2))

    final_path = OUTPUT_DIR / "valuation_final.json"
    final_path.write_text(json.dumps(finals, indent=2))
    print(f"\nSaved: {final_path}")


if __name__ == "__main__":
    main()
