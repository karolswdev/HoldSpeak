"""HS-200-05 walk runner: physical voice, correction and custody.

The automatable half of HS-200-05 is proven by
`tests/unit/test_phase200_voice_custody.py` and
`tests/integration/test_phase200_voice_custody.py`. Six things a test cannot
prove need his hand and his Mac: a real microphone, the hotkey, a DENIED
permission dialog, an interruption, a replay he watches change, and a restart
of the hub. This runner takes the read-only census at both ends of that walk,
shoots the Speak faces, prints the script for his hand, and asserts the write
set his own beats should have produced.

THE LIVE LAWS (Article IV — the runner writes nothing):

1. THE RUNNER IS READ-ONLY. Every write it could make is DENIED by a
   fail-closed guard and printed. It never speaks, never presses `Talk`, never
   opens the mic, never teaches or forgets a correction, never replays a row,
   never clears or deletes, never delivers, never restarts his hub.
2. THE PRODUCT WRITES WHAT HIS OWN HAND PRODUCES: one journal row per
   utterance HE speaks (retention-pruned as always), one correction row from
   HIS `Teach`, the `taught_from` flag and `corrections_applied` the product
   sets itself. The runner asserts that write set before and after and fails
   on any other delta.
3. NO HARDCODED TOKENS. The hub token is read from `--hub` and REDACTED
   (`token=<redacted>`) in every line this runner prints or writes.
4. FACE-DRIVEN. The read-only beats drive the real faces; the census reads the
   product's own routes.
5. NO BUNDLE, NO WALK. A hub serving no React build is refused (the 173 law) —
   a hollow walk proves nothing.
6. STANDALONE. Not collected by pytest. Never run beside the parallel suite
   (CPU starvation reads as a discovery hang).

Usage:

  # boot an ISOLATED hub first (never his own installation for a rehearsal):
  #   HOME=$(mktemp -d) uv run holdspeak web --no-open

  # read-only: the census, the faces at both widths, then the attended script
  # printed for him (the runner stops).
  uv run python tests/e2e/live200_voice_walk.py \\
      --hub "http://127.0.0.1:PORT/?token=TOKEN"

  # attended: the same, then a PAUSE on stdin while he walks beats 0-6, then
  # the after-census and the decision table.
  uv run python tests/e2e/live200_voice_walk.py \\
      --hub "http://127.0.0.1:PORT/?token=TOKEN" --attended

  # attended, answers supplied instead of stdin (development / proof):
  #   --answers "<utterances he spoke>,<corrections he taught 0|1>"
  uv run python tests/e2e/live200_voice_walk.py \\
      --hub "http://127.0.0.1:PORT/?token=TOKEN" --attended --answers "3,1"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

# -- pytest collection guard --
collect_ignore_glob = ["live200_voice_walk.py"]


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = (
    REPO / "pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-05-shots"
)

VIEWPORTS = [
    {"width": 1440, "height": 900, "suffix": "1440"},
    {"width": 393, "height": 852, "suffix": "393"},
]

WING_LABELS = ["SPEAK", "JOURNAL", "BLOCKS", "LEARNED"]

#: The mic's own phase vocabulary (web/src/pages/cores/dictation/shared.ts).
MIC_PHASES = {"CLOSED", "SUSPENDED", "OPEN", "SEGMENTING", "HELD"}


# ---------------------------------------------------------------------------
# Token redaction (law 3)
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"(token=)[^&\s\"']+")
#: His home directory, so a route's own error detail (`model file missing at
#: /Users/<him>/...`) cannot carry his filesystem into a committed artifact.
_HOME = str(Path.home())


def _redact(text: str) -> str:
    """Replace every `token=...` with `token=<redacted>`, and his home with `~`.

        _redact("http://127.0.0.1:8080/?token=abc123")
            -> "http://127.0.0.1:8080/?token=<redacted>"
        _redact("no token here") -> "no token here"
    """
    out = _TOKEN_RE.sub(r"\1<redacted>", text or "")
    return out.replace(_HOME, "~") if _HOME else out


def _say(text: str = "") -> None:
    """Print, always redacted."""
    print(_redact(text))


# ---------------------------------------------------------------------------
# Write guard (fail-closed: the RUNNER writes nothing)
# ---------------------------------------------------------------------------

_DENIALS: dict[str, str] = {
    "press_talk": "never presses Talk (one mic authority, and it is his)",
    "open_mic": "never opens the mic (a grant is his to give)",
    "land_utterance": "never lands an utterance (his voice speaks, not the runner)",
    "deliver_text": "never posts to /api/dictation/remote (typing is an effect)",
    "press_hotkey": "never sends the hotkey (a keystroke into his focused app)",
    "grant_permission": "never answers a microphone permission dialog",
    "deny_permission": "never answers a microphone permission dialog",
    "teach_correction": "never teaches a correction (his hand teaches)",
    "forget_correction": "never presses Forget",
    "replay_journal_row": "never presses Replay",
    "correct_journal_row": "never posts to /journal/{id}/correct",
    "clear_journal": "never presses Clear",
    "delete_journal_row": "never opens or presses a row's Delete",
    "export_journal": "never presses Export",
    "enable_corrections": "never flips corrections_enabled (it reads and reports)",
    "restart_hub": "never restarts his hub (his process, his hand)",
    "dismiss_chair": "never clicks Continue later (dismissal persists = a write)",
    "seed": "never seeds his desk (a walk seeds nothing)",
}


def _write_allowed(
    operation: str | None,
    context: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Decide whether a write operation is allowed in this walk.

    Returns (allowed: bool, reason: str). NOTHING is allowed: the walk's only
    writes are the product's, produced by the owner's own hand.

    Decision table:
        _write_allowed("press_talk")      -> (False, "never presses Talk ...")
        _write_allowed("press_hotkey")    -> (False, "never sends the hotkey ...")
        _write_allowed("restart_hub")     -> (False, "never restarts his hub ...")
        _write_allowed("unknown")         -> (False, "unknown operation denied by default")
        _write_allowed("")                -> (False, "empty operation denied")
        _write_allowed(None)              -> (False, "null operation denied")
    """
    del context
    if not operation:
        return False, (
            "empty operation denied" if operation == "" else "null operation denied"
        )
    return False, _DENIALS.get(operation, "unknown operation denied by default")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class FaceFact:
    face: str
    field: str
    expected: str
    observed: str
    verdict: str
    why: str


