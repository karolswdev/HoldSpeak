"""Voice drawer resolution (HS-118-05).

LLM-powered resolution of natural-language zone references from voice
transcripts. Runs against a configured resolver profile (inference target).
"""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from .logging_config import get_logger

log = get_logger("voice_resolver")

# ── Operational bounds ──────────────────────────────────────────────────────
MAX_TRANSCRIPT_CHARS = 2048
MAX_ZONES = 256
MAX_REFS = 16
OUTPUT_TOKENS = 128
ATTEMPT_TIMEOUT_SECONDS = 5.0
MAX_ATTEMPTS = 3
RATE_LIMIT_SECONDS = 2.0

# ── Prompts ─────────────────────────────────────────────────────────────────

RESOLVER_PROMPT = """You are a reference resolver. The user has zones (directories) on their desk. Given the user's spoken instruction, identify which zones they are referring to.

ZONES (JSON):
{zone_catalog_json}

USER SAID (verbatim transcript):
{transcript_json}

Return ONLY a JSON object with this exact shape:
{{"zone_ids": ["dir_abc", "dir_def"]}}

Rules:
- Return only zone IDs from the ZONES list above.
- If no zones were referenced, return {{"zone_ids": []}}.
- Do not explain. Do not add commentary.
- Do not invent zone IDs not present in the ZONES list.
- Maximum {max_refs} zone IDs.

Examples:
ZONES: [{{"id":"dir_1","name":"Monday Standup","items":3}},{{"id":"dir_2","name":"Research Notes","items":5}}]
USER: "summarize the standup and compare with research"
Output: {{"zone_ids":["dir_1","dir_2"]}}

ZONES: [{{"id":"dir_3","name":"Inbox","items":2}},{{"id":"dir_4","name":"Archive","items":10}}]
USER: "what did I do today"
Output: {{"zone_ids":[]}}"""

RESOLVER_RETRY_CHAIN = [
    # Attempt 2: correction prompt with catalog + previous failed response
    """Your previous response was invalid:
>>> {previous_response} <<<

ZONES (JSON):
{zone_catalog_json}

USER SAID:
{transcript_json}

Return ONLY a JSON object: {{"zone_ids": ["dir_abc", "dir_def"]}}
If no zones referenced: {{"zone_ids": []}}
No explanation. No markdown. Just the JSON object.""",

    # Attempt 3: minimal forced-choice with catalog
    """ZONES: {zone_catalog_json}
USER: {transcript_json}
Return one JSON object: {{"zone_ids": [...]}}
Output: """,
]


# ── Data types ──────────────────────────────────────────────────────────────

@dataclass
class ResolvedRef:
    name: str
    id: str
    ref: str
    kind: str = "zone"


@dataclass
class ZoneCatalogEntry:
    id: str
    name: str
    items: int = 0


@dataclass
class ResolverResult:
    refs: list[ResolvedRef] = field(default_factory=list)
    egress: dict[str, str] = field(default_factory=dict)
    request_id: str = ""
    attempts: int = 0
    terminal_state: str = "success"  # success | timeout | parse_failure | refusal | error


# ── Parsing ─────────────────────────────────────────────────────────────────

def _extract_json_from_response(text: str) -> Optional[dict]:
    """Extract JSON object from model response, tolerating markdown fences."""
    text = text.strip()
    # Remove markdown code fences
    fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    # Try to parse
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    # Try to find a JSON object in the text
    brace_match = re.search(r'\{[^{}]*\}', text)
    if brace_match:
        try:
            obj = json.loads(brace_match.group())
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass
    return None


def _validate_response(parsed: dict, valid_ids: set[str]) -> Optional[list[str]]:
    """Validate shape and filter to known IDs. Returns None if shape is wrong."""
    zone_ids = parsed.get("zone_ids")
    if not isinstance(zone_ids, list):
        return None
    if not all(isinstance(zid, str) for zid in zone_ids):
        return None
    # Filter to valid IDs, deduplicate, limit
    seen: set[str] = set()
    valid: list[str] = []
    for zid in zone_ids:
        if zid in valid_ids and zid not in seen:
            seen.add(zid)
            valid.append(zid)
            if len(valid) >= MAX_REFS:
                break
    return valid


# ── Catalog formatting ──────────────────────────────────────────────────────

def format_zone_catalog(zones: list[ZoneCatalogEntry]) -> str:
    """Format zone catalog as JSON for the prompt."""
    entries = [{"id": z.id, "name": z.name, "items": z.items} for z in zones[:MAX_ZONES]]
    return json.dumps(entries, separators=(",", ":"))


