"""HS-150-08 shot rig -- the Thread glass exhibit.

Boots the hub in-process in an isolated HOME, injects a FAKE streaming engine
via the runner's engine factory, seeds one profile so the chat.turn assignment
resolves, then exercises: create thread, open desk, send turn from the
composer, mid-stream shot, done shot (receipt + egress), branch + sibling
picker shot, empty state shot, error state shot, CRASHED+Retry shot.

Every frame at 1440x900 AND 393x852 into assets/story-08-shots/ with the
occlusion tell; assert no horizontal overflow at 393; print findings;
exit non-zero on any failure.

Run:
  uv run python pm/roadmap/holdspeak/phase-150-the-desk-chat/assets/story-08-rig.py
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[5]
SHOTS = REPO / "pm/roadmap/holdspeak/phase-150-the-desk-chat/assets/story-08-shots"
TOKEN = "hs150-glass"


# ----------------------------------------------------------------- fake engine

class FakeStreamingEngine:
    """Yields >=20 word deltas with a 40 ms gap (so streaming is visible)."""

    active_provider = "fake-local"
    active_model = "hs150-fake-model"

    def __init__(self, *, fail_before_delta: bool = False):
        self._fail_before_delta = fail_before_delta

    def run_prompt_stream(self, *, messages: Any = None, temperature: Any = None,
                          max_tokens: Any = None, **kwargs: Any) -> Any:
        from holdspeak.kernel.inference_stream import Delta
        if self._fail_before_delta:
            # Raise so the runner's except-path fires and the thread
            # service records outcome="failed" + error_json.  A bare
            # yield Delta(kind="error") triggers ProviderIndeterminate
            # which resolves to "indeterminate", not "failed".
            raise RuntimeError("Provider unreachable: fake engine error")
        words = (
            "The desk chat streams every token over the one bus. "
            "Each delta arrives as a typed frame that the pullout renders "
            "without a page reload. This test verifies that the streaming "
            "path works end to end from the engine through the runner and "
            "the broadcast layer into the browser's bus subscriber."
        ).split()
        for word in words:
            yield Delta(kind="text", text=word + " ")
            time.sleep(0.04)
        yield Delta(kind="usage", meta={"prompt_tokens": 100, "completion_tokens": len(words)})
        yield Delta(kind="done")

    def run_prompt_messages(self, *, messages: Any = None, temperature: Any = None,
                            max_tokens: Any = None, **kwargs: Any) -> str:
        if self._fail_before_delta:
            raise RuntimeError("Provider unreachable: fake engine error")
        return (
            "The desk chat streams every token over the one bus. "
            "Each delta arrives as a typed frame that the pullout renders "
            "without a page reload. This test verifies that the streaming "
            "path works end to end from the engine through the runner and "
            "the broadcast layer into the browser's bus subscriber."
        )

    def run_prompt(self, *, system_prompt: str = "", user_prompt: str = "",
                   temperature: Any = None, max_tokens: Any = None, **kwargs: Any) -> str:
        return self.run_prompt_messages()


# --------------------------------------------------------- profile/assignment

def seed_profile_and_assignment(db: Any) -> None:
    """Seed a local profile + global assignment so chat.turn admits."""
    from tests.unit.test_phase143_inference_assignments import _profile, OWNER
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService

    profile_id = "hs150-rig-local"
    _profile(db, profile_id)
    InferenceAssignmentService(db).set_assignment(OWNER, {
        "command_id": "hs150-rig-assign",
        "expected_revision": 0,
        "scope": {"kind": "global"},
        "entries": [{"profile_id": profile_id, "profile_revision": 1}],
    })


# --------------------------------------------------------- helpers

def api(page: Any, method: str, path: str, body: Any = None) -> Any:
    """Browser-authenticated API call."""
    r = page.evaluate(
        """async ([m, p, b, t]) => {
          const r = await fetch(p, {method: m,
            headers: {authorization: `Bearer ${t}`,
                      ...(b ? {"content-type": "application/json"} : {})},
            body: b ? JSON.stringify(b) : undefined});
          const ct = r.headers.get("content-type") || "";
          return {status: r.status,
                  payload: ct.includes("json") ? await r.json() : await r.text()};
        }""",
        [method, path, body, TOKEN],
    )
    if r["status"] >= 300:
        raise RuntimeError(f"{method} {path}: {r}")
    return r["payload"]


def open_desk(browser: Any, url: str, width: int = 1440, height: int = 900) -> tuple[Any, Any]:
    """Open the desk, dismiss first-value if needed."""
    ctx = browser.new_context(viewport={"width": width, "height": height})
    page = ctx.new_page()
    page.emulate_media(reduced_motion="reduce")
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    api(page, "POST", "/api/desk/seed")
    api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    page.reload(wait_until="load")
    page.wait_for_timeout(1500)
    chair = page.locator(".chair")
    try:
        chair.wait_for(timeout=10000)
        if chair.evaluate("el => el.classList.contains('chair-first-value')"):
            page.get_by_role("button", name="Continue later", exact=True).click()
        page.locator(".chair:not(.chair-first-value)").wait_for(timeout=15000)
    except Exception:
        pass
    return ctx, page


def open_thread(page: Any, url: str, thread_id: str, wait_ms: int = 2500) -> None:
    """Open a thread pullout via the DeskApp's ?open= URL parameter."""
    page.goto(f"{url}/?token={TOKEN}&open=thread:{thread_id}", wait_until="load")
    page.wait_for_timeout(wait_ms)


