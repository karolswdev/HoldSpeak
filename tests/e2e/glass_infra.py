"""HS-167-03 — shared glass test infrastructure.

ONE copy of _boot, _api, _assert_clean, _ensure_build.
The eight 158..166 glass rigs import from here; every rig builds first
(the 163 stale-pixels law).
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]

# ── pinned_desk_zone: keep "now" away from the local week's edge ──
#
# HS-200-03 follow-through. Several rigs seed calendar events relative to
# "now" and then assert they land inside the CURRENT Mon-Sun week the hub
# computes (`DoorService._local_week_bounds`,
# holdspeak/services/door_service.py:482, and
# `_iso_week_range_local`, holdspeak/web/routes/calendar_sources.py). That
# is a true statement about the product only while "now" is far enough
# from the local week's edge. The macOS runner (UTC) ran them late on a
# Sunday: the seeded events fell into next week and nine rigs failed on
# counts. The product is right; the rig's clock was the accident.
#
# So a rig pins the DESK's zone -- the process TZ, which is what
# `datetime.now().astimezone()` in the hub reads and what the browser
# inherits -- to a fixed-offset zone in which "now" is far from both week
# edges. Offsets span 26 hours while the bad band is a few hours wide, so
# such a zone always exists: sweeping every instant of a week, the best
# available zone always leaves at least 13 hours on BOTH sides of "now"
# inside its local week.

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

DESK_ZONE_OFFSETS = range(-12, 15)  # UTC-12 .. UTC+14


def zone_name(offset_hours: int) -> str:
    """The IANA name for a whole-hour fixed offset.

    `Etc/GMT+6` is UTC-06:00 (POSIX sign inversion); Python's TZ handling
    and Chromium read the name identically, and no Etc/GMT zone has DST.
    """
    if offset_hours == 0:
        return "UTC"
    return f"Etc/GMT{'+' if offset_hours < 0 else '-'}{abs(offset_hours)}"


def week_room_hours(offset_hours: int, utc_now: datetime) -> float:
    """Hours of the local Mon-Sun week on the tighter side of ``utc_now``."""
    local = utc_now + timedelta(hours=offset_hours)
    monday = (local - timedelta(days=local.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    before = (local - monday).total_seconds() / 3600
    after = (monday + timedelta(days=7) - local).total_seconds() / 3600
    return min(before, after)


def lawful_desk_zone(utc_now: datetime | None = None) -> str:
    """The fixed-offset zone leaving the most room on both week edges."""
    now = utc_now or datetime.now(tz=timezone.utc)
    best = max(DESK_ZONE_OFFSETS, key=lambda off: week_room_hours(off, now))
    return zone_name(best)


@contextmanager
def pinned_desk_zone():
    """Run the block with the desk's local zone pinned away from the edge."""
    import time as _time

    previous = os.environ.get("TZ")
    os.environ["TZ"] = lawful_desk_zone()
    _time.tzset()
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = previous
        _time.tzset()


