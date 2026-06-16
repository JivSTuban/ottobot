"""
CI threshold checker for promptfoo eval results.

Usage:
    python evals/check_thresholds.py --results evals/results/latest.json
    python evals/check_thresholds.py --results evals/results/latest.json --min-pass-rate 0.85

Exit codes:
    0 — all critical dimensions meet or exceed the threshold
    1 — one or more critical dimensions below threshold
"""

import argparse
import json
import sys


CRITICAL_DIMENSIONS = [
    "taglish_register",
    "ai_disclosure",
    "price_accuracy",
    "objection_handling",
    "escalation_trigger",
]


def load_results(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def compute_pass_rate(results: dict, dimension: str) -> float | None:
    """Extract pass rate for a given dimension from promptfoo results JSON.

    Returns None when no tests match the dimension — caller must treat as FAIL
    to prevent a missing dimension from silently reporting 100% pass (WR-03).
    """
    # promptfoo results format: results.results[] with description and pass fields
    tests = results.get("results", [])
    dimension_tests = [t for t in tests if dimension in t.get("description", "").lower().replace(" ", "_")]
    if not dimension_tests:
        return None  # signal: no tests found for this dimension
    passed = sum(1 for t in dimension_tests if t.get("success", False))
    return passed / len(dimension_tests)


def main():
    parser = argparse.ArgumentParser(
        description="Check promptfoo eval results against pass-rate thresholds.",
    )
    parser.add_argument(
        "--results",
        required=True,
        metavar="PATH",
        help="Path to promptfoo results JSON file (e.g. evals/results/latest.json)",
    )
    parser.add_argument(
        "--min-pass-rate",
        type=float,
        default=0.90,
        metavar="FLOAT",
        help="Minimum pass rate (0.0-1.0) for all critical dimensions (default: 0.90)",
    )
    args = parser.parse_args()

    try:
        results = load_results(args.results)
    except FileNotFoundError:
        print(f"ERROR: Results file not found: {args.results}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in results file: {e}", file=sys.stderr)
        sys.exit(1)

    failed_dimensions = []
    print(f"\nPass Rate Summary (threshold: {args.min_pass_rate:.0%})")
    print("-" * 50)

    for dim in CRITICAL_DIMENSIONS:
        rate = compute_pass_rate(results, dim)
        if rate is None:
            # No tests matched — treat as FAIL to prevent silent 100% pass (WR-03)
            print(f"  {dim:<30} NO TESTS  [FAIL]")
            failed_dimensions.append(dim)
            continue
        status = "PASS" if rate >= args.min_pass_rate else "FAIL"
        print(f"  {dim:<30} {rate:.0%}  [{status}]")
        if rate < args.min_pass_rate:
            failed_dimensions.append(dim)

    print("-" * 50)

    if failed_dimensions:
        print(f"\nFAILED: {len(failed_dimensions)} dimension(s) below {args.min_pass_rate:.0%} threshold:")
        for dim in failed_dimensions:
            print(f"  - {dim}")
        sys.exit(1)
    else:
        print(f"\nAll {len(CRITICAL_DIMENSIONS)} dimensions meet the {args.min_pass_rate:.0%} threshold.")
        sys.exit(0)


if __name__ == "__main__":
    main()