def truncate_transcript(transcript: str) -> str:
    """Truncate transcript at word boundary if too long."""
    if len(transcript) <= MAX_TRANSCRIPT_CHARS:
        return transcript
    truncated = transcript[:MAX_TRANSCRIPT_CHARS]
    last_space = truncated.rfind(" ")
    if last_space > MAX_TRANSCRIPT_CHARS // 2:
        truncated = truncated[:last_space]
    return truncated


# ── Resolution engine ───────────────────────────────────────────────────────

def build_resolver_prompt(
    zones: list[ZoneCatalogEntry],
    transcript: str,
) -> str:
    """Build the initial resolver prompt."""
    catalog_json = format_zone_catalog(zones)
    transcript_json = json.dumps(truncate_transcript(transcript))
    return RESOLVER_PROMPT.format(
        zone_catalog_json=catalog_json,
        transcript_json=transcript_json,
        max_refs=MAX_REFS,
    )


def build_retry_prompt(
    attempt_index: int,
    zones: list[ZoneCatalogEntry],
    transcript: str,
    previous_response: str,
) -> str:
    """Build a retry prompt for attempt_index (0-indexed into RESOLVER_RETRY_CHAIN)."""
    if attempt_index >= len(RESOLVER_RETRY_CHAIN):
        raise ValueError(f"No retry prompt at index {attempt_index}")

    valid_ids = [z.id for z in zones[:MAX_ZONES]]
    catalog_json = format_zone_catalog(zones)
    template = RESOLVER_RETRY_CHAIN[attempt_index]
    return template.format(
        previous_response=previous_response[:500],
        zone_catalog_json=catalog_json,
        valid_ids_json=json.dumps(valid_ids),
        valid_ids_csv=", ".join(valid_ids),
        transcript_json=json.dumps(truncate_transcript(transcript)),
    )


def resolve_voice_references(
    *,
    zones: list[ZoneCatalogEntry],
    transcript: str,
    run_prompt_fn: Any,
    profile_id: str,
    request_id: str = "",
) -> ResolverResult:
    """Run the voice resolution with retry chain.

    run_prompt_fn(prompt: str, profile_id: str, max_tokens: int, timeout: float) -> str
    """
    if not request_id:
        request_id = f"vr_{uuid.uuid4().hex[:12]}"

    result = ResolverResult(request_id=request_id)

    # Empty catalog: skip model call
    if not zones:
        result.terminal_state = "success"
        return result

    # Truncate transcript
    transcript = truncate_transcript(transcript)
    if not transcript.strip():
        result.terminal_state = "success"
        return result

    # Warn if zone catalog is large
    if len(zones) > MAX_ZONES:
        log.warning("Zone catalog has %d zones, truncating to %d", len(zones), MAX_ZONES)

    valid_ids = {z.id for z in zones[:MAX_ZONES]}
    zone_by_id = {z.id: z for z in zones[:MAX_ZONES]}

    previous_response = ""

    for attempt in range(MAX_ATTEMPTS):
        result.attempts = attempt + 1

        # Build prompt
        if attempt == 0:
            prompt = build_resolver_prompt(zones, transcript)
        else:
            prompt = build_retry_prompt(attempt - 1, zones, transcript, previous_response)

        # Call model
        try:
            raw_response = run_prompt_fn(
                prompt=prompt,
                profile_id=profile_id,
                max_tokens=OUTPUT_TOKENS,
                timeout=ATTEMPT_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            log.warning("Resolver attempt %d timed out", attempt + 1)
            previous_response = "<timeout>"
            if attempt == MAX_ATTEMPTS - 1:
                result.terminal_state = "timeout"
                return result
            continue
        except Exception as exc:
            log.error("Resolver attempt %d failed: %s", attempt + 1, exc)
            previous_response = f"<error: {exc}>"
            if attempt == MAX_ATTEMPTS - 1:
                result.terminal_state = "error"
                return result
            continue

        previous_response = str(raw_response)

        # Parse response
        parsed = _extract_json_from_response(raw_response)
        if parsed is None:
            log.warning("Resolver attempt %d: response not parseable JSON", attempt + 1)
            if attempt == MAX_ATTEMPTS - 1:
                result.terminal_state = "parse_failure"
                return result
            continue

        validated_ids = _validate_response(parsed, valid_ids)
        if validated_ids is None:
            log.warning("Resolver attempt %d: response has wrong shape", attempt + 1)
            if attempt == MAX_ATTEMPTS - 1:
                result.terminal_state = "parse_failure"
                return result
            continue

        # Success — build refs
        result.refs = [
            ResolvedRef(
                name=zone_by_id[zid].name,
                id=zid,
                ref=f"zone:{zid}",
                kind="zone",
            )
            for zid in validated_ids
            if zid in zone_by_id
        ]
        result.terminal_state = "success"
        return result

    # Should not reach here
    result.terminal_state = "parse_failure"
    return result