@dataclass
class Beat:
    """One row of the walk's decision table."""

    beat: str
    expected: str
    observed: str = "---"
    write: str = "none"  # none | DENIED | HIS HAND
    verdict: str = "DATA"


@dataclass
class WalkReport:
    generated_at: str = ""
    hub_host: str = ""
    attended: bool = False
    viewports: list[dict] = field(default_factory=list)
    census_before: dict = field(default_factory=dict)
    census_after: dict = field(default_factory=dict)
    beats: list[dict] = field(default_factory=list)
    shots: list[dict] = field(default_factory=list)
    facts: list[dict] = field(default_factory=list)
    answers: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    surprises: list[str] = field(default_factory=list)
    defects: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Page helpers
# ---------------------------------------------------------------------------


def _settle(page: Any) -> None:
    page.evaluate("""() => {
        const anims = document.getAnimations();
        if (anims.length === 0) return;
        return Promise.race([
            Promise.all(anims.map(a => a.finished.catch(() => null))),
            new Promise(r => setTimeout(r, 2000)),
        ]);
    }""")
    page.wait_for_timeout(200)


def _shoot(page: Any, out_dir: Path, name: str, w: int, report: WalkReport) -> Path:
    _settle(page)
    path = out_dir / f"{name}-{w}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    win = page.locator(".desk-surface-window").first
    if win.count() > 0 and win.is_visible():
        win.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    if not path.exists() or path.stat().st_size <= 1_000:
        raise RuntimeError(f"Shot {path.name} missing or too small")
    report.shots.append({"name": path.name, "width": w})
    return path


_FETCH_JS = """async ([method, path, token]) => {
  const response = await fetch(path, {
    method,
    headers: {authorization: `Bearer ${token}`},
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("json")
    ? await response.json()
    : await response.text();
  return {status: response.status, payload};
}"""

#: The only HTTP verbs the runner may issue. Anything else is a write and the
#: guard refuses it before the request is built.
_READ_VERBS = {"GET", "HEAD"}


def _api(page: Any, method: str, path: str, token: str) -> dict[str, Any]:
    """Read one product route. A non-read verb is DENIED, not sent."""
    if method.upper() not in _READ_VERBS:
        _allowed, reason = _write_allowed(f"http_{method.lower()}")
        _say(f"        WRITE DENIED: {method} {path} -- {reason}")
        return {"status": 0, "payload": {}}
    return page.evaluate(_FETCH_JS, [method, path, token])


def _require_bundle(page: Any) -> None:
    """The 173 law: a hub with no React build makes every beat hollow."""
    if "React Web build is missing" in page.content():
        raise RuntimeError(
            "HUB SERVES NO BUNDLE: the web build is missing; every face beat "
            "would be hollow. Run `npm --prefix web run build` and restart the hub."
        )


def _note_chair(page: Any, report: WalkReport) -> None:
    """Report the first-value chair; NEVER dismiss it (a write)."""
    try:
        chair = page.locator(".chair")
        if chair.count() == 0:
            return
        chair.wait_for(timeout=5000)
        if chair.evaluate("el => el.classList.contains('chair-first-value')"):
            _allowed, reason = _write_allowed("dismiss_chair")
            report.surprises.append(
                f"first-value chair present on the desk; not dismissed ({reason})"
            )
            _say(f"        note: first-value chair present -- {reason}")
    except Exception:
        return


class ChairHoldsTheDesk(RuntimeError):
    """The first-value chair is the first thing his hand meets, and it is HIS.

    On a fresh installation the desk opens on the first-value chair (`VOICE
    TYPING · Dictate one sentence`), and no surface is reachable behind it.
    Getting past it means `Continue later` or completing the chair, and both
    are writes: the runner refuses and says so instead of timing out six times.
    """


