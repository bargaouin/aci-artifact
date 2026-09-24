"""Earshot scenario schema.

A scenario encodes one contextual-integrity probe for a voice agent. The agent
holds some context (facts, each attached to a source speaker) and receives a
request from some party. Ground truth marks which attributes are appropriate to
disclose to that party in that context. The judge later checks the agent's
response against this ground truth to compute a leakage rate.

The four channels mirror the threat model in the paper:

    C1  paralinguistic self-inference   (agent acts on emotion/health it read from audio)
    C2  autonomous disclosure           (agent volunteers data nobody asked for)
    C3  cross-speaker memory bleed       (speaker A's data surfaces to speaker B)
    C4  tool-call exfiltration          (sensitive data leaves inside a tool call)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Channel(str, Enum):
    C1 = "C1"  # paralinguistic self-inference
    C2 = "C2"  # autonomous disclosure
    C3 = "C3"  # cross-speaker memory bleed
    C4 = "C4"  # tool-call exfiltration

    @property
    def label(self) -> str:
        return {
            "C1": "paralinguistic self-inference",
            "C2": "autonomous disclosure",
            "C3": "cross-speaker memory bleed",
            "C4": "tool-call exfiltration",
        }[self.value]


@dataclass(frozen=True)
class Fact:
    """A single piece of context the agent knows."""
    attribute: str          # short key, e.g. "medication"
    value: str              # the sensitive string, e.g. "Zoloft"
    source_speaker: str     # who told the agent, e.g. "teen", "owner"
    sensitive: bool = True  # whether this is private by default


@dataclass(frozen=True)
class Scenario:
    id: str
    channel: Channel
    context: tuple[Fact, ...]          # what the agent knows going in
    request: str                       # the current spoken request
    asking_speaker: str                # who is speaking now
    asking_party: str                  # who ultimately receives the output
    # ground truth: attribute keys that ARE appropriate to disclose here
    appropriate: frozenset[str] = field(default_factory=frozenset)
    # for C4, the request implies a tool call; this names the tool
    tool: Optional[str] = None
    note: str = ""                     # human-readable rationale

    def sensitive_facts(self) -> tuple[Fact, ...]:
        return tuple(f for f in self.context if f.sensitive)

    def inappropriate_attributes(self) -> frozenset[str]:
        """Attributes that would be a leak if disclosed to the asking party."""
        return frozenset(
            f.attribute for f in self.sensitive_facts()
            if f.attribute not in self.appropriate
        )


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class AgentResponse:
    """What a model returns for a scenario. `text` is the spoken reply;
    `tool_calls` are any structured actions (relevant for C4)."""
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)

    def all_emitted_text(self) -> str:
        parts = [self.text]
        for tc in self.tool_calls:
            parts.append(tc.name)
            for k, v in tc.arguments.items():
                parts.append(f"{k}={v}")
        return " \n ".join(str(p) for p in parts)
