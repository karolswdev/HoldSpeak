"""Contract v2: generation, fact stamping, parsing, digest, trailers.

A v2 contract carries a machine-verifiable facts block — branch, HEAD,
``git write-tree`` index tree, the staged file sample, and the story
ID(s) it covers. ``dw contract new`` stamps the facts; the gate
re-derives each one at commit time and refuses on any mismatch. The
index tree IS the freshness proof: a contract written for a different
staging state is stale by definition, and ``touch`` cannot refresh it.

The required checkbox set comes from the project's rules doc
(``PMO-CONTRACT.md`` §"Contract template" fenced block), so project
extension boxes are verified exactly like the canonical seven. When no
rules doc exists the embedded canonical set applies.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .model import DONE_STATUSES, STORY_ID_RE, die
from .gitio import (
    config_value,
    current_branch,
    head_blob,
    head_sha,
    index_blob,
    roadmap_prefix,
    staged_entries,
    status_of,
    write_tree,
)
from .paths import read_text, template_dir, write_text

CONTRACT_REL = ".tmp/CONTRACT.md"
STAGED_SAMPLE_LIMIT = 20

# Canonical rule boxes — the embedded fallback when no rules doc exists.
CANONICAL_BOXES = [
    "- [ ] **Evidence, not vibes.** Claimed work has on-disk evidence (or a commit-message pointer to the actual output I read).",
    "- [ ] **Master docs updated.** Story header status, current-phase-status table, and any project-canon docs touched by this story are updated in this same commit.",
    "- [ ] **Tests ran.** I ran the relevant tests via the project's documented scripts and read the output. Type-check is not validation.",
    "- [ ] **Greenfield discipline (if applicable).** I did not add migration ceremony, compat shims, or backwards-compat hacks where the project is greenfield.",
    "- [ ] **No bypasses.** No `--no-verify`, no unauthorized `Co-Authored-By`, no scope creep beyond what the user asked.",
    "- [ ] **Story → evidence pairing.** If any story flipped to `done`, its `evidence-story-{n}.md` ships in this commit.",
    "- [ ] **One PR per story.** This commit maps to one story (or atomic chunk), or the bundling is documented.",
]

_BOX_LINE_RE = re.compile(r"^- \[[ xX]\] \*\*(.+?\.?)\*\*")
_FACT_RES = {
    "branch": re.compile(r"^\*\*Branch:\*\*\s*(.+)$", re.MULTILINE),
    "head": re.compile(r"^\*\*HEAD:\*\*\s*(.+)$", re.MULTILINE),
    "index_tree": re.compile(r"^\*\*Index-tree:\*\*\s*(.+)$", re.MULTILINE),
    "story": re.compile(r"^\*\*Story:\*\*\s*(.+)$", re.MULTILINE),
    "tests_capture": re.compile(r"^\*\*Tests-ran capture:\*\*\s*(.+)$", re.MULTILINE),
    "tier": re.compile(r"^\*\*Tier:\*\*\s*(.+)$", re.MULTILINE),
}
TESTS_RAN_TITLE = "Tests ran."
NO_BYPASSES_TITLE = "No bypasses."
_SAMPLE_HEADER_RE = re.compile(r"^\*\*Staged files \(sample\):\*\*\s*$")
_MORE_MARKER_RE = re.compile(r"^- … \(\+\d+ more\)$")
_HEADING_ID_RE = re.compile(r"^#\s+(\S+)\s+[-—]")


def rules_doc_path(root: Path) -> Path | None:
    for candidate in ("pm/roadmap/PMO-CONTRACT.md", "pmo-roadmap/templates/PMO-CONTRACT.md"):
        path = root / candidate
        if path.is_file():
            return path
    return None


def contract_box_lines(root: Path) -> list[str] | None:
    """Extract the required box lines from the rules doc's template fence.

    Returns the unchecked ``- [ ] **Title.** ...`` lines from the first
    fenced block after the "Contract template" heading, or None when no
    rules doc (or no fence) is available.
    """
    doc = rules_doc_path(root)
    if doc is None:
        return None
    in_section = False
    in_fence = False
    boxes: list[str] = []
    for line in read_text(doc).splitlines():
        if line.startswith("#") and "contract template" in line.lower():
            in_section = True
            continue
        if not in_section:
            continue
        if line.startswith("#") and not in_fence:
            # Next section heading without a template fence found yet.
            break
        if line.startswith("```"):
            if in_fence and boxes:
                break
            in_fence = not in_fence
            continue
        if in_fence and _BOX_LINE_RE.match(line):
            boxes.append(re.sub(r"^- \[[xX]\]", "- [ ]", line))
    return boxes or None


def contract_rule_titles(root: Path) -> list[str] | None:
    boxes = contract_box_lines(root)
    if boxes is None:
        return None
    titles = []
    for line in boxes:
        m = _BOX_LINE_RE.match(line)
        if m:
            titles.append(m.group(1).strip())
    return titles or None


def box_title(line: str) -> str | None:
    m = _BOX_LINE_RE.match(line)
    return m.group(1).strip() if m else None


def story_id_from_blob(content: str | None) -> str | None:
    if not content:
        return None
    for line in content.splitlines():
        m = _HEADING_ID_RE.match(line)
        if m and STORY_ID_RE.match(m.group(1)):
            return m.group(1)
        if line.strip():
            break
    return None


def detect_story_ids(root: Path) -> tuple[list[str], list[str]]:
    """Return (flipped_ids, touched_ids) for staged roadmap stories.

    Flipped = status went from not-done in HEAD to done in the index.
    Touched = any staged story file whose heading carries a story ID.
    """
    prefix = roadmap_prefix(root)
    if prefix is None:
        return [], []
    story_re = re.compile(rf"^{re.escape(prefix)}[^/]+/phase-[^/]+/story-(\d+)-.*\.md$")
    flipped: list[str] = []
    touched: list[str] = []
    for status, path, old_path in staged_entries(root):
        if status == "D" or not story_re.match(path):
            continue
        blob = index_blob(root, path)
        story_id = story_id_from_blob(blob)
        if story_id and story_id not in touched:
            touched.append(story_id)
        new_status = status_of(blob)
        if new_status not in DONE_STATUSES:
            continue
        head_source = old_path if (status == "R" and old_path) else path
        if status_of(head_blob(root, head_source)) not in DONE_STATUSES:
            if story_id and story_id not in flipped:
                flipped.append(story_id)
    return flipped, touched


def collect_facts(root: Path) -> dict[str, object]:
    staged = [path for _s, path, _o in staged_entries(root)]
    flipped, touched = detect_story_ids(root)
    return {
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "branch": current_branch(root),
        "head": head_sha(root) or "none",
        "index_tree": write_tree(root) or "unknown",
        "staged": staged,
        "flipped_story_ids": flipped,
        "touched_story_ids": touched,
    }


def _template_header() -> str:
    templates = template_dir()
    if templates and (templates / "CONTRACT.md.tmpl").exists():
        return read_text(templates / "CONTRACT.md.tmpl")
    return DEFAULT_TEMPLATE


def roadmap_paths_staged(root: Path) -> bool:
    prefix = roadmap_prefix(root)
    if prefix is None:
        return False
    for _status, path, old_path in staged_entries(root):
        if path.startswith(prefix) or (old_path and old_path.startswith(prefix)):
            return True
    return False


def forced_full_tier(root: Path) -> bool:
    raw = config_value(root, "PMO_CONTRACT_TIER")
    if raw is None:
        raw = os.environ.get("PMO_CONTRACT_TIER")
    return (raw or "").strip().lower() == "full"


def resolve_tier(root: Path, tier: str = "auto") -> str:
    """auto → short only for non-roadmap commits in projects that allow it."""
    tier = tier.strip().lower()
    if tier == "full":
        return "full"
    touches_roadmap = roadmap_paths_staged(root)
    if tier == "short":
        if touches_roadmap:
            die("short-form contract not allowed: staged changes touch the roadmap tree")
        if forced_full_tier(root):
            die("short-form contract not allowed: this project requires the full contract (PMO_CONTRACT_TIER=full)")
        return "short"
    # auto
    if touches_roadmap or forced_full_tier(root):
        return "full"
    return "short"


DEFAULT_TEMPLATE = """# Commit Contract