def _open_speak(page: Any, report: WalkReport) -> None:
    page.evaluate(
        """([key]) => {
            sessionStorage.setItem(
              "hs.desk.staged-surface-open",
              JSON.stringify({key})
            );
        }""",
        ["dictate"],
    )
    page.reload(wait_until="load")
    _require_bundle(page)
    _note_chair(page, report)
    face = page.locator(".speak-face")
    try:
        face.wait_for(timeout=8000)
    except Exception:
        chair = page.locator(".chair.chair-first-value")
        if chair.count() > 0:
            _allowed, reason = _write_allowed("dismiss_chair")
            raise ChairHoldsTheDesk(
                "the first-value chair holds the desk; the Speak surface is "
                f"unreachable without a write ({reason})"
            ) from None
        raise
    _settle(page)


def _fact(report: WalkReport, face: str, fld: str, expected: str,
          observed: str, verdict: str, why: str) -> None:
    report.facts.append(
        asdict(FaceFact(face=face, field=fld, expected=expected,
                        observed=observed, verdict=verdict, why=why))
    )


# ---------------------------------------------------------------------------
# The census (read-only, both ends of the walk)
# ---------------------------------------------------------------------------


def _census(page: Any, token: str, report: WalkReport, label: str) -> dict:
    """Read the write set and the readiness. ZERO writes."""
    out: dict[str, Any] = {"label": label}

    journal = _api(page, "GET", "/api/dictation/journal?limit=200", token)
    if journal["status"] == 200 and isinstance(journal["payload"], dict):
        payload = journal["payload"]
        rows = payload.get("items") or []
        out["journal_count"] = int(payload.get("count", 0))
        out["journal_enabled"] = bool(payload.get("enabled", False))
        out["journal_retention"] = int(payload.get("retention", 0))
        sources: dict[str, int] = {}
        for row in rows:
            key = str(row.get("source") or "unknown")
            sources[key] = sources.get(key, 0) + 1
        out["journal_sources"] = sources
        out["journal_taught_from"] = sum(
            1 for row in rows if bool(row.get("taught_from") or row.get("corrected"))
        )
        out["journal_with_applied"] = sum(
            1 for row in rows if (row.get("corrections_applied") or [])
        )
    else:
        out["journal_count"] = None
        report.errors.append(
            f"census({label}): GET /api/dictation/journal -> {journal['status']}"
        )

    corrections = _api(page, "GET", "/api/dictation/corrections", token)
    if corrections["status"] == 200 and isinstance(corrections["payload"], dict):
        payload = corrections["payload"]
        out["corrections_size"] = int(payload.get("size", 0))
        out["corrections_enabled"] = bool(payload.get("enabled", False))
        out["correction_keys"] = [str(i.get("key", "")) for i in payload.get("items", [])]
        out["applied_total"] = sum(
            int(i.get("applied", 0) or 0) for i in payload.get("items", [])
        )
    else:
        out["corrections_size"] = None
        out["corrections_enabled"] = None
        out["applied_total"] = None
        report.errors.append(
            f"census({label}): GET /api/dictation/corrections -> {corrections['status']}"
        )

    readiness = _api(page, "GET", "/api/dictation/readiness", token)
    if readiness["status"] == 200 and isinstance(readiness["payload"], dict):
        payload = readiness["payload"]
        runtime = payload.get("runtime") or {}
        out["ready"] = bool(payload.get("ready", False))
        out["runtime_status"] = str(runtime.get("status", "unknown"))
        out["runtime_detail"] = str(runtime.get("detail", ""))[:120]
        out["engine_backend"] = str((payload.get("config") or {}).get("backend", "unknown"))
        out["egress_boundary"] = str(payload.get("egress_boundary", "unknown"))
    else:
        out["ready"] = None
        out["runtime_status"] = "unknown"
        report.errors.append(
            f"census({label}): GET /api/dictation/readiness -> {readiness['status']}"
        )

    # C1 custody: the runtime this census was taken against. A restart beat is
    # only meaningful if the process identity actually changed. Only the opaque
    # fields are read: `database_path` is on that payload and never leaves it.
    identity = _api(page, "GET", "/api/system/identity", token)
    if identity["status"] == 200 and isinstance(identity["payload"], dict):
        payload = identity["payload"].get("identity") or identity["payload"]
        out["process_pid"] = payload.get("pid")
        out["process_started_at"] = payload.get("process_start")
        out["database_id"] = payload.get("database_id")
        out["schema_loaded"] = payload.get("schema_version_loaded")
        out["backend_version"] = payload.get("backend_version")
    else:
        out["process_pid"] = None
        out["process_started_at"] = None
        report.surprises.append(
            f"census({label}): GET /api/system/identity -> {identity['status']}; "
            "the restart beat cannot be proven from the runtime identity"
        )

    _say(f"  census [{label}]: journal={out.get('journal_count')} "
         f"sources={out.get('journal_sources')} "
         f"corrections={out.get('corrections_size')} "
         f"applied={out.get('applied_total')} "
         f"pid={out.get('process_pid')} "
         f"runtime={out.get('runtime_status')}")
    return out


# ---------------------------------------------------------------------------
# The read-only face beats
# ---------------------------------------------------------------------------


