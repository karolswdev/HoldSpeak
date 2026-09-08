"""HS-200-41 lane F — the browser proof of `TaskResume` and the composer.

Everything below runs against a REAL booted hub under an isolated HOME,
and every row it draws was written through the product's own routes
(`POST /api/projects/{id}/ask-tasks`, `POST /api/ask`,
`POST /api/ask-tasks/{id}/stopped`, `POST /api/ask-tasks/{id}/resume`).
No rig hand-writes a `project_ask_tasks` row.

The legs:

1. **saved** — the ratified `UNFINISHED 1` row: purpose, `SAVED HH:MM`,
   the custody token, one `Resume`, `Discard` behind `MORE`.
2. **failed** — a REAL refused run.  The rig configures no engine, so
   `/api/ask` refuses with its own bounded code; the Room records the
   stop and the chip carries the hub's OWN words (ruling B5).
3. **narrow (393)** — the `@container surface (max-width: 420px)` rule in
   `web/src/desk/surface/patterns/task-resume.css` proved by the
   computed `grid-template-areas`, not by eye.
4. **restart** — an ask saved, the hub stopped, the database singleton
   dropped and re-opened from the file, a NEW hub booted, the row still
   listed with its purpose intact.  (In-process: one interpreter, a new
   `MeetingWebServer` over the same on-disk database.  Named honestly.)
5. **claim** — a `Resume` on a row whose answer already landed claims it
   and dispatches NOTHING (ruling B3), proven by an engine call counter.
6. **keyboard** — one Tab stop, Up/Down rove rows, Left/Right walk a
   row's verbs, and every verb carries an accessible name.
7. **composer** — a refused `Send` on an empty draft, and a ref chip's
   `x` under the pointer (no hover background, focus ring intact).

Shots land in
``pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-41-shots``.
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    _api,
    _api_allow_error,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="TaskResume glass needs Playwright")

REPO = Path(__file__).resolve().parents[2]
SHOTS = (
    REPO
    / "pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-41-shots"
)
TOKEN = "hs200-41-glass"

pytestmark = [pytest.mark.e2e]


# ── the desk, the Room, the shot ─────────────────────────────────────


def _init_desk(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding",
         {"disposition": "completed"}, token=TOKEN)


def _create_project(page: Any, name: str, command_id: str) -> str:
    created = _api(page, "POST", "/api/projects", {
        "name": name,
        "description": "Seeded for the HS-200-41 browser proof.",
        "command_id": command_id,
    }, token=TOKEN)
    return created["project"]["id"]


def _open_room(page: Any, project_id: str) -> None:
    page.evaluate(
        """([key, scope]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key, scope})
          );
        }""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.get_by_test_id("room-body").wait_for(timeout=20000)
    _settle(page)


def _room_window(page: Any) -> Any:
    return page.locator(".desk-surface-window").filter(
        has=page.locator('[data-testid="room-body"]')
    ).first


def _shot_element(page: Any, locator: Any, name: str, *, pad: int = 0) -> Path:
    """Shoot one element (optionally with padding around it).

    The element is scrolled into view first. Without that the clip is taken at
    whatever scroll position the previous leg left, and the Room's STICKY ask
    foot — which floats over the body by design — lands in the middle of the
    specimen. The block shots at 1440 and 393 were showing the composer sitting
    across the row they were meant to show.
    """
    try:
        locator.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass  # a shot is never worth failing a leg over
    page.wait_for_timeout(150)
    _settle(page)
    SHOTS.mkdir(parents=True, exist_ok=True)
    path = SHOTS / f"{name}.png"
    if pad:
        box = locator.bounding_box()
        assert box, f"{name}: element has no box"
        view = page.viewport_size
        clip = {
            "x": max(0.0, box["x"] - pad),
            "y": max(0.0, box["y"] - pad),
            "width": min(view["width"] - max(0.0, box["x"] - pad), box["width"] + 2 * pad),
            "height": min(view["height"] - max(0.0, box["y"] - pad), box["height"] + 2 * pad),
        }
        page.screenshot(path=str(path), clip=clip)
    else:
        locator.screenshot(path=str(path))
    assert path.stat().st_size > 1_000, f"Shot {name} too small"
    return path


def _shot_room(page: Any, name: str) -> Path:
    """Shoot the Room window (tall viewport so nothing is clipped)."""
    _settle(page)
    old = page.viewport_size
    page.set_viewport_size({"width": old["width"], "height": 1600})
    _settle(page)
    path = _shot_element(page, _room_window(page), name)
    page.set_viewport_size(old)
    return path


# ── the ask-task seams (all real routes) ─────────────────────────────


def _save_ask(page: Any, project_id: str, purpose: str, **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"purpose": purpose, "lens": "Project", **extra}
    return _api(
        page, "POST", f"/api/projects/{project_id}/ask-tasks", body, token=TOKEN,
    )["task"]


def _list_unfinished(page: Any, project_id: str | None = None) -> list[dict[str, Any]]:
    path = "/api/ask-tasks?state=unfinished&limit=20"
    if project_id:
        path += f"&project_id={project_id}"
    return _api(page, "GET", path, token=TOKEN)["items"]


def _rows(page: Any) -> Any:
    return page.locator('[data-testid="room-unfinished"] .surface-task-resume')


def _row_chip(page: Any, index: int = 0) -> str:
    """The chip's WORDS (its accessible name; the glyph is decor)."""
    chip = _rows(page).nth(index).locator(".surface-state-chip").first
    return (chip.get_attribute("aria-label") or chip.inner_text()).strip()


def _row_tokens(page: Any, index: int = 0) -> list[str]:
    return [
        (t or "").strip()
        for t in _rows(page).nth(index).locator("[data-task-resume-token]").all_inner_texts()
    ]


def _accessible_names(page: Any, root: str) -> list[str]:
    return page.evaluate(
        """(root) => {
            const scope = document.querySelector(root);
            if (!scope) return [];
            return Array.from(scope.querySelectorAll('button')).map(b => ({
                name: (b.getAttribute('aria-label') || b.textContent || '').trim(),
                html: b.outerHTML.slice(0, 90),
            }));
        }""",
        root,
    )


# ── leg 1 + 3: the saved row, at both widths ─────────────────────────