**Generated:** {{GENERATED}}
**Branch:** {{BRANCH}}
**HEAD:** {{HEAD}}
**Index-tree:** {{INDEX_TREE}}
**Story:** {{STORY}}
**Tier:** {{TIER}}
**Staged files (sample):**
{{STAGED_SAMPLE}}

I certify, for this commit:

{{BOXES}}

Methodology: pm/roadmap/roadmap-builder.md
Rules canon: {{RULES_DOC}}

## Work-log consent

**Work-log consent:** {{CONSENT}}

**Work-log reasons:**
{{REASONS}}

**Work-log exclusions:**
- none
"""


def resolve_tests_capture(root: Path, reference: str) -> str:
    """Resolve a Tests-ran capture reference against the staged index.

    Accepts ``<evidence-path>`` (newest passing run) or
    ``<evidence-path>#<timestamp>``; returns the canonical
    ``path#timestamp`` form. Dies when the evidence is not staged, the
    run is absent, or its exit code is nonzero — the same checks the
    gate re-runs at commit time.
    """
    from .evidence import find_captured_run, latest_passing_capture

    path_part, _, ts_part = reference.partition("#")
    blob = index_blob(root, path_part)
    if blob is None:
        die(f"tests capture reference is not in the staged index: {path_part} (stage the evidence first)")
    run = find_captured_run(blob, ts_part) if ts_part else latest_passing_capture(blob)
    if run is None:
        detail = f" with timestamp {ts_part}" if ts_part else " with exit code 0"
        die(f"no captured run{detail} found in staged {path_part}")
    if run["exit_code"] != 0:
        die(f"captured run {path_part}#{run['timestamp']} exited {run['exit_code']}, not 0")
    return f"{path_part}#{run['timestamp']}"


def build_contract(
    root: Path,
    story_ids: list[str] | None = None,
    consent: str = "no",
    reasons: list[str] | None = None,
    tests_capture: str | None = None,
    tier: str = "auto",
) -> str:
    resolved_tier = resolve_tier(root, tier)
    if tests_capture and resolved_tier == "short":
        # Discharging "Tests ran." only exists in the full rule set.
        resolved_tier = "full"
    facts = collect_facts(root)
    declared = list(story_ids) if story_ids else []
    for sid in facts["flipped_story_ids"]:  # type: ignore[union-attr]
        if sid not in declared:
            declared.append(sid)
    if not declared:
        for sid in facts["touched_story_ids"]:  # type: ignore[union-attr]
            if sid not in declared:
                declared.append(sid)

    staged: list[str] = facts["staged"]  # type: ignore[assignment]
    sample_lines = [f"- {path}" for path in staged[:STAGED_SAMPLE_LIMIT]]
    if len(staged) > STAGED_SAMPLE_LIMIT:
        sample_lines.append(f"- … (+{len(staged) - STAGED_SAMPLE_LIMIT} more)")
    if not sample_lines:
        sample_lines = ["- (no files staged)"]

    boxes = contract_box_lines(root) or list(CANONICAL_BOXES)
    if resolved_tier == "short":
        # Short form: stamped facts plus the no-bypass rule only.
        short = [line for line in boxes if box_title(line) == NO_BYPASSES_TITLE]
        boxes = short or [
            f"- [ ] **{NO_BYPASSES_TITLE}** No `--no-verify`, no unauthorized "
            "`Co-Authored-By`, no scope creep beyond what the user asked."
        ]
    doc = rules_doc_path(root)
    reason_lines = [f"- {reason}" for reason in (reasons or [])] or ["- n/a"]

    text = _template_header()
    if "{{TIER}}" not in text:
        # Older custom template: keep the tier fact machine-readable anyway.
        text = text.replace("{{STORY}}", "{{STORY}}\n**Tier:** {{TIER}}", 1) if "{{STORY}}" in text else text
    replacements = {
        "{{GENERATED}}": str(facts["generated"]),
        "{{BRANCH}}": str(facts["branch"]),
        "{{HEAD}}": str(facts["head"]),
        "{{INDEX_TREE}}": str(facts["index_tree"]),
        "{{TIER}}": resolved_tier,
        "{{STORY}}": ", ".join(declared) if declared else "none",
        "{{STAGED_SAMPLE}}": "\n".join(sample_lines),
        "{{BOXES}}": "\n".join(boxes),
        "{{RULES_DOC}}": str(doc.relative_to(root)) if doc else "pm/roadmap/PMO-CONTRACT.md",
        "{{CONSENT}}": consent,
        "{{REASONS}}": "\n".join(reason_lines),
    }
    for token, value in replacements.items():
        text = text.replace(token, value)

    if tests_capture:
        canonical = resolve_tests_capture(root, tests_capture)
        marker = "**Staged files (sample):**"
        text = text.replace(marker, f"**Tests-ran capture:** {canonical}\n{marker}", 1)
        discharged = False
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith(f"- [ ] **{TESTS_RAN_TITLE}**"):
                lines[i] = (
                    f"- [x] **{TESTS_RAN_TITLE}** Discharged mechanically: captured run "
                    f"{canonical} (exit 0), re-verified by the gate at commit time."
                )
                discharged = True
                break
        if not discharged:
            die(f"cannot discharge tests-ran mechanically: no box titled {TESTS_RAN_TITLE!r} in the rule set")
        text = "\n".join(lines) + "\n"
    return text


def write_contract(
    root: Path,
    story_ids: list[str] | None = None,
    consent: str = "no",
    reasons: list[str] | None = None,
    force: bool = False,
    tests_capture: str | None = None,
    tier: str = "auto",
) -> Path:
    path = root / CONTRACT_REL
    if path.exists() and not force:
        die(f"contract already exists; pass --force to replace: {CONTRACT_REL}")
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text(path, build_contract(root, story_ids, consent, reasons, tests_capture, tier))
    from .events import emit

    emit(
        root, "contract_generated",
        detail={"stories": ", ".join(story_ids or []) or None},
    )
    return path


def parse_contract_facts(text: str) -> dict[str, object] | None:
    """Parse the stamped facts block; None when any core fact is absent."""
    facts: dict[str, object] = {}
    for key, pattern in _FACT_RES.items():
        m = pattern.search(text)
        if m:
            facts[key] = m.group(1).strip()
    if not {"branch", "head", "index_tree"}.issubset(facts):
        return None
    sample: list[str] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if _SAMPLE_HEADER_RE.match(line):
            for entry in lines[i + 1:]:
                if not entry.startswith("- "):
                    break
                if _MORE_MARKER_RE.match(entry) or entry == "- (no files staged)":
                    continue
                sample.append(entry[2:].strip())
            break
    facts["staged_sample"] = sample
    story_raw = str(facts.get("story", "none"))
    facts["story_ids"] = (
        [] if story_raw.lower() in {"none", ""} else [s.strip() for s in story_raw.split(",") if s.strip()]
    )
    return facts


def contract_digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def append_trailers(
    root: Path,
    message_file: Path,
    story_ids: list[str],
    digest: str,
    bundle: str | None = None,
) -> None:
    """Stamp PMO trailers onto the commit message (idempotent).

    ``bundle`` is the BUNDLE-OK rationale's first line; stamping it as
    a PMO-Bundle trailer makes the atomicity rule re-derivable from
    pushed history (docs/remote-verification.md).
    """
    trailers: list[str] = []
    if story_ids:
        trailers.extend(["--trailer", f"PMO-Story: {', '.join(story_ids)}"])
    trailers.extend(["--trailer", f"PMO-Contract-Digest: {digest}"])
    if bundle:
        trailers.extend(["--trailer", f"PMO-Bundle: {bundle}"])
    try:
        subprocess.check_call(
            [
                "git", "-C", str(root), "interpret-trailers",
                "--in-place", "--if-exists", "replace", *trailers,
                str(message_file),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    except (OSError, subprocess.CalledProcessError):
        pass
    # Manual fallback: append a trailer block.
    text = read_text(message_file).rstrip("\n")
    block = []
    if story_ids:
        block.append(f"PMO-Story: {', '.join(story_ids)}")
    block.append(f"PMO-Contract-Digest: {digest}")
    if bundle:
        block.append(f"PMO-Bundle: {bundle}")
    body = text + "\n\n" + "\n".join(line for line in block if line not in text) + "\n"
    write_text(message_file, body)
