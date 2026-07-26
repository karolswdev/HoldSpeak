"""Session receipts (HS-104-05) — honest numbers on the card.

One composed line, three tiers, every figure labeled by provenance
(Article VI):

- **always-true** — elapsed wall time and steer/hold counts computed
  from records the hub itself wrote (`steering_audit`, the gate
  tables). Authoritative by construction, always shown.
- **reported** — token figures, ONLY when the adapter's ledger row
  says ``usage_tokens: authoritative`` (the Claude Code Stop hook
  reports the session totals from the agent's own transcript). Cache
  read/creation stay separate figures, never summed. The call site
  goes through :func:`require_capability`; the census pins it.
- **estimated** — cost, ONLY when tokens are reported AND the
  user-editable pricing table (`~/.holdspeak/pricing.json`) carries a
  price row for the model — rendered upstream as
  ``≈ $X.XX (price table, YYYY-MM-DD)``. No price row → NO cost
  entry: an absent number, never a zero.

Held-call decision latency per tool rides along sample-floored:
p50/p95 only at ≥ 20 paired (created → decided) observations in the
session; below the floor, count and max only. Tools are never
blended into one percentile.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .agent_capabilities import (
    Capability,
    CapabilityUnavailableError,
    require_capability,
)

PRICING_FILE = Path.home() / ".holdspeak" / "pricing.json"
PERCENTILE_SAMPLE_FLOOR = 20


def load_pricing(path: Path | None = None) -> dict[str, Any]:
    """The user-editable price table. Missing/corrupt = no prices —
    the estimate tier simply does not render."""
    target = path or PRICING_FILE
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _adapter_for(session_key: str) -> str:
    return "claude-code-hooks" if session_key.startswith("claude:") else "tmux-pane"


def _percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    index = min(len(sorted_values) - 1, max(0, round(q * (len(sorted_values) - 1))))
    return sorted_values[index]


def build_receipt(
    session_key: str,
    *,
    db: Any,
    pricing: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """The wire receipt for one session. Every tier states what it is;
    a tier the ledger cannot vouch for is ABSENT, not zero."""
    steering = db.steering.list(session_key=session_key, limit=500)
    proposals = db.gate.proposals_for_session(session_key)

    # ── always-true: the hub's own records ───────────────────────────
    timestamps: list[float] = [p.created_at for p in proposals]
    timestamps += [p.decided_at for p in proposals if p.decided_at]
    iso_times = sorted(e.ts for e in steering if e.ts)
    delivered = sum(1 for e in steering if e.outcome == "delivered")
    refused = len(steering) - delivered
    holds = {
        state: sum(1 for p in proposals if p.state == state)
        for state in ("held", "approved", "denied", "expired", "invalidated")
    }
    elapsed: Optional[float] = None
    if timestamps:
        elapsed = max(timestamps) - min(timestamps)
    if iso_times:
        from datetime import datetime

        def _epoch(iso: str) -> Optional[float]:
            try:
                return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
            except ValueError:
                return None

        parsed = [t for t in (_epoch(x) for x in iso_times) if t is not None]
        if parsed:
            span = (min(parsed + timestamps), max(parsed + timestamps)) if timestamps else (min(parsed), max(parsed))
            elapsed = span[1] - span[0]

    receipt: dict[str, Any] = {
        "receipt_schema": 1,
        "session_key": session_key,
        "always": {
            "provenance": "hub records",
            "elapsed_seconds": round(elapsed, 1) if elapsed is not None else None,
            "steers_delivered": delivered,
            "steers_refused": refused,
            "holds": holds,
        },
    }

    # ── held-call decision latency, per tool, sample-floored ─────────
    by_tool: dict[str, list[float]] = {}
    for p in proposals:
        if p.decided_at and p.state in ("approved", "denied"):
            by_tool.setdefault(p.tool, []).append(p.decided_at - p.created_at)
    tools = []
    for tool, samples in sorted(by_tool.items()):
        samples.sort()
        entry: dict[str, Any] = {"tool": tool, "samples": len(samples)}
        if len(samples) >= PERCENTILE_SAMPLE_FLOOR:
            entry["p50_seconds"] = round(_percentile(samples, 0.50), 2)
            entry["p95_seconds"] = round(_percentile(samples, 0.95), 2)
        else:
            entry["max_seconds"] = round(samples[-1], 2)
        tools.append(entry)
    receipt["tools"] = tools

    # ── reported: only what the ledger vouches for ───────────────────
    usage = db.gate.usage_for(session_key)
    if usage is not None:
        try:
            standing = require_capability(_adapter_for(session_key), Capability.USAGE_TOKENS)
        except CapabilityUnavailableError:
            usage = None
        else:
            receipt["reported"] = {
                "provenance": standing.value,
                "model": usage["model"],
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                # Cache figures stay separate, never summed.
                "cache_read_tokens": usage["cache_read_tokens"],
                "cache_creation_tokens": usage["cache_creation_tokens"],
                "reported_at": usage["reported_at"],
            }

    # ── estimated: tokens reported AND a price row, or nothing ───────
    if usage is not None:
        table = load_pricing() if pricing is None else pricing
        models = table.get("models") if isinstance(table.get("models"), dict) else {}
        row = models.get(usage["model"])
        if isinstance(row, dict):
            try:
                cost = (
                    usage["input_tokens"] * float(row.get("input_per_mtok", 0.0))
                    + usage["output_tokens"] * float(row.get("output_per_mtok", 0.0))
                ) / 1_000_000.0
            except (TypeError, ValueError):
                cost = None
            if cost is not None:
                receipt["estimated"] = {
                    "provenance": "price table",
                    "cost_usd": round(cost, 2),
                    "source": "price table",
                    "as_of": str(table.get("updated") or ""),
                }

    return receipt
