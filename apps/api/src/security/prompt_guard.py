from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from audit import log_security_event
from database import SessionLocal

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SANITIZE_RULES = [
    ("override_previous_instructions", re.compile(r"ignore|disregard|forget|override", re.I), "medium"),
    ("system_prompt_reference", re.compile(r"system prompt|developer message|hidden instructions", re.I), "high"),
    ("tool_exfiltration_attempt", re.compile(r"tool output|chain of thought|reveal .*prompt", re.I), "high"),
]


@dataclass
class PromptGuardResult:
    sanitized_text: str
    events: list[dict[str, Any]]
    blocked: bool


def _normalize_text(value: str) -> str:
    normalized = _CONTROL_RE.sub(" ", value or "")
    normalized = normalized.replace("\r", "\n")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _log_guard_events(
    *,
    source: str,
    events: list[dict[str, Any]],
    tenant_id: str | None,
    user_id: str | None,
    resource_type: str | None,
    resource_id: str | None,
) -> None:
    if not events:
        return
    with SessionLocal() as db:
        for event in events:
            log_security_event(
                db=db,
                action="prompt_injection_attempt",
                tenant_id=tenant_id,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                details={
                    "source": source,
                    "rule": event["rule"],
                    "severity": event["severity"],
                    "action_taken": event["action_taken"],
                    "preview": event["preview"],
                },
            )


def guard_prompt_text(
    text: str,
    *,
    source: str,
    tenant_id: str | None = None,
    user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    block_policy: str = "sanitize",
) -> PromptGuardResult:
    normalized = _normalize_text(text)
    if not normalized:
        return PromptGuardResult(sanitized_text="", events=[], blocked=False)

    events: list[dict[str, Any]] = []
    safe_lines: list[str] = []
    blocked = False

    for raw_line in normalized.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matched_rules = []
        for rule_name, pattern, severity in _SANITIZE_RULES:
            if pattern.search(line):
                matched_rules.append((rule_name, severity))

        if matched_rules:
            highest = "low"
            if any(severity == "high" for _, severity in matched_rules):
                highest = "high"
            elif any(severity == "medium" for _, severity in matched_rules):
                highest = "medium"

            action_taken = "removed"
            if highest == "high" and block_policy == "block":
                blocked = True
                action_taken = "blocked"

            events.append(
                {
                    "rule": ",".join(rule for rule, _ in matched_rules),
                    "severity": highest,
                    "action_taken": action_taken,
                    "preview": line[:180],
                }
            )
            continue

        safe_lines.append(line)

    sanitized = "\n".join(safe_lines).strip()
    _log_guard_events(
        source=source,
        events=events,
        tenant_id=tenant_id,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    return PromptGuardResult(sanitized_text=sanitized, events=events, blocked=blocked)


def sanitize_payload_strings(
    payload: Any,
    *,
    source_prefix: str,
    tenant_id: str | None = None,
    user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    block_policy: str = "sanitize",
) -> dict[str, Any]:
    events: list[dict[str, Any]] = []

    def _walk(value: Any, path: str) -> tuple[Any, bool]:
        if isinstance(value, str):
            guard = guard_prompt_text(
                value,
                source=f"{source_prefix}:{path}",
                tenant_id=tenant_id,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                block_policy=block_policy,
            )
            events.extend(
                [
                    {
                        **event,
                        "source": f"{source_prefix}:{path}",
                    }
                    for event in guard.events
                ]
            )
            return guard.sanitized_text, guard.blocked
        if isinstance(value, list):
            blocked = False
            sanitized = []
            for idx, item in enumerate(value):
                cleaned, item_blocked = _walk(item, f"{path}[{idx}]")
                blocked = blocked or item_blocked
                sanitized.append(cleaned)
            return sanitized, blocked
        if isinstance(value, dict):
            blocked = False
            sanitized: dict[str, Any] = {}
            for key, item in value.items():
                cleaned, item_blocked = _walk(item, f"{path}.{key}")
                blocked = blocked or item_blocked
                sanitized[key] = cleaned
            return sanitized, blocked
        return value, False

    sanitized_payload, blocked = _walk(payload, "root")
    return {
        "value": sanitized_payload,
        "events": events,
        "blocked": blocked,
        "summary": json.dumps({"events": len(events), "blocked": blocked}),
    }
