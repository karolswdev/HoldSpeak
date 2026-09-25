#!/usr/bin/env python3
"""Verify the retained PHILO-5-04 rehearsal without starting any service.

The input is an archived run directory.  This verifier reads the retained
Codex events, MCP HTTP transcript, observations, shots, and read-only SQLite
backup.  Its mutation cases operate on deep copies in memory.  They are
reported as EXPECTED REJECTION; no failed pytest run or second rehearsal is
invented by this artifact.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote


STAGES = ("import", "summary", "decision_thought", "tomorrow_brief")
REQUIRED_TOOLS = {
    "import": {"meeting.import"},
    "summary": {"meeting.run_intelligence"},
    "decision_thought": {"desk.create", "thought.create", "thought.update_working"},
    "tomorrow_brief": {"monday_brief.generate"},
}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
FINAL_RUN = "20260925T001407Z-his-words-real"
FINAL_SENTENCE = "Saved after the meeting review."


class AuditError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def wire(value: Any) -> Any:
    """Decode both recorder representations used by this retained run."""
    if isinstance(value, (dict, list)) or value is None:
        return value
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value


def canonical_result(value: Any) -> Any:
    """Normalize only MCP envelope omissions, retaining all semantic fields."""
    if not isinstance(value, dict):
        return {"value": value, "structured_content": None, "isError": False}
    result = dict(value)
    if "structured_content" not in result:
        result["structured_content"] = result.pop("structuredContent", None)
    else:
        result.pop("structuredContent", None)
    if "isError" not in result:
        result["isError"] = bool(result.pop("is_error", False) or "error" in result)
    else:
        result.pop("is_error", None)
    return result


def result_hash(value: Any) -> str:
    encoded = json.dumps(canonical_result(value), sort_keys=True, default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def response_result(response: Any) -> Any:
    if not isinstance(response, dict):
        return None
    if "result" in response:
        return response["result"]
    if "error" in response:
        return {"error": response["error"]}
    return None


def event_calls(stage_dir: Path) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for event in load_jsonl(stage_dir / "events.jsonl"):
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        if event.get("type") != "item.completed" or item.get("type") != "mcp_tool_call":
            continue
        if item.get("server") != "holdspeak":
            continue
        if "result" in item:
            result = item.get("result")
        elif "error" in item:
            result = {"error": item.get("error")}
        else:
            raise AuditError(f"completed MCP item has no result or error: {item!r}")
        calls.append({
            "tool": item.get("tool"),
            "arguments": item.get("arguments") or {},
            "result": result,
            "is_refusal": bool(item.get("error"))
                or bool(isinstance(result, dict) and result.get("isError")),
            "result_sha256": result_hash(result),
        })
    return calls


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def in_window(row: dict[str, Any], timing: dict[str, Any]) -> bool:
    started = parse_time(row.get("started_at"))
    lower = parse_time(timing.get("started_at"))
    upper = parse_time(timing.get("finished_at"))
    return bool(started and lower and upper and lower <= started <= upper)


def request_body(row: dict[str, Any]) -> dict[str, Any] | None:
    parsed = wire(row.get("request_body", row.get("request")))
    return parsed if isinstance(parsed, dict) else None


def response_body(row: dict[str, Any]) -> dict[str, Any] | None:
    parsed = wire(row.get("response_body", row.get("response")))
    return parsed if isinstance(parsed, dict) else None


def mcp_call_row(row: dict[str, Any]) -> bool:
    request = request_body(row)
    return bool(
        str(row.get("method", "")).upper() == "POST"
        and row.get("path") == "/api/mcp"
        and isinstance(request, dict)
        and request.get("method") == "tools/call"
    )


def reconcile(calls: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pair every completed Codex call with one POST /api/mcp occurrence."""
    candidates = [row for row in rows if mcp_call_row(row)]
    used: set[int] = set()
    matches: list[dict[str, Any]] = []
    for call in calls:
        found: int | None = None
        for index, row in enumerate(candidates):
            if index in used:
                continue
            request = request_body(row) or {}
            params = request.get("params") or {}
            if params.get("name") != call["tool"]:
                continue
            if (params.get("arguments") or {}) != call["arguments"]:
                continue
            if result_hash(response_result(response_body(row))) != call["result_sha256"]:
                continue
            found = index
            break
        if found is None:
            raise AuditError(
                f"no POST /api/mcp occurrence for {call['tool']} with exact args/result hash "
                f"{call['result_sha256']}"
            )
        used.add(found)
        matches.append({"tool": call["tool"], "row": candidates[found], "candidate_index": found})
    return matches


