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
    on_start: Any = None,
    on_stop: Any = None,
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
    on_start, on_stop : Any, optional
        The capture boundary (PHILO-13-13 C3-W): what the hub's runtime
        answers when the face asks it to start or stop a meeting. Omitted,
        the real route refuses a start (501, no capture control).
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
    # PHILO-16 R2: EventKit is per macOS user, not per HOME; a glass hub never
    # reads the owner's real calendars (holdspeak/macos_calendar.py). A test
    # that needs calendars replaces the module's calls.
    monkeypatch.setenv("HOLDSPEAK_MACOS_CALENDAR", "0")
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    # HS-201-04 (counsel item 7): `reset_database()` runs on the way IN and
    # never on the way out, so the singleton this rig creates — pointing at
    # its own seeded tmp database — outlived the module and was read by the
    # next one in the same process. `monkeypatch` restores these to the
    # `None` they hold right now, so the next module builds its own.
    monkeypatch.setattr(db_core, "_db", None, raising=False)
    monkeypatch.setattr(db_core, "_observer", None, raising=False)

    kwargs: dict[str, Any] = {}
    if gh_runner is not None:
        kwargs["gh_runner"] = gh_runner
    if acli_runner is not None:
        kwargs["acli_runner"] = acli_runner

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=on_stop or (lambda: None),
            get_state=lambda: {},
            on_start=on_start,
        ),
        auth_token=token,
        **kwargs,
    )
    return server, server.start()


def park_builtin_folder() -> None:
    """Park the built-in "HoldSpeak folder" destination in this rig's database.

    The owner's ruling of 2026-10-05 gives every desk that destination. The
    Phase 10, 11 and 13 Send boards were drawn and ratified on desks without
    it (their first board is NO DESTINATION; their rows, counts and pointer
    passes are measured on their own destinations). Those rigs call this
    right after ``_boot`` to keep the desk they were drawn on. The product
    has no verb that parks it (``channel.remove_destination`` refuses
    ``destination_builtin``); this is a direct write to the rig's database.
    """
    from holdspeak.db import get_database
    from holdspeak.db.channels import BUILTIN_FOLDER_ID

    with get_database()._connection() as conn:
        conn.execute("UPDATE channel_destinations SET state='parked', parked_at=datetime('now') WHERE id=?",
                     (BUILTIN_FOLDER_ID,))
        conn.commit()


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


_CLEAR_WINDOWS_JS = """async (token) => {
  const headers = {authorization: `Bearer ${token}`, "content-type": "application/json"};
  const listed = await (await fetch("/api/desk/windows", {headers})).json();
  for (const w of listed.windows || []) {
    await fetch(`/api/desk/windows/${encodeURIComponent(w.id)}/close`, {method: "POST", headers, body: "{}"});
  }
  return (listed.windows || []).length;
}"""


def clear_hub_windows_http(base: str, token: str = "glass-test") -> int:
    """:func:`clear_hub_windows` with no page (a rig whose page may be blank)."""
    import json as _json
    import urllib.parse
    import urllib.request

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    with urllib.request.urlopen(urllib.request.Request(f"{base}/api/desk/windows", headers=headers)) as resp:
        windows = _json.loads(resp.read() or b"{}").get("windows") or []
    for window in windows:
        request = urllib.request.Request(
            f"{base}/api/desk/windows/{urllib.parse.quote(window['id'], safe='')}/close",
            data=b"{}", method="POST", headers=headers)
        urllib.request.urlopen(request).close()
    return len(windows)


def clear_hub_windows(page: Any, token: str = "glass-test") -> int:
    """PHILO-16 (16b): close every window the hub holds for this desk.

    The hub owns the desk's windows; every browser context on one hub is a
    view of the SAME desk (COMPOSITOR.md §13 L1). A rig that opens a second
    page and wants it to start on an empty desk (the way a fresh browser
    cache used to) clears the hub's windows first. Returns how many closed.
    """
    return int(page.evaluate(_CLEAR_WINDOWS_JS, token))


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