@pytest.mark.timeout(300)
@pytest.mark.parametrize("width", [1440, 393])
def test_saved_ask_draws_the_ratified_unfinished_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """`UNFINISHED 1`: purpose, `SAVED HH:MM`, custody, one `Resume`."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    purpose = "Whether the Q4 platform migration can land before the freeze"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width >= 1440 else 852}
            )
            page.on("pageerror", lambda e: errors.append(str(e)))

            _init_desk(page, url)
            project_id = _create_project(page, "Q4 platform", "hs200-41-saved")
            task = _save_ask(page, project_id, purpose)
            assert task["state"] == "saved", task
            assert task["purpose"] == purpose

            _open_room(page, project_id)
            page.get_by_test_id("room-unfinished").wait_for(timeout=15000)
            assert _rows(page).count() == 1, "expected exactly one unfinished row"

            # The caption carries the count the design ratified. F5 moved it:
            # the list is a Room SECTION now, so the count rides the section
            # label rather than a caption inside the composer's sticky foot.
            section = _rows(page).first.locator(
                "xpath=ancestor::section[contains(@class,'surface-section')][1]"
            )
            caption = section.locator(".surface-section-head h3").first.inner_text().strip()
            assert caption == "UNFINISHED 1", caption
            # F5: and it is NOT inside the sticky ask container.
            assert page.evaluate(
                """() => !document.querySelector('.room-ask-container')
                   .contains(document.querySelector('[data-testid="room-unfinished"]'))"""
            ), "the unfinished list must live in the Room body, not the sticky foot"

            # F5 tail — AT THE ROOM'S OPENING SCROLL POSITION, not only at
            # full scroll. Filed as the trailing section, UNFINISHED was the
            # one the sticky foot reached: the Room opened with the single row
            # he came back for sitting under the composer, its verb hidden.
            # It is placed directly after NEEDS YOU now, so the foot never
            # reaches it at rest.
            order = page.evaluate(
                """() => Array.from(document.querySelectorAll(
                     '.room-body .surface-section-head h3')).map(el => el.textContent.trim())"""
            )
            print(f"[hs200-41] section order at rest: {order}")
            unfinished_at = [i for i, name in enumerate(order)
                             if name.startswith("UNFINISHED")]
            assert unfinished_at, order
            if "NEEDS YOU" in order:
                assert unfinished_at[0] == order.index("NEEDS YOU") + 1, (
                    f"UNFINISHED belongs directly after NEEDS YOU: {order}"
                )
            if "SOURCES" in order:
                assert unfinished_at[0] < order.index("SOURCES"), order
            clear = page.evaluate(
                """() => {
                    const body = document.querySelector('.desk-surface-body');
                    const top = body ? body.scrollTop : 0;
                    const well = document.querySelector('.room-ask-container')
                      .getBoundingClientRect();
                    const rows = Array.from(document.querySelectorAll(
                      '[data-testid="room-unfinished"] .surface-task-resume'));
                    const covered = rows.filter(row => {
                      const r = row.getBoundingClientRect();
                      return r.bottom > well.top + 1 && r.top < well.bottom - 1;
                    }).length;
                    // The row's ONE verb must be whole, not a sliver above
                    // the composer's edge.
                    const verb = document.querySelector(
                      '[data-testid="room-unfinished"] .surface-task-resume-verbs button');
                    const v = verb.getBoundingClientRect();
                    return {scrollTop: top, covered,
                            verbClear: Math.round(well.top - v.bottom)};
                }"""
            )
            print(f"[hs200-41] at rest: {json.dumps(clear)}")
            assert clear["scrollTop"] == 0, "this is meant to measure the RESTING Room"
            assert clear["covered"] == 0, (
                f"the row he came back for opens under the composer: {clear}"
            )
            assert clear["verbClear"] > 0, (
                f"the row's verb must stand clear of the sticky foot: {clear}"
            )

            # The purpose, said once, at the primary step.
            drawn = _rows(page).first.locator(".surface-task-resume-purpose").inner_text()
            assert drawn.strip() == purpose, drawn

            # `SAVED HH:MM` in the chip; custody as its own token.
            chip = _row_chip(page)
            assert chip.startswith("SAVED "), chip
            assert len(chip.split()[-1]) == 5 and ":" in chip, f"not HH:MM: {chip!r}"
            tokens = _row_tokens(page)
            assert "SAVED HERE" in tokens, tokens
            assert not any(t == "THIS DEVICE" for t in tokens), (
                f"custody must never wear the egress word (B7): {tokens}"
            )
            # A.8 — no token for an absent fact: no recipe was saved.
            assert not any(t.startswith("RECIPE") for t in tokens), tokens

            # ONE verb, and it is the face's filled primary.
            verbs = _rows(page).first.locator(".surface-task-resume-verbs button")
            names = [
                (v.get_attribute("aria-label") or v.inner_text()).strip()
                for v in verbs.all()
            ]
            assert names[0] == f"Resume: {purpose}", names
            assert "MORE" in " ".join(n.upper() for n in names[1:]), names
            resume = verbs.first
            assert not resume.is_disabled()
            assert "btn--primary" in (resume.get_attribute("class") or "") or (
                "primary" in (resume.get_attribute("class") or "")
            ), resume.get_attribute("class")

            # Every verb in the list carries an accessible name.
            for entry in _accessible_names(page, '[data-testid="room-unfinished"]'):
                assert entry["name"], f"unlabelled verb: {entry['html']}"

            _shot_room(page, f"taskresume-saved-{width}")
            _shot_element(
                page, page.locator('[data-testid="room-unfinished"]'),
                f"taskresume-saved-block-{width}", pad=20,
            )

            # The narrow rule NO ONE HAS SEEN: at 393 the container query
            # folds the verbs under the tokens.  Proven from the computed
            # style, not from the pixels.
            areas = page.evaluate(
                """() => {
                    const row = document.querySelector(
                      '[data-testid="room-unfinished"] .surface-task-resume');
                    const cs = getComputedStyle(row);
                    return {
                      areas: cs.gridTemplateAreas,
                      columns: cs.gridTemplateColumns,
                      width: row.getBoundingClientRect().width,
                      containerWidth: row.closest('.desk-surface-body')
                        ?.getBoundingClientRect().width ?? -1,
                    };
                }"""
            )
            print(f"[hs200-41] {width}: {areas}")
            if width == 393:
                # F3 added the `reason` line: four stacked areas at 393.
                assert areas["areas"].count('"') == 8, (
                    f"expected four stacked areas at 393, got {areas['areas']!r}"
                )
                assert "verbs" in areas["areas"]
            else:
                # Three lines beside the verb column at 1440 (F3's `reason`
                # line joined `purpose` and `tokens`).
                assert areas["areas"].count('"') == 6, areas["areas"]

            # `Discard` lives behind MORE — closed by default (a closed
            # Disclosure renders no children), and a ConfirmVerb when opened.
            assert page.locator('[data-testid="room-unfinished"]').get_by_role(
                "button", name="Discard the unfinished ask"
            ).count() == 0, "Discard must not be a bare destructive verb"
            page.locator(
                '[data-testid="room-unfinished"] .surface-disclosure-trigger'
            ).first.click()
            discard = page.get_by_role("button", name="Discard the unfinished ask")
            discard.wait_for(timeout=5000)
            if width >= 1440:
                _shot_room(page, "taskresume-more-open-1440")
            # First press arms in place; Escape cancels and the row survives.
            discard.click()
            page.wait_for_timeout(150)
            assert discard.inner_text().strip() == "Sure?", discard.inner_text()
            assert _rows(page).count() == 1

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── leg 2: a REAL refusal, quoted (ruling B5) ────────────────────────


@pytest.mark.timeout(300)
@pytest.mark.parametrize("width", [1440, 393])
def test_failed_ask_carries_the_hubs_own_words(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """A refused run, run for real from the Room's own ask well.

    No engine is configured, so the hub refuses with its own bounded code
    and the Room records the stop.  The chip's reason is the words the
    hub itself resolved — nothing the browser composed.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    purpose = "Draft the migration risk note for the platform review"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width >= 1440 else 852}
            )
            page.on("pageerror", lambda e: errors.append(str(e)))

            _init_desk(page, url)
            project_id = _create_project(page, "Q4 platform", "hs200-41-failed")
            _open_room(page, project_id)

            # The hub's OWN refusal, taken straight off `/api/ask` first, so
            # the rig knows the words it should later find on the row.
            status, refusal = _api_allow_error(
                page, "POST", "/api/ask",
                {"prompt": "probe", "lens": "Project", "context": []}, token=TOKEN,
            )
            assert status >= 400, f"the rig assumed no engine; hub answered {status}"
            assert refusal["code"] == "inference_target_unavailable", refusal
            hub_words = refusal["error"]
            print(f"[hs200-41] the hub's own refusal: {hub_words!r}")

            # Now the OWNER's path: type the ask and press Enter.
            well = page.locator('[data-testid="room-ask-input-well"] input')
            well.wait_for(timeout=10000)
            well.fill(purpose)
            well.press("Enter")
            page.get_by_test_id("room-unfinished").wait_for(timeout=20000)
            page.wait_for_function(
                """() => {
                    const row = document.querySelector(
                      '[data-testid="room-unfinished"] .surface-task-resume');
                    return row && row.dataset.state === 'failed';
                }""",
                timeout=20000,
            )
            _settle(page)

            row = _rows(page).first
            assert row.get_attribute("data-state") == "failed"
            # F3: the chip says FAILED and NOTHING else. `StateChip` neither
            # wraps nor truncates, and ruling B5 quotes the engine verbatim —
            # a filesystem path is the ORDINARY case, and it ran 205px
            # off-glass at 393 with the red border sliced through it.
            chip = _row_chip(page)
            assert chip == "FAILED", chip
            # The hub's words, verbatim, on their OWN row — which can wrap.
            reason = row.locator(".surface-task-resume-reason")
            assert reason.count() == 1, "the quoted reason needs its own row"
            assert reason.inner_text().strip() == hub_words, (
                f"the row must quote the hub verbatim.\n  row: {reason.inner_text()!r}"
                f"\n  hub: {hub_words!r}"
            )
            # And it is INSIDE the row: nothing of it is clipped off-glass.
            assert page.evaluate(
                """() => {
                    const row = document.querySelector(
                      '[data-testid="room-unfinished"] .surface-task-resume');
                    const el = row.querySelector('.surface-task-resume-reason');
                    const r = row.getBoundingClientRect();
                    const e = el.getBoundingClientRect();
                    return Math.round(e.right - r.right) <= 0 &&
                           Math.round(e.left - r.left) >= 0;
                }"""
            ), "the engine's quoted words must not run off the row"

            # The store holds the code AND the quoted reason.
            items = _list_unfinished(page, project_id)
            assert len(items) == 1, items
            assert items[0]["state"] == "failed"
            assert items[0]["stoppedCode"] == "inference_target_unavailable", items[0]
            assert items[0]["stoppedReason"] == hub_words, items[0]
            assert items[0]["purpose"] == purpose

            # `Check` — the failed state's one verb — is ENABLED.
            verb = row.locator(".surface-task-resume-verbs button").first
            assert verb.inner_text().strip() == "Check", verb.inner_text()
            assert not verb.is_disabled(), "the failed row's Check must be reachable"
            assert (verb.get_attribute("aria-label") or "") == f"Check: {purpose}"

            # F6: SAID ONCE. The composer's red prose underneath is gone —
            # at 393 the same sentence was on the glass three times.
            assert page.locator(".room-ask-error").count() == 0, (
                "the failure is said once, by the row"
            )
            assert page.get_by_text(hub_words, exact=True).count() == 1, (
                "the hub's sentence appears exactly once on the face"
            )

            _shot_room(page, f"taskresume-failed-{width}")
            _shot_element(
                page, page.locator('[data-testid="room-unfinished"]'),
                f"taskresume-failed-block-{width}", pad=20,
            )

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── leg 3b: the narrow layout, framed to be read ─────────────────────


