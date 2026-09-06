"""HS-176-06 walk runner: The Speak Loop -- the owner's attended walk.

Shoots four Speak faces (Speak, Journal, Learned, Review) at 1440x900 and
393x852, takes a read-only census before and after, and PAUSES for his
hand between them.

THE LIVE LAWS (Article IV -- the runner writes nothing):
1. THE RUNNER IS READ-ONLY.  Every write the runner could make is DENIED
   by a fail-closed guard and printed.  It never teaches a correction,
   never clears the journal, never deletes a row, never forgets a rule,
   never lands an utterance, never presses `Talk`, never submits a Room
   ask or a Door field, never dismisses the first-value chair
   ("Continue later" is a write -- it persists the dismissal).
2. THE PRODUCT WRITES WHAT HIS OWN HAND PRODUCES (design D5, ruling R10):
   one journal row per utterance HE speaks (retention-pruned as always),
   one correction row from HIS `Teach`, the `taught_from` flag and
   `corrections_applied` the product sets itself.  The runner asserts
   that write set before and after and fails on any other delta.
3. NO HARDCODED TOKENS.  The hub token is read from --hub and REDACTED
   (`token=<redacted>`) in every line this runner prints or writes.
4. FACE-DRIVEN.  The read-only beats drive the real faces; the census
   reads the product's own routes.
5. NO BUNDLE, NO WALK.  A hub serving no React build is refused (the 173
   law) -- a hollow walk proves nothing.
6. STANDALONE.  Not collected by pytest.  Never run beside the parallel
   suite (CPU starvation reads as a discovery hang).

Usage:

  # read-only: the census, the four faces at both widths, then the
  # attended script printed for him (the runner stops).
  uv run python tests/e2e/live176_walk.py \\
      --hub "http://127.0.0.1:PORT/?token=TOKEN"

  # attended: the same, then a PAUSE on stdin while he walks beats 0-7,
  # then the after-census and the decision table.
  uv run python tests/e2e/live176_walk.py \\
      --hub "http://127.0.0.1:PORT/?token=TOKEN" --attended

  # attended, answers supplied instead of stdin (development / proof):
  #   --answers "<utterances he spoke>,<corrections he taught 0|1>"
  uv run python tests/e2e/live176_walk.py \\
      --hub "http://127.0.0.1:PORT/?token=TOKEN" --attended --answers "2,1"
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
collect_ignore_glob = ["live176_walk.py"]


REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = (
    REPO / "pm/roadmap/holdspeak/phase-176-the-speak-loop/assets/story-06-shots"
)

VIEWPORTS = [
    {"width": 1440, "height": 900, "suffix": "1440"},
    {"width": 393, "height": 852, "suffix": "393"},
]

WING_LABELS = ["SPEAK", "JOURNAL", "BLOCKS", "LEARNED"]
FILTER_LABELS = ["ALL", "DICTATION", "BROWSER", "HOTKEY"]


# ---------------------------------------------------------------------------
# Token redaction (law 3)
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"(token=)[^&\s\"']+")


def _redact(text: str) -> str:
    """Replace every `token=...` with `token=<redacted>`.

        _redact("http://127.0.0.1:8080/?token=abc123")
            -> "http://127.0.0.1:8080/?token=<redacted>"
        _redact("no token here") -> "no token here"
    """
    return _TOKEN_RE.sub(r"\1<redacted>", text or "")


def _say(text: str = "") -> None:
    """Print, always redacted."""
    print(_redact(text))


# ---------------------------------------------------------------------------
# Write guard (fail-closed: the RUNNER writes nothing)
# ---------------------------------------------------------------------------

_DENIALS: dict[str, str] = {
    "land_utterance": "never lands an utterance (his hand speaks, not the runner)",
    "press_talk": "never presses Talk (one mic authority, and it is his)",
    "teach_correction": "never teaches a correction (his hand teaches)",
    "forget_correction": "never presses Forget",
    "clear_journal": "never presses Clear",
    "delete_journal_row": "never opens or presses a row's Delete",
    "replay_journal_row": "never presses Replay",
    "correct_journal_row": "never posts to /journal/{id}/correct",
    "enable_corrections": "never flips corrections_enabled (it reads and reports)",
    "dismiss_chair": "never clicks Continue later (dismissal persists = a write)",
    "submit_room_ask": "never submits a Room ask",
    "submit_door_field": "never submits the Door",
    "export_journal": "never presses Export",
    "seed": "never seeds his desk (a walk seeds nothing)",
}


def _write_allowed(
    operation: str | None,
    context: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Decide whether a write operation is allowed in this walk.

    Returns (allowed: bool, reason: str).  NOTHING is allowed: the walk's
    only writes are the product's, produced by the owner's own hand.

    Decision table:
        _write_allowed("land_utterance")   -> (False, "never lands an utterance ...")
        _write_allowed("teach_correction") -> (False, "never teaches a correction ...")
        _write_allowed("clear_journal")    -> (False, "never presses Clear")
        _write_allowed("unknown")          -> (False, "unknown operation denied by default")
        _write_allowed("")                 -> (False, "empty operation denied")
        _write_allowed(None)               -> (False, "null operation denied")
    """
    if not operation:
        return False, "empty operation denied" if operation == "" else "null operation denied"
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


