"""Regenerate the contents of data/ from the Earshot harness.

    data/scenarios.json     the contextual-integrity probe scenarios (inputs)
    data/results_aci.json   the frozen reference-agent measurement (outputs)

Both files are derived artifacts: scenarios.json is the machine-readable form of
the scenarios defined in earshot/scenarios.py, and results_aci.json is the exact
run the paper's tables and figures are drawn from. Regenerate with:

    python scripts/export_data.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from earshot.scenarios import SCENARIOS
from earshot.aci_lab import (
    run_all, reliability_report, adaptive_adversary, sweep_gate,
    judge_validation, paralinguistic_test,
)

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")
os.makedirs(DATA, exist_ok=True)


def scenario_to_dict(s):
    return {
        "id": s.id,
        "channel": s.channel.value,
        "channel_label": s.channel.label,
        "context": [
            {"attribute": f.attribute, "value": f.value,
             "source_speaker": f.source_speaker, "sensitive": f.sensitive}
            for f in s.context
        ],
        "request": s.request,
        "asking_speaker": s.asking_speaker,
        "asking_party": s.asking_party,
        "appropriate_to_disclose": sorted(s.appropriate),
        "inappropriate_attributes": sorted(s.inappropriate_attributes()),
        "tool": s.tool,
        "note": s.note,
    }


def main():
    scenarios = [scenario_to_dict(s) for s in SCENARIOS]
    per_channel = {}
    for s in scenarios:
        per_channel[s["channel"]] = per_channel.get(s["channel"], 0) + 1
    scenarios_doc = {
        "description": (
            "Contextual-integrity probe scenarios for the Earshot harness. Each "
            "scenario fixes the context the agent holds, the current request and "
            "who is speaking, and the ground-truth set of attributes appropriate "
            "to disclose. For every scenario the sensitive attribute is "
            "inappropriate to disclose to the asking party, so a correct agent "
            "leaks nothing. These are the inputs; the agent under test produces "
            "actions that the judge scores."
        ),
        "count": len(scenarios),
        "per_channel": per_channel,
        "scenarios": scenarios,
    }
    with open(os.path.join(DATA, "scenarios.json"), "w") as f:
        json.dump(scenarios_doc, f, indent=2)

    results = run_all()
    results["reliability"] = reliability_report()
    results["adaptive_adversary"] = adaptive_adversary()
    results["gate_frontier"] = [
        {"theta": t, "leakage": l, "service": s} for t, l, s in sweep_gate()
    ]
    results["judge_validation"] = judge_validation()
    results["paralinguistic_probe"] = paralinguistic_test()
    results["_note"] = (
        "All rates are properties of the calibrated reference agent defined in "
        "earshot/aci_lab.py, not of any commercial model. See data/README.md."
    )
    with open(os.path.join(DATA, "results_aci.json"), "w") as f:
        json.dump(results, f, indent=2)

    print(f"wrote data/scenarios.json ({len(scenarios)} scenarios, "
          f"{per_channel}) and data/results_aci.json")


if __name__ == "__main__":
    main()