def _beat_speak(page: Any, out_dir: Path, w: int, report: WalkReport) -> None:
    """R1: the Speak face — the transport, the one mic authority, the Details."""
    face = f"speak@{w}"
    _open_speak(page, report)

    wings = [
        t.strip().upper()
        for t in page.locator(".desk-wings-tabs [role=tab]").all_inner_texts()
    ]
    _fact(report, face, "wings", " ".join(WING_LABELS), " ".join(wings),
          "MATCH" if wings == WING_LABELS else "BOUNCE",
          "the four wings of the Speak surface")
    if wings != WING_LABELS:
        report.defects.append(f"SPEAK@{w}: wings {wings} != {WING_LABELS}")

    well_mics = page.locator(".speak-well .desk-mic").count()
    _fact(report, face, "well_mic_count", "0", str(well_mics),
          "MATCH" if well_mics == 0 else "BOUNCE",
          "ONE mic authority (Article IV.3): the well carries none")
    if well_mics != 0:
        report.defects.append(
            f"SPEAK@{w}: the utterance well carries {well_mics} mic(s)"
        )

    talk = page.get_by_role("button", name=re.compile("Talk"))
    _fact(report, face, "talk_present", ">= 1", str(talk.count()),
          "MATCH" if talk.count() >= 1 else "BOUNCE",
          "`Talk` is the face's one transport (the runner never presses it)")
    _allowed, reason = _write_allowed("press_talk")
    _say(f"        WRITE DENIED: press Talk -- {reason}")
    _allowed, reason = _write_allowed("open_mic")
    _say(f"        WRITE DENIED: open the mic -- {reason}")

    _shoot(page, out_dir, "speak-face", w, report)

    # The mic-ownership row lives behind > Details. Opening a disclosure is a
    # READ (watching is free).
    details = page.get_by_role("button", name=re.compile("Details"))
    if details.count() > 0:
        details.first.click()
        _settle(page)
        rows = page.locator(".speak-detail-row").all_inner_texts()
        mic_row = next((r for r in rows if r.strip().upper().startswith("MIC")), "")
        phase = mic_row.strip().upper().replace("MIC", "", 1).strip()
        _fact(report, face, "mic_ownership_phase", " | ".join(sorted(MIC_PHASES)),
              phase or "(absent)",
              "MATCH" if phase in MIC_PHASES else "BOUNCE",
              "AC2: the face names who owns the mic, one word")
        if phase not in MIC_PHASES:
            report.defects.append(
                f"SPEAK@{w}: the Details `Mic` row reads {phase!r}, "
                "not one of the mic phases"
            )
        _shoot(page, out_dir, "speak-details-mic", w, report)
    else:
        _fact(report, face, "mic_ownership_phase", "a Details fold", "(absent)",
              "BOUNCE", "AC2: the mic-ownership row could not be reached")
        report.defects.append(f"SPEAK@{w}: no Details disclosure on the Speak face")


def _beat_journal(page: Any, out_dir: Path, w: int, report: WalkReport) -> None:
    """R2: the Journal wing — his rows, their sources, and no runner write."""
    face = f"journal@{w}"
    _open_speak(page, report)
    page.get_by_role("tab", name="JOURNAL").click()
    _settle(page)

    for op in ("clear_journal", "delete_journal_row", "replay_journal_row",
               "export_journal", "correct_journal_row"):
        _allowed, reason = _write_allowed(op)
        _say(f"        WRITE DENIED: {op} -- {reason}")

    body = page.locator(".desk-surface-window").first.inner_text(timeout=10000)
    sources = sorted({
        token for token in ("HOTKEY", "BROWSER", "DICTATION", "DRY RUN")
        if token in body.upper()
    })
    _fact(report, face, "row_sources", "HOTKEY / BROWSER / DICTATION",
          ", ".join(sources) or "(no rows)", "DATA",
          "AC1: a hotkey dictation leaves a row tagged HOTKEY; the runner adds none")
    _shoot(page, out_dir, "speak-journal", w, report)


def _beat_learned(page: Any, out_dir: Path, w: int, report: WalkReport) -> None:
    """R3: the Learned wing — the rules and their honest APPLIED counts."""
    face = f"learned@{w}"
    _open_speak(page, report)
    page.get_by_role("tab", name="LEARNED").click()
    _settle(page)

    _allowed, reason = _write_allowed("forget_correction")
    _say(f"        WRITE DENIED: Forget -- {reason}")
    _allowed, reason = _write_allowed("teach_correction")
    _say(f"        WRITE DENIED: Teach -- {reason}")

    # `.speak-face` is the SPEAK wing's own root and is unmounted here; the
    # surface window is the container every wing shares.
    body = page.locator(".desk-surface-window").first.inner_text(timeout=10000)
    applied_tokens = re.findall(r"(\d+)\s+APPLIED", body.upper())
    _fact(report, face, "applied_tokens", "real firings only",
          ",".join(applied_tokens) or "(none)", "DATA",
          "AC4: `N APPLIED` counts retained journal rows that named the rule")
    _shoot(page, out_dir, "speak-learned", w, report)


# ---------------------------------------------------------------------------
# The attended script (his hand, his Mac)
# ---------------------------------------------------------------------------


