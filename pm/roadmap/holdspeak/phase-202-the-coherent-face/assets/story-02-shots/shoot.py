#!/usr/bin/env python3
"""HS-202-02 — the shot walk for the first-use doors and truthful state.

One real hub per run, isolated HOME, Playwright Chromium, 1440x900 and
393x852. It changes no product code and never opens the microphone: the
browser context is given NO microphone permission, so `getUserMedia` is
refused by the browser exactly as it is for a person whose permission
dialog they dismissed — which is the state job 1 is about.

Run:
    HOME=$(mktemp -d) \
    PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright \
        uv run python pm/roadmap/holdspeak/phase-202-the-coherent-face/\
assets/story-02-shots/shoot.py
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[6]
TOKEN = "hs-202-02-shot-walk-token"
VIEWPORTS = ((1440, 900), (393, 852))


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class Hub:
    def __init__(self, port: int, token: str, home: str) -> None:
        self.port, self.token, self.home = port, token, home
        self.url = f"http://127.0.0.1:{port}"
        self.proc: subprocess.Popen[str] | None = None

    def start(self, timeout: float = 180.0) -> "Hub":
        env = dict(os.environ)
        env["HOME"] = self.home
        env["HOLDSPEAK_WEB_PORT"] = str(self.port)
        # The arrival's `No brief yet` + `Generate` branch only exists on a
        # desk without one (HS-202-02, Astra's condition 8).
        env["HOLDSPEAK_WALK_SKIP_BRIEF"] = "1"
        env.setdefault("PYTHONUNBUFFERED", "1")
        self.proc = subprocess.Popen(
            [
                sys.executable,
                str(REPO / "scripts" / "walk_working_desk.py"),
                "serve",
                "--port", str(self.port),
                "--token", self.token,
            ],
            cwd=str(REPO), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        print(f"  hub pid={self.proc.pid} home={self.home} port={self.port}", flush=True)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.proc.poll() is not None:
                out = self.proc.stdout.read() if self.proc.stdout else ""
                raise RuntimeError(f"hub died on boot:\n{out[-4000:]}")
            if self.healthy():
                return self
            time.sleep(0.4)
        raise RuntimeError(f"hub never became healthy at {self.url}")

    def healthy(self) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=1.0):
                pass
        except OSError:
            return False
        try:
            req = urllib.request.Request(
                f"{self.url}/health", headers={"X-HoldSpeak-Token": self.token})
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def api(self, method: str, path: str, body: Any = None) -> tuple[int, Any]:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            f"{self.url}{path}", data=data, method=method,
            headers={"X-HoldSpeak-Token": self.token,
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
                try:
                    return resp.status, json.loads(raw)
                except Exception:
                    return resp.status, raw[:400]
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()[:400]
        except Exception as exc:  # noqa: BLE001
            return 0, repr(exc)

    def api_multipart_txt(
        self, path: str, filename: str, text: str, *, title: str = ""
    ) -> tuple[int, Any]:
        """POST one .txt as a multipart upload (the product's own import
        door for a transcript; no audio, no microphone)."""
        boundary = "----hs202boundary"
        parts = [
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\";"
            f" filename=\"{filename}\"\r\nContent-Type: text/plain\r\n\r\n{text}\r\n"
        ]
        if title:
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data;"
                f" name=\"title\"\r\n\r\n{title}\r\n"
            )
        parts.append(f"--{boundary}--\r\n")
        data = "".join(parts).encode()
        req = urllib.request.Request(
            f"{self.url}{path}", data=data, method="POST",
            headers={
                "X-HoldSpeak-Token": self.token,
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.status, resp.read().decode()[:300]
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()[:300]
        except Exception as exc:  # noqa: BLE001
            return 0, repr(exc)

    def stop(self) -> None:
        if self.proc is None or self.proc.poll() is not None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=10)


def close_shelf(page) -> None:
    """The ⌘K shelf is a portal over the whole desk: leave it closed."""
    for _ in range(3):
        if not page.locator("#desk-tool-shelf").count():
            return
        box = page.locator("#desk-tool-shelf input")
        if box.count():
            try:
                box.first.press("Escape")
            except Exception:  # noqa: BLE001
                pass
        page.wait_for_timeout(400)
        if not page.locator("#desk-tool-shelf").count():
            return
        launch = page.locator(".desk-tools-launch")
        if launch.count():
            try:
                launch.first.click(timeout=3000, force=True)
            except Exception:  # noqa: BLE001
                pass
        page.wait_for_timeout(400)


def close_windows(page) -> None:
    """Leave the desk clear for the next shot."""
    for _ in range(3):
        lights = page.locator("[aria-label^='Close ']")
        if not lights.count():
            break
        for i in range(lights.count() - 1, -1, -1):
            try:
                lights.nth(i).click(timeout=1500)
            except Exception:  # noqa: BLE001
                pass
        page.wait_for_timeout(500)
    page.wait_for_timeout(500)


def shoot(page, name: str, width: int) -> None:
    path = HERE / f"{name}-{width}.png"
    page.screenshot(path=str(path))
    print(f"    shot {path.name}", flush=True)


def settle(page, ms: int = 900) -> None:
    page.wait_for_timeout(ms)


def step(name: str, facts: dict[str, Any], width: int, fn) -> None:
    """One step. A miss is RECORDED, never fatal and never silent."""
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        facts.setdefault("step_errors", {}).setdefault(str(width), {})[name] = repr(exc)[:300]
        print(f"    !! {name}: {exc}", flush=True)


def goto_desk(page, hub: Hub, width: int, facts: dict[str, Any] | None = None) -> None:
    """Load the desk. A cold desk answers with the First Words gate; its
    only escape ("Continue later") reaches the desk behind it."""
    page.goto(f"{hub.url}/?token={hub.token}", wait_until="domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=20_000)
    except Exception:  # noqa: BLE001
        pass
    settle(page, 2500)
    gate = page.locator(".desk-first-words")
    if gate.count():
        shoot(page, "first-run", width)
        # HS-202-02 (coordinator ruling): the microphone refusal, on the
        # card a stranger actually meets. This context holds NO microphone
        # permission, so the browser refuses `getUserMedia` and no device
        # is ever opened.
        talk = page.locator(".desk-first-talk")
        if talk.count():
            try:
                talk.first.click(timeout=8000)
                page.wait_for_timeout(5000)
            except Exception:  # noqa: BLE001
                pass
            state = page.locator(".desk-first-words .surface-state-error, "
                                 ".desk-first-words [role='alert']")
            (facts if facts is not None else {}).setdefault("mic_refusal", {})[width] = {
                "message": state.first.inner_text().strip()
                if state.count() else "NONE",
                "verbs": [b.inner_text().strip() for b in
                          page.locator(".desk-first-words button").all()],
            }
            shoot(page, "first-run-mic-refused", width)
            # Astra's counsel finding 1 + condition 8: PRESS it. A photo of
            # a verb is not proof the verb works; the cold-desk registry
            # admitted only `project-setup`, so this press used to fall
            # back to `/` and open nothing.
            check = page.get_by_role("button", name="Check the microphone")
            if check.count():
                try:
                    check.first.click(timeout=8000)
                    page.wait_for_timeout(4000)
                except Exception:  # noqa: BLE001
                    pass
                (facts if facts is not None else {}).setdefault(
                    "mic_recovery_opens", {})[width] = {
                    "setup_window": page.locator("#surface-setup").count(),
                    "new_project_window": page.locator(
                        "#surface-project-setup").count(),
                    "readiness_face": page.locator(
                        "#surface-setup .surface-section, #surface-setup").count(),
                }
                shoot(page, "first-run-microphone-checked", width)
                # The doctor window now sits over the card; close it so the
                # card's own way out is reachable again.
                close_windows(page)
        escape = page.locator(".desk-first-words .btn--ghost")
        if escape.count():
            try:
                escape.first.click(timeout=15000, force=True)
            except Exception:  # noqa: BLE001
                # The card's escape is the one door out of first value; if
                # it is covered, say so rather than leaving a half-walk.
                (facts if facts is not None else {}).setdefault(
                    "gate_escape_failed", {})[width] = True
            settle(page, 3000)


def walk(page, width: int, hub: Hub, facts: dict[str, Any]) -> None:
    goto_desk(page, hub, width, facts)

    def arrival() -> None:
        shoot(page, "arrival", width)
        badge = page.locator('[data-testid="arrival-brief"] .gadget-chip-egress')
        facts.setdefault("brief_badge", {})[width] = (
            badge.first.inner_text().strip() if badge.count() else "ABSENT"
        )
        dock = page.locator(".desk-dock")
        box = dock.first.bounding_box() if dock.count() else None
        facts.setdefault("dock_box", {})[width] = box
        buttons = page.locator(".desk-dock .desk-dock-launch")
        inside = 0
        for i in range(buttons.count()):
            b = buttons.nth(i).bounding_box()
            if b and b["x"] >= 0 and b["x"] + b["width"] <= width + 1:
                inside += 1
        facts.setdefault("dock_buttons", {})[width] = {
            "total": buttons.count(), "inside_viewport": inside,
        }
        orb = page.locator(".desk-dock .desk-orb")
        ob = orb.first.bounding_box() if orb.count() else None
        facts.setdefault("record_orb", {})[width] = ob
        shoot(page, "dock", width)

    def menus() -> None:
        titles = page.locator("[data-menu-id]")
        facts.setdefault("menu_titles", {})[width] = [
            titles.nth(i).get_attribute("data-menu-id") for i in range(titles.count())
        ]
        go = page.locator('[data-menu-id="go"] .desk-verbbar-title')
        if go.count():
            go.first.click()
            settle(page, 700)
        new_note = page.get_by_role("menuitem", name="New Note")
        facts.setdefault("go_has_new_note", {})[width] = new_note.count() > 0
        shoot(page, "go-menu", width)
        page.keyboard.press("Escape")
        settle(page, 500)

    def shelf() -> None:
        launch = page.locator(".desk-tools-launch")
        if launch.count():
            launch.first.click()
        settle(page, 900)
        # The cold shelf: how many doors wear the name `Ask AI`, and how
        # many of them are ghosts (03-interaction-walk.md finding 8).
        facts.setdefault("shelf_ask_doors", {})[width] = page.locator(
            "#desk-tool-shelf .desk-deck-row", has_text="Ask AI").count()
        facts.setdefault("shelf_ask_ghosts", {})[width] = page.locator(
            "#desk-tool-shelf .desk-deck-row.is-ghost", has_text="Ask AI").count()
        box = page.locator("#desk-tool-shelf input")
        if box.count():
            box.first.fill("Notes")
        settle(page, 900)
        selected = page.locator("#desk-tool-shelf .desk-deck-row.is-selected")
        facts.setdefault("shelf_notes_top", {})[width] = (
            selected.first.locator(".desk-deck-label").inner_text().strip()
            if selected.count() else "NONE"
        )
        facts.setdefault("shelf_ghost_rows", {})[width] = page.locator(
            "#desk-tool-shelf .desk-deck-row.is-ghost").count()
        facts.setdefault("shelf_ask_rows", {})[width] = page.locator(
            "#desk-tool-shelf .desk-deck-row", has_text="Ask AI").count()
        shoot(page, "shelf-notes", width)
        close_shelf(page)

    def write_a_thought() -> None:
        thought = page.locator('[data-testid="arrival-develop-thought"]')
        if not thought.count():
            facts.setdefault("thought_window", {})[width] = "VERB ABSENT"
            return
        thought.first.scroll_into_view_if_needed()
        thought.first.click(force=True)
        settle(page, 9000)
        facts.setdefault("thought_window", {})[width] = {
            "thought_face": page.locator(".thought-workspace-window").count(),
            "any_pullout": page.locator(".desk-pullout").count(),
            "speak_surface": page.locator("#surface-dictation").count(),
        }
        shoot(page, "write-a-thought", width)
        close_windows(page)

    def surface(query: str, name: str, after=None) -> None:
        """Open a surface the way a person does: the ⌘K shelf. The hub
        serves only a few SPA routes, so a URL is not a door."""
        close_shelf(page)
        launch = page.locator(".desk-tools-launch")
        if launch.count():
            launch.first.click(timeout=8000)
            settle(page, 700)
        box = page.locator("#desk-tool-shelf input")
        if box.count():
            box.first.fill(query)
            settle(page, 900)
            page.keyboard.press("Enter")
        settle(page, 4500)
        if after is not None:
            after()
        shoot(page, name, width)
        close_shelf(page)
        close_windows(page)

    def desk_memory_facts() -> None:
        facts.setdefault("desk_memory", {})[width] = {
            "body": page.locator('[data-testid="desk-memory-body"]').count(),
            "results_region": page.locator('[data-testid="recall-results"]').count(),
            "rows": page.locator("[data-recall-row]").count(),
            "aria": (page.locator('[data-testid="recall-results"]')
                     .first.get_attribute("aria-label")
                     if page.locator('[data-testid="recall-results"]').count() else ""),
        }

    def concierge_facts() -> None:
        add = page.get_by_role("button", name="Add an engine")
        if add.count():
            add.first.click()
            settle(page, 1200)
        field = page.get_by_role("textbox", name="Server address")
        facts.setdefault("server_placeholder", {})[width] = (
            field.first.get_attribute("placeholder") if field.count() else "ABSENT"
        )

    def settings_facts() -> None:
        rows = page.locator(".surface-ledger-row-primary, .surface-ledger-primary")
        facts.setdefault("settings_rows", {})[width] = [
            rows.nth(i).inner_text().strip() for i in range(rows.count())
        ]

    def meeting_facts() -> None:
        rows = page.locator(".meetings-stream-row-body")
        if rows.count():
            rows.first.click(timeout=8000)
            settle(page, 4000)
        before = len([r for r in facts.get("record_reads", []) if r == width])
        # The product's own return signal — the one the Concierge fires
        # after it applies a set (desk/returnToTask.ts:37).
        page.evaluate(
            "() => window.dispatchEvent("
            "new CustomEvent('holdspeak:settings-updated'))"
        )
        settle(page, 3000)
        after = len([r for r in facts.get("record_reads", []) if r == width])
        facts.setdefault("meeting_record", {})[width] = {
            "title": (
                page.locator(".meetings-detail-head .surface-display")
                .first.inner_text().strip()
                if page.locator(".meetings-detail-head .surface-display").count()
                else "NONE"
            ),
            "route_disclosed": page.locator(
                "[data-testid='detail-route'], [data-testid='detail-route-unavailable']"
            ).count(),
            "run_verb": page.locator(
                "[data-testid='detail-run-intelligence-btn']").count(),
            "record_rereads_on_signal": after - before,
        }
        shoot(page, "meeting-record-refreshed", width)

    def speak_facts() -> None:
        chips = page.locator("#surface-dictation .gadget-chip-egress")
        facts.setdefault("speak_footer_chips", {})[width] = [
            chips.nth(i).inner_text().strip() for i in range(chips.count())
        ]

    def generate_brief() -> None:
        """Astra's condition 8: RUN Generate, on a desk with no brief."""
        section = page.locator('[data-testid="arrival-brief"]')
        verb = page.locator('[data-testid="arrival-brief-generate"]')
        facts.setdefault("generate", {})[width] = {
            "verb_present": verb.count(),
            "badge_before": (
                section.locator(".gadget-chip-egress").first.inner_text().strip()
                if section.locator(".gadget-chip-egress").count() else "ABSENT"
            ),
        }
        if not verb.count():
            return
        shoot(page, "generate-before", width)
        verb.first.click(timeout=8000)
        page.wait_for_timeout(6000)
        receipt = page.locator('[data-testid="arrival-brief-receipt"]')
        facts["generate"][width]["receipt_after"] = (
            receipt.first.inner_text().strip() if receipt.count() else "ABSENT"
        )
        shoot(page, "generate-after", width)

    def meeting_refresh() -> None:
        """Astra's condition 8: a record with a REAL transcript, refreshed
        by the product's own return signal — no browser reload."""
        status, body = hub.api_multipart_txt(
            "/api/meetings/import",
            "hs-202-02-transcript.txt",
            "Karol: The freeze window moves to Sunday.\n"
            "Priya: I will confirm with payments before Friday.\n",
            title="HS-202-02 transcript",
        )
        facts.setdefault("transcript_import", {})[width] = status
        page.reload(wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        surface("Meetings", "meeting-record", meeting_facts)

    step("arrival", facts, width, arrival)
    step("generate", facts, width, generate_brief)
    step("menus", facts, width, menus)
    step("shelf", facts, width, shelf)
    step("write-a-thought", facts, width, write_a_thought)
    def new_note() -> None:
        """Desk > New Note, then the foot's keep receipt (job 3, part 2)."""
        close_shelf(page)
        launch = page.locator(".desk-tools-launch")
        if launch.count():
            launch.first.click(timeout=8000)
            settle(page, 800)
        box = page.locator("#desk-tool-shelf input")
        if box.count():
            box.first.fill("New Note")
            settle(page, 900)
            page.keyboard.press("Enter")
        settle(page, 4000)
        title = page.locator(".desk-editor-body input").first
        if title.count():
            title.fill("A thought I want kept")
        # The editor writes through a 450 ms debounce; wait past it.
        settle(page, 2500)
        receipt = page.locator(".desk-editor-window .surface-footer-receipt-line")
        facts.setdefault("note_keep_receipt", {})[width] = (
            receipt.first.inner_text().strip() if receipt.count() else "ABSENT"
        )
        shoot(page, "note-kept", width)
        close_windows(page)

    step("new-note", facts, width, new_note)
    step("desk-memory", facts, width,
         lambda: surface("Desk memory", "desk-memory", desk_memory_facts))
    step("concierge", facts, width,
         lambda: surface("Models", "concierge-address", concierge_facts))
    step("settings", facts, width,
         lambda: surface("Settings", "settings-hub", settings_facts))
    step("meetings", facts, width, meeting_refresh)
    step("speak", facts, width,
         lambda: surface("Speak", "speak-face", speak_facts))

    def dock_presses() -> None:
        """Astra's counsel finding 9: geometry is not pressability. This
        step is LAST because it is destructive — it opens every window and
        toggles the Floor, which no arrival-dependent step survives."""
        goto_desk(page, hub, width, facts)
        buttons = page.locator(".desk-dock .desk-dock-launch")
        # Astra's counsel finding 9: geometry is not pressability. PRESS
        # every dock launcher and record what answered. The inventory's
        # 393 measure was 0 of 11 clickable.
        # Snapshot the names FIRST: pressing a launcher folds it into a
        # window chip, so an index-based loop goes stale mid-walk.
        names = [
            buttons.nth(i).get_attribute("aria-label") or f"#{i}"
            for i in range(buttons.count())
        ]
        pressed, refused = [], []
        for name in names:
            target = page.locator(
                f'.desk-dock .desk-dock-launch[aria-label="{name}"]')
            try:
                if not target.count():
                    # Already open, so it wears a chip rather than a
                    # launcher — reached, not refused.
                    pressed.append(name)
                    continue
                target.first.click(timeout=4000)
                pressed.append(name)
                page.wait_for_timeout(250)
            except Exception:  # noqa: BLE001
                refused.append(name)
            close_shelf(page)
        facts.setdefault("dock_presses", {})[width] = {
            "total": len(names), "pressed": len(pressed), "refused": refused,
        }
        close_windows(page)

    step("dock-presses", facts, width, dock_presses)



def main() -> int:
    home = os.environ.get("HOME", "")
    if not home or home.startswith("/Users/karol") and not home.startswith("/var"):
        if Path(home).resolve() == Path.home().resolve() and "T/" not in home:
            print("REFUSED: run with an isolated HOME=$(mktemp -d)", file=sys.stderr)
            return 2
    from playwright.sync_api import sync_playwright

    HERE.mkdir(parents=True, exist_ok=True)
    facts: dict[str, Any] = {"home": home}
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for width, height in VIEWPORTS:
            print(f"  == {width}x{height} ==", flush=True)
            # ONE hub per viewport, each with its own HOME: the first-run
            # card is a once-per-desk state, and escaping it at 1440
            # records the disposition on the hub, so a shared hub can never
            # show it twice.
            viewport_home = tempfile.mkdtemp(prefix=f"hs202-{width}-")
            hub = Hub(_free_port(), TOKEN, viewport_home).start()
            facts.setdefault("hubs", {})[width] = hub.url
            # NO microphone permission: the browser refuses `getUserMedia`,
            # which is the state job 1 is about, and no device is opened.
            context = browser.new_context(
                viewport={"width": width, "height": height},
                permissions=[],
            )
            page = context.new_page()
            page.on("pageerror",
                    lambda e: facts.setdefault("page_errors", []).append(str(e)[:300]))
            page.on("console", lambda m: (
                facts.setdefault("console_errors", []).append(m.text[:300])
                if m.type == "error" else None))
            page.on("request", lambda rq: (
                facts.setdefault("record_reads", []).append(width)
                if "/api/meetings/" in rq.url and "?" not in rq.url
                and rq.url.rstrip("/").count("/") == 5 else None))
            page.on("response", lambda r: (
                facts.setdefault("bad_responses", []).append(
                    f"{r.status} {r.request.method} {r.url.split('?')[0]}")
                if r.status >= 400 else None))
            try:
                walk(page, width, hub, facts)
            finally:
                context.close()
                hub.stop()
        browser.close()
    (HERE / "walk-facts.json").write_text(json.dumps(facts, indent=2) + "\n")
    print(json.dumps(facts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