def local_week_bounds_now() -> tuple[datetime, datetime]:
    """Monday 00:00 and next Monday 00:00 of the CURRENT LOCAL week.

    The hub runs in this process's zone, so a rig that reads this reads the
    same week the product draws.
    """
    local_now = datetime.now().astimezone()
    monday = (local_now - timedelta(days=local_now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0,
    )
    return monday, monday + timedelta(days=7)


# ── _ensure_build: the 163 stale-bundle law, honestly ──
#
# A rig that trusts an existing bundle shoots stale pixels with fresh
# timestamps (the 163 scar). So: build whenever ANY web source is newer
# than the built marker, under a cross-process file lock so xdist
# workers never rebuild over each other (the first builds, the rest
# wait and find a fresh marker). Once per process after that.

import fcntl
import time

_build_done = False
_WEB_SRC_DIRS = ("src", "public")
_WEB_FILES = ("package.json", "vite.config.ts", "tsconfig.json", "index.html")


def _newest_web_source_mtime() -> float:
    web = REPO / "web"
    newest = 0.0
    for name in _WEB_FILES:
        f = web / name
        if f.exists():
            newest = max(newest, f.stat().st_mtime)
    for d in _WEB_SRC_DIRS:
        root = web / d
        if not root.exists():
            continue
        for f in root.rglob("*"):
            if f.is_file():
                newest = max(newest, f.stat().st_mtime)
    return newest


def _ensure_build() -> None:
    """Build the web bundle if any web source is newer than the marker.

    Cross-process safe (fcntl lock under web/); once per process after
    the first check. Never trusts a marker older than the sources.
    """
    global _build_done
    if _build_done:
        return
    built_marker = REPO / "holdspeak" / "static" / "_built" / "index.html"
    lock_path = REPO / "web" / ".glass-build.lock"
    with open(lock_path, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            # Trust the OLDEST built chunk, never index.html: the marker
            # can be touched by anything; a build that raced or failed
            # midway leaves stale chunks behind it (seen live 2026-09-03:
            # a fresh marker over 13-minute-old chunks).
            assets_dir = built_marker.parent / "assets"
            chunk_mtimes = [f.stat().st_mtime for f in assets_dir.glob("*.js")] if assets_dir.exists() else []
            built_mtime = min(chunk_mtimes) if (chunk_mtimes and built_marker.exists()) else 0.0
            if built_mtime >= _newest_web_source_mtime():
                _build_done = True
                return
            started = time.monotonic()
            result = subprocess.run(
                ["npm", "--prefix", str(REPO / "web"), "run", "build"],
                capture_output=True, text=True, timeout=300,
            )
            assert result.returncode == 0, (
                f"Web build failed:\n{result.stderr}\n{result.stdout}"
            )
            assert built_marker.exists(), "Web build produced no marker"
            _build_done = True
            print(f"[glass_infra] web bundle rebuilt in {time.monotonic() - started:.1f}s")
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


# ── _boot: isolated MeetingWebServer with fresh DB ──

def _boot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    token: str = "glass-test",
    gh_runner: Any = None,
    acli_runner: Any = None,
) -> tuple[Any, str]:
    """Boot a real MeetingWebServer with isolated DB and HOME.

    Parameters
    ----------
    token : str
        Auth token for the hub.
    gh_runner : Any, optional
        Injected gh CLI runner (hs161/hs164 GitHub glass).
    acli_runner : Any, optional
        Injected acli runner (hs166 Jira glass).
    """
    global _current_token
    _current_token = token

    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    browser_cache = Path(
        os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH",
            Path.home() / "Library/Caches/ms-playwright",
        )
    )
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_cache))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()

    kwargs: dict[str, Any] = {}
    if gh_runner is not None:
        kwargs["gh_runner"] = gh_runner
    if acli_runner is not None:
        kwargs["acli_runner"] = acli_runner

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=token,
        **kwargs,
    )
    return server, server.start()


# ── _api: browser-side fetch (asserting, returns payload dict) ──

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


def _api(
    page: Any,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    *,
    token: str = "glass-test",
) -> dict[str, Any]:
    """Browser-side fetch through the real hub.  Asserts status < 300."""
    result = page.evaluate(_FETCH_JS, [method, path, body, token])
    assert result["status"] < 300, f"HTTP {result['status']}: {result}"
    payload = result["payload"]
    return payload if isinstance(payload, dict) else {}


def _api_allow_error(
    page: Any,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    *,
    token: str = "glass-test",
) -> tuple[int, Any]:
    """Like _api but returns (status, payload) without asserting."""
    result = page.evaluate(_FETCH_JS, [method, path, body, token])
    return result["status"], result["payload"]


def _api_text(
    page: Any,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    *,
    token: str = "glass-test",
) -> str:
    """Browser-side fetch returning raw text (no JSON parse, no assert)."""
    result = page.evaluate(
        """async ([method, path, body, token]) => {
          const response = await fetch(path, {
            method,
            headers: {
              authorization: `Bearer ${token}`,
              ...(body ? {"content-type": "application/json"} : {}),
            },
            body: body ? JSON.stringify(body) : undefined,
          });
          return await response.text();
        }""",
        [method, path, body, token],
    )
    return result


# ── _settle: wait for all CSS animations to finish ──