def _shoot(page: Any, out_dir: Path, name: str, w: int) -> Path:
    _settle(page)
    path = out_dir / f"{name}-{w}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    win = page.locator(".desk-surface-window").first
    if win.count() > 0 and win.is_visible():
        win.screenshot(path=str(path))
    else:
        page.screenshot(path=str(path), full_page=False)
    assert path.exists() and path.stat().st_size > 1_000, (
        f"Shot {path.name} missing or too small"
    )
    return path


_FETCH_JS = """async ([method, path, body, token]) => {
  const response = await fetch(path, {
    method,
    headers: {
      authorization: `Bearer ${token}`,
      ...(body ? {"content-type": "application/json"} : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("json")
    ? await response.json()
    : await response.text();
  return {status: response.status, payload};
}"""

#: The only HTTP verb the runner is permitted to issue.  Anything else is
#: a write and the guard refuses it before the request is built.
_READ_VERBS = {"GET", "HEAD"}


def _api(page: Any, method: str, path: str, token: str) -> dict[str, Any]:
    """Read one product route.  A non-read verb is DENIED, not sent."""
    if method.upper() not in _READ_VERBS:
        allowed, reason = _write_allowed(f"http_{method.lower()}")
        _say(f"        WRITE DENIED: {method} {path} -- {reason}")
        return {"status": 0, "payload": {}}
    return page.evaluate(_FETCH_JS, [method, path, None, token])


def _require_bundle(page: Any) -> None:
    """The 173 law: a hub with no React build makes every beat hollow."""
    if "React Web build is missing" in page.content():
        raise RuntimeError(
            "HUB SERVES NO BUNDLE: the web build is missing; every face "
            "beat would be hollow. Run `npm --prefix web run build` and "
            "restart the hub."
        )


def _note_chair(page: Any, report: WalkReport) -> None:
    """Report the first-value chair; NEVER dismiss it (a write)."""
    try:
        chair = page.locator(".chair")
        if chair.count() == 0:
            return
        chair.wait_for(timeout=5000)
        if chair.evaluate("el => el.classList.contains('chair-first-value')"):
            allowed, reason = _write_allowed("dismiss_chair")
            report.surprises.append(
                "first-value chair present on the desk; not dismissed "
                f"({reason})"
            )
            _say(f"        note: first-value chair present -- {reason}")
    except Exception:
        pass


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
    page.locator(".speak-face").wait_for(timeout=20000)
    _settle(page)


def _wing(page: Any, label: str) -> None:
    """Cross to a wing.  A wing change is a READ (watching is free)."""
    page.get_by_role("tab", name=label).click()
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


def _mic_total() -> int | None:
    """The scanner's `mic` violation total over the tree.

    The walk changes no code, so this number must be identical before and
    after.  Returns None when the scanner cannot be imported (reported,
    never silently zero).
    """
    try:
        sys.path.insert(0, str(REPO / "scripts"))
        import ux_canon_scan  # type: ignore

        _per_face, all_violations = ux_canon_scan.scan_all(REPO)
        return sum(1 for v in all_violations if v.rule == "mic")
    except Exception:
        return None


