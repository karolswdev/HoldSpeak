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
            marker_mtime = built_marker.stat().st_mtime if built_marker.exists() else 0.0
            if marker_mtime >= _newest_web_source_mtime():
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
            # The marker must now be the newest thing on disk.
            os.utime(built_marker, None)
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