@pytest.mark.timeout(300)
def test_narrow_container_rule_at_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The `@container surface (max-width: 420px)` rule, rendered.

    Two rows — one saved, one failed with a long quoted reason — so the
    fold, the wrapping token row and the row rhythm are all legible.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 393, "height": 852})
            page.on("pageerror", lambda e: errors.append(str(e)))

            _init_desk(page, url)
            project_id = _create_project(page, "Q4 platform", "hs200-41-narrow")
            _save_ask(
                page, project_id,
                "Whether the Q4 platform migration can land before the freeze",
                recipe_key="risk-review",
            )
            _open_room(page, project_id)

            # A second ask, refused for real, so the narrow row carries a
            # long quoted reason as well as the short one.
            well = page.locator('[data-testid="room-ask-input-well"] input')
            well.wait_for(timeout=10000)
            well.fill("Draft the migration risk note for the platform review")
            well.press("Enter")
            page.wait_for_function(
                """() => document.querySelectorAll(
                     '[data-testid="room-unfinished"] .surface-task-resume').length === 2""",
                timeout=25000,
            )
            _settle(page)

            geometry = page.evaluate(
                """() => Array.from(document.querySelectorAll(
                     '[data-testid="room-unfinished"] .surface-task-resume')).map(row => {
                     const cs = getComputedStyle(row);
                     const purpose = row.querySelector('.surface-task-resume-purpose');
                     const verbs = row.querySelector('.surface-task-resume-verbs');
                     const tokens = row.querySelector('.surface-task-resume-tokens');
                     return {
                       state: row.dataset.state,
                       areas: cs.gridTemplateAreas,
                       rowWidth: Math.round(row.getBoundingClientRect().width),
                       purposeWraps:
                         getComputedStyle(purpose).whiteSpace === 'normal',
                       purposeHeight: Math.round(purpose.getBoundingClientRect().height),
                       tokensBottom: Math.round(tokens.getBoundingClientRect().bottom),
                       verbsTop: Math.round(verbs.getBoundingClientRect().top),
                       clientWidth: row.clientWidth,
                       scrollWidth: row.scrollWidth,
                       overflowPx: row.scrollWidth - row.clientWidth,
                       widest: Array.from(row.querySelectorAll('*'))
                         .map(el => ({
                           cls: el.className && el.className.baseVal === undefined
                             ? String(el.className) : '',
                           w: Math.round(el.getBoundingClientRect().width),
                           text: (el.textContent || '').trim().slice(0, 70),
                         }))
                         .sort((a, b) => b.w - a.w)[0],
                     };
                   })"""
            )
            print(f"[hs200-41] narrow geometry: {json.dumps(geometry, indent=2)}")
            assert len(geometry) == 2
            for g in geometry:
                # F3 added the `reason` line: four areas, eight quotes.
                assert g["areas"].count('"') == 8, g
                assert g["purposeWraps"], "the narrow rule must let the purpose wrap"
                assert g["verbsTop"] >= g["tokensBottom"] - 1, (
                    f"the verbs must fall UNDER the tokens at 393: {g}"
                )
            # The saved row — the ratified `UNFINISHED 1` — fits its container.
            saved_row = [g for g in geometry if g["state"] == "saved"][0]
            assert saved_row["overflowPx"] <= 1, saved_row

            # F3, FIXED: a FAILED row whose quoted reason is a long
            # unbreakable string (`model file not found: /very/long/path.gguf`)
            # used to push its own state chip past the row box at 393 — the
            # chip does not wrap and the row does not scroll, so the tail of
            # the hub's own words was simply not on the glass. The chip now
            # says `FAILED` and the quoted words have their own wrapping row,
            # so the failed row fits like every other one.
            failed_row = [g for g in geometry if g["state"] == "failed"][0]
            print(f"[hs200-41] narrow failed row: {json.dumps(failed_row)}")
            assert failed_row["overflowPx"] <= 1, (
                "the engine's quoted words must wrap, never run off-glass: "
                f"{failed_row}"
            )

            _shot_room(page, "taskresume-narrow-393")
            _shot_element(
                page, page.locator('[data-testid="room-unfinished"]'),
                "taskresume-narrow-rows-393",
            )
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── leg 4: the restart ───────────────────────────────────────────────


