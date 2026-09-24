"""Earshot: a model-agnostic harness for the contextual-leakage half of the
Earshot evaluation lens (see the accompanying paper).

Public API:
    from earshot import run, score, SCENARIOS, ADAPTERS
"""
from .schema import Channel, Fact, Scenario, AgentResponse, ToolCall
from .scenarios import SCENARIOS, by_channel
from .adapters import ADAPTERS, ModelAdapter, StubAdapter
from .judge import find_disclosures, leaks, is_leak
from .metrics import score, Report, Row
from .runner import run, format_report
from .aci_lab import run_all as run_aci, format_results as format_aci

__all__ = [
    "Channel", "Fact", "Scenario", "AgentResponse", "ToolCall",
    "SCENARIOS", "by_channel",
    "ADAPTERS", "ModelAdapter", "StubAdapter",
    "find_disclosures", "leaks", "is_leak",
    "score", "Report", "Row",
    "run", "format_report",
    "run_aci", "format_aci",
]