def non_mcp_writes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row for row in rows
        if str(row.get("method", "")).upper() in WRITE_METHODS
        and row.get("path") != "/api/mcp"
    ]


def catalog_from_tools_list(rows: list[dict[str, Any]]) -> tuple[set[str], set[str], int]:
    names: set[str] = set()
    argument_keys: set[str] = set()
    count = 0
    for row in rows:
        request = request_body(row) or {}
        if request.get("method") != "tools/list":
            continue
        response = response_body(row) or {}
        result = response.get("result")
        tools = result.get("tools") if isinstance(result, dict) else None
        if not isinstance(tools, list):
            continue
        count += 1
        for tool in tools:
            if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
                continue
            names.add(tool["name"])
            schema = tool.get("inputSchema")
            properties = schema.get("properties") if isinstance(schema, dict) else None
            if isinstance(properties, dict):
                argument_keys.update(str(key) for key in properties)
    return names, argument_keys, count


def ordinary_fence(text: str, tool_names: set[str], argument_keys: set[str]) -> list[str]:
    found: list[str] = []
    for name in sorted(tool_names, key=len, reverse=True):
        if re.search(r"(?<![\w])" + re.escape(name) + r"(?![\w])", text):
            found.append(name)
    for key in sorted(argument_keys, key=len, reverse=True):
        if "_" in key and re.search(r"\b" + re.escape(key) + r"\b\s*=", text):
            found.append(key + "=")
    patterns = {
        "clock.python_wall": r"\bclock\.python_wall\b",
        "advance_days": r"\badvance_days\b",
        "producer clock": r"\bproducer[- ]clock\b",
        "clock offset": r"\bclock\s+offset\b",
        "offset": r"\boffset\b",
        "ISO date": r"\b\d{4}-\d{2}-\d{2}\b",
    }
    for label, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(label)
    return found


MUTATION_PATTERN = re.compile(
    r"(?:\bsqlite3\b|\brm\s|\bmv\s|\bcp\s|\btouch\s|\btee\s|"
    r"\bsed\s+-i|\bgit\s+(?:add|commit|reset|checkout|restore|clean|stash)\b|"
    r"\bcurl\b[^\n]*\s-X\s*(?:POST|PUT|PATCH|DELETE)|"
    r"\b(?:write_text|write_bytes|unlink|remove|rename)\b|(?:^|\s)>>?\s*)",
    re.IGNORECASE,
)


def shell_commands(stage_dir: Path) -> tuple[list[str], list[str]]:
    commands: list[str] = []
    mutations: list[str] = []
    for event in load_jsonl(stage_dir / "events.jsonl"):
        item = event.get("item")
        if event.get("type") != "item.completed" or not isinstance(item, dict) or item.get("type") not in {
            "command_execution", "shell_command", "exec",
        }:
            continue
        command = item.get("command", "")
        command = command if isinstance(command, str) else json.dumps(command, sort_keys=True, default=str)
        commands.append(command)
        if MUTATION_PATTERN.search(command):
            mutations.append(command)
    return commands, mutations


def response_record(record: Any) -> Any:
    if not isinstance(record, dict):
        return record
    if isinstance(record.get("final"), dict):
        record = record["final"]
    if isinstance(record.get("response"), (dict, list)):
        return record["response"]
    if isinstance(record.get("domain_response"), (dict, list)):
        return record["domain_response"]
    return record


def walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def has_id(value: Any, expected: str) -> bool:
    return any(isinstance(node, str) and node == expected for node in walk(value))


def brief_items(payload: Any) -> list[dict[str, Any]]:
    payload = response_record(payload)
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("items"), list):
        return [item for item in payload["items"] if isinstance(item, dict)]
    sections = payload.get("sections")
    if not isinstance(sections, dict):
        return []
    return [item for values in sections.values() if isinstance(values, list) for item in values if isinstance(item, dict)]