ATTENDED_SCRIPT = """
=== HS-200-05 ATTENDED SCRIPT — the six beats only your hand can walk ===

Everything a test can carry is already green
(tests/unit/test_phase200_voice_custody.py,
 tests/integration/test_phase200_voice_custody.py).
These six need a real microphone, a real hotkey and a real restart.

Beat 0  READINESS.  On a FRESH installation the desk opens on the first-value
        chair (`VOICE TYPING - Dictate one sentence`) and no surface is
        reachable behind it; the runner will not answer it, because both
        `Continue later` and completing it are writes. Answer it yourself.
        Then, on the Speak face, read the engine row and the egress chip. If it
        says KEY NOT SET or the runtime is unavailable, STOP and pick a local
        engine first: every beat below would be hollow.
        -> the product writes nothing until your hand answers the chair.

Beat 1  THE HOTKEY, INTO A TARGET.  Put the caret in a real app (Notes, a
        terminal, an editor). Hold the dictation hotkey, say one sentence,
        release.
        -> the words appear IN THAT APP, and the Journal wing gains ONE row
           with source HOTKEY carrying that transcript.
        -> if the words land somewhere else, that is the defect to name.

Beat 2  DENIED PERMISSION.  Revoke microphone access for your browser
        (System Settings > Privacy & Security > Microphone), return to the
        Speak face and press `Talk`.
        -> the face names the refusal and the words you had typed in the well
           REMAIN EDITABLE. Retry / Copy / Keep as note are offered.
        -> the product writes NO journal row.
        Restore microphone access before beat 3.

Beat 3  SILENCE.  Press `Talk`, say nothing, release.
        -> the face says nothing was heard. No row, no error banner, no
           counter of zero.

Beat 4  INTERRUPTION MID-UTTERANCE.  Press `Talk`, begin a sentence, and
        while you are still speaking press `Talk` again (or start a meeting)
        so the mic is taken.
        -> the face names WHO has the microphone (the Details `Mic` row and
           the refusal token), and the partial words are not silently typed
           into whatever is focused.

Beat 5  ONE CORRECTION, THEN A REPLAY.  Open a journal row whose transcript
        has a word the mic got wrong. Teach the TEXT correction (heard ->
        said). Then press `Replay` on that same row.
        -> the replay shows the corrected words: the rule really fires.
        -> the Learned wing's `N APPLIED` does NOT move on a replay. A replay
           is a preview: it writes no journal row, so it cannot count as a
           firing. Confirm that reads right to you; if you want a replay to
           count, say so and it becomes a story.

Beat 6  RESTART.  Quit the hub (Ctrl-C in its terminal) and start it again on
        the SAME data root.
        -> the journal rows from beats 1-5 are all there.
        -> the correction from beat 5 is still listed AND still fires on the
           next utterance that contains the phrase.
        -> the `N APPLIED` count is the same number it was before the restart.

=== THE WALK QUESTION ===
Q  A delivery whose outcome is UNKNOWN (the typing adapter died mid-keystroke)
   parks as `delivery_pending` and is never retyped automatically; the words
   stay in the well for you to send again. Is "never automatically, always
   your hand" the right rule, or do you want a one-tap `Send again` on that
   receipt?

=== END OF SCRIPT ===
"""


def _ask(prompt: str, supplied: str | None) -> str:
    if supplied is not None:
        _say(f"  {prompt} {supplied}   (supplied via --answers)")
        return supplied
    _say(f"  {prompt} ")
    try:
        return input().strip()
    except EOFError:
        return ""


def _collect_answers(answers_flag: str | None, report: WalkReport) -> dict:
    """Pause for his hand, then read the two counts and the walk question."""
    supplied: list[str] = []
    if answers_flag:
        supplied = [a.strip() for a in answers_flag.split(",")]

    def _nth(i: int) -> str | None:
        return supplied[i] if i < len(supplied) else None

    _say(ATTENDED_SCRIPT)
    if answers_flag is None:
        _say("  >>> WALK THE BEATS NOW. Press RETURN here when you are done. <<<")
        try:
            input()
        except EOFError:
            pass

    spoken_raw = _ask(
        "How many utterances actually LANDED (beat 1 hotkey + any spoken beat "
        "that produced words -> normally 1; beats 2,3,4 land none)?",
        _nth(0),
    )
    taught_raw = _ask("How many corrections did you TEACH (normally 1)?", _nth(1))
    restarted_raw = _ask("Did you restart the hub in beat 6 (1 = yes, 0 = no)?", _nth(2))
    question = _ask(
        "Q -- uncertain delivery: never automatic, or a one-tap `Send again`?",
        _nth(3),
    )

    def _int(raw: str, fallback: int) -> int:
        try:
            return int(raw)
        except (TypeError, ValueError):
            return fallback

    out = {
        "utterances_landed": _int(spoken_raw, 0),
        "corrections_taught": _int(taught_raw, 0),
        "hub_restarted": bool(_int(restarted_raw, 0)),
        "q_uncertain_delivery": question or "(not answered)",
    }
    report.answers = out
    return out


# ---------------------------------------------------------------------------
# The write-set assertion + the decision table
# ---------------------------------------------------------------------------