def _images_loaded(page: Any, scope: str = "[data-testid=desk-screen]", timeout: int = 15_000) -> None:
    """Wait until every img in `scope` is decoded (complete, naturalWidth > 0).

    PHILO-14 A1d: _settle waits for animations only, so a shot could catch
    the icons with their names drawn and no sprite yet. On a timeout the
    error names each img that did not load, with its src.
    """
    js = f"""() => [...document.querySelectorAll({scope!r} + ' img')]
        .filter(i => !(i.complete && i.naturalWidth > 0)).map(i => i.getAttribute('src'))"""
    try:
        page.wait_for_function(f"() => ({js})().length === 0", timeout=timeout)
    except Exception as exc:  # name the misses, then fail
        raise AssertionError(f"images not loaded in {scope}: {page.evaluate(js)}") from exc


# ── _rendered_text_faults: the frame glass's F3 law, for any scope ──
#
# PHILO-13-02 r2 (Astra's single pass on #734): a receipt check that reads
# innerText proves nothing about readability, because innerText includes the
# text a container clips. This reads the RENDERED boxes, the way
# test_philo13_11_frame_glass.py F3 does: a visible text node whose range runs
# past its nearest clipping ancestor is clipped (an ellipsis counts: the
# words are not on the glass); and no two visible things (text runs outside
# controls, and controls) overlap.

