"""The commit gate engine.

Single implementation of every structural rule the pre-commit hook
enforces: contract presence, stamped-fact verification, checkbox
validation, shipped-story detection, one-story-per-commit atomicity,
forward and reverse evidence pairing, and work-log capture
preconditions. The bash pre-commit shim only wires configuration and
invokes this engine; the verdict here is the verdict everywhere.

Contract v2 semantics (WLA-6-03): the contract must carry stamped
facts (branch, HEAD, index tree, staged sample, story). The gate
re-derives each fact and refuses on mismatch — the index tree IS the
freshness proof, so ``touch`` cannot refresh a stale contract and an
aborted commit's contract survives for the retry (post-commit, not
pre-commit, consumes it). Checkbox lines are verified against the rule
titles in the project's rules doc (canonical plus extensions); count-
only checking survives only as a fallback when no rules doc exists.

Structural semantics carried over from WLA-6-02: a story "ships" when
its ``**Status:**`` header flips from not-done in HEAD to any
``DONE_STATUSES`` synonym in the index (renames/reformats are not
flips); evidence numbers pair as integers; staged paths parse
NUL-separated; evidence deletions pass unless they orphan a story that
remains done in the index.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from .model import DONE_STATUSES
from .contract import (
    CONTRACT_REL,
    NO_BYPASSES_TITLE,
    box_title,
    contract_digest,
    contract_rule_titles,
    forced_full_tier,
    parse_contract_facts,
    roadmap_paths_staged,
    rules_doc_path,
    story_id_from_blob,
)
from .gitio import (
    config_value,
    current_branch,
    enabled_flag,
    head_blob,
    head_sha,
    in_rewrite_state,
    index_blob,
    roadmap_prefix,
    run_git,
    staged_entries,
    status_of,
    write_tree,
)
from .paths import read_text

BUNDLE_OK_REL = ".tmp/BUNDLE-OK.md"

_CHECKED_BOX_RE = re.compile(r"^- \[[xX]\]")
_UNCHECKED_BOX_RE = re.compile(r"^- \[ \]")
_CONSENT_RE = re.compile(r"^\*\*Work-log consent:\*\*[ \t]*yes([ \t]|$)", re.IGNORECASE | re.MULTILINE)


@dataclass
class GateFailure:
    rule: str
    message: str
    remediation: str
    details: list[str] = field(default_factory=list)


@dataclass
class GateResult:
    ok: bool
    root: Path
    failure: GateFailure | None
    expected_boxes: int
    checked_boxes: int
    tier: str = "full"
    contract_digest: str = ""
    declared_stories: list[str] = field(default_factory=list)
    staged: list[str] = field(default_factory=list)
    staged_stories: list[str] = field(default_factory=list)
    staged_evidence: list[str] = field(default_factory=list)
    shipped_stories: list[str] = field(default_factory=list)
    worklog_capture: bool = False


def _index_story_status_for(root: Path, phase_dir: str, num: int, story_re: re.Pattern[str]) -> tuple[str | None, str | None]:
    """Find the story file for (phase_dir, num) in the index; return (path, status)."""
    out = run_git(root, "ls-files", "-z", "--", phase_dir)
    if out is None:
        return None, None
    for path in out.split("\0"):
        if not path:
            continue
        m = story_re.match(path)
        if m and Path(path).parent.as_posix() == phase_dir and int(m.group(1)) == num:
            return path, status_of(index_blob(root, path))
    return None, None


def run_gate(
    root: Path,
    expected_boxes: int | None = None,
    work_log_enabled: bool | None = None,
) -> GateResult:
    result = _run_gate_inner(root, expected_boxes, work_log_enabled)
    from .events import emit

    if result.ok:
        emit(
            root, "gate_pass",
            detail={"stories": ", ".join(result.shipped_stories) or None},
        )
    else:
        emit(
            root, "gate_refusal",
            detail={"rule": result.failure.rule if result.failure else None},
        )
    return result


def _run_gate_inner(
    root: Path,
    expected_boxes: int | None = None,
    work_log_enabled: bool | None = None,
) -> GateResult:
    if expected_boxes is None:
        raw = config_value(root, "EXPECTED_BOXES") or os.environ.get("EXPECTED_BOXES") or "7"
        try:
            expected_boxes = int(raw)
        except ValueError:
            expected_boxes = 7
    if work_log_enabled is None:
        raw_enabled = config_value(root, "PMO_WORK_LOG_ENABLED")
        if raw_enabled is None:
            raw_enabled = os.environ.get("PMO_WORK_LOG_ENABLED")
        work_log_enabled = enabled_flag(raw_enabled)

    result = GateResult(
        ok=True,
        root=root,
        failure=None,
        expected_boxes=expected_boxes,
        checked_boxes=0,
    )

    def failed(rule: str, message: str, remediation: str, details: list[str] | None = None) -> GateResult:
        result.ok = False
        result.failure = GateFailure(rule, message, remediation, details or [])
        return result

    contract_path = root / CONTRACT_REL
    bundle_ok_path = root / BUNDLE_OK_REL

    # 1. Contract exists.
    if not contract_path.is_file():
        return failed(
            "contract-missing",
            "Missing .tmp/CONTRACT.md — commit blocked.",
            f"Run `dw contract new` after staging, verify each rule, and flip every box to [x]. "
            f"The contract is archived and cleared after the commit is created.",
        )

    contract_text = read_text(contract_path)
    result.contract_digest = contract_digest(contract_text)

    # 2. Stamped facts present and true. The index tree is the freshness
    #    proof; mtime plays no role.
    facts = parse_contract_facts(contract_text)
    if facts is None:
        return failed(
            "contract-facts-missing",
            ".tmp/CONTRACT.md carries no stamped facts block (Branch / HEAD / Index-tree).",
            "Regenerate the contract with `dw contract new` after staging.",
        )

    result.declared_stories = list(facts["story_ids"])  # type: ignore[arg-type]

    # Tier: the gate decides the required tier mechanically. A commit
    # that touches the roadmap tree (which includes every story flip)
    # requires the full contract; projects can force full everywhere
    # with PMO_CONTRACT_TIER=full.
    result.tier = str(facts.get("tier", "full")).strip().lower() or "full"
    if result.tier not in {"full", "short"}:
        return failed(
            "contract-tier-mismatch",
            f"Unknown contract tier {result.tier!r} (expected full or short).",
            "Regenerate with `dw contract new --force`.",
        )
    if result.tier == "short":
        if roadmap_paths_staged(root):
            return failed(
                "contract-tier-mismatch",
                "Short-form contract rejected — staged changes touch the roadmap tree, which requires the full contract.",
                "Re-run `dw contract new --force` (auto-tier picks full) and certify the full rule set.",
            )
        if forced_full_tier(root):
            return failed(
                "contract-tier-mismatch",
                "Short-form contract rejected — this project requires the full contract (PMO_CONTRACT_TIER=full).",
                "Re-run `dw contract new --force --tier full` and certify the full rule set.",
            )

    actual_tree = write_tree(root) or "unknown"
    if facts["index_tree"] != actual_tree:
        return failed(
            "contract-index-tree-mismatch",
            f"Stale contract — stamped index tree {facts['index_tree']} does not match the staged index {actual_tree}.",
            "The staged index changed since the contract was written (touching the file cannot "
            "refresh it). Re-run `dw contract new --force` after finalizing the stage.",
        )

    actual_head = head_sha(root) or "none"
    if facts["head"] != actual_head:
        return failed(
            "contract-head-mismatch",
            f"Stale contract — stamped HEAD {facts['head']} does not match current HEAD {actual_head}.",
            "History moved since the contract was written. Re-run `dw contract new --force` and re-certify.",
        )

    actual_branch = current_branch(root)
    if facts["branch"] != actual_branch:
        return failed(
            "contract-branch-mismatch",
            f"Contract was written for branch {facts['branch']!r} but the commit is on {actual_branch!r}.",
            "Re-run `dw contract new --force` on the branch that will carry this commit.",
        )

    staged_set = {path for _s, path, _o in staged_entries(root)}
    for sample_path in facts["staged_sample"]:  # type: ignore[union-attr]
        if sample_path not in staged_set:
            return failed(
                "contract-sample-mismatch",
                f"Contract staged-file sample names {sample_path!r}, which is not in the staged index.",
                "The sample must reflect reality. Re-run `dw contract new --force` after staging.",
            )

    # Mechanical tests-ran discharge: the referenced captured run must
    # exist in the staged evidence with exit code 0.
    tests_capture = facts.get("tests_capture")
    if tests_capture:
        from .evidence import find_captured_run, latest_passing_capture

        ref = str(tests_capture)
        cap_path, _, cap_ts = ref.partition("#")
        blob = index_blob(root, cap_path)
        if blob is None:
            return failed(
                "contract-tests-capture-mismatch",
                f"Tests-ran capture references {cap_path!r}, which is not in the staged index.",
                "Stage the evidence file carrying the captured run, or regenerate the contract.",
            )
        run = find_captured_run(blob, cap_ts) if cap_ts else latest_passing_capture(blob)
        if run is None:
            return failed(
                "contract-tests-capture-mismatch",
                f"No captured run {cap_ts or '(passing)'} found in staged {cap_path}.",
                "Re-run `dw evidence capture`, stage the evidence, and regenerate the contract.",
            )
        if run["exit_code"] != 0:
            return failed(
                "contract-tests-capture-mismatch",
                f"Referenced captured run {cap_path}#{run['timestamp']} exited {run['exit_code']}, not 0.",
                "Tests must pass to discharge the rule mechanically; fix them and re-capture.",
            )

    # 3. No unchecked boxes.
    unchecked = [
        f"{i}: {line}"
        for i, line in enumerate(contract_text.splitlines(), start=1)
        if _UNCHECKED_BOX_RE.match(line)
    ]
    if unchecked:
        return failed(
            "contract-unchecked",
            ".tmp/CONTRACT.md still has unchecked items.",
            "Flip every '- [ ]' to '- [x]' only after honestly verifying each rule.",
            details=unchecked,
        )

    # 4. Checkbox verification. With a rules doc: every checked box must
    #    match a known rule title and every known rule must be checked.
    #    Without one: legacy count check.
    checked_lines = [line for line in contract_text.splitlines() if _CHECKED_BOX_RE.match(line)]
    result.checked_boxes = len(checked_lines)
    known_titles = contract_rule_titles(root)
    if result.tier == "short":
        # Short form: the no-bypass rule is the whole checked surface.
        result.expected_boxes = 1
        allowed = set(known_titles or []) | {NO_BYPASSES_TITLE}
        seen_titles = []
        for line in checked_lines:
            title = box_title(line)
            if title is None or title not in allowed:
                return failed(
                    "contract-unknown-box",
                    f"Checked box does not correspond to any known rule: {line.strip()!r}",
                    "Short-form contracts carry the No bypasses. rule; regenerate with `dw contract new --force`.",
                )
            seen_titles.append(title)
        if NO_BYPASSES_TITLE not in seen_titles:
            return failed(
                "contract-missing-box",
                f"Short-form contract is missing the required box: {NO_BYPASSES_TITLE}",
                "Regenerate with `dw contract new --force` and certify the no-bypass rule.",
            )
    elif known_titles:
        result.expected_boxes = len(known_titles)
        expected_boxes = len(known_titles)
        seen: list[str] = []
        for line in checked_lines:
            title = box_title(line)
            if title is None or title not in known_titles:
                return failed(
                    "contract-unknown-box",
                    f"Checked box does not correspond to any known rule: {line.strip()!r}",
                    f"Boxes must match the rule titles in {rules_doc_path(root).relative_to(root)}"  # type: ignore[union-attr]
                    " §\"Contract template\" (canonical plus project extensions).",
                )
            seen.append(title)
        missing = [title for title in known_titles if title not in seen]
        if missing:
            return failed(
                "contract-missing-box",
                f"Contract is missing required rule box(es): {', '.join(missing)}",
                "Regenerate with `dw contract new --force` to pick up the full rule set, then certify each box.",
            )
    elif result.checked_boxes < expected_boxes:
        return failed(
            "contract-boxes",
            f".tmp/CONTRACT.md has only {result.checked_boxes}/{expected_boxes} required [x] checkboxes.",
            "Complete the contract template; project extensions may raise the count via EXPECTED_BOXES.",
        )

    # Work-log capture preconditions (reported even when no stories staged).
    result.worklog_capture = bool(
        work_log_enabled and _CONSENT_RE.search(contract_text) and not in_rewrite_state(root)
    )

    # Structural checks are scoped to the actual roadmap tree.
    entries = staged_entries(root)
    result.staged = [path for _status, path, _old in entries]

    prefix = roadmap_prefix(root)
    if prefix is None:
        return result

    story_re = re.compile(rf"^{re.escape(prefix)}[^/]+/phase-[^/]+/story-(\d+)-.*\.md$")
    evidence_re = re.compile(rf"^{re.escape(prefix)}[^/]+/phase-[^/]+/evidence-story-(\d+)\.md$")

    story_entries: list[tuple[str, str, str | None, int]] = []
    evidence_entries: list[tuple[str, str, int]] = []
    for status, path, old_path in entries:
        m = story_re.match(path)
        if m:
            story_entries.append((status, path, old_path, int(m.group(1))))
            result.staged_stories.append(path)
        m = evidence_re.match(path)
        if m:
            evidence_entries.append((status, path, int(m.group(1))))
            result.staged_evidence.append(path)
        if status == "R" and old_path:
            m_old = evidence_re.match(old_path)
            if m_old:
                evidence_entries.append(("D", old_path, int(m_old.group(1))))

    # 5. Shipped-story detection: HEAD status vs index status, shared vocabulary.
    shipped_ids: list[str] = []
    for status, path, old_path, _num in story_entries:
        if status == "D":
            continue
        blob = index_blob(root, path)
        new_status = status_of(blob)
        if new_status not in DONE_STATUSES:
            continue
        head_source = old_path if (status == "R" and old_path) else path
        old_status = status_of(head_blob(root, head_source))
        if old_status not in DONE_STATUSES:
            result.shipped_stories.append(path)
            sid = story_id_from_blob(blob)
            if sid:
                shipped_ids.append(sid)

    shipped_keys = {
        (Path(p).parent.as_posix(), int(story_re.match(p).group(1)))  # type: ignore[union-attr]
        for p in result.shipped_stories
    }

    # 6. Atomicity: one shipped story per commit unless BUNDLE-OK exists.
    if len(result.shipped_stories) > 1 and not bundle_ok_path.is_file():
        return failed(
            "atomicity",
            f"Atomicity violation — {len(result.shipped_stories)} stories flipped to done in one commit.",
            "Rule: one PR per story. To bundle intentionally, write .tmp/BUNDLE-OK.md "
            "with a one-line rationale (archived and cleared after the commit is created).",
            details=[f"shipped: {p}" for p in result.shipped_stories],
        )

    # 7. Story declaration: every flipped story ID must be declared in the
    #    contract's Story fact (it feeds the PMO-Story trailer).
    undeclared = [sid for sid in shipped_ids if sid not in result.declared_stories]
    if undeclared:
        return failed(
            "contract-story-mismatch",
            f"Story flip(s) not declared in the contract's Story fact: {', '.join(undeclared)}.",
            "Re-run `dw contract new --force` (it detects flipped stories) or pass --story explicitly.",
        )

    # 8. Forward pairing: each shipped story ships its evidence in this commit.
    staged_evidence_present = {
        (Path(p).parent.as_posix(), num)
        for status, p, num in evidence_entries
        if status != "D"
    }
    for path in result.shipped_stories:
        phase_dir = Path(path).parent.as_posix()
        num = int(story_re.match(path).group(1))  # type: ignore[union-attr]
        if (phase_dir, num) not in staged_evidence_present:
            expected_name = f"{phase_dir}/evidence-story-{num:02d}.md"
            return failed(
                "evidence-missing",
                f"Evidence missing — story {path} flipped to done but {expected_name} is not in this commit.",
                "A story flipping to done must ship its evidence file in the same commit "
                "(unpadded numbering is accepted).",
            )

    # 9. Reverse pairing: evidence appears/disappears only in legal states.
    for status, path, num in evidence_entries:
        phase_dir = Path(path).parent.as_posix()
        story_path, story_status = _index_story_status_for(root, phase_dir, num, story_re)
        if status == "D":
            if story_path is not None and story_status in DONE_STATUSES:
                return failed(
                    "evidence-deletion-orphans-story",
                    f"Evidence deletion blocked — deleting {path} would orphan done story {story_path}.",
                    "Regress or remove the story in the same commit, or keep its evidence.",
                )
            continue
        if status == "A":
            if (phase_dir, num) not in shipped_keys:
                return failed(
                    "orphan-evidence",
                    f"Orphan evidence — {path} added but no story-{num}-*.md in this phase "
                    "flipped to done in this commit.",
                    "Evidence files appear only when their story ships.",
                )
            continue
        # Modified (or rename target) evidence: legal while its story is done in the index.
        if (phase_dir, num) in shipped_keys:
            continue
        if story_path is None or story_status not in DONE_STATUSES:
            return failed(
                "orphan-evidence",
                f"Orphan evidence — {path} changed but its story is not done in this commit's index.",
                "Amend evidence only for a story that is (or is flipping) done.",
            )

    return result


# ── rendering ────────────────────────────────────────────────────────

_BAR = "━" * 68

_RULES_REMINDER = """Before this commit lands, certify in .tmp/CONTRACT.md that you followed:

  1. Evidence, not vibes — claimed work has on-disk command output.
  2. Master docs updated in this same commit (story header,
     current-phase-status, project README, BACKLOG/CHANGELOG).
  3. Tests actually ran via the project's documented scripts.
  4. Greenfield discipline (no migrations / shims, where applicable).
  5. No --no-verify, no unauthorized Co-Authored-By, no scope creep.
  6. If a story flipped to "done", evidence-story-*.md ships with it.
  7. One PR per story (or bundling documented).