def _write_set(report: WalkReport, before: dict, after: dict,
               answers: dict | None, beats: list[Beat]) -> bool:
    """Assert the true write set. Returns ok."""
    ok = True
    landed = int(answers.get("utterances_landed", 0)) if answers else 0
    taught = int(answers.get("corrections_taught", 0)) if answers else 0
    restarted = bool(answers.get("hub_restarted")) if answers else False

    jb, ja = before.get("journal_count"), after.get("journal_count")
    retention = int(before.get("journal_retention") or 0)
    if jb is None or ja is None:
        beats.append(Beat("write-set: journal rows", f"+{landed}", "unreadable",
                          "HIS HAND", "DATA"))
        ok = False
    else:
        added = ja - jb
        expected = landed
        note = ""
        if retention and jb >= retention:
            # The recorder prunes to `retention` on every write, so at the
            # ceiling a row written evicts a row: the count cannot rise.
            expected = 0
            note = f" (at retention {retention}: each write evicts one row)"
        verdict = "MATCH" if added == expected else "BOUNCE"
        if verdict == "BOUNCE":
            ok = False
            report.defects.append(
                f"WRITE SET: journal rows added {added}, expected {expected} "
                f"(utterances that landed: {landed}){note}"
            )
        beats.append(Beat(
            beat="write-set: journal rows",
            expected=f"+{expected}{note}",
            observed=f"+{added} ({jb} -> {ja})",
            write="HIS HAND",
            verdict=verdict,
        ))

    cb, ca = before.get("corrections_size"), after.get("corrections_size")
    if cb is None or ca is None:
        beats.append(Beat("write-set: correction rows", f"+{taught}", "unreadable",
                          "HIS HAND", "DATA"))
        ok = False
    else:
        added = ca - cb
        verdict = "MATCH" if added == taught else "BOUNCE"
        if verdict == "BOUNCE":
            ok = False
            report.defects.append(
                f"WRITE SET: correction rows added {added}, expected {taught}"
            )
        beats.append(Beat(
            beat="write-set: correction rows",
            expected=f"+{taught}",
            observed=f"+{added} ({cb} -> {ca})",
            write="HIS HAND",
            verdict=verdict,
        ))

    # AC5: the restart beat. The custody claim is only proven if the process
    # actually changed AND the rows came back.
    pb, pa = before.get("process_pid"), after.get("process_pid")
    if restarted:
        if pb is None or pa is None:
            beats.append(Beat("beat 6: restart identity", "a NEW pid",
                              "identity unreadable", "none", "DATA"))
            report.surprises.append(
                "the restart beat could not be proven: /api/system/identity "
                "did not report a pid at both ends"
            )
        else:
            verdict = "MATCH" if pb != pa else "BOUNCE"
            if verdict == "BOUNCE":
                ok = False
                report.defects.append(
                    f"BEAT 6: he says he restarted, but the pid is unchanged ({pa})"
                )
            beats.append(Beat(
                beat="beat 6: restart identity",
                expected="a NEW pid on the same database",
                observed=f"{pb} -> {pa}",
                write="HIS HAND",
                verdict=verdict,
            ))
        dbb, dba = before.get("database_id"), after.get("database_id")
        beats.append(Beat(
            beat="beat 6: same database",
            expected=f"unchanged ({dbb})",
            observed=str(dba),
            write="none",
            verdict="MATCH" if dbb == dba else "BOUNCE",
        ))
        if dbb != dba:
            ok = False
            report.defects.append(
                "BEAT 6: the database identity changed across the restart; the "
                "custody proof is against a different store"
            )
    else:
        beats.append(Beat("beat 6: restart identity", "a NEW pid",
                          "not walked", "none", "DATA"))

    # A correction that survives the restart must still be listed by key.
    kb = set(before.get("correction_keys") or [])
    ka = set(after.get("correction_keys") or [])
    lost = sorted(kb - ka)
    beats.append(Beat(
        beat="custody: correction keys kept",
        expected="nothing lost",
        observed=("all kept" if not lost else f"LOST {lost}"),
        write="none",
        verdict="MATCH" if not lost else "BOUNCE",
    ))
    if lost:
        ok = False
        report.defects.append(f"CUSTODY: correction keys lost across the walk: {lost}")

    return ok


def _print_table(beats: list[Beat]) -> None:
    _say("")
    _say("=== DECISION TABLE ===")
    w1 = max([len(b.beat) for b in beats] + [4])
    w2 = max([len(b.expected) for b in beats] + [8])
    w3 = max([len(b.observed) for b in beats] + [8])
    head = (f"  {'BEAT'.ljust(w1)} | {'EXPECTED'.ljust(w2)} | "
            f"{'OBSERVED'.ljust(w3)} | WRITE? | VERDICT")
    _say(head)
    _say("  " + "-" * (len(head) - 2))
    for b in beats:
        _say(
            f"  {b.beat.ljust(w1)} | {b.expected.ljust(w2)} | "
            f"{b.observed.ljust(w3)} | {b.write.ljust(6)} | {b.verdict}"
        )
    _say("")


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------


def _write_facts_json(report: WalkReport, out_dir: Path) -> Path:
    path = out_dir / "walk-facts.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_redact(json.dumps(asdict(report), indent=2)), encoding="utf-8")
    return path