_RENDERED_TEXT_JS = """(args) => {
  const [sel, onGlass] = Array.isArray(args) ? args : [args, false];
  // PHILO-13-18 (onGlass, opt-in): read what is ON THE GLASS.
  //  * A text box a vertical scroll container scrolls to is reachable, so it
  //    is not clipped there (sideways scrolling and a hidden clip still fail).
  //  * Content a closed <details> does not render is not read
  //    (checkVisibility, content-visibility).
  //  * Overlap compares the PAINTED part of each box: the box cut to every
  //    clipping ancestor and the viewport. A row scrolled under a footer, or
  //    the hidden tail of an ellipsis, is not on the glass.
  //  * A single-line ellipsis (text-overflow: ellipsis, nowrap; UX-CANON A.6,
  //    the canvas fence's rule) is recorded in `ellipsis`, not failed.
  //  * A visually-hidden (sr-only, 1 x 1) box is not on the glass.
  //  * An inset (see below) is recorded in `inset`, not failed.
  //  * Words inside a control are read for overlap too.
  // Off (the default), the reader is exactly the #734 reader.
  // a vertical scroller exempts only text the reader can scroll to: the text
  // lies inside the scroll range (an auto box with words shifted above its
  // top, or past its scrollHeight, cannot be scrolled into view)
  const scrollY = (e, tr) => {
    if (!['auto', 'scroll'].includes(getComputedStyle(e).overflowY)) return false;
    const er = e.getBoundingClientRect(), top = tr.top - er.top - e.clientTop + e.scrollTop;
    return top >= -1 && top + tr.height <= e.scrollHeight + 1;
  };
  const painted = (r, el) => {  // el: the first box that may clip r (the text's own element; a control's parent)
    let L = Math.max(r.left, 0), T = Math.max(r.top, 0), R = Math.min(r.right, innerWidth), B = Math.min(r.bottom, innerHeight);
    for (let a = el; a && a !== document.documentElement; a = a.parentElement) {
      const cs = getComputedStyle(a);
      if (cs.overflowX === 'visible' && cs.overflowY === 'visible') continue;
      const ar = a.getBoundingClientRect();
      if (cs.overflowX !== 'visible') { L = Math.max(L, ar.left); R = Math.min(R, ar.right); }
      if (cs.overflowY !== 'visible') { T = Math.max(T, ar.top); B = Math.min(B, ar.bottom); }
    }
    return (R - L > 1 && B - T > 1) ? {left: L, top: T, right: R, bottom: B} : null;
  };
  const rendered = (e) => !onGlass || !e.checkVisibility || e.checkVisibility({contentVisibilityAuto: true});
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && Number(cs.opacity) > 0.05
      && rendered(e) && !(onGlass && (r.width <= 1 || r.height <= 1 || cs.clip === 'rect(0px, 0px, 0px, 0px)')); };  // a visually-hidden (sr-only) box is not on the glass
  const out = {scopes: 0, clipped: [], overlaps: [], ellipsis: [], inset: []};
  const ctl = 'button, [role=button], input, textarea, select, a[href]';
  for (const scope of [...document.querySelectorAll(sel)].filter(visible)) {
    out.scopes++;
    const boxes = [];
    const walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      const text = n.textContent.trim();
      if (!text || !visible(n.parentElement)) continue;
      const range = document.createRange(); range.selectNodeContents(n);
      const tr = range.getBoundingClientRect();
      if (tr.width < 1 || tr.height < 1) continue;
      for (let a = n.parentElement; a && a !== document.documentElement; a = a.parentElement) {
        const cs = getComputedStyle(a);
        const clipX = cs.overflowX !== 'visible', clipY = cs.overflowY !== 'visible';
        if (!clipX && !clipY) continue;
        const ar = a.getBoundingClientRect();
        // on the glass, only a box the reader can scroll sideways (auto/scroll) is "sideways";
        // a hidden overflow that pokes past by its own frame is judged by the text box alone
        const side = a.scrollWidth > a.clientWidth + 1 && (!onGlass || ['auto', 'scroll'].includes(cs.overflowX));
        const pastX = clipX && (tr.left < ar.left - 1 || tr.right > ar.right + 1 || side);
        const pastY = clipY && !(onGlass && scrollY(a, tr)) && (tr.top < ar.top - 1 || tr.bottom > ar.bottom + 1);
        // the ellipsis is drawn by the box that clips (`a`), or by the text's own box
        const es = getComputedStyle(a), hs = getComputedStyle(n.parentElement);
        const ell = onGlass && pastX && !pastY && es.textOverflow === 'ellipsis' && es.whiteSpace === 'nowrap'
          && (a === n.parentElement || hs.whiteSpace === 'nowrap' || es.whiteSpace === 'nowrap');
        if (ell) out.ellipsis.push({text: text.slice(0, 60), in: (a.className || a.tagName).toString().slice(0, 60)});
        else if (pastX || pastY) out.clipped.push(Object.assign({text: text.slice(0, 60), in: (a.className || a.tagName).toString().slice(0, 60)},
          onGlass ? {box: [tr.left, tr.top, tr.right, tr.bottom].map(Math.round), clip: [ar.left, ar.top, ar.right, ar.bottom].map(Math.round),
                     sideways: side} : {}));
        break;
      }
      const tp = onGlass ? painted(tr, n.parentElement) : tr;
      if (!tp) continue;
      const holder = n.parentElement.closest(ctl);
      // on the glass, words INSIDE a control are read too: two words of one
      // control drawn over each other are an overlap (a control and its own
      // words are one thing: `contains` skips that pair)
      if (onGlass || !holder || !scope.contains(holder)) boxes.push({what: text.slice(0, 40), r: tp, el: n.parentElement});
    }
    for (const c of [...scope.querySelectorAll(ctl)].filter(visible)) {
      if (c.parentElement && c.parentElement.closest(ctl)) continue;
      const cp = onGlass ? painted(c.getBoundingClientRect(), c.parentElement) : c.getBoundingClientRect();
      if (!cp) continue;
      boxes.push({what: (c.getAttribute('aria-label') || c.textContent || '').trim().slice(0, 40), r: cp, el: c});
    }
    for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j];
      if (a.el.contains(b.el) || b.el.contains(a.el)) continue;
      const w = Math.min(a.r.right, b.r.right) - Math.max(a.r.left, b.r.left);
      const h = Math.min(a.r.bottom, b.r.bottom) - Math.max(a.r.top, b.r.top);
      if (!(w > 1 && h > 1)) continue;
      if (onGlass) {
        // An inset: a box drawn wholly INSIDE a control's painted box by design
        // -- an aria-hidden nontext glyph (the cycle gadget's arrow), or a
        // control inside a text entry (the in-well mic). Recorded, not failed.
        const inside = (x, y) => x.r.left >= y.r.left - 1 && x.r.right <= y.r.right + 1
          && x.r.top >= y.r.top - 1 && x.r.bottom <= y.r.bottom + 1;
        const glyph = (x) => /^[^\\p{L}\\p{N}]+$/u.test(x.what) && x.el.closest('[aria-hidden="true"]');
        const inset = (x, y) => y.el.matches(ctl) && inside(x, y)
          && (glyph(x) || (x.el.matches(ctl) && y.el.matches('textarea, input')));
        if (inset(a, b) || inset(b, a)) { out.inset.push([a.what, b.what]); continue; }
      }
      out.overlaps.push(onGlass ? [a.what, b.what, [a.r, b.r].map((q) => [q.left, q.top, q.right, q.bottom].map(Math.round))]
        : [a.what, b.what]);
    }
  }
  return out;
}"""