def _census(page: Any, token: str, report: WalkReport, label: str) -> dict:
    """Read the write set and the readiness.  ZERO writes."""
    out: dict[str, Any] = {"label": label}

    journal = _api(page, "GET", "/api/dictation/journal?limit=1", token)
    if journal["status"] == 200 and isinstance(journal["payload"], dict):
        out["journal_count"] = int(journal["payload"].get("count", 0))
        out["journal_enabled"] = bool(journal["payload"].get("enabled", False))
        out["journal_retention"] = int(journal["payload"].get("retention", 0))
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
        out["correction_keys"] = [
            str(i.get("key", "")) for i in payload.get("items", [])
        ]
    else:
        out["corrections_size"] = None
        out["corrections_enabled"] = None
        report.errors.append(
            f"census({label}): GET /api/dictation/corrections -> {corrections['status']}"
        )

    readiness = _api(page, "GET", "/api/dictation/readiness", token)
    if readiness["status"] == 200 and isinstance(readiness["payload"], dict):
        payload = readiness["payload"]
        runtime = payload.get("runtime") or {}
        depth = payload.get("depth") or {}
        depth_corr = depth.get("corrections") or {}
        out["ready"] = bool(payload.get("ready", False))
        out["runtime_status"] = str(runtime.get("status", "unknown"))
        out["runtime_detail"] = str(runtime.get("detail", ""))[:120]
        out["engine_backend"] = str(
            (payload.get("config") or {}).get("backend", "unknown")
        )
        out["egress_boundary"] = str(payload.get("egress_boundary", "unknown"))
        # Beat 0: corrections_enabled.  Every read of it falls back to
        # False (design D5), so a stale config makes the loop a silent
        # no-op.  Two independent reads must agree.
        out["readiness_corrections_enabled"] = bool(depth_corr.get("enabled", False))
    else:
        out["ready"] = None
        out["runtime_status"] = "unknown"
        out["readiness_corrections_enabled"] = None
        report.errors.append(
            f"census({label}): GET /api/dictation/readiness -> {readiness['status']}"
        )

    out["mic_total"] = _mic_total()

    _say(f"  census [{label}]: journal={out.get('journal_count')} "
         f"corrections={out.get('corrections_size')} "
         f"corrections_enabled={out.get('corrections_enabled')} "
         f"mic={out.get('mic_total')} "
         f"runtime={out.get('runtime_status')}")
    return out


# ---------------------------------------------------------------------------
# The read-only beats (R1-R4), driven at each width
# ---------------------------------------------------------------------------


def _beat_speak(page: Any, out_dir: Path, w: int, report: WalkReport) -> None:
    """R1: the Speak face -- four wings, the well mic-less, `Talk` present."""
    face = f"speak@{w}"
    _open_speak(page, report)

    wings = [
        t.strip().upper()
        for t in page.locator(".desk-wings-tabs [role=tab]").all_inner_texts()
    ]
    _fact(report, face, "wings", " ".join(WING_LABELS), " ".join(wings),
          "MATCH" if wings == WING_LABELS else "BOUNCE",
          "the four wings of the Speak surface (design D2(c))")
    if wings != WING_LABELS:
        report.defects.append(f"SPEAK@{w}: wings {wings} != {WING_LABELS}")

    well_mics = page.locator(".speak-well .desk-mic").count()
    _fact(report, face, "well_mic_count", "0", str(well_mics),
          "MATCH" if well_mics == 0 else "BOUNCE",
          "ONE mic authority (Article IV.3, ruling R13): the well carries none")
    if well_mics != 0:
        report.defects.append(
            f"SPEAK@{w}: the utterance well carries {well_mics} mic(s) -- R13"
        )

    talk = page.locator(".speak-transport .desk-mic")
    talk_word = page.locator(".speak-transport .gadget-transport-word").first
    # The transport word is uppercased by the species' CSS, so `inner_text`
    # returns TALK; the source says `Talk`. Compare case-insensitively.
    talk_text = talk_word.inner_text().strip().upper() if talk_word.count() > 0 else "---"
    talk_ok = talk.count() >= 1 and talk_text == "TALK"
    _fact(report, face, "talk", "TALK", talk_text,
          "MATCH" if talk_ok else "BOUNCE",
          "the transport is this face's mic authority")
    if not talk_ok:
        report.defects.append(
            f"SPEAK@{w}: `Talk` transport absent or unnamed "
            f"(mics={talk.count()}, word={talk_text})"
        )

    footer = page.locator(".surface-footer-layout")
    footer_text = footer.inner_text().replace("\n", " ") if footer.count() else "---"
    _fact(report, face, "footer", "THIS DEVICE + Review + Export",
          footer_text[:80], "DATA", "the Speak footer, as found")

    shot = _shoot(page, out_dir, "speak", w)
    report.shots.append({"beat": "speak", "width": w, "path": str(shot)})