def row_texts(browser_page: dict[str, Any]) -> list[str]:
    values = browser_page.get("row_texts")
    return values if isinstance(values, list) else []


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.failures: list[str] = []
        self.gaps: list[str] = []

    def section(self, title: str) -> None:
        self.lines.extend(["", title])

    def check(self, label: str, condition: bool, detail: str) -> None:
        state = "PASS" if condition else "FAIL"
        self.lines.append(f"{state}  {label}: {detail}")
        if not condition:
            self.failures.append(f"{label}: {detail}")

    def note(self, label: str, detail: str) -> None:
        self.lines.append(f"NOTE  {label}: {detail}")

    def rejection(self, label: str, detail: str) -> None:
        self.lines.append(f"EXPECTED REJECTION  {label}: {detail}")


def expected_rejections(report: Report, calls: list[dict[str, Any]], rows: list[dict[str, Any]], prompt: str, tool_names: set[str]) -> None:
    if not calls:
        raise AuditError("cannot run in-memory mutation cases without a retained MCP call")
    tool = str(calls[0]["tool"])
    try:
        if not ordinary_fence(prompt + f"\nPlease call {tool}.", tool_names, set()):
            raise AssertionError("prompt mutation was accepted")
        report.rejection("prompt operation-name mutation", f"the retained catalog name {tool!r} was detected")
    except Exception as exc:
        raise AuditError(f"prompt mutation case did not reject: {exc}") from exc

    baseline = copy.deepcopy(rows)
    candidate = next((i for i, row in enumerate(baseline) if mcp_call_row(row)), None)
    if candidate is None:
        raise AuditError("no retained MCP row for mutation cases")

    changed_result = copy.deepcopy(baseline)
    response = response_body(changed_result[candidate]) or {}
    result = response.get("result")
    if isinstance(result, dict) and isinstance(result.get("content"), list) and result["content"]:
        first = result["content"][0]
        if isinstance(first, dict) and isinstance(first.get("text"), str):
            first["text"] += " MUTATED"
    else:
        response["result"] = {"content": [{"type": "text", "text": "MUTATED"}]}
    changed_result[candidate]["response_body"] = json.dumps(response)
    changed_result[candidate]["response"] = json.dumps(response)
    try:
        reconcile(calls, changed_result)
    except AuditError as exc:
        report.rejection("MCP result mismatch", str(exc))
    else:
        raise AuditError("MCP result mutation was accepted")

    bypass = copy.deepcopy(baseline)
    bypass[candidate]["method"] = "GET"
    bypass[candidate]["path"] = "/api/direct-write"
    try:
        reconcile(calls, bypass)
    except AuditError as exc:
        report.rejection("method/path bypass", str(exc))
    else:
        raise AuditError("method/path bypass was accepted")

    extra = copy.deepcopy(baseline)
    extra.append({"method": "POST", "path": "/api/desk/direct-write", "status": "200"})
    try:
        writes = non_mcp_writes(extra)
        if not writes:
            raise AssertionError("extra write was not found")
        report.rejection("extra non-MCP write", f"detected {writes[-1]['method']} {writes[-1]['path']}")
    except Exception as exc:
        raise AuditError(f"extra non-MCP write case did not reject: {exc}") from exc


def readonly_db(path: Path) -> sqlite3.Connection:
    uri = "file:" + quote(str(path)) + "?mode=ro&immutable=1"
    db = sqlite3.connect(uri, uri=True)
    db.execute("PRAGMA query_only=ON")
    return db