def _rendered_text_faults(page: Any, selector: str, *, on_glass: bool = False) -> dict[str, Any]:
    """Clipped text and overlapping text or controls inside ``selector``, as rendered.

    ``on_glass`` (PHILO-13-18, opt-in) reads only what is on the glass: text a
    vertical scroll container scrolls to is not clipped, a box scrolled out of
    view is not read for overlap, and a single-line ellipsis is recorded in
    ``ellipsis``. Off, the reader is unchanged.
    """
    return page.evaluate(_RENDERED_TEXT_JS, [selector, on_glass])


def _assert_readable(page: Any, selector: str, where: str = "") -> None:
    """Every visible text inside ``selector`` is whole on the glass; nothing overlaps."""
    faults = _rendered_text_faults(page, selector)
    assert faults["scopes"], f"{where}: no visible {selector}"
    assert not faults["clipped"] and not faults["overlaps"], f"{where}: {faults}"


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


# ── FOLDED_WORD_JS: the ONE exception to the 12 px floor for a hidden word ──
#
# PHILO-13-11 (C1, §4 393; owner-ratified 2026-10-02): the phone's screen bar
# draws three controls as pictures and folds their words into the control's
# name. Astra's counsel on #730 found the first reader far too broad (any
# zero-size text under any named ancestor passed: a blank zero-size "Save"
# button, "SEND FAILED" hidden inside a control named "Open"). The exception
# is now exactly the intended picture controls. A text leaf is a folded word
# ONLY when ALL hold:
#   1. the viewport is the phone width (<= 720 px) and the leaf's computed
#      size is 0 (nothing is painted);
#   2. it sits inside one of the screen bar's picture controls: the mark,
#      the egress chip, Search;
#   3. that control PAINTS a replacement (Astra counsel r2): a picture
#      (img/svg) or a ::before glyph that is visible, not display:none, at
#      opacity > 0 with every ancestor at opacity > 0, with a non-zero box
#      inside the viewport; an img must be loaded (complete, naturalWidth >
#      0); a ::before glyph must have content and a non-transparent colour;
#   4. the control's EXPLICIT name (aria-label or title, never the hidden
#      text itself) contains the hidden word.
# Anything else at size 0 is text under the floor. Defines `foldedWord(el, text)`.
FOLDED_WORD_JS = r"""
  const foldedWord = (el, text) => {
    if (window.innerWidth > 720) return false;
    if (parseFloat(getComputedStyle(el).fontSize) !== 0) return false;
    const host = el.closest('.desk-menubar .desk-mark, .desk-menubar .egress-badge, .desk-menubar .desk-tools-launch');
    if (!host) return false;
    const opaque = (node) => {  // the node and every ancestor are painted
      for (let n = node; n && n.nodeType === 1; n = n.parentElement) {
        const s = getComputedStyle(n);
        if (s.display === 'none' || Number(s.opacity) <= 0) return false;
      }
      return getComputedStyle(node).visibility === 'visible';
    };
    const inView = (r) => r.width > 0 && r.height > 0 && r.right > 0 && r.bottom > 0
      && r.left < window.innerWidth && r.top < window.innerHeight;
    const pics = [...host.querySelectorAll('img, svg')].some((p) => {
      if (!opaque(p) || !inView(p.getBoundingClientRect())) return false;
      return p.tagName.toLowerCase() !== 'img' || (p.complete && p.naturalWidth > 0);
    });
    const before = getComputedStyle(host, '::before');
    const ink = /rgba?\(([^)]+)\)/.exec(before.color || '');
    const inkAlpha = ink ? (ink[1].split(/[ ,/]+/).filter(Boolean).map(Number)[3] ?? 1) : 1;
    const glyph = before.content && !['none', 'normal', '""', "''"].includes(before.content)
      && parseFloat(before.fontSize) > 0 && inkAlpha > 0 && before.visibility === 'visible'
      && Number(before.opacity) > 0 && opaque(host) && inView(host.getBoundingClientRect());
    if (!pics && !glyph) return false;
    const norm = (s) => String(s || '').toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
    const word = norm(text);
    const name = norm(host.getAttribute('aria-label')) + '|' + norm(host.getAttribute('title'));
    return word.length > 0 && name.includes(word);
  };
"""