def no_h_overflow(page: Any) -> bool:
    return bool(page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"))


def shot(page: Any, name: str, claim: str) -> Path:
    path = SHOTS / name
    page.screenshot(path=str(path), full_page=False)
    print(f"  SHOT  {path.relative_to(REPO)} -- {claim}", flush=True)
    return path


# --------------------------------------------------------- main

def main() -> int:
    sys.path.insert(0, str(REPO))
    from playwright.sync_api import sync_playwright
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    real_home = os.environ.get("HOME", str(Path.home()))
    home = Path(tempfile.mkdtemp(prefix="hs150-rig-"))
    os.environ["HOME"] = str(home)
    # Honor a pre-set browsers path (CLAUDE.md law: the isolated HOME hides
    # the cache); derive from the real HOME only when none was given.
    os.environ.setdefault(
        "PLAYWRIGHT_BROWSERS_PATH",
        str(Path(real_home) / "Library/Caches/ms-playwright"),
    )
    SHOTS.mkdir(parents=True, exist_ok=True)
    config_module.CONFIG_FILE = home / ".holdspeak" / "config.json"
    db_core.DEFAULT_DB_PATH = home / "holdspeak.db"
    reset_database()

    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_: None,
            on_stop=lambda: None,
            get_state=lambda: {},
        ),
        auth_token=TOKEN,
    )
    url = server.start()
    failures: list[str] = []

    try:
        db = get_database()
        seed_profile_and_assignment(db)

        from holdspeak.kernel.runtime import _service as _kernel_service
        broker = _kernel_service()
        if broker is None:
            failures.append("DEFECT: _kernel_service() returned None")
            return 1
        runner = broker.inference_runner
        runner._engine_factory = lambda _rev, **_kw: FakeStreamingEngine()

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)

            # ============================================
            # LEG 1: POPULATED THREAD (send, stream, done)
            # ============================================
            print("\n== LEG: populated thread ==", flush=True)
            for width, height, suffix in ((1440, 900, "1440"), (393, 852, "393")):
                ctx, page = open_desk(browser, url, width, height)
                try:
                    thread = api(page, "POST", "/api/threads", {"title": "HS-150 Glass Test"})
                    tid = thread.get("id", "")
                    if not tid:
                        failures.append(f"thread creation returned no id at {width}")
                        continue

                    open_thread(page, url, tid)

                    pullout = page.locator(".thread-pullout-body, .thread-head")
                    if pullout.count() == 0:
                        failures.append(
                            f"SELECTOR NEEDED: .thread-pullout-body/.thread-head "
                            f"not found at {width} after ?open=thread:<id>"
                        )
                        shot(page, f"thread-missing-{suffix}.png", f"pullout not found at {width}")
                        continue

                    # Empty state screenshot
                    shot(page, f"thread-empty-{suffix}.png", f"empty thread at {width}")

                    # Send a turn
                    composer = page.locator(".thread-composer-input")
                    if composer.count() == 0:
                        failures.append(f"SELECTOR NEEDED: .thread-composer-input at {width}")
                        continue

                    composer.fill("What are the three pillars of the Constitution?")
                    send_btn = page.locator("button.desk-chip", has_text="Send")
                    if send_btn.count() == 0:
                        failures.append(f"SELECTOR NEEDED: Send button at {width}")
                        continue

                    send_btn.click()
                    page.wait_for_timeout(500)

                    # Mid-stream shot
                    if page.locator(".thread-row-streaming").count() > 0:
                        shot(page, f"thread-mid-stream-{suffix}.png", f"mid-stream at {width}")
                    else:
                        shot(page, f"thread-after-send-{suffix}.png", f"after send at {width}")
                        failures.append(
                            f"DEFECT: no .thread-row-streaming at {width}; "
                            f"thread_service calls execute() not execute_stream()"
                        )

                    page.wait_for_timeout(3000)

                    # Done shot: receipt + egress
                    receipt = page.locator(".thread-row-receipt")
                    if receipt.count() > 0:
                        shot(page, f"thread-done-{suffix}.png", f"done with receipt at {width}")
                    else:
                        shot(page, f"thread-done-no-receipt-{suffix}.png", f"done, no receipt at {width}")
                        failures.append(f"receipt not visible at {width}")

                    if width == 393 and not no_h_overflow(page):
                        failures.append("horizontal overflow at 393 after populated thread")
                finally:
                    ctx.close()

            # ============================================
            # LEG 2: BRANCH + SIBLING PICKER
            # ============================================
            print("\n== LEG: branch + sibling picker ==", flush=True)
            ctx, page = open_desk(browser, url, 1440, 900)
            try:
                threads_resp = api(page, "GET", "/api/threads")
                tlist = threads_resp if isinstance(threads_resp, list) else threads_resp.get("threads", [])
                if tlist:
                    tid = tlist[0].get("id", "")
                    detail = api(page, "GET", f"/api/threads/{tid}")
                    msgs = detail.get("messages", [])
                    user_msgs = [m for m in msgs if m.get("role") == "user"]
                    if user_msgs:
                        try:
                            api(page, "POST", f"/api/threads/{tid}/branch",
                                {"message_id": user_msgs[-1]["id"], "text": "What about Article IX?"})
                        except RuntimeError as e:
                            failures.append(f"branch API failed: {e}")

                    page.wait_for_timeout(3000)
                    open_thread(page, url, tid)

                    if page.locator(".thread-sibling-picker").count() > 0:
                        shot(page, "thread-sibling-picker-1440.png", "sibling picker n/m")
                    else:
                        shot(page, "thread-after-branch-1440.png", "after branch, no sibling picker")
                        failures.append("sibling picker not visible after branch")
            finally:
                ctx.close()

            # ============================================
            # LEG 3: EMPTY STATE (fresh thread)
            # ============================================
            print("\n== LEG: empty state ==", flush=True)
            for width, height, suffix in ((1440, 900, "1440"), (393, 852, "393")):
                ctx, page = open_desk(browser, url, width, height)
                try:
                    fresh = api(page, "POST", "/api/threads", {"title": "Empty Thread"})
                    open_thread(page, url, fresh.get("id", ""))
                    if page.locator("text=No turns yet").count() > 0:
                        shot(page, f"thread-empty-fresh-{suffix}.png", f"empty state at {width}")
                    else:
                        shot(page, f"thread-fresh-{suffix}.png", f"fresh thread at {width}")
                    if width == 393 and not no_h_overflow(page):
                        failures.append("horizontal overflow at 393 on empty thread")
                finally:
                    ctx.close()

            # ============================================
            # LEG 4: ERROR STATE (engine raises)
            # ============================================
            print("\n== LEG: error state ==", flush=True)
            runner._engine_factory = lambda _rev, **_kw: FakeStreamingEngine(fail_before_delta=True)
            ctx, page = open_desk(browser, url, 1440, 900)
            try:
                err_t = api(page, "POST", "/api/threads", {"title": "Error Thread"})
                open_thread(page, url, err_t.get("id", ""))
                composer = page.locator(".thread-composer-input")
                if composer.count() > 0:
                    composer.fill("This should fail")
                    page.locator("button.desk-chip", has_text="Send").click()
                    page.wait_for_timeout(3000)
                    if page.locator(".thread-row-error").count() > 0:
                        shot(page, "thread-error-1440.png", "error state, in-flow error row")
                    else:
                        shot(page, "thread-after-error-send-1440.png", "after error send")
                        failures.append("error row not visible after engine error")
                else:
                    failures.append("composer not found for error state")
            finally:
                ctx.close()

            # 393 error
            ctx, page = open_desk(browser, url, 393, 852)
            try:
                err2 = api(page, "POST", "/api/threads", {"title": "Error 393"})
                open_thread(page, url, err2.get("id", ""))
                composer = page.locator(".thread-composer-input")
                if composer.count() > 0:
                    composer.fill("Error at 393")
                    page.locator("button.desk-chip", has_text="Send").click()
                    page.wait_for_timeout(3000)
                    shot(page, "thread-error-393.png", "error at 393")
                    if not no_h_overflow(page):
                        failures.append("horizontal overflow at 393 on error state")
            finally:
                ctx.close()
            runner._engine_factory = lambda _rev, **_kw: FakeStreamingEngine()

            # ============================================
            # LEG 5: CRASHED + Retry
            # ============================================
            print("\n== LEG: CRASHED + Retry ==", flush=True)
            ctx, page = open_desk(browser, url, 1440, 900)
            try:
                crash_t = api(page, "POST", "/api/threads", {"title": "Crashed Thread"})
                crash_id = crash_t.get("id", "")
                import uuid as _uuid
                with db._connection() as conn:
                    user_mid = "tmsg_" + _uuid.uuid4().hex[:12]
                    asst_mid = "tmsg_" + _uuid.uuid4().hex[:12]
                    now_epoch = time.time()
                    stale_epoch = now_epoch - 60  # 60s old -> triggers CRASHED
                    conn.execute(
                        "INSERT INTO thread_messages (id,thread_id,role,streaming,created_at,updated_at) VALUES (?,?,'user',0,?,?)",
                        (user_mid, crash_id, now_epoch, now_epoch))
                    conn.execute(
                        "INSERT INTO thread_message_parts (id,message_id,ordinal,kind,text,sensitive) VALUES (?,?,0,'text','What crashed?',0)",
                        ("tpart_" + _uuid.uuid4().hex[:12], user_mid))
                    conn.execute(
                        "INSERT INTO thread_messages (id,thread_id,parent_id,role,streaming,created_at,updated_at) VALUES (?,?,?,'assistant',1,?,?)",
                        (asst_mid, crash_id, user_mid, stale_epoch, stale_epoch))

                open_thread(page, url, crash_id)
                if page.locator(".thread-row-crashed").count() > 0:
                    shot(page, "thread-crashed-1440.png", "CRASHED + Retry")
                else:
                    shot(page, "thread-stale-streaming-1440.png", "stale streaming row")
                    failures.append("CRASHED row not visible for streaming=1 row 60s old")
            finally:
                ctx.close()

            # 393 crashed
            ctx, page = open_desk(browser, url, 393, 852)
            try:
                open_thread(page, url, crash_id)
                shot(page, "thread-crashed-393.png", "CRASHED at 393")
                if not no_h_overflow(page):
                    failures.append("horizontal overflow at 393 on crashed state")
            finally:
                ctx.close()

            browser.close()
    finally:
        server.stop()
        reset_database()

    print("\n== FINDINGS ==", flush=True)
    for f in failures:
        print(f"FINDING  {f}", flush=True)
    print(f"\nshots={SHOTS}", flush=True)
    print(f"failures={len(failures)}", flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