def one(db: sqlite3.Connection, sql: str, args: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    db.row_factory = sqlite3.Row
    row = db.execute(sql, args).fetchone()
    return dict(row) if row else None


def many(db: sqlite3.Connection, sql: str, args: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    db.row_factory = sqlite3.Row
    return [dict(row) for row in db.execute(sql, args).fetchall()]


def run_audit(run: Path, output: Path) -> int:
    report = Report()
    report.lines.append("PHILO-5-04 FINAL REHEARSAL ARTIFACT AUDIT")
    report.lines.append(f"RUN: {run}")
    report.lines.append("MODE: read-only retained artifacts; no hub, browser, Codex, or pytest process")

    required = [run / "rehearsal-transcript.jsonl", run / "db-proof.sqlite", run / "run-status.json"]
    required += [run / "codex" / stage / "events.jsonl" for stage in STAGES]
    for path in required:
        report.check("retained file", path.exists(), str(path.relative_to(run)))
    if report.failures:
        output.write_text("\n".join(report.lines) + "\n", encoding="utf-8")
        return 1

    transcript = load_jsonl(run / "rehearsal-transcript.jsonl")
    all_tool_names, all_argument_keys, catalog_count = catalog_from_tools_list(transcript)
    report.section("Transport and catalog")
    report.check("tools/list retained", catalog_count >= len(STAGES), f"{catalog_count} tools/list responses; {len(all_tool_names)} tool names")
    report.check("recorded MCP transport", any(mcp_call_row(row) for row in transcript), "POST /api/mcp tools/call rows are present")

    stage_data: dict[str, dict[str, Any]] = {}
    all_calls: list[dict[str, Any]] = []
    all_matches = 0
    all_shell: list[str] = []
    shell_mutations: list[tuple[str, str]] = []
    report.section("Codex turns")
    window_starts: dict[str, int] = {}
    window_ranges: dict[str, tuple[int, int]] = {}
    for stage in STAGES:
        window = load_json(run / "codex" / stage / "transcript-window.json")
        audit_window = load_json(run / "codex" / stage / "mcp-audit.json").get("reconciliation", {})
        start = int(window["exchange_start"])
        audit_start = int(audit_window.get("turn_exchange_start", -1))
        count = int(audit_window.get("turn_exchanges", -1))
        report.check(f"{stage} retained window start", start == audit_start, f"transcript-window={start}; mcp-audit={audit_start}")
        window_starts[stage] = start
        window_ranges[stage] = (start, start + count)
    ordered_starts = [window_starts[stage] for stage in STAGES]
    valid_ranges = all(
        0 <= start < end <= len(transcript)
        for start, end in window_ranges.values()
    )
    non_overlapping = all(
        window_ranges[left][1] <= window_ranges[right][0]
        for left, right in zip(STAGES, STAGES[1:])
    )
    report.check("transcript window bounds", ordered_starts == sorted(ordered_starts) and valid_ranges and non_overlapping, f"ranges={window_ranges}; rows={len(transcript)}")
    for stage in STAGES:
        stage_dir = run / "codex" / stage
        timing = load_json(stage_dir / "timing.json")
        calls = event_calls(stage_dir)
        window_start, window_end = window_ranges[stage]
        window_rows = transcript[window_start:window_end]
        mcp_window_rows = [row for row in window_rows if mcp_call_row(row)]
        try:
            matches = reconcile(calls, window_rows)
            reconcile_ok = True
            reconcile_detail = f"{len(matches)}/{len(calls)} calls matched occurrence-by-occurrence"
        except AuditError as exc:
            matches = []
            reconcile_ok = False
            reconcile_detail = str(exc)
        writes = non_mcp_writes(window_rows)
        commands, mutations = shell_commands(stage_dir)
        all_calls.extend(calls)
        all_matches += len(matches)
        all_shell.extend(commands)
        shell_mutations.extend((stage, command) for command in mutations)
        required_ok = REQUIRED_TOOLS[stage] <= {str(call.get("tool")) for call in calls}
        report.check(f"{stage} call reconciliation", reconcile_ok, reconcile_detail)
        report.check(f"{stage} required producer", required_ok, f"required={sorted(REQUIRED_TOOLS[stage])}")
        report.check(f"{stage} non-MCP write fence", not writes, f"{len(writes)} unmatched write rows in indexed transcript window")
        report.check(f"{stage} shell mutation fence", not mutations, f"{len(commands)} shell commands; {len(mutations)} mutation commands")
        report.check(f"{stage} process outcome", timing.get("outcome") == "process_completed", json.dumps(timing, sort_keys=True))
        sequence = [str(call.get("tool")) for call in calls]
        report.note(f"{stage} tool sequence", " -> ".join(sequence) or "<none>")
        report.note(f"{stage} duration", f"{timing.get('elapsed_s')}s; transcript window={window_start}:{window_end}; MCP call rows={len(mcp_window_rows)}")
        stage_data[stage] = {
            "timing": timing,
            "calls": calls,
            "window_rows": window_rows,
            "matches": matches,
        }

    report.check("all completed calls reconciled", all_matches == len(all_calls), f"{all_matches}/{len(all_calls)} retained completed holdspeak MCP calls")
    refusals = [call for call in all_calls if call["is_refusal"]]
    report.note("refused/error calls", str(len(refusals)) + " (retained and included in reconciliation)")
    report.check("no shell mutation commands", not shell_mutations, f"{len(all_shell)} commands inspected")
    if shell_mutations:
        for stage, command in shell_mutations:
            report.note("shell mutation command", f"{stage}: {command}")

    report.section("Ordinary-language prompts")
    prompt_failures: list[str] = []
    for stage in STAGES:
        stage_dir = run / "codex" / stage
        owner_prompt = (stage_dir / "owner-prompt.txt").read_text(encoding="utf-8")
        sent_brief = (stage_dir / "brief.md").read_text(encoding="utf-8")
        found = ordinary_fence(sent_brief, all_tool_names, all_argument_keys)
        owner_found = ordinary_fence(owner_prompt, all_tool_names, all_argument_keys)
        if found or owner_found:
            prompt_failures.append(f"{stage}: brief={found}, owner-prompt={owner_found}")
        report.check(f"{stage} prompt fence", not found and not owner_found, f"catalog/tool/technical tokens={found + owner_found}")
    report.check("all prompts ordinary", not prompt_failures, "all retained as-sent prompts pass the actual tools/list catalog fence")

    report.section("In-memory rejection cases")
    first_stage = stage_data["import"]
    expected_rejections(
        report,
        first_stage["calls"],
        first_stage["window_rows"],
        (run / "codex" / "import" / "brief.md").read_text(encoding="utf-8"),
        all_tool_names,
    )

    report.section("Readbacks and identity")
    observations = {stage: load_json(run / "observations" / f"{stage}.json") for stage in ("import", "summary", "decision", "thought", "brief")}
    meeting_id = observations["import"].get("meeting_id")
    decision_id = observations["decision"].get("decision_id")
    thought_id = observations["thought"].get("thought_id")
    brief_id = observations["brief"].get("brief_id")
    source_ref = observations["brief"].get("decision_source_ref")
    report.check("canonical meeting id", bool(meeting_id), repr(meeting_id))
    report.check("canonical decision id", bool(decision_id), repr(decision_id))
    report.check("canonical Thought id", bool(thought_id), repr(thought_id))
    report.check("canonical brief id", bool(brief_id), repr(brief_id))

    import_read = response_record(observations["import"].get("meeting_read"))
    summary_read = response_record(observations["summary"].get("meeting_read"))
    decision_read = response_record(observations["decision"].get("decision_read"))
    thought_read = response_record(observations["thought"].get("thought_read"))
    brief_read = response_record(observations["brief"].get("brief_read"))
    report.check("meeting import readback", has_id(import_read, str(meeting_id)) and "transcription_status" in json.dumps(import_read), "meeting id and complete transcript readback retained")
    summary_text = ""
    if isinstance(summary_read, dict):
        intel = summary_read.get("intel")
        summary_text = str(intel.get("summary") or "") if isinstance(intel, dict) else ""
    host_ok = bool(isinstance(summary_read, dict) and any(
        isinstance(attempt, dict) and attempt.get("host") == "192.168.1.43"
        for attempt in ((summary_read.get("run_receipt") or {}).get("attempts") or [])
    ))
    report.check("summary readback", bool(summary_text) and host_ok and has_id(summary_read, str(meeting_id)), f"summary={len(summary_text)} chars; LAN host receipt={host_ok}")
    report.check("decision readback", has_id(decision_read, str(decision_id)) and "Keep summary retrieval on the local desk" in json.dumps(decision_read), "decision content and identity retained")
    thought_json = json.dumps(thought_read, ensure_ascii=False)
    report.check("Thought saved body", FINAL_SENTENCE in thought_json and "The meeting loop stays on the local desk." in thought_json, "final appended sentence and original body retained")
    before_rev = observations["thought"].get("working_revision_before_save")
    after_rev = observations["thought"].get("working_revision_after_save")
    report.check("Thought revision advanced", isinstance(before_rev, int) and isinstance(after_rev, int) and after_rev > before_rev, f"{before_rev} -> {after_rev}")
    items = observations["brief"].get("matching_brief_items") or brief_items(brief_read)
    source_ok = source_ref == f"decision:{decision_id}" and any(item.get("source_ref") == source_ref for item in items if isinstance(item, dict))
    report.check("brief decision source", source_ok, f"{source_ref!r}; {len(items)} matching retained items")

    db = readonly_db(run / "db-proof.sqlite")
    try:
        report.check("SQLite immutable read-only open", db.execute("PRAGMA query_only").fetchone()[0] == 1, "query_only=1")
        report.check("SQLite integrity", db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "integrity_check=ok")
        meeting_row = one(db, "SELECT * FROM meetings WHERE id=?", (meeting_id,))
        decision_row = one(db, "SELECT * FROM desk_decisions WHERE id=?", (decision_id,))
        thought_row = one(db, "SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,))
        note_id = thought_row.get("working_note_id") if thought_row else None
        note_row = one(db, "SELECT * FROM notes WHERE id=?", (note_id,)) if note_id else None
        brief_row = one(db, "SELECT * FROM monday_briefs WHERE id=?", (brief_id,))
        brief_db_items = many(db, "SELECT * FROM monday_brief_items WHERE brief_id=?", (brief_id,))
        report.check("meeting id in immutable DB backup", meeting_row is not None, str(meeting_id))
        report.check("decision id in immutable DB backup", decision_row is not None, str(decision_id))
        report.check("Thought id in immutable DB backup", thought_row is not None and note_row is not None, f"thought={thought_id}; note={note_id}")
        report.check("brief id in immutable DB backup", brief_row is not None and bool(brief_db_items), f"brief={brief_id}; items={len(brief_db_items)}")
        report.check("DB Thought final body/revision", bool(note_row and FINAL_SENTENCE in note_row.get("body_markdown", "") and thought_row.get("working_revision") == after_rev), f"working_revision={thought_row.get('working_revision') if thought_row else None}")
        report.check("DB brief decision source", any(row.get("source_ref") == source_ref for row in brief_db_items), str(source_ref))
        expected_ids = {
            "meetings": {str(meeting_id)},
            "desk_decisions": {str(decision_id)},
            "refinement_thoughts": {str(thought_id)},
            "monday_briefs": {str(brief_id)},
            "monday_brief_items": {str(row.get("id")) for row in brief_db_items},
        }
        unexpected: dict[str, list[str]] = {}
        for table, ids in expected_ids.items():
            rows = many(db, f"SELECT id FROM {table}")
            extras = [str(row["id"]) for row in rows if str(row["id"]) not in ids]
            if extras:
                unexpected[table] = extras
        report.check("unexpected audited created objects", not unexpected, json.dumps(unexpected, sort_keys=True) if unexpected else "none in meeting/decision/Thought/brief tables")
    finally:
        db.close()

    report.section("Browser predicates and retained shots")
    summary_pages = observations["summary"].get("browser", {}).get("pages", [])
    report.check("summary both widths", len(summary_pages) == 2, f"pages={len(summary_pages)}")
    for page in summary_pages:
        width = page.get("viewport")
        metrics = page.get("after", {}).get("summary_metrics", {})
        report.check(f"summary {width}px visible", bool(page.get("after", {}).get("summary_text")), "summary text present")
        report.check(f"summary {width}px host", "192.168.1.43" in str(page.get("after", {}).get("summary_host_text", "")), "LAN host receipt visible")
        report.check(f"summary {width}px in place", page.get("updated_without_refresh") is True and page.get("manual_refresh") is False and page.get("navigation_after_open") == 0, "same page, no refresh/navigation")
        report.check(f"summary {width}px hit-test", all(bool(metrics.get(key)) for key in ("visible", "in_viewport", "hit")), json.dumps(metrics, sort_keys=True))
    for stage in ("decision", "thought", "brief"):
        pages = observations[stage].get("browser", {}).get("pages", [])
        report.check(f"{stage} both widths", len(pages) == 2, f"pages={len(pages)}")
        for page in pages:
            width = page.get("viewport")
            if stage == "brief":
                receipt = bool(page.get("receipt_present")) and "Brief ready" in str(page.get("receipt_text", ""))
                row = any("Keep summary retrieval on the local desk" in text for text in row_texts(page))
                report.check(f"brief {width}px receipt", receipt, str(page.get("receipt_text")))
                report.check(f"brief {width}px decision row", row, json.dumps(row_texts(page), ensure_ascii=False))
            else:
                report.check(f"{stage} {width}px content", page.get("expected_text_present") is True, "expected content visible")
            shot_name = Path(str(page.get("shot", ""))).name
            report.check(f"{stage} {width}px shot", (run / "shots" / stage / shot_name).exists(), shot_name)
            for key in ("receipt_shot", "row_shot"):
                if page.get(key):
                    name = Path(str(page[key])).name
                    report.check(f"{stage} {width}px {key}", (run / "shots" / stage / name).exists(), name)

    report.section("Run proof and limitations")
    status = load_json(run / "run-status.json")
    report.check("run completed", status.get("outcome") == "completed" and status.get("error") is None, json.dumps(status, sort_keys=True))
    report.note("total duration", f"{status.get('elapsed_s')}s; started={status.get('started_at')}; finished={status.get('finished_at')}")
    requested = load_json(run / "requested-codex-config.json")
    effective = load_json(run / "effective-codex-config.json")
    report.check("Codex hub HOME separation", requested.get("env", {}).get("HOME") == load_json(run / "run.json").get("hub_home"), "Codex config points at fresh hub HOME")
    report.check("MCP config exact", str(requested.get("command", "")).endswith("/.venv/bin/holdspeak-mcp") and requested.get("cwd") and requested.get("args") == [] and requested.get("required") is True, json.dumps(requested, sort_keys=True))
    report.check("effective Codex config", effective.get("exit_code") == 0 and effective.get("effective", {}).get("enabled") is True, "codex mcp get succeeded and holdspeak enabled")
    report.check("owner review label", load_json(run / "run.json").get("owner_review_label") == "REHEARSED; OWNER REVIEW PENDING", "review remains pending")
    preflight = (run / "engine-preflight-curl.txt").read_text(encoding="utf-8")
    report.check("real engine preflight", "exit=0" in preflight and "192.168.1.43" in preflight, "LAN model endpoint returned successfully")
    hub_log = (run / "hub.log").read_text(encoding="utf-8")
    if "resource_tracker" in hub_log:
        report.note("hub shutdown warning", "resource_tracker reported one leaked semaphore; run completed and DB proof is intact")
    report.note("tool catalog", f"{len(all_tool_names)} names retained from {catalog_count} tools/list responses")
    report.note("proof boundary", "Codex calls and shell/transcript writes are audited; browser/setup reads and rig producer writes are outside Codex timing windows")

    verdict = "PASS" if not report.failures else "FAIL"
    report.lines[0] = f"PHILO-5-04 FINAL REHEARSAL ARTIFACT AUDIT — {verdict}"
    if report.gaps:
        report.section("Proof gaps")
        report.lines.extend(f"GAP  {gap}" for gap in report.gaps)
    report.section("Counts")
    report.lines.append(f"Codex stages={len(STAGES)}; completed MCP calls={len(all_calls)}; refusals/errors={len(refusals)}; shell commands={len(all_shell)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(report.lines) + "\n", encoding="utf-8")
    return 0 if verdict == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument("--run", type=Path, default=here.parent / "final" / FINAL_RUN)
    parser.add_argument("--out", type=Path, default=here / "final-rehearsal-audit.txt")
    args = parser.parse_args()
    try:
        return run_audit(args.run.resolve(), args.out.resolve())
    except Exception as exc:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            "PHILO-5-04 FINAL REHEARSAL ARTIFACT AUDIT — ERROR\n"
            f"RUN: {args.run.resolve()}\nERROR: {type(exc).__name__}: {exc}\n",
            encoding="utf-8",
        )
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