# ── pick_wing: choose a window face, strip or strip menu ──

def pick_wing(page: Any, label: str) -> None:
    """Pick a window face by its label.

    PHILO-13-11 (C1, §3a; owner-ratified 2026-10-02): at 393 a wing strip
    that does not fit the head's one 44 px row folds into ONE strip menu
    Button (``.surface-strip-menu``, the current face + ▾); the face is then
    a checked row of its menu. A strip that fits stays tabs.
    """
    # The fold is measured after the first layout: a strip can show as tabs
    # for a moment and then fold. Wait for the wings, then take the form that
    # is on the glass; a tab that left before the click is a fold, so look again.
    strip = page.locator(".desk-wings .surface-strip-menu")
    tab = page.get_by_role("tab", name=label)
    page.locator(".desk-wings").first.wait_for(timeout=15000)
    for _ in range(20):
        if strip.count():
            strip.first.click()
            page.get_by_role("menuitemcheckbox", name=label).click()
            return
        try:
            tab.click(timeout=1500)
            return
        except Exception:  # noqa: BLE001 - the strip folded under the click; look again
            continue
    raise AssertionError(f"no window face named {label!r}: no tab and no strip menu")


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

    The real InferenceAssignmentService at `capability:` scope. The meeting
    queue's route policy (meeting-intel-queue@2) also reads the group and
    global heads; this helper pins the exact head (PHILO-15 01).
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


# ── PHILO-14 A2: a Project opens as its drawer; the Room is one press away ──

def _room_through_drawer(page: Any, press: Any = None) -> None:
    """A generic open of a Project lands in its drawer (the ruling: the
    drawer is the Project's face; the Room is its intelligence, one press
    away). Press the drawer's Room verb; ``press`` is the rig's own press
    (a tap at 393), default a click."""
    drawer = page.locator(".drawer-window").last
    drawer.wait_for(timeout=30_000)
    room = drawer.get_by_role("button", name="Room", exact=True)
    room.wait_for(timeout=30_000)
    if press:
        press(room)
    else:
        room.click()
    page.locator("#surface-project-memory").wait_for(timeout=30_000)