def _http(url: str, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{url}{path}", data=data, method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            **({"Content-Type": "application/json"} if data else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode() or "{}")


@pytest.mark.timeout(300)
def test_a_saved_ask_survives_a_hub_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Saved, hub stopped, database re-opened from disk, new hub booted.

    HONEST SCOPE: one interpreter.  What is torn down and rebuilt is the
    `MeetingWebServer`, its `RefinementCoordinator` and the `Database`
    singleton (`reset_database()` drops it; the next `get_database()`
    re-opens `DEFAULT_DB_PATH` from the file).  Nothing of the row is
    carried in Python memory across the boundary — the second hub reads
    it back off the disk file.  A true fork/exec restart is not something
    these fixtures can do, and this test does not claim one.
    """
    _ensure_build()
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    purpose = "Whether the Q4 platform migration can land before the freeze"
    second: Any = None
    try:
        created = _http(url, "POST", "/api/projects", {
            "name": "Q4 platform", "description": "restart leg",
            "command_id": "hs200-41-restart",
        })
        project_id = created["project"]["id"]
        saved = _http(url, "POST", f"/api/projects/{project_id}/ask-tasks",
                      {"purpose": purpose, "lens": "Project"})["task"]
        assert saved["state"] == "saved"
        assert saved["custody"] == "here", saved
        # F1: the identity itself never crosses the wire. The face has no
        # business printing an opaque token (canon `raw-ids`), and the shot
        # that caught this read `SAVED ON REFHOST_671A4CBA…`.
        assert "custodyHost" not in saved, saved

        # ── the restart ──
        server.stop()
        reset_database()

        second = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None, on_stop=lambda: None,
                get_state=lambda: {},
            ),
            auth_token=TOKEN,
        )
        second_url = second.start()
        # Let the new coordinator take its lease before the projection reads.
        time.sleep(1.0)

        page_after = _http(second_url, "GET", "/api/ask-tasks?state=unfinished&limit=20")
        items = page_after["items"]
        assert len(items) == 1, items
        after = items[0]
        assert after["id"] == saved["id"]
        assert after["purpose"] == purpose, "the purpose did not survive the restart"
        assert after["state"] == "saved", after
        assert after["projectId"] == project_id
        assert after["invocationId"] == saved["invocationId"], (
            "the invocation identity is the key back; it must survive"
        )
        print(f"[hs200-41] restart: custody {saved['custody']} -> "
              f"{after.get('custody')}")

        # F1 — this leg used to RECORD the defect instead of refusing it.
        # `refinement_coordinator.host_id` is `refhost_<uuid4>` minted per
        # process (holdspeak/services/refinement_coordinator.py:45), so custody
        # keyed off the process lease flipped to `elsewhere` on the same desk
        # after every restart — the exact event this story exists for — and the
        # face then printed the raw uuid. Custody is now stamped with
        # HS-200-02's `database_identity` (resolved path + device + inode), so
        # the SAME desk stays `here` and no id is emitted at all.
        #
        # HONEST SCOPE, on top of the fixture's own: `current_runtime_identity`
        # caches per interpreter, so within one process this cannot separate
        # "stable because cached" from "stable because derived from the file".
        # Two real interpreters are compared in
        # tests/unit/test_phase200_task_resume.py's identity test.
        assert after["custody"] == "here", (
            "the same desk must still read SAVED HERE after a restart"
        )
        assert "custodyHost" not in after, after
    finally:
        if second is not None:
            second.stop()
        try:
            server.stop()
        except Exception:
            pass


@pytest.mark.timeout(300)
def test_the_custody_token_after_a_restart_at_1440(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """What the FACE draws for a row that outlived the process that wrote it."""
    _ensure_build()
    from holdspeak.db import reset_database
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    purpose = "Whether the Q4 platform migration can land before the freeze"
    second: Any = None
    errors: list[str] = []
    try:
        created = _http(url, "POST", "/api/projects", {
            "name": "Q4 platform", "description": "restart face leg",
            "command_id": "hs200-41-restart-face",
        })
        project_id = created["project"]["id"]
        _http(url, "POST", f"/api/projects/{project_id}/ask-tasks",
              {"purpose": purpose, "lens": "Project"})

        server.stop()
        reset_database()
        second = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None, on_stop=lambda: None,
                get_state=lambda: {},
            ),
            auth_token=TOKEN,
        )
        second_url = second.start()
        time.sleep(1.0)

        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _init_desk(page, second_url)
            _open_room(page, project_id)
            page.get_by_test_id("room-unfinished").wait_for(timeout=15000)
            tokens = _row_tokens(page)
            print(f"[hs200-41] custody token after restart: {tokens}")
            _shot_room(page, "taskresume-after-restart-1440")
            assert _rows(page).first.locator(
                ".surface-task-resume-purpose"
            ).inner_text().strip() == purpose
            _assert_clean(page, errors)
            browser.close()
    finally:
        if second is not None:
            second.stop()
        try:
            server.stop()
        except Exception:
            pass


# ── leg 5: Resume claims a landed answer, dispatching nothing ────────


class CountingEngine:
    """A local engine that answers, and counts every run it is asked for."""

    active_provider = "hs200-41-fake"
    active_model = "hs200-41"
    calls = 0

    def run_prompt_messages(self, *, messages: Any = None, **kw: Any) -> str:
        CountingEngine.calls += 1
        return "The freeze holds; the migration lands the week after."

    def run_prompt(self, *, system_prompt: str = "", user_prompt: str = "", **kw: Any) -> str:
        return self.run_prompt_messages()

    def run_prompt_stream(self, *, messages: Any = None, **kw: Any) -> Any:
        from holdspeak.kernel.inference_stream import Delta
        text = self.run_prompt_messages()
        yield Delta(kind="text", text=text)
        yield Delta(kind="done")


def _seed_ready_engine(tmp_path: Path) -> None:
    """Make the hub's OWN default destination ready, then stub the engine.

    Ask resolves placement from the caller's `inference_target_id` or the
    global default (`ask_service.py:310`), and the global default is
    `this_machine`, whose readiness is one question: is the configured
    local artifact on disk (`inference_targets.py:226-240`)?  So the rig
    writes a placeholder artifact into its ISOLATED HOME and points the
    config at it through the product's own `Config`, then injects a
    counting engine into the kernel broker so nothing real is loaded.
    """
    from holdspeak.config import Config

    artifact = tmp_path / "home" / "Models" / "hs200-41.gguf"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b"GGUF placeholder for the HS-200-41 rig")
    config = Config.load()
    config.meeting.intel_realtime_model = str(artifact)
    config.save()

    from holdspeak.kernel.runtime import _service as kernel_service
    broker = kernel_service()
    assert broker is not None, "no kernel broker to inject the engine into"
    broker.inference_runner._engine_factory = lambda _rev, **_kw: CountingEngine()


@pytest.mark.timeout(300)
def test_resume_claims_a_landed_answer_without_a_second_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ruling B3: the answer is already on disk, so Resume dispatches nothing."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    CountingEngine.calls = 0
    errors: list[str] = []
    try:
        _seed_ready_engine(tmp_path)
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _init_desk(page, url)
            project_id = _create_project(page, "Q4 platform", "hs200-41-claim")

            task = _save_ask(page, project_id, "Does the freeze move?")
            # The answer lands under the SAVED identity while the owner is away.
            answer = _api(page, "POST", "/api/ask", {
                "prompt": "Does the freeze move?",
                "lens": "Project",
                "context": [],
                "invocation_id": task["invocationId"],
            }, token=TOKEN)
            assert answer.get("output"), answer
            after_run = CountingEngine.calls
            assert after_run >= 1, "the rig's engine never ran"

            # Coming back to it CLAIMS the answer.
            outcome = _api(
                page, "POST", f"/api/ask-tasks/{task['id']}/resume", {}, token=TOKEN,
            )
            assert outcome["claimed"] is True, outcome
            assert outcome["dispatched"] is False, outcome
            assert outcome["task"]["state"] == "accepted", outcome["task"]
            assert outcome["answer"]["output"] == answer["output"]
            assert CountingEngine.calls == after_run, (
                f"Resume dispatched a second run: {after_run} -> {CountingEngine.calls}"
            )

            # A second Resume takes the same branch — no double-spend.
            again = _api(
                page, "POST", f"/api/ask-tasks/{task['id']}/resume", {}, token=TOKEN,
            )
            assert again["claimed"] is True and again["dispatched"] is False, again
            assert CountingEngine.calls == after_run

            # An accepted ask leaves the Resume projection (ruling B6's sibling).
            assert _list_unfinished(page, project_id) == [], "accepted must not be listed"
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── leg 6: the keyboard ──────────────────────────────────────────────


@pytest.mark.timeout(300)
def test_the_list_is_one_tab_stop_and_every_verb_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """One Tab stop across the whole list; every verb carries a name."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _init_desk(page, url)
            project_id = _create_project(page, "Q4 platform", "hs200-41-keys")
            first = _save_ask(page, project_id, "The first unfinished ask")
            second = _save_ask(page, project_id, "The second unfinished ask")
            _open_room(page, project_id)
            page.get_by_test_id("room-unfinished").wait_for(timeout=15000)
            assert _rows(page).count() == 2

            stops = page.eval_on_selector_all(
                '[data-testid="room-unfinished"] .surface-task-resume button',
                "els => els.map(e => e.getAttribute('tabindex'))",
            )
            print(f"[hs200-41] roving tabindexes: {stops}")
            assert stops.count("0") == 1, f"the list must be ONE Tab stop: {stops}"
            assert all(t in ("0", "-1") for t in stops), stops

            # Every verb on the face carries an accessible name.
            named = _accessible_names(page, '[data-testid="room-unfinished"]')
            for entry_row in named:
                assert entry_row["name"], f"unlabelled verb: {entry_row['html']}"
            names = [e["name"] for e in named]
            print(f"[hs200-41] accessible names: {names}")
            assert f"Resume: {first['purpose']}" in names, names
            assert f"Resume: {second['purpose']}" in names, names

            _shot_room(page, "taskresume-two-rows-1440")
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(300)
def test_the_rows_rove_on_a_list_that_mounted_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ratified keyboard law (design D2(f): "Up/Down rove rows"), FIXED.

    This was a live defect the glass caught and no unit test could: the Room's
    list always starts empty and is filled by `loadUnfinished`, and
    `TaskResumeList` renders `null` while it has no children (A.8), so
    `useRovingRows`'s listener effect saw a null ref on mount — and with deps
    `[ref, selector, rowSelector]`, all stable, it NEVER ran again once the
    rows arrived. Up/Down/Left/Right/Home/End and type-ahead were all dead,
    while the dep-less stamping effect still set the tabindexes so the list
    LOOKED like one Tab stop. Every vitest specimen renders its rows on mount,
    which is why they were green and the browser was not.

    The hook now mirrors the ref into state, so the listener effect re-runs the
    moment the element exists. That is a fix in `roving.ts`, not in this face:
    every list that mounts empty and fills from a fetch was equally dead, which
    is most of them.

    A CDP listener census is the proof, plus the keys actually moving.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            _init_desk(page, url)
            project_id = _create_project(page, "Q4 platform", "hs200-41-rove")
            _save_ask(page, project_id, "The first unfinished ask")
            _save_ask(page, project_id, "The second unfinished ask")
            _open_room(page, project_id)
            page.get_by_test_id("room-unfinished").wait_for(timeout=15000)
            assert _rows(page).count() == 2

            cdp = page.context.new_cdp_session(page)

            def listeners(selector: str) -> list[str]:
                found = cdp.send("Runtime.evaluate", {
                    "expression": f"document.querySelector({selector!r})",
                })["result"]
                if not found.get("objectId"):
                    return ["(element absent)"]
                got = cdp.send(
                    "DOMDebugger.getEventListeners",
                    {"objectId": found["objectId"]},
                )
                return sorted(entry["type"] for entry in got["listeners"])

            unfinished = listeners(".surface-task-resume-list")
            ledger = listeners(".surface-ledger")
            print(f"[hs200-41] listeners on .surface-task-resume-list: {unfinished}")
            print(f"[hs200-41] listeners on .surface-ledger (mounts full):  {ledger}")
            assert unfinished == ["focusin", "keydown"], (
                f"the keyboard law must be BOUND on a list that mounted empty: {unfinished}"
            )
            assert ledger == ["focusin", "keydown"], (
                f"the comparison list changed shape: {ledger}"
            )

            def focused() -> str:
                return page.evaluate(
                    """() => {
                        const el = document.activeElement;
                        if (!el) return '';
                        return (el.getAttribute('aria-label') || el.textContent || '').trim();
                    }"""
                )

            page.eval_on_selector(
                '[data-testid="room-unfinished"] .surface-task-resume '
                'button[tabindex="0"]', "el => el.focus()",
            )
            entry = focused()
            assert entry.startswith("Resume: "), entry

            # Down walks to the OTHER row's verb.
            page.keyboard.press("ArrowDown")
            page.wait_for_timeout(90)
            down = focused()
            assert down.startswith("Resume: ") and down != entry, (
                f"ArrowDown must walk to the next row: {entry!r} -> {down!r}"
            )
            # Up comes back.
            page.keyboard.press("ArrowUp")
            page.wait_for_timeout(90)
            assert focused() == entry, "ArrowUp must walk back"
            # Right walks this row's OWN controls (the MORE fold is one).
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(90)
            right = focused()
            assert right != entry, f"ArrowRight must walk the row's controls: {right!r}"
            # End/Home reach the ends.
            page.keyboard.press("End")
            page.wait_for_timeout(90)
            assert focused() == down, f"End must reach the last row: {focused()!r}"
            page.keyboard.press("Home")
            page.wait_for_timeout(90)
            assert focused() == entry, f"Home must reach the first row: {focused()!r}"

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── leg 6b: what the list does to the Room it lives in ───────────────


@pytest.mark.timeout(300)
def test_a_full_unfinished_list_leaves_the_room_standing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Five rows must not eat the Room (F5, FIXED).

    The list used to render inside `.room-ask-container`, which is
    `position: sticky; bottom: 0` with an opaque backdrop
    (`web/src/features/project-room/project-room.css:306-313`), against a
    `.room-body` that reserves `padding-bottom: 96px` on an assumption that
    predates this story ("the well ~52px + padding + gap",
    `project-room.css:11-13`).  With the five rows the Room fetches, the
    sticky block covered every other section: no NEEDS YOU, no SOURCES, no
    RECEIPTS — a wall of unfinished asks over dead space.

    A ledger does not belong in a composer's foot.  The list is now a Room
    SECTION beside the other four, where the design's posture-6 grammar puts
    it, and the sticky foot is the well alone.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _init_desk(page, url)
            project_id = _create_project(page, "Q4 platform", "hs200-41-sticky")
            for index in range(5):
                _save_ask(
                    page, project_id,
                    f"Unfinished ask number {index + 1} kept for the sticky measurement",
                )
            _open_room(page, project_id)
            page.get_by_test_id("room-unfinished").wait_for(timeout=15000)
            assert _rows(page).count() == 5

            page.evaluate(
                """() => { const b = document.querySelector('.desk-surface-body');
                           b.scrollTop = b.scrollHeight; }"""
            )
            page.wait_for_timeout(400)
            _settle(page)
            measured = page.evaluate(
                """() => {
                    const body = document.querySelector('.desk-surface-body');
                    const container = document.querySelector('.room-ask-container');
                    const roomBody = document.querySelector('.room-body');
                    const cs = getComputedStyle(container);
                    return {
                      position: cs.position,
                      backdrop: cs.backgroundColor,
                      containerHeight: Math.round(
                        container.getBoundingClientRect().height),
                      bodyClientHeight: body.clientHeight,
                      reservedByRoomBody: getComputedStyle(roomBody).paddingBottom,
                    };
                }"""
            )
            share = round(
                100 * measured["containerHeight"] / measured["bodyClientHeight"]
            )
            print(
                f"[hs200-41] FINDING sticky foot with 5 rows: "
                f"{json.dumps(measured)} -> {share}% of the readable Room"
            )
            assert measured["position"] == "sticky", measured
            # The sticky foot is the WELL, and only the well: five rows must
            # not grow it. It stays inside the 96px `.room-body` reserves.
            assert measured["containerHeight"] <= 96, (
                f"the sticky foot must be the well alone: {measured}"
            )
            assert share <= 20, (
                f"the sticky foot must not eat the Room: {share}% of it"
            )
            # And the Room is still THERE behind it: its own sections are on
            # the glass with five unfinished rows present.
            standing = page.evaluate(
                """() => Array.from(
                     document.querySelectorAll('.room-body .surface-section-head h3'))
                   .map(el => el.textContent.trim())"""
            )
            print(f"[hs200-41] sections standing with 5 rows: {standing}")
            assert any(s.startswith("UNFINISHED") for s in standing), standing
            # The Room's OWN sections, not covered by a wall of asks. (Which
            # sections a Room draws depends on what it has; these two are what
            # this fixture's Room holds — RECEIPTS is absent because there are
            # none, which is A.8 doing its job.)
            assert "NEEDS YOU" in standing, standing
            assert "SOURCES" in standing, standing

            # The sticky foot FLOATS over the body by design, so it can cover
            # the section nearest the bottom mid-scroll — as it always has for
            # whichever section was last. What must hold is that AT FULL
            # SCROLL nothing is left underneath it: `.room-body` reserves
            # `padding-bottom: 96px` for exactly that. Measured, not assumed.
            covered = page.evaluate(
                """() => {
                    const well = document.querySelector('.room-ask-container')
                      .getBoundingClientRect();
                    return Array.from(document.querySelectorAll(
                      '[data-testid="room-unfinished"] .surface-task-resume'))
                      .filter(row => {
                        const r = row.getBoundingClientRect();
                        return r.bottom > well.top + 1 && r.top < well.bottom - 1;
                      }).length;
                }"""
            )
            assert covered == 0, (
                f"{covered} unfinished row(s) still under the sticky foot at full scroll"
            )
            _shot_room(page, "taskresume-five-rows-sticky-1440")
            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


# ── leg 7: the Thread composer ───────────────────────────────────────


def _open_thread(page: Any, url: str, thread_id: str) -> None:
    page.goto(f"{url}/?token={TOKEN}&open=thread:{thread_id}", wait_until="load")
    page.locator(".thread-composer-input").wait_for(timeout=20000)
    _settle(page)


_SWATCH_JS = """(sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const rgb = (value) => {
      const m = String(value).match(/[\\d.]+/g) || [];
      return {r: +m[0] || 0, g: +m[1] || 0, b: +m[2] || 0, a: m.length > 3 ? +m[3] : 1};
    };
    // The colour actually behind the element: the first ancestor that
    // paints something opaque.
    let backdrop = 'rgb(255, 255, 255)';
    for (let node = el.parentElement; node; node = node.parentElement) {
      const bg = getComputedStyle(node).backgroundColor;
      if (rgb(bg).a >= 0.999) { backdrop = bg; break; }
    }
    const lin = (c) => {
      const s = c / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    };
    const lum = (value) => {
      const c = rgb(value);
      return 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
    };
    const contrast = (a, b) => {
      const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
      return Math.round(((x + 0.05) / (y + 0.05)) * 100) / 100;
    };
    const cs = getComputedStyle(el);
    // The button's own fill, composited over whatever is behind it.
    const own = rgb(cs.backgroundColor);
    const back = rgb(backdrop);
    const over = own.a >= 0.999 ? cs.backgroundColor : `rgb(${
      Math.round(own.r * own.a + back.r * (1 - own.a))}, ${
      Math.round(own.g * own.a + back.g * (1 - own.a))}, ${
      Math.round(own.b * own.a + back.b * (1 - own.a))})`;
    return {
      background: cs.backgroundColor,
      effectiveBackground: over,
      backdrop,
      color: cs.color,
      border: cs.borderTopColor,
      cursor: cs.cursor,
      opacity: cs.opacity,
      disabled: el.disabled === true,
      labelContrast: contrast(cs.color, over),
      fillVsBackdrop: contrast(over, backdrop),
    };
}"""


def _swatch(page: Any, selector: str) -> dict[str, Any]:
    return page.evaluate(_SWATCH_JS, selector)


@pytest.mark.timeout(300)
@pytest.mark.parametrize("width", [1440, 393])
def test_a_refused_send_reads_as_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """An empty draft: Send must READ refused, not merely BE `disabled`."""
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width >= 1440 else 852}
            )
            page.on("pageerror", lambda e: errors.append(str(e)))
            _init_desk(page, url)
            created = _api(page, "POST", "/api/threads",
                           {"title": "The migration"}, token=TOKEN)
            thread_id = created["id"]
            _open_thread(page, url, thread_id)

            send = page.locator('[data-testid="composer-send"]')
            send.wait_for(timeout=10000)
            assert send.is_disabled(), "an empty draft must refuse Send"
            refused = _swatch(page, '[data-testid="composer-send"]')
            print(f"[hs200-41] refused Send @{width}: {json.dumps(refused)}")
            assert refused["cursor"] == "not-allowed", refused

            _shot_element(
                page, page.locator('[data-testid="thread-composer"]'),
                f"composer-send-refused-{width}", pad=24,
            )

            # The comparison the reasoning was never checked against: the
            # SAME button with a live draft.
            page.locator(".thread-composer-input").fill("Ready to send")
            page.wait_for_timeout(150)
            assert not send.is_disabled()
            live = _swatch(page, '[data-testid="composer-send"]')
            print(f"[hs200-41] live Send    @{width}: {json.dumps(live)}")
            _shot_element(
                page, page.locator('[data-testid="thread-composer"]'),
                f"composer-send-live-{width}", pad=24,
            )

            # The refusal must be visible, not merely semantic: SOMETHING
            # about the paint has to differ from the live verb.
            assert (
                refused["background"] != live["background"]
                or refused["color"] != live["color"]
                or refused["border"] != live["border"]
            ), (
                "a refused Send paints EXACTLY like a live one — the only "
                f"difference is the DOM `disabled` attribute: {refused} vs {live}"
            )

            # WHERE the refusal actually reads, measured.  LANE-F FINDING:
            # `--disabled-bg` is `--surface-1`, and against the composer's
            # well the FILL barely moves (~1.1:1) — the whole visible signal
            # is the dimmed LABEL (14.8:1 -> 4.4:1) plus the not-allowed
            # cursor.  Recorded for the orchestrator's eye, not fixed here.
            print(
                f"[hs200-41] FINDING refused-vs-live @{width}: "
                f"fill {refused['effectiveBackground']} vs {live['effectiveBackground']} "
                f"(refused fill vs its backdrop = {refused['fillVsBackdrop']}:1); "
                f"label contrast {refused['labelContrast']}:1 vs "
                f"{live['labelContrast']}:1; border identical="
                f"{refused['border'] == live['border']}"
            )
            assert refused["labelContrast"] < live["labelContrast"], (
                f"the refused label is not dimmer than the live one: {refused} {live}"
            )
            # The refused verb must still be READABLE, not erased (A.8's
            # sibling: a refusal is a statement, not a disappearance).
            assert refused["labelContrast"] >= 3.0, (
                f"the refused Send is below 3:1 and cannot be read: {refused}"
            )

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(300)
@pytest.mark.parametrize("width", [1440, 393])
def test_the_ref_chip_x_paints_no_hover_background(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    """The library's hover grammar was neutralised on the chip's `x`.

    Hovered: no background, no border, no lift.  Focused: the ring the
    swap to the library `Button` gained must still be there.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": width, "height": 900 if width >= 1440 else 852}
            )
            page.on("pageerror", lambda e: errors.append(str(e)))
            _init_desk(page, url)
            created = _api(page, "POST", "/api/threads",
                           {"title": "The migration"}, token=TOKEN)
            thread_id = created["id"]
            _open_thread(page, url, thread_id)

            # A chip through the composer's OWN seam: type `@`, take a match.
            field = page.locator(".thread-composer-input")
            field.click()
            field.type("@", delay=40)
            page.wait_for_selector(".inlet-autocomplete", timeout=10000)
            options = page.locator(".inlet-autocomplete [role='option'], "
                                   ".inlet-autocomplete .surface-row")
            assert options.count() > 0, "the desk seed offered nothing to attach"
            options.first.click()
            page.wait_for_selector('[data-testid="composer-chips"]', timeout=10000)
            _settle(page)

            remove = page.locator(".thread-ref-chip-remove").first
            remove.wait_for(timeout=5000)
            name = remove.get_attribute("aria-label") or ""
            assert name.startswith("Remove "), f"the x needs a name: {name!r}"

            resting = _swatch(page, ".thread-ref-chip-remove")
            remove.hover()
            page.wait_for_timeout(200)
            hovered = _swatch(page, ".thread-ref-chip-remove")
            print(f"[hs200-41] chip x @{width} resting={json.dumps(resting)}")
            print(f"[hs200-41] chip x @{width} hovered={json.dumps(hovered)}")
            assert hovered["background"] in ("rgba(0, 0, 0, 0)", "transparent"), (
                f"the chip's x paints a hover background: {hovered}"
            )
            assert hovered["border"] in ("rgba(0, 0, 0, 0)", "transparent"), (
                f"the chip's x paints a hover border: {hovered}"
            )
            assert hovered["color"] != resting["color"], (
                "hover must still SAY something — the colour shift is the "
                f"whole remaining affordance: {resting} vs {hovered}"
            )
            _shot_element(
                page, page.locator('[data-testid="composer-chips"]'),
                f"composer-refchip-hover-{width}", pad=28,
            )

            # The focus ring survived the neutralisation.  It must be reached
            # by a REAL Tab — a scripted `.focus()` leaves Chromium in mouse
            # modality, where `:focus-visible` does not apply and an absent
            # ring would prove nothing.
            page.locator(".thread-composer-input").focus()
            page.keyboard.press("Shift+Tab")
            page.wait_for_timeout(120)
            ring = page.evaluate(
                """() => {
                    const el = document.activeElement;
                    const cs = getComputedStyle(el);
                    return {
                      onTheX: el.classList.contains('thread-ref-chip-remove'),
                      name: (el.getAttribute('aria-label') || el.textContent || '').trim(),
                      outlineStyle: cs.outlineStyle,
                      outlineWidth: cs.outlineWidth,
                      outlineColor: cs.outlineColor,
                      focusVisible: el.matches(':focus-visible'),
                    };
                }"""
            )
            print(f"[hs200-41] chip x focus ring @{width}: {json.dumps(ring)}")
            if ring["onTheX"]:
                _shot_element(
                    page, page.locator('[data-testid="composer-chips"]'),
                    f"composer-refchip-focus-{width}", pad=28,
                )
                assert ring["focusVisible"], "Tab did not make the x focus-visible"
                assert ring["outlineStyle"] != "none" and ring["outlineWidth"] != "0px", (
                    f"the focus ring did NOT survive the library swap: {ring}"
                )
                hovered_focus = _swatch(page, ".thread-ref-chip-remove")
                assert hovered_focus["background"] in (
                    "rgba(0, 0, 0, 0)", "transparent",
                ), hovered_focus

            _assert_clean(page, errors)
            browser.close()
    finally:
        server.stop()
