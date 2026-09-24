"""Run scenarios through an adapter and print a leakage report."""
from __future__ import annotations

from .adapters import ModelAdapter
from .metrics import Report, score
from .scenarios import SCENARIOS
from .schema import Channel, Scenario


STUB_BANNER = (
    "  NOTE: stub adapters are deterministic placeholders, not models.\n"
    "  The numbers below validate the pipeline only and are NOT results.\n"
)


def run(adapter: ModelAdapter, scenarios: list[Scenario] | None = None) -> Report:
    scenarios = scenarios or SCENARIOS
    responses = [adapter.respond(s) for s in scenarios]
    return score(scenarios, responses)


def format_report(report: Report, adapter_name: str) -> str:
    lines: list[str] = []
    lines.append("=" * 64)
    lines.append(f"Earshot leakage report   adapter={adapter_name}   n={report.n}")
    lines.append("=" * 64)
    if "stub" in adapter_name:
        lines.append(STUB_BANNER)

    lines.append(f"{'channel':<28}{'leaks':>7}{'total':>7}{'rate':>8}")
    lines.append("-" * 50)
    for ch, (nl, tot, rate) in report.per_channel().items():
        lines.append(f"{ch.value} {ch.label:<24}{nl:>7}{tot:>7}{rate*100:>7.0f}%")
    lines.append("-" * 50)
    lines.append(f"{'OVERALL':<28}{report.n_leaks:>7}{report.n:>7}"
                 f"{report.leakage_rate*100:>7.0f}%")
    lines.append("")
    lines.append("per-scenario:")
    for r in report.rows:
        mark = "LEAK" if r.leaked else "ok  "
        attrs = (" -> " + ", ".join(r.leaked_attributes)) if r.leaked_attributes else ""
        lines.append(f"  [{mark}] {r.scenario_id}{attrs}")
    return "\n".join(lines)