def _write_facts_md(report: WalkReport, out_dir: Path) -> Path:
    path = out_dir / "walk-facts.md"
    lines = [
        "# HS-200-05 walk facts — physical voice, correction and custody",
        "",
        f"- Generated: {report.generated_at}",
        f"- Hub: {report.hub_host}",
        f"- Mode: {'ATTENDED' if report.attended else 'READ-ONLY'}",
        "",
        "## Census",
        "",
        "| Field | Before | After |",
        "|---|---|---|",
    ]
    keys = sorted(set(report.census_before) | set(report.census_after) - {"label"})
    for key in keys:
        if key == "label":
            continue
        lines.append(
            f"| `{key}` | {report.census_before.get(key)} | "
            f"{report.census_after.get(key)} |"
        )
    lines += ["", "## Decision table", "",
              "| Beat | Expected | Observed | Write? | Verdict |", "|---|---|---|---|---|"]
    for beat in report.beats:
        lines.append(
            f"| {beat['beat']} | {beat['expected']} | {beat['observed']} | "
            f"{beat['write']} | {beat['verdict']} |"
        )
    if report.facts:
        lines += ["", "## Face facts", "",
                  "| Face | Field | Expected | Observed | Verdict | Why |",
                  "|---|---|---|---|---|---|"]
        for f in report.facts:
            lines.append(
                f"| {f['face']} | {f['field']} | {f['expected']} | "
                f"{f['observed']} | {f['verdict']} | {f['why']} |"
            )
    for title, items in (
        ("Defects", report.defects),
        ("Surprises", report.surprises),
        ("Errors", report.errors),
    ):
        lines += ["", f"## {title}", ""]
        lines += [f"- {item}" for item in items] or ["- (none)"]
    path = out_dir / "walk-facts.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_redact("\n".join(lines) + "\n"), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="HS-200-05 voice + custody walk runner")
    parser.add_argument("--hub", required=True, help="Hub URL with token")
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help="Output directory for shots and facts")
    parser.add_argument("--attended", action="store_true",
                        help="Pause for his hand between the two censuses")
    parser.add_argument("--answers", default=None,
                        help='Attended answers instead of stdin: '
                             '"<landed>,<corrections>,<restarted 0|1>[,<Q>]"')
    args = parser.parse_args()

    parsed = urlparse(args.hub)
    token = parse_qs(parsed.query).get("token", [""])[0]
    if not token:
        _say("ERROR: --hub URL must include ?token=...")
        return 1
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = WalkReport(
        generated_at=datetime.now().isoformat(),
        hub_host=parsed.netloc,
        attended=bool(args.attended),
        viewports=[{"width": v["width"], "height": v["height"]} for v in VIEWPORTS],
    )
    beats: list[Beat] = []
    fatal: list[str] = []

    _say("=== HS-200-05 WALK: PHYSICAL VOICE, CORRECTION AND CUSTODY ===")
    _say(f"  Hub:  {args.hub}")
    _say(f"  Out:  {out_dir}")
    _say(f"  Mode: {'ATTENDED' if args.attended else 'READ-ONLY (script printed, no pause)'}")
    _say("")
    _say("=== WRITE GUARD DECISION TABLE (the RUNNER writes nothing) ===")
    for op in list(_DENIALS) + ["unknown", "", None]:  # type: ignore[list-item]
        allowed, reason = _write_allowed(op)
        _say(f"  {str(op):24s} -> allowed={allowed}, reason={reason}")
    _say("  ALL RUNNER WRITES DENIED. The only writes are the product's,")
    _say("  produced by HIS OWN HAND.")
    _say("")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _say("ERROR: playwright not installed")
        return 1

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        page0 = browser.new_page(viewport={"width": 1440, "height": 900})
        page0.goto(f"{base_url}/?token={token}", wait_until="load")
        try:
            _require_bundle(page0)
        except RuntimeError as exc:
            _say(f"REFUSED: {exc}")
            browser.close()
            return 1
        page0.wait_for_timeout(1500)

        _say("  [1/8] Census BEFORE (read-only)...")
        before = _census(page0, token, report, "before")
        report.census_before = before

        corr_on = before.get("corrections_enabled")
        beats.append(Beat(
            beat="beat 0: corrections_enabled",
            expected="True (else beat 5 teaches into a silent no-op)",
            observed=str(corr_on),
            write="none",
            verdict="MATCH" if corr_on is True else "BOUNCE",
        ))
        if corr_on is not True:
            msg = (f"BEAT 0: corrections_enabled is {corr_on} — a teach would "
                   "write and never fire. Turn it on in the Speak gear before walking.")
            _say(f"        {msg}")
            report.defects.append(msg)
            if args.attended:
                fatal.append(msg)

        beats.append(Beat(
            beat="beat 0: engine readiness",
            expected="(a runtime that can hear him)",
            observed=f"{before.get('runtime_status')} / backend="
                     f"{before.get('engine_backend')} / egress="
                     f"{before.get('egress_boundary')}",
            write="none",
            verdict="DATA",
        ))
        page0.close()

        step = 1
        #: Set once the first-value chair proves the desk unreachable; the
        #: remaining face beats are HELD rather than retried into timeouts.
        chair_holds = ""
        for vp in VIEWPORTS:
            w, h = vp["width"], vp["height"]
            _say(f"\n=== Viewport {w}x{h} ===")
            page = browser.new_page(viewport={"width": w, "height": h})
            page.emulate_media(reduced_motion="reduce")
            page_errors: list[str] = []
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.goto(f"{base_url}/?token={token}", wait_until="load")
            try:
                _require_bundle(page)
            except RuntimeError as exc:
                _say(f"REFUSED: {exc}")
                browser.close()
                return 1
            page.wait_for_timeout(1500)
            _note_chair(page, report)

            for name, fn in (("Speak", _beat_speak),
                             ("Journal", _beat_journal),
                             ("Learned", _beat_learned)):
                step += 1
                _say(f"  [{step}/8] {name} @ {w}...")
                if chair_holds:
                    _say("        HELD: the first-value chair owns the desk.")
                    continue
                try:
                    fn(page, out_dir, w, report)
                    _say("        done.")
                except ChairHoldsTheDesk as exc:
                    chair_holds = str(exc)
                    _say(f"        HELD: {exc}")
                    report.surprises.append(f"{name.lower()}@{w}: {exc}")
                except Exception as exc:
                    msg = f"{name.lower()}@{w}: {exc}"
                    _say(f"        FAILED: {msg}")
                    report.errors.append(msg)
                    fatal.append(msg)

            critical = [e for e in page_errors if "ResizeObserver" not in e]
            if critical:
                report.errors.extend([f"JS@{w}: {e}" for e in critical])
            page.close()

        if chair_holds:
            beats.append(Beat(
                beat="beat -1: the first-value chair",
                expected="the desk, or the chair he must answer first",
                observed="the chair holds the desk (VOICE TYPING)",
                write="DENIED (Continue later persists)",
                verdict="HIS HAND",
            ))
        beats.append(Beat(
            beat="R1 Speak (1440+393)",
            expected="four wings; well mic-less; Talk present; a named mic phase",
            observed=_verdict_of(report, "speak"),
            write="DENIED (Talk / Open mic)",
            verdict=_worst(report, "speak"),
        ))
        beats.append(Beat(
            beat="R2 Journal (1440+393)",
            expected="his rows only",
            observed=_verdict_of(report, "journal"),
            write="DENIED (Clear / Delete / Replay / Export)",
            verdict=_worst(report, "journal"),
        ))
        beats.append(Beat(
            beat="R3 Learned (1440+393)",
            expected="his rules with honest APPLIED counts",
            observed=_verdict_of(report, "learned"),
            write="DENIED (Teach / Forget)",
            verdict=_worst(report, "learned"),
        ))

        answers = None
        if args.attended:
            if fatal:
                _say("")
                _say("REFUSED TO PAUSE: a read-only beat already failed:")
                for msg in fatal:
                    _say(f"  - {msg}")
                browser.close()
                return 1
            answers = _collect_answers(args.answers, report)

            page1 = browser.new_page(viewport={"width": 1440, "height": 900})
            page1.goto(f"{base_url}/?token={token}", wait_until="load")
            page1.wait_for_timeout(1500)
            _say("  [8/8] Census AFTER (read-only)...")
            after = _census(page1, token, report, "after")
            report.census_after = after
            page1.close()
        else:
            _say(ATTENDED_SCRIPT)
            after = {}
            report.census_after = after

        browser.close()

    ok = True
    if args.attended:
        ok = _write_set(report, report.census_before, report.census_after,
                        answers, beats)
    report.beats = [asdict(b) for b in beats]
    _print_table(beats)

    facts_json = _write_facts_json(report, out_dir)
    facts_md = _write_facts_md(report, out_dir)
    _say(f"  facts: {facts_json}")
    _say(f"  facts: {facts_md}")

    if report.defects:
        _say("")
        _say("=== DEFECTS ===")
        for d in report.defects:
            _say(f"  - {d}")
    if report.surprises:
        _say("")
        _say("=== SURPRISES ===")
        for s in report.surprises:
            _say(f"  - {s}")
    if report.errors:
        _say("")
        _say("=== ERRORS ===")
        for e in report.errors:
            _say(f"  - {e}")

    return 0 if (ok and not report.errors) else 1


def _facts_for(report: WalkReport, prefix: str) -> list[dict]:
    return [f for f in report.facts if str(f.get("face", "")).startswith(prefix)]


def _verdict_of(report: WalkReport, prefix: str) -> str:
    facts = _facts_for(report, prefix)
    if not facts:
        return "no facts"
    bounces = [f for f in facts if f.get("verdict") == "BOUNCE"]
    if bounces:
        return f"{len(bounces)}/{len(facts)} BOUNCE"
    return f"{len(facts)} facts MATCH"


def _worst(report: WalkReport, prefix: str) -> str:
    facts = _facts_for(report, prefix)
    if not facts:
        return "DATA"
    if any(f.get("verdict") == "BOUNCE" for f in facts):
        return "BOUNCE"
    return "MATCH"


if __name__ == "__main__":
    sys.exit(main())
