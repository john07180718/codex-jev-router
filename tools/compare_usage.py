"""Compare imported, matched A/B runs; never estimate missing Codex usage."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from typing import Any

COUNTS = ("codex_input_tokens", "codex_output_tokens", "codex_cached_input_tokens", "jev_input_tokens", "jev_attempts")

def compare(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("runs"), list):
        raise ValueError("Expected runs array")
    groups: dict[str, dict[str, Any]] = {}
    incomplete = 0
    for row in data["runs"]:
        if not isinstance(row, dict) or row.get("arm") not in ("baseline", "jev") or not isinstance(row.get("pair_id"), str):
            raise ValueError("Invalid run metadata")
        pair = groups.setdefault(row["pair_id"], {})
        if row["arm"] in pair:
            raise ValueError("Duplicate arm for pair")
        pair[row["arm"]] = row
    accepted = []
    mismatches = 0
    for pair in groups.values():
        if set(pair) != {"baseline", "jev"}:
            incomplete += 1; continue
        left, right = pair["baseline"], pair["jev"]
        if any(not isinstance(left.get(k), str) or not left[k] or left.get(k) != right.get(k)
               for k in ("task_ref", "codex_model", "reasoning_effort", "starting_commit")):
            mismatches += 1; continue
        if any(type(r.get(k)) is not int or r[k] < 0 for r in (left, right) for k in COUNTS):
            incomplete += 1; continue
        if any(r["codex_cached_input_tokens"] > r["codex_input_tokens"] for r in (left, right)):
            raise ValueError("Cached input cannot exceed total input")
        if any(type(r.get("quality_pass")) is not bool or type(r.get("elapsed_seconds")) not in (int, float)
               or not math.isfinite(r["elapsed_seconds"]) or r["elapsed_seconds"] < 0 for r in (left, right)):
            incomplete += 1; continue
        if left["jev_attempts"] or left["jev_input_tokens"]:
            raise ValueError("Baseline is not JEV-free")
        accepted.append((left, right))
    totals = {arm: {**{k: 0 for k in COUNTS}, "elapsed_seconds": 0.0, "quality_passes": 0} for arm in ("baseline", "jev")}
    for left, right in accepted:
        for arm, row in (("baseline", left), ("jev", right)):
            for key in COUNTS:
                totals[arm][key] += row[key]
            totals[arm]["elapsed_seconds"] += row["elapsed_seconds"]
            totals[arm]["quality_passes"] += int(row["quality_pass"])
    base = totals["baseline"]["codex_input_tokens"] + totals["baseline"]["codex_output_tokens"]
    new = totals["jev"]["codex_input_tokens"] + totals["jev"]["codex_output_tokens"]
    return {
        "matched_pairs": len(accepted), "incomplete_pairs": incomplete, "configuration_mismatch_pairs": mismatches,
        "totals": totals, "observed_codex_token_reduction_fraction": ((base - new) / base) if base else None,
        "both_arms_passed_all_checks": bool(accepted) and all(a["quality_pass"] and b["quality_pass"] for a, b in accepted),
        "codex_subscription_quota_savings": None, "dollar_savings": None,
        "note": "Imported observations, not automatic Codex metering. Cached tokens are a subset of input and not added twice. Includes failed-quality runs; no statistical significance or general savings claim."
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        if args.input.stat().st_size > 2000000:
            raise ValueError("Input too large")
        report = compare(json.loads(args.input.read_text(encoding="utf-8-sig")))
        print(json.dumps(report, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError):
        print(json.dumps({"status": "ERROR", "reason": "invalid_benchmark_input"}))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