def _beat_journal(page: Any, out_dir: Path, w: int, report: WalkReport) -> dict:
    """R2: the Journal wing -- his real rows, the four filter tokens.

    Reads only.  `Clear` is never pressed; no row is opened; no row's
    `Delete` is touched.
    """
    face = f"journal@{w}"
    _wing(page, "Journal")
    page.locator(".speak-journal").wait_for(timeout=15000)
    page.wait_for_timeout(800)
    _settle(page)

    rows = page.locator(".speak-journal .surface-ledger-row").count()
    tokens = [
        t.strip().upper()
        for t in page.locator(".speak-journal .surface-filter-token").all_inner_texts()
    ]
    _fact(report, face, "filter_tokens", " ".join(FILTER_LABELS), " ".join(tokens),
          "MATCH" if tokens == FILTER_LABELS else "BOUNCE",
          "the four source filter tokens (ruling R6: present even when quiet)")
    if tokens != FILTER_LABELS:
        report.defects.append(f"JOURNAL@{w}: filter tokens {tokens} != {FILTER_LABELS}")

    body = page.locator(".speak-journal").inner_text()
    _fact(report, face, "rows", "(his real journal rows)", str(rows),
          "DATA", "rows rendered on his desk; the runner opens none")
    if rows == 0:
        _fact(report, face, "empty_state", "NOTHING SPOKEN",
              "NOTHING SPOKEN" if "NOTHING SPOKEN" in body else body[:60],
              "MATCH" if "NOTHING SPOKEN" in body else "BOUNCE",
              "the quiet state is one token, never a sentence")

    caption = page.locator(".speak-journal .surface-ledger-count")
    caption_text = caption.inner_text().strip() if caption.count() else ""
    _fact(report, face, "caption_count", "(absent -- the footer's N TODAY is the one count)",
          caption_text or "(absent)",
          "MATCH" if caption_text == "" else "BOUNCE",
          "ruling N5b / A.7: the wing carries no caption count")

    # The two verbs the runner must never press -- named, denied, printed.
    for op in ("clear_journal", "delete_journal_row", "replay_journal_row"):
        allowed, reason = _write_allowed(op)
        _fact(report, face, f"guard:{op}", "DENIED",
              f"DENIED ({reason})", "MATCH", "the runner writes nothing")

    shot = _shoot(page, out_dir, "journal", w)
    report.shots.append({"beat": "journal", "width": w, "path": str(shot)})
    return {"rows": rows, "tokens": tokens}


def _beat_learned(page: Any, out_dir: Path, w: int, report: WalkReport) -> dict:
    """R3: the Learned wing -- NOTHING LEARNED expected; rows listed read-only."""
    face = f"learned@{w}"
    _wing(page, "Learned")
    page.locator(".speak-learned").wait_for(timeout=15000)
    page.wait_for_timeout(600)
    _settle(page)

    rows = page.locator(".speak-learned .surface-ledger-row")
    count = rows.count()
    body = page.locator(".speak-learned").inner_text()

    if count == 0:
        _fact(report, face, "empty_state", "NOTHING LEARNED",
              "NOTHING LEARNED" if "NOTHING LEARNED" in body else body[:60],
              "MATCH" if "NOTHING LEARNED" in body else "BOUNCE",
              "his desk has taught nothing yet (the expected state before beat 3)")
        listed: list[str] = []
    else:
        listed = []
        for i in range(count):
            row = rows.nth(i)
            kind = row.locator(".learned-kind")
            key = row.locator(".surface-ledger-primary")
            value = row.locator(".learned-value")
            applied = row.locator(".learned-applied")
            listed.append(
                " | ".join(
                    [
                        kind.inner_text().strip() if kind.count() else "?",
                        key.inner_text().strip() if key.count() else "?",
                        value.inner_text().strip() if value.count() else "",
                        applied.inner_text().strip() if applied.count() else "",
                    ]
                )
            )
        _fact(report, face, "rows", "(NOTHING LEARNED expected)",
              f"{count} row(s): " + " ;; ".join(listed)[:160],
              "DATA", "rules already on his desk, read-only (never Forgotten)")
        report.surprises.append(
            f"LEARNED@{w}: {count} rule(s) already taught: " + " ;; ".join(listed)
        )

    allowed, reason = _write_allowed("forget_correction")
    _fact(report, face, "guard:forget_correction", "DENIED",
          f"DENIED ({reason})", "MATCH", "the runner writes nothing")

    shot = _shoot(page, out_dir, "learned", w)
    report.shots.append({"beat": "learned", "width": w, "path": str(shot)})
    return {"rows": count, "listed": listed}