Generate the contract with stamped facts after staging:

  .githooks/dw contract new"""


def _rules_doc(root: Path) -> str:
    doc = rules_doc_path(root)
    return str(doc.relative_to(root)) if doc else "pm/roadmap/PMO-CONTRACT.md"


def render_gate_failure(result: GateResult) -> str:
    failure = result.failure
    if failure is None:
        return ""
    lines = [_BAR, "PMO HYGIENE GATE — dw gate", _BAR]
    if failure.rule.startswith("contract-"):
        lines.append(_RULES_REMINDER)
        lines.append("")
        lines.append(f"  Full rules: {_rules_doc(result.root)} §\"Contract template\"")
        lines.append("")
    lines.append(f"✗ {failure.message}")
    for detail in failure.details:
        lines.append(f"    {detail}")
    lines.append(f"  To proceed: {failure.remediation}")
    if failure.rule in {"contract-missing", "contract-facts-missing"}:
        # Copy-pasteable template with live facts and the project's
        # actual rule set (canonical plus extensions).
        try:
            from .contract import build_contract

            lines.append("")
            lines.append("  Contract for this staging state (or just run `.githooks/dw contract new`):")
            lines.append("")
            for template_line in build_contract(result.root).splitlines():
                lines.append(f"    {template_line}")
        except Exception:
            pass
    lines.append(_BAR)
    return "\n".join(lines) + "\n"


def render_gate_porcelain(result: GateResult) -> str:
    lines = [
        f"gate={'pass' if result.ok else 'fail'}",
        f"expected_boxes={result.expected_boxes}",
        f"checked_boxes={result.checked_boxes}",
        f"shipped_count={len(result.shipped_stories)}",
        f"worklog_capture={'yes' if result.worklog_capture else 'no'}",
        f"tier={result.tier}",
        f"contract_digest={result.contract_digest or 'none'}",
    ]
    lines.extend(f"declared_story={sid}" for sid in result.declared_stories)
    lines.extend(f"staged={p}" for p in result.staged)
    lines.extend(f"staged_story={p}" for p in result.staged_stories)
    lines.extend(f"staged_evidence={p}" for p in result.staged_evidence)
    lines.extend(f"shipped_story={p}" for p in result.shipped_stories)
    if result.failure is not None:
        lines.append(f"rule={result.failure.rule}")
        lines.append(f"message={result.failure.message}")
        lines.append(f"remediation={result.failure.remediation}")
    return "\n".join(lines) + "\n"