def _settle(page: Any) -> None:
    """Wait for all CSS animations to finish before screenshotting.

    HS-168-04: surface.css animates sections/cards with surface-rise-in
    (opacity 0 -> 1 over --duration-medium).  A shot taken mid-animation
    captures elements at partial opacity -- the 163 stale-pixels family's
    sibling: mid-animation pixels.
    """
    page.evaluate(
        """() => {
            const anims = document.getAnimations();
            if (anims.length === 0) return;
            return Promise.race([
                Promise.all(anims.map(a => a.finished.catch(() => null))),
                new Promise(r => setTimeout(r, 2000)),
            ]);
        }"""
    )
    page.wait_for_timeout(120)


# ── _assert_clean: overflow + JS error check ──

def _assert_clean(page: Any, errors: list[str]) -> None:
    """Overflow + JS error assertion.

    Filters ResizeObserver loop-limit warnings (browser noise, not a
    real error — the 5-copy majority already filters them).
    """
    real_errors = [e for e in errors if "ResizeObserver" not in e]
    assert not real_errors, real_errors
    assert page.evaluate(
        "document.documentElement.scrollWidth <= window.innerWidth"
    )


# ── _normal_chair: cross the First Sentence gate ──

def _normal_chair(page: Any) -> None:
    """Cross the First Sentence gate without blocking."""
    chair = page.locator(".chair")
    chair.wait_for()
    if chair.evaluate("element => element.classList.contains('chair-first-value')"):
        page.get_by_role("button", name="Continue later", exact=True).click()
    page.locator(".chair:not(.chair-first-value)").wait_for()


# ── seed_meeting_engines: pin the meeting path so a rig can be quiet ──
#
# HS-201-01: the Chair names the ONE thing the meeting path needs. On a
# cold HOME nothing is assigned, so `Nothing needs you` is no longer the
# truth of an empty desk -- a SETUP row says `No engine yet`. A rig whose
# subject is NOT setup (the Door, the arrival's quiet state, the
# attention band, coverage) pins both halves of the path first, and then
# asserts the same quiet face it always did.

SUMMARY_CAPABILITY = "meeting.deferred_analysis"
SPEECH_CAPABILITY = "speech.transcribe"
ENGINE_PROFILE = "hs201-meeting-engine"


def engine_profile(profile_id: str = ENGINE_PROFILE) -> None:
    """One real local profile that can serve BOTH halves of the path.

    The summary capability declares structured output and its own result
    schema (`holdspeak/inference_capabilities.py:1068`), so the profile
    must claim both or the assignment is refused as incompatible;
    `speech.transcribe` admits audio (`:1063`), so the profile carries the
    audio modality and that capability's result claim too.
    """
    from holdspeak.db import get_database
    from tests.unit.test_phase143_inference_assignments import _profile, _result_claim

    _profile(
        get_database(),
        profile_id,
        claims=(
            "language",
            "structured_output",
            _result_claim(SUMMARY_CAPABILITY),
            _result_claim(SPEECH_CAPABILITY),
        ),
        modalities=("language", "text", "audio"),
    )


def assign_engine(capability: str, ordinal: int, *, profile_id: str = ENGINE_PROFILE) -> None:
    """Assign that engine to ONE capability, the product's way.

    The real InferenceAssignmentService at `capability:` scope — the only
    scope the meeting queue's service route policy may read
    (`inference_service_route_policy.py:43`, `:93`).
    """
    from holdspeak.db import get_database
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    db = get_database()
    owner = Principal(PrincipalKind.OWNER, "hs201-owner")
    # The head's own revision, exactly as the service reads it
    # (`inference_assignment_service.py:402`): a cleared head keeps its
    # revision ledger, so 0 would collide on the next save.
    with db._connection() as conn:
        row = conn.execute(
            "SELECT revision FROM inference_assignment_heads WHERE assignment_key=?",
            (f"capability:{capability}",),
        ).fetchone()
    expected = int(row["revision"]) if row is not None else 0
    InferenceAssignmentService(db).set_assignment(owner, {
        "command_id": f"hs201-assign-{capability.replace('.', '-')}-{ordinal}",
        "expected_revision": expected,
        "scope": {"kind": "capability", "capability_id": capability},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })


def seed_meeting_engines() -> None:
    """Both halves of the meeting path assigned: no SETUP row on the Chair."""
    engine_profile()
    assign_engine(SUMMARY_CAPABILITY, 1)
    assign_engine(SPEECH_CAPABILITY, 2)