def _beat_review(page: Any, out_dir: Path, w: int, report: WalkReport) -> None:
    """R4: `Review` from Speak -- a READ that crosses to the Journal wing."""
    face = f"review@{w}"
    _wing(page, "Speak")
    page.locator(".speak-face").wait_for(timeout=15000)
    _settle(page)

    page.get_by_role("button", name="Review").first.click()
    page.locator(".speak-journal").wait_for(timeout=10000)
    _settle(page)

    selected = page.get_by_role("tab", name="Journal").get_attribute("aria-selected")
    _fact(report, face, "review_target", "the JOURNAL wing (aria-selected=true)",
          str(selected), "MATCH" if selected == "true" else "BOUNCE",
          "design D2(b).9: `Review` reviews; it no longer opens the Configure door")
    doors = page.locator(".surface-door").count()
    _fact(report, face, "configure_door", "0", str(doors),
          "MATCH" if doors == 0 else "BOUNCE",
          "the Configure door stays the gear's job")
    if selected != "true":
        report.defects.append(f"REVIEW@{w}: Review did not cross to the Journal wing")

    shot = _shoot(page, out_dir, "review", w)
    report.shots.append({"beat": "review", "width": w, "path": str(shot)})


# ---------------------------------------------------------------------------
# The attended script (his hand)
# ---------------------------------------------------------------------------

