"""
Heuristic guard — the default backend when no trained DeBERTa checkpoint
is configured. Deliberately simple and explainable (pattern matching on
the same instruction-override / jailbreak / tool-confusion / URI-spoofing
/ chained-trigger language the mcp-ipi-guard data-pipeline's hand-crafted
attacks use) so the whole system is runnable and demo-able on day one.

This is NOT a substitute for the trained model and should not be reported
as your dissertation's guard classifier — it exists purely so this API is
useful before training finishes, and as a baseline your real DeBERTa guard
should clearly outperform in your results chapter.
"""
import re

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("instruction_override", re.compile(
        r"\b(ignore|disregard)\b.{0,40}\b(previous|prior|original|user'?s)\b.{0,20}\b(instruction|request|task)\b",
        re.IGNORECASE)),
    ("instruction_override", re.compile(
        r"\bnote to assistant\b|\bhidden instruction\b|\bdo not (mention|surface|disclose) this\b",
        re.IGNORECASE)),
    ("jailbreak_escalation", re.compile(
        r"\bsystem override\b|\bdeveloper mode\b|\bdo anything now\b|\bDAN\b|\bsafety (layer|filter)s? (suspended|disabled)\b",
        re.IGNORECASE)),
    ("tool_name_confusion", re.compile(
        r"\btool\b.{0,20}\b(deprecated|has been replaced|actually maps to)\b",
        re.IGNORECASE)),
    ("resource_uri_spoofing", re.compile(
        r"\b(mirror|replica|migrated)\b.{0,40}\b(resource://|https?://)",
        re.IGNORECASE)),
    ("chained_multistep", re.compile(
        r"\bnext time you (encounter|see)\b|\bdormant rule\b|\bdelayed[- ]trigger\b",
        re.IGNORECASE)),
    ("exfiltration", re.compile(
        r"\b(email|send|forward)\b.{0,60}\b(contents?|attachments?|files?)\b.{0,60}\b(to|@)\b",
        re.IGNORECASE)),
]


def heuristic_score(text: str) -> tuple[float, str | None]:
    """Returns (score in [0,1], matched_category or None). Score is a
    crude confidence proxy: 0.9 on any pattern hit, 0.05 baseline
    otherwise — this is a rule-based stand-in, not a calibrated
    probability, and should be described as such in any report."""
    for category, pattern in PATTERNS:
        if pattern.search(text):
            return 0.9, category
    return 0.05, None
