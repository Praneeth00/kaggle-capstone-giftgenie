"""
Evaluation harness for GiftGenie (JSON pipeline).

Goal:
- Run the multi-agent pipeline for a few fixed test personas
  WITHOUT user input.
- Compute simple metrics:
    * Interest coverage (how many persona interests appear in reasons/titles)
    * Budget fit (roughly based on priceRange text)

This demonstrates "agent evaluation" for the Kaggle capstone.
"""

import re
from typing import Dict, Any, List

from main import (
    setup_gemini,
    setup_logging,
    run_pipeline,
)


# -----------------------------
# 1. TEST CASES
# -----------------------------
TEST_CASES = [
    {
        "name": "10-year-old nephew (Lego, budget 30)",
        "raw_info": {
            "recipient_name": "my 10-year-old nephew",
            "age": "10",
            "relationship": "nephew",
            "occasion": "birthday",
            "budget": "30",
            "interests": "lego, building toys, puzzles",
            "dislikes": "anything too fragile",
        },
    },
    {
        "name": "25-year-old sister (books + plants, budget 50)",
        "raw_info": {
            "recipient_name": "my sister",
            "age": "25",
            "relationship": "sister",
            "occasion": "graduation",
            "budget": "50",
            "interests": "books, plants, cozy home decor",
            "dislikes": "loud gadgets",
        },
    },
    {
        "name": "coworker gender-neutral (coffee, budget 20)",
        "raw_info": {
            "recipient_name": "a coworker",
            "age": "30s",
            "relationship": "coworker",
            "occasion": "thank you",
            "budget": "20",
            "interests": "coffee, notebooks, desk accessories",
            "dislikes": "",
        },
    },
]


# -----------------------------
# 2. HELPER FUNCTIONS FOR METRICS
# -----------------------------
def parse_budget(budget_str: str):
    """
    Parse a budget string (e.g. '50', '30-50') into a single numeric value.

    Very simple heuristic:
    - Extract all integers.
    - If a range is given, take the upper bound.
    """
    digits = re.findall(r"\d+", budget_str or "")
    if not digits:
        return None
    nums = [int(d) for d in digits]
    return nums[-1]


def evaluate_budget_fit(gifts: List[Dict[str, str]], budget_value: int):
    """
    Lightweight budget check using priceRange fields.
    """
    if budget_value is None:
        return "N/A (no numeric budget)"

    prices = []
    for g in gifts:
        pr = g.get("priceRange", "") or ""
        nums = re.findall(r"\d+", pr)
        prices.extend(int(n) for n in nums)

    if not prices:
        return "unknown (no numeric prices found)"

    max_price = max(prices)

    if max_price <= budget_value * 1.5:
        return f"good (max ~{max_price}, budget {budget_value})"
    elif max_price <= budget_value * 2.0:
        return f"stretch (max ~{max_price}, budget {budget_value})"
    else:
        return f"poor (max ~{max_price}, budget {budget_value})"


def evaluate_interest_coverage(
    gifts: List[Dict[str, str]], interests: List[str]
):
    """
    Simple coverage metric:
    - Count how many distinct interests appear in any title/reason.
    """
    if not interests:
        return 0, 0, 0.0

    text = " ".join(
        (g.get("title", "") + " " + g.get("reason", "")) for g in gifts
    ).lower()

    hits = 0
    for interest in interests:
        if interest.lower() in text:
            hits += 1

    total = len(interests)
    ratio = hits / total if total else 0.0
    return hits, total, ratio


# -----------------------------
# 3. EVALUATION PIPELINE
# -----------------------------
def run_test_case(model, test_case: Dict[str, Any]):
    """
    Run a full multi-agent pipeline for one test scenario
    using run_pipeline(...), then compute simple metrics.
    """
    name = test_case["name"]
    raw_info = test_case["raw_info"]

    print(f"\n==============================")
    print(f"SCENARIO: {name}")
    print(f"==============================")

    pipeline_result = run_pipeline(model, raw_info)
    persona = pipeline_result["persona_profile"]
    gifts = pipeline_result["final_gifts"]

    budget_value = parse_budget(persona.get("budget", ""))
    budget_fit = evaluate_budget_fit(gifts, budget_value)
    hits, total, ratio = evaluate_interest_coverage(
        gifts, persona.get("interests", [])
    )

    print("\n--- Preview of final gifts ---")
    for i, g in enumerate(gifts[:5], start=1):
        print(f"{i}. {g.get('title', 'Gift idea')} ({g.get('priceRange', '')})")
        if g.get("reason"):
            print(f"   {g['reason']}")
    print("\n--- Metrics ---")
    print(f"Budget fit: {budget_fit}")
    print(f"Interest coverage: {hits}/{total} interests mentioned (~{ratio:.0%})")

    return {
        "name": name,
        "budget_fit": budget_fit,
        "interest_hits": hits,
        "interest_total": total,
        "interest_ratio": ratio,
    }


def main():
    """
    Evaluation entry point for the capstone:
    - Shares the same JSON pipeline as the main app (no duplicated logic)
    - Provides simple quantitative metrics
    - Leverages logging for observability
    """
    setup_logging()
    print("🔎 Running GiftGenie evaluation on predefined scenarios...\n")

    model = setup_gemini()

    results = []
    for tc in TEST_CASES:
        result = run_test_case(model, tc)
        results.append(result)

    print("\n==============================")
    print("OVERALL EVALUATION SUMMARY")
    print("==============================")
    for r in results:
        print(
            f"- {r['name']}: "
            f"Budget fit = {r['budget_fit']}, "
            f"Interest coverage = {r['interest_hits']}/{r['interest_total']} "
            f"({r['interest_ratio']:.0%})"
        )

    print(
        "\nDone. Metrics above can be referenced in the Kaggle writeup under "
        "'Agent Evaluation' and 'Observability'."
    )
    print("Check logs/agent.log for detailed traces of each run.")


if __name__ == "__main__":
    main()