ATTENDED_SCRIPT = """
=== THE ATTENDED WALK -- HIS HAND, BEATS 0-7 (design D5) ===

Beat 0  CONFIRM THE LOOP IS ARMED.
        Speak surface -> the gear (Configure dictation) -> corrections.
        `corrections_enabled` must be ON.  Every read of it falls back to
        False, so a stale config makes the whole loop a silent no-op.
        (The runner already read it -- see the census line above.)

Beat 1  TALK.  Press `Talk` on the Speak transport.  Say a sentence.
        It lands in the RESULT row; LANDS IN reads the target label and
        the latency.
        -> the product writes ONE journal row.

Beat 2  A WRONG LANDING.  Say a sentence with a word the transcript gets
        wrong (his Tuesday word: "postgress" for PostgreSQL, or "queue
        for" for Q4).  Press `Wrong`.
        -> the product writes ONE journal row.

Beat 3  TEACH -- FIELD = TEXT.  The teach row unfolds with the landed
        text pre-filled.  Edit the ONE word.  Press `Teach`.
        Expect the receipt: TAUGHT - <heard> -> <said>.
        -> the product writes ONE correction row and flags `taught_from`
           on the row of beat 2.

Beat 4  THE SAME PHRASE AGAIN.  Say a sentence containing it.
        Expect the RESULT row to carry the CORRECTED text and the chip
        `APPLIED`.  Open the chip: HEARD / SAID / kind.
        -> the product writes ONE journal row with `corrections_applied`.

Beat 5  THE JOURNAL.  Cross to the Journal wing (the wing strip or
        `Review`).  Expect the newest row `APPLIED`, the beat-2 row
        `TAUGHT`, the source badge DICTATION, day bands, and NO caption
        count.  Do not press `Clear`.

Beat 6  THE MIC ON A ROOM.  Open a Room.  Click the MicButton on the
        ask well (click to TOGGLE, never press-and-hold).  Dictate a
        sentence; the text lands in the field.  DO NOT SUBMIT.
        -> the product writes ONE journal row, source BROWSER.

Beat 7  THE MIC ON THE DOOR.  Open the Door.  Click the MicButton on the
        name/outcome field.  Dictate a project name.  DO NOT SUBMIT.
        -> the product writes ONE journal row, source BROWSER.

Then return to the Speak window and confirm the Journal shows the beat-6
and beat-7 utterances with source BROWSER.

--- THE TWO WALK QUESTIONS (design D5) ---
Q1  Is the correction a routing fix or a words fix?  176 answers BOTH,
    with TEXT as the default.  Your word confirms or flips it.
Q2  How wide should a correction reach?  A routing correction nudges at
    0.5 Jaccard.  AND: should a TEXT rule's FIRST application confirm?
    A rule on a common phrase ("queue for" -> "Q4") rewrites the words
    you type on every source, forever, with no similarity floor.
    Silent-and-undoable (the APPLIED chip names it, `Forget` removes it),
    or confirm-once?

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
    """Pause for his hand, then read the two counts and the two questions."""
    supplied: list[str] = []
    if answers_flag:
        supplied = [a.strip() for a in answers_flag.split(",")]

    def _nth(i: int) -> str | None:
        return supplied[i] if i < len(supplied) else None

    _say(ATTENDED_SCRIPT)
    if answers_flag is None:
        _say("  >>> WALK THE BEATS NOW.  Press RETURN here when you are done. <<<")
        try:
            input()
        except EOFError:
            pass

    spoken_raw = _ask(
        "How many utterances did you SPEAK (beats 1,2,4,6,7 -> normally 5)?",
        _nth(0),
    )
    taught_raw = _ask(
        "How many corrections did you TEACH (0 if none, normally 1)?",
        _nth(1),
    )
    q1 = _ask("Q1 -- routing fix or words fix (or both)?", _nth(2))
    q2 = _ask("Q2 -- should a TEXT rule's FIRST application confirm?", _nth(3))

    def _int(raw: str, fallback: int) -> int:
        try:
            return int(raw)
        except (TypeError, ValueError):
            return fallback

    out = {
        "utterances_spoken": _int(spoken_raw, 0),
        "corrections_taught": _int(taught_raw, 0),
        "q1_routing_or_words": q1 or "(not answered)",
        "q2_first_application_confirms": q2 or "(not answered)",
    }
    report.answers = out
    return out


# ---------------------------------------------------------------------------
# The write-set assertion + the decision table
# ---------------------------------------------------------------------------


def _write_set(report: WalkReport, before: dict, after: dict,
               answers: dict | None, beats: list[Beat]) -> bool:
    """Assert the true write set (design D5 / ruling R10).  Returns ok."""
    ok = True

    spoken = int(answers.get("utterances_spoken", 0)) if answers else 0
    taught = int(answers.get("corrections_taught", 0)) if answers else 0

    jb, ja = before.get("journal_count"), after.get("journal_count")
    retention = int(before.get("journal_retention") or 0)
    if jb is None or ja is None:
        beats.append(Beat("write-set: journal rows", f"+{spoken}", "unreadable",
                          "HIS HAND", "DATA"))
        ok = False
    else:
        added = ja - jb
        expected = spoken
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
                f"WRITE SET: journal rows added {added}, expected {expected}"
                f" (he spoke {spoken}){note}"
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

    mb, ma = before.get("mic_total"), after.get("mic_total")
    if mb is None or ma is None:
        beats.append(Beat("write-set: scanner mic total", "unchanged",
                          "scanner unavailable", "none", "DATA"))
        report.surprises.append(
            "the ux_canon scanner could not be imported; mic total unverified"
        )
    else:
        verdict = "MATCH" if mb == ma else "BOUNCE"
        if verdict == "BOUNCE":
            ok = False
            report.defects.append(
                f"WRITE SET: scanner mic total moved {mb} -> {ma}; a walk "
                "changes no code"
            )
        beats.append(Beat(
            beat="write-set: scanner mic total",
            expected=f"unchanged ({mb})",
            observed=str(ma),
            write="none",
            verdict=verdict,
        ))

    return ok


def _print_table(beats: list[Beat]) -> None:
    _say("")
    _say("=== DECISION TABLE ===")
    w1 = max([len(b.beat) for b in beats] + [4])
    w2 = max([len(b.expected) for b in beats] + [8])
    w3 = max([len(b.observed) for b in beats] + [8])
    head = f"  {'BEAT'.ljust(w1)} | {'EXPECTED'.ljust(w2)} | {'OBSERVED'.ljust(w3)} | WRITE? | VERDICT"
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
    path.write_text(_redact(json.dumps(asdict(report), indent=2)) + "\n")
    return path


def _write_facts_md(report: WalkReport, out_dir: Path) -> Path:
    path = out_dir / "walk-facts.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# HS-176-06 walk facts -- The Speak Loop",
        "",
        f"Generated: {report.generated_at}",
        f"Hub: {report.hub_host}",
        f"Attended: {report.attended}",
        "",
        "## Census",
        "",
        "| Field | Before | After |",
        "|-------|--------|-------|",
    ]
    keys = sorted((set(report.census_before) | set(report.census_after)) - {"label"})
    for key in keys:
        lines.append(
            f"| {key} | {report.census_before.get(key, '---')} | "
            f"{report.census_after.get(key, '---')} |"
        )
    lines.append("")

    if report.beats:
        lines += [
            "## Decision table",
            "",
            "| Beat | Expected | Observed | WRITE? | Verdict |",
            "|------|----------|----------|--------|---------|",
        ]
        for b in report.beats:
            lines.append(
                f"| {b['beat']} | {b['expected']} | {b['observed']} | "
                f"{b['write']} | {b['verdict']} |"
            )
        lines.append("")

    faces: dict[str, list[dict]] = {}
    for fact in report.facts:
        faces.setdefault(fact["face"], []).append(fact)
    for face_name, facts in faces.items():
        lines += [f"## {face_name}", "",
                  "| Field | Expected | Observed | Verdict | Why |",
                  "|-------|----------|----------|---------|-----|"]
        for f in facts:
            lines.append(
                "| {} | {} | {} | {} | {} |".format(
                    f["field"],
                    f["expected"].replace("|", "\\|"),
                    f["observed"].replace("|", "\\|"),
                    f["verdict"],
                    f["why"].replace("|", "\\|"),
                )
            )
        lines.append("")

    if report.answers:
        lines += ["## His answers", ""]
        for k, v in report.answers.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")

    if report.shots:
        lines += ["## Shots", ""]
        for s in report.shots:
            lines.append(f"- {s['beat']} @ {s['width']}: `{Path(s['path']).name}`")
        lines.append("")

    for title, items in (("Errors", report.errors),
                         ("Surprises", report.surprises),
                         ("Defects", report.defects)):
        lines += [f"## {title}", ""]
        if items:
            for i in items:
                lines.append(f"- {i}")
        else:
            lines.append("None.")
        lines.append("")

    path.write_text(_redact("\n".join(lines)) + "\n")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="HS-176-06 walk runner")
    parser.add_argument("--hub", required=True, help="Hub URL with token")
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help="Output directory for shots and facts")
    parser.add_argument("--attended", action="store_true",
                        help="Pause for his hand between the two censuses")
    parser.add_argument("--answers", default=None,
                        help='Attended answers instead of stdin: '
                             '"<utterances>,<corrections>[,<Q1>,<Q2>]"')
    args = parser.parse_args()

    parsed = urlparse(args.hub)
    qs = parse_qs(parsed.query)
    token = qs.get("token", [""])[0]
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

    _say("=== HS-176-06 WALK: THE SPEAK LOOP ===")
    _say(f"  Hub:  {args.hub}")
    _say(f"  Out:  {out_dir}")
    _say(f"  Mode: {'ATTENDED' if args.attended else 'READ-ONLY (script printed, no pause)'}")
    _say("")
    _say("=== WRITE GUARD DECISION TABLE (the RUNNER writes nothing) ===")
    for op in list(_DENIALS) + ["unknown"]:
        allowed, reason = _write_allowed(op)
        _say(f"  {op:24s} -> allowed={allowed}, reason={reason}")
    _say("  ALL RUNNER WRITES DENIED.  The only writes are the product's,")
    _say("  produced by HIS OWN HAND (design D5, ruling R10).")
    _say("")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        _say("ERROR: playwright not installed")
        return 1

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        # -- the API page: census before, and the bundle law --
        page0 = browser.new_page(viewport={"width": 1440, "height": 900})
        page0.goto(f"{base_url}/?token={token}", wait_until="load")
        try:
            _require_bundle(page0)
        except RuntimeError as exc:
            _say(f"REFUSED: {exc}")
            browser.close()
            return 1
        page0.wait_for_timeout(1500)

        _say("  [1/10] Census BEFORE (read-only)...")
        before = _census(page0, token, report, "before")
        report.census_before = before

        corr_on = before.get("corrections_enabled")
        beats.append(Beat(
            beat="beat 0: corrections_enabled",
            expected="True (else the whole loop is a silent no-op)",
            observed=str(corr_on),
            write="none",
            verdict="MATCH" if corr_on is True else "BOUNCE",
        ))
        if corr_on is not True:
            msg = ("BEAT 0 FAILS: corrections_enabled is "
                   f"{corr_on} -- teach would write and never fire. "
                   "Turn it on in the Speak gear (Configure dictation) "
                   "before walking.")
            _say(f"        {msg}")
            report.defects.append(msg)
            if args.attended:
                fatal.append(msg)

        beats.append(Beat(
            beat="beat 0: engine readiness",
            expected="(runtime available)",
            observed=f"{before.get('runtime_status')} / backend="
                     f"{before.get('engine_backend')} / egress="
                     f"{before.get('egress_boundary')}",
            write="none",
            verdict="DATA",
        ))
        page0.close()

        # -- the read-only face beats, both widths --
        step = 1
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
                             ("Learned", _beat_learned),
                             ("Review", _beat_review)):
                step += 1
                _say(f"  [{step}/10] {name} @ {w}...")
                try:
                    fn(page, out_dir, w, report)
                    _say("        done.")
                except Exception as exc:
                    msg = f"{name.lower()}@{w}: {exc}"
                    _say(f"        FAILED: {msg}")
                    report.errors.append(msg)
                    fatal.append(msg)

            critical = [e for e in page_errors if "ResizeObserver" not in e]
            if critical:
                report.errors.extend([f"JS@{w}: {e}" for e in critical])
            page.close()

        # -- the read-only beats, recorded --
        beats.append(Beat(
            beat="R1 Speak (1440+393)",
            expected="four wings; well mic-less; Talk present",
            observed=_verdict_of(report, "speak"),
            write="none",
            verdict=_worst(report, "speak"),
        ))
        beats.append(Beat(
            beat="R2 Journal (1440+393)",
            expected="his rows; ALL DICTATION BROWSER HOTKEY; no caption count",
            observed=_verdict_of(report, "journal"),
            write="DENIED (Clear / Delete / Replay)",
            verdict=_worst(report, "journal"),
        ))
        beats.append(Beat(
            beat="R3 Learned (1440+393)",
            expected="NOTHING LEARNED (rows listed read-only if present)",
            observed=_verdict_of(report, "learned"),
            write="DENIED (Forget)",
            verdict=_worst(report, "learned"),
        ))
        beats.append(Beat(
            beat="R4 Review (1440+393)",
            expected="crosses to the Journal wing; no Configure door",
            observed=_verdict_of(report, "review"),
            write="none",
            verdict=_worst(report, "review"),
        ))

        # -- his hand --
        answers: dict | None = None
        if args.attended and not fatal:
            answers = _collect_answers(args.answers, report)
            beats.append(Beat(
                beat="beats 1,2,4,6,7: he spoke",
                expected="(his count)",
                observed=str(answers["utterances_spoken"]),
                write="HIS HAND",
                verdict="DATA",
            ))
            beats.append(Beat(
                beat="beat 3: he taught",
                expected="1 (0 if he did not teach)",
                observed=str(answers["corrections_taught"]),
                write="HIS HAND",
                verdict="DATA",
            ))
        elif args.attended:
            _say("\n  ATTENDED PAUSE SKIPPED: beat 0 failed; fix it and re-run.")
        else:
            _say(ATTENDED_SCRIPT)
            _say("  READ-ONLY MODE: the runner stops here.  Re-run with "
                 "--attended to walk the beats and take the after-census.")

        # -- census after --
        if args.attended and answers is not None:
            _say("\n  [10/10] Census AFTER (read-only)...")
            page2 = browser.new_page(viewport={"width": 1440, "height": 900})
            page2.goto(f"{base_url}/?token={token}", wait_until="load")
            page2.wait_for_timeout(1000)
            after = _census(page2, token, report, "after")
            report.census_after = after
            page2.close()
            if not _write_set(report, before, after, answers, beats):
                fatal.append("the write set does not match his hand")

        browser.close()

    report.beats = [asdict(b) for b in beats]
    _print_table(beats)

    json_path = _write_facts_json(report, out_dir)
    md_path = _write_facts_md(report, out_dir)

    _say("=== WALK 176 COMPLETE ===")
    _say(f"  Facts JSON: {json_path}")
    _say(f"  Facts MD:   {md_path}")
    _say(f"  Shots:      {len(report.shots)}")
    _say(f"  Errors:     {len(report.errors)}")
    _say(f"  Surprises:  {len(report.surprises)}")
    _say(f"  Defects:    {len(report.defects)}")
    for d in report.defects:
        _say(f"    - {d}")
    for s in report.surprises:
        _say(f"    ~ {s}")

    if fatal:
        _say("\nFATAL:")
        for f in fatal:
            _say(f"  - {f}")
        return 1
    if any(b.verdict == "BOUNCE" for b in beats):
        _say("\nBOUNCE verdicts in the decision table.")
        return 1
    return 0


def _facts_for(report: WalkReport, prefix: str) -> list[dict]:
    return [f for f in report.facts if f["face"].startswith(prefix + "@")]


def _verdict_of(report: WalkReport, prefix: str) -> str:
    facts = _facts_for(report, prefix)
    if not facts:
        return "not reached"
    bounces = [f"{f['face']}/{f['field']}" for f in facts if f["verdict"] == "BOUNCE"]
    if bounces:
        return "BOUNCE: " + ", ".join(bounces)
    return f"{len(facts)} facts, no bounce"


def _worst(report: WalkReport, prefix: str) -> str:
    facts = _facts_for(report, prefix)
    if not facts:
        return "BOUNCE"
    return "BOUNCE" if any(f["verdict"] == "BOUNCE" for f in facts) else "MATCH"


if __name__ == "__main__":
    sys.exit(main())
