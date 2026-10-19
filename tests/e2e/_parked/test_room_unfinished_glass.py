"""PARKED (Betterment Q5, 2026-10-18): the Room's unfinished-ask list in a real
browser (HS-200-41). The Room's Ask field now opens the one Ask window with the
project in About; the Room's own answer face and UNFINISHED list are parked
(web/src/features/project-room/_parked/roomAskAnswer.tsx). These three tests
were in tests/e2e/test_room_glass.py; kept, not run (this folder's conftest)."""
from __future__ import annotations

from tests.e2e.test_room_glass import *  # noqa: F401,F403
from tests.e2e.test_room_glass import (  # noqa: F401
    _rows, _save_ask, _shot_element, _shot_room, _task_create_project, _task_init_desk,
    _task_open_room, _task_room_window,
)


@pytest.mark.timeout(300)
def test_narrow_container_rule_at_393(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The `@container surface (max-width: 420px)` rule, rendered.

    Two rows — one saved, one failed with a long quoted reason — so the
    fold, the wrapping token row and the row rhythm are all legible.
    """
    _ensure_build()
    server, url = _boot(tmp_path, monkeypatch, token=TASK_TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 393, "height": 852})
            page.on("pageerror", lambda e: errors.append(str(e)))

            _task_init_desk(page, url)
            project_id = _task_create_project(page, "Q4 platform", "hs200-41-narrow")
            _save_ask(
                page, project_id,
                "Whether the Q4 platform migration can land before the freeze",
                recipe_key="risk-review",
            )
            _task_open_room(page, project_id)

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
    server, url = _boot(tmp_path, monkeypatch, token=TASK_TOKEN)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            _task_init_desk(page, url)
            project_id = _task_create_project(page, "Q4 platform", "hs200-41-rove")
            _save_ask(page, project_id, "The first unfinished ask")
            _save_ask(page, project_id, "The second unfinished ask")
            _task_open_room(page, project_id)
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
    server, url = _boot(tmp_path, monkeypatch, token=TASK_TOKEN)
    errors: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("pageerror", lambda e: errors.append(str(e)))
            _task_init_desk(page, url)
            project_id = _task_create_project(page, "Q4 platform", "hs200-41-sticky")
            for index in range(5):
                _save_ask(
                    page, project_id,
                    f"Unfinished ask number {index + 1} kept for the sticky measurement",
                )
            _task_open_room(page, project_id)
            page.get_by_test_id("room-unfinished").wait_for(timeout=15000)
            assert _rows(page).count() == 5
            # PHILO-17 sources (#1068, U10): a Room with no source opens Add
            # source at once, and the well goes into the flow while it is
            # open. This leg measures the Room in use: close it first.
            cancel = page.get_by_test_id("room-add-sources-cancel")
            if cancel.count():
                cancel.click()
                page.get_by_test_id("room-add-sources").wait_for(state="detached", timeout=10000)

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
            # PHILO-17 refit: the ask is in the flow (no sticky foot); the
            # rest of this leg still holds: five rows never grow the well.
            assert measured["position"] == "static", measured
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
            assert "OPEN HERE" in standing, standing
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


