"""P06 Room visual pass: Files, compact Sources, and the real Note return door.

The Project, resource membership, and Note are real isolated hub records.
The Components example uses the production Files view with a local adapter.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from tests._evidence import evidence_dir
from .glass_infra import _api, _ensure_build, _normal_chair
from .test_desk_sweep import TARGET_JS
from .test_native_project_source_return_glass import (
    HEIGHT,
    NOTE_REF,
    NOTE_TITLE,
    PROJECT_A,
    PROJECT_A_NAME,
    TOKEN,
    _boot_isolated,
    _components_ready,
    _focused_filed_row,
    _open_project,
    _return_project,
    _seed,
    _start,
)

pytest.importorskip("playwright.sync_api", reason="Room visual glass needs Playwright")

SHOTS = "native-room-visual-wave8"


def _at_rest(page: Any, selector: str) -> dict[str, Any]:
    """Read the action before Playwright can scroll it into view."""
    state = page.evaluate("""selector => {
      const e = document.querySelector(selector);
      if (!e) return {missing: selector};
      const r = e.getBoundingClientRect();
      const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      return {box: r.toJSON(), inViewport: r.left >= 0 && r.right <= innerWidth &&
        r.top >= 0 && r.bottom <= innerHeight, hit: hit === e || e.contains(hit)};
    }""", selector)
    assert "missing" not in state, state
    return state


def _reachable_action(page: Any, selector: str, width: int, probes: dict[str, Any]) -> None:
    """Explicitly bring a below-fold verb into view, then test its hit area."""
    probes[selector] = {"beforeScroll": _at_rest(page, selector)}
    page.evaluate("""selector => document.querySelector(selector).scrollIntoView({block:'center'})""", selector)
    page.evaluate("""() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))""")
    state = _at_rest(page, selector)
    probes[selector]["afterScroll"] = state
    assert state["inViewport"] and state["hit"], (selector, state)
    box = state["box"]
    if width == 393:
        assert box["width"] >= 44 and box["height"] >= 44, (selector, box)
    # Centre, edge midpoints, and corners, inset one pixel. A real pointer
    # move must agree with elementFromPoint at every sample.
    x0, x1 = box["left"] + 1, box["right"] - 1
    y0, y1 = box["top"] + 1, box["bottom"] - 1
    xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
    points = [(xc, yc), (xc, y0), (x1, yc), (xc, y1), (x0, yc),
              (x0, y0), (x1, y0), (x0, y1), (x1, y1)]
    page.evaluate("""() => {
      if (!window.__roomVisualPointerArmed) {
        window.__roomVisualPointerArmed = true;
        document.addEventListener('pointermove', event => {
          window.__roomVisualPointerTarget = event.target;
        }, true);
      }
    }""")
    faults = []
    for x, y in points:
        before_owner = page.evaluate("""([x,y]) => document.elementsFromPoint(x,y).slice(0,5)
          .map(e => ({tag:e.tagName, id:e.id, className:typeof e.className==='string'?e.className:'',
            box:e.getBoundingClientRect().toJSON()}))""", [x, y])
        hit = page.evaluate("""([selector, x, y]) => {
          const e = document.querySelector(selector), h = document.elementFromPoint(x, y);
          return !!e && !!h && (e === h || e.contains(h));
        }""", [selector, x, y])
        page.mouse.move(x, y)
        pointer = page.evaluate("""selector => {
          const e = document.querySelector(selector), h = window.__roomVisualPointerTarget;
          return !!e && !!h && (e === h || e.contains(h));
        }""", selector)
        if not (hit and pointer):
            owner = page.evaluate("""([x,y]) => document.elementsFromPoint(x,y).slice(0,4)
              .map(e => ({tag:e.tagName, id:e.id, className:typeof e.className==='string'?e.className:''}))""", [x, y])
            layout = page.evaluate("""([selector,x,y]) => {
              const e=document.querySelector(selector), h=document.elementFromPoint(x,y);
              const chain=node=>{const out=[];for(let i=0;node&&i<6;i++,node=node.parentElement){
                const s=getComputedStyle(node);out.push({tag:node.tagName,id:node.id,
                  className:typeof node.className==='string'?node.className:'',
                  box:node.getBoundingClientRect().toJSON(),z:s.zIndex,position:s.position,
                  pointerEvents:s.pointerEvents,transform:s.transform,overflow:s.overflow});}return out;};
              return {target:chain(e),hit:chain(h),fronts:[...document.querySelectorAll('.desk-window')]
                .map(n=>({id:n.id,front:n.classList.contains('is-front'),
                  z:getComputedStyle(n).zIndex,box:n.getBoundingClientRect().toJSON()}))};
            }""", [selector, x, y])
            faults.append({"x": x, "y": y, "hit": hit, "pointer": pointer,
                           "beforeOwners": before_owner, "owners": owner, "layout": layout})
    probes[selector]["ninePointFaults"] = faults
    if faults:
        evidence = evidence_dir(SHOTS)
        slug = re.sub(r"[^a-z0-9]+", "-", selector.lower()).strip("-")[-90:]
        (evidence / f"fault-{width}-{slug}.json").write_text(json.dumps(probes[selector], indent=2) + "\n")
        page.screenshot(path=str(evidence / f"fault-{width}-{slug}.png"))
    assert not faults, (selector, faults)


def _columns(scope: Any) -> dict[str, Any]:
    """Header and actual cells must name the same two visible columns."""
    result = scope.evaluate("""root => {
      const grid = root.querySelector('[role=grid][aria-label="Filed notes"]');
      if (!grid) return {missing:'Filed notes grid'};
      const head = [...grid.querySelectorAll('[role=columnheader]')].map(e => e.dataset.col);
      const row = grid.querySelector('[role=row][data-object-id]');
      const cells = row ? [...row.querySelectorAll('[role=gridcell]')].map(e => e.dataset.col) : [];
      const shown = selector => [...grid.querySelectorAll(selector)].filter(e => {
        const s = getComputedStyle(e), r = e.getBoundingClientRect();
        return s.display !== 'none' && s.visibility !== 'hidden' && r.width && r.height;
      }).map(e => e.dataset.col);
      return {head, cells, visibleHead:shown('[role=columnheader]'),
        visibleCells:shown('[role=row][data-object-id] [role=gridcell]')};
    }""")
    assert result == {"head": ["name", "kind"], "cells": ["name", "kind"],
                      "visibleHead": ["name", "kind"], "visibleCells": ["name", "kind"]}, result
    return result


def _hierarchy(room: Any) -> dict[str, Any]:
    result = room.evaluate("""root => {
      const selectors = ['[data-testid=room-head]', '.room-ask-container',
        '[data-testid=room-fold-files]', '[data-testid=room-fold-sources]'];
      const nodes = selectors.map(s => root.querySelector(s));
      return {present:nodes.map(Boolean), order:nodes.map(n => n?.getBoundingClientRect().top),
        sameFlow:nodes.every((n,i) => !i ||
          !!(nodes[i-1].compareDocumentPosition(n) & Node.DOCUMENT_POSITION_FOLLOWING))};
    }""")
    assert result["present"] == [True] * 4 and result["sameFlow"], result
    assert result["order"] == sorted(result["order"]), result
    return result


def _files_geometry(room: Any) -> dict[str, float]:
    """Offsets from Files, so ordinary Room scrolling does not look like jump."""
    result = room.evaluate("""root => {
      const files=root.querySelector('[data-testid=room-fold-files] > details > summary');
      const row=root.querySelector('[data-testid=room-files] [data-object-id]');
      const sources=root.querySelector('[data-testid=room-fold-sources] > details > summary');
      if (!files || !row || !sources) return {missing:true};
      const f=files.getBoundingClientRect(), r=row.getBoundingClientRect(), s=sources.getBoundingClientRect();
      return {rowTop:r.top-f.top, rowHeight:r.height, sourcesTop:s.top-f.top};
    }""")
    assert not result.get("missing"), result
    return result


def _same_files_geometry(before: dict[str, float], after: dict[str, float]) -> None:
    assert all(abs(before[key] - after[key]) <= 1 for key in before), (before, after)


@pytest.mark.timeout(150)
@pytest.mark.parametrize("width", [1440, 393])
def test_room_files_before_compact_sources_and_real_note_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from playwright.sync_api import expect, sync_playwright

    _ensure_build()
    server, base = _boot_isolated(tmp_path, monkeypatch)
    _seed()
    shots = evidence_dir(SHOTS)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": HEIGHT[width]},
                                    has_touch=width == 393, is_mobile=width == 393,
                                    reduced_motion="reduce")
            page.set_default_timeout(20_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            _start(page, base)
            room = _open_project(page, PROJECT_A, PROJECT_A_NAME)
            files_fold = room.get_by_test_id("room-fold-files")
            sources_fold = room.get_by_test_id("room-fold-sources")
            files_fold.wait_for()
            sources_fold.wait_for()
            hierarchy = _hierarchy(room)
            assert sources_fold.locator("details").first.get_attribute("open") is None
            expect(room.get_by_test_id("room-add-sources")).to_have_count(0)
            expect(room.locator("[data-testid^='door-row-']")).to_have_count(0)
            probes: dict[str, Any] = {"hierarchy": hierarchy}
            page.screenshot(path=str(shots / f"room-compact-{width}.png"))

            _reachable_action(page, "#surface-project-memory [data-testid='room-fold-files'] summary", width, probes)
            files_fold.locator("summary").click()
            files = room.get_by_test_id("room-files")
            row = files.locator(f"[data-object-id='{NOTE_REF}']")
            expect(row).to_contain_text(NOTE_TITLE)
            probes["columns"] = _columns(files)
            _reachable_action(page, f"#surface-project-memory [data-object-id='{NOTE_REF}'] .object-list-open", width, probes)
            row.locator(".object-list-open").click()
            expect(files.get_by_test_id("room-files-open")).to_be_enabled()
            _reachable_action(page, "#surface-project-memory [data-testid='room-files-open']", width, probes)
            page.screenshot(path=str(shots / f"room-files-selected-{width}.png"))
            files.get_by_test_id("room-files-open").click()
            note = page.locator(f"[id='pullout:{NOTE_REF}']")
            note.locator(".thought-note-body .cm-content").wait_for()
            expect(note).to_have_class(re.compile(r"\bis-front\b"))
            assert NOTE_TITLE in note.inner_text()
            page.screenshot(path=str(shots / f"room-note-open-{width}.png"))
            room = _return_project(page, note, PROJECT_A_NAME, width)
            expect(room.get_by_test_id("room-files-return")).to_have_text("Filed here")
            files = room.get_by_test_id("room-files")
            probes["returnFocus"] = _focused_filed_row(room)
            probes["returnColumns"] = _columns(files)
            page.screenshot(path=str(shots / f"room-file-return-{width}.png"))

            # The accepted-watch count is still zero after a Note round trip.
            sources_fold = room.get_by_test_id("room-fold-sources")
            _reachable_action(page, "#surface-project-memory [data-testid='room-fold-sources'] > .gadget-fold > summary", width, probes)
            sources_fold.locator(".gadget-fold > summary").first.click()
            expect(room.get_by_test_id("room-add-source")).to_be_visible()
            expect(room.get_by_test_id("room-add-sources")).to_have_count(0)
            expect(room.locator("[data-testid^='door-row-']")).to_have_count(0)
            page.screenshot(path=str(shots / f"room-sources-disclosed-{width}.png"))
            _reachable_action(page, "#surface-project-memory [data-testid='room-add-source']", width, probes)
            room.get_by_test_id("room-add-source").click()
            chooser = room.get_by_test_id("room-add-sources")
            expect(chooser).to_be_visible()
            for provider in ("github", "jira", "confluence"):
                expect(chooser.get_by_test_id(f"door-row-{provider}")).to_be_visible()
            page.screenshot(path=str(shots / f"room-source-chooser-{width}.png"))
            _reachable_action(page, "#surface-project-memory [data-testid='room-add-sources-cancel']", width, probes)
            chooser.get_by_test_id("room-add-sources-cancel").click()
            expect(chooser).to_have_count(0)
            # Cancel leaves the compact Sources tab. The Add entry remains
            # available on the next explicit disclosure.
            expect(sources_fold.locator("details").first).not_to_have_attribute("open", "")
            expect(room.get_by_test_id("room-add-source")).to_have_count(1)
            expect(room.locator("[data-testid^='door-row-']")).to_have_count(0)
            page.screenshot(path=str(shots / f"room-source-cancel-{width}.png"))
            _reachable_action(page, "#surface-project-memory [data-testid='room-fold-sources'] > .gadget-fold > summary", width, probes)
            sources_fold.locator(".gadget-fold > summary").first.click()
            expect(room.get_by_test_id("room-add-source")).to_be_visible()

            # A real Room read-marker write announces desk_changed; the
            # production Files hook then requests the real resource list.
            # Hold only that response after it reaches the server to inspect
            # the retained-loading face without inventing a successful read.
            expect(files.get_by_test_id("room-files-open")).to_be_enabled()
            before_refresh = _files_geometry(room)
            page.evaluate("""projectId => {
              const original=window.fetch.bind(window);
              const hold={taken:false,serverRead:false,release:null};
              window.__roomVisualResourceHold=hold;
              window.fetch=(...args)=>{
                const url=String(typeof args[0]==='string'?args[0]:args[0].url);
                if (!hold.taken && url.includes(`/api/projects/${projectId}/resources`)) {
                  hold.taken=true;
                  return new Promise((resolve,reject)=>original(...args).then(response=>{
                    hold.serverRead=response.ok;
                    hold.release=()=>resolve(response);
                  },reject));
                }
                return original(...args);
              };
            }""", PROJECT_A)
            _api(page, "POST", f"/api/projects/{PROJECT_A}/room/read", {}, token=TOKEN)
            page.wait_for_function("() => !!window.__roomVisualResourceHold?.release")
            assert page.evaluate("window.__roomVisualResourceHold.serverRead")
            chip = files.locator(".surface-section-head [role=status][aria-label='Reading files · Last read']")
            expect(chip).to_be_visible()
            assert files.locator("[role=status][aria-label^='Reading files']").count() == 1
            held_refresh = _files_geometry(room)
            _same_files_geometry(before_refresh, held_refresh)
            page.screenshot(path=str(shots / f"room-files-refresh-held-{width}.png"))
            page.evaluate("window.__roomVisualResourceHold.release()")
            expect(chip).to_have_count(0)
            expect(files.get_by_test_id("room-files-open")).to_be_enabled()
            after_refresh = _files_geometry(room)
            _same_files_geometry(before_refresh, after_refresh)
            probes["retainedRead"] = {"before": before_refresh, "held": held_refresh, "after": after_refresh}
            page.screenshot(path=str(shots / f"room-files-refresh-settled-{width}.png"))

            # The server's Room is real except for one fault-isolated Sources
            # section read. Retry removes that fault and reads the real server
            # response; no synthetic successful watch or provider is supplied.
            fault = {"retry_armed": False, "reads": 0, "real_reads": 0}
            page.add_init_script("window.__roomSourcesFaultActive = true")

            def sources_read(route: Any) -> None:
                response = route.fetch()
                body = response.json()
                assert body["sources"]["state"] == "ok", body["sources"]
                # Decide at fulfillment, so an older server read that
                # finishes after Retry cannot inject a late stale refusal.
                # Once the Retry control is shown, decide from the browser's
                # actual press flag. Ambient reads cannot clear the fault.
                active = not fault["retry_armed"] or page.evaluate(
                    "() => window.__roomSourcesFaultActive === true")
                if active:
                    body["sources"] = {"state": "degraded", "error_code": "sources_read_failed"}
                    fault["reads"] += 1
                    route.fulfill(response=response, json=body)
                else:
                    fault["real_reads"] += 1
                    route.fulfill(response=response)

            page.route(f"**/api/projects/{PROJECT_A}/room", sources_read)
            page.reload(wait_until="load")
            _normal_chair(page)
            room = _open_project(page, PROJECT_A, PROJECT_A_NAME)
            sources_fold = room.get_by_test_id("room-fold-sources")
            expect(sources_fold.locator("details").first).to_have_attribute("open", "")
            expect(sources_fold.get_by_text("Could not read the sources · Nothing changed · Try again")).to_be_visible()
            expect(sources_fold.get_by_test_id("room-sources-not-read")).to_contain_text("Sources not read")
            expect(room.get_by_test_id("room-fold-files")).to_be_visible()
            expect(room.get_by_test_id("room-add-sources")).to_have_count(0)
            expect(room.locator("[data-testid^='door-row-']")).to_have_count(0)
            page.screenshot(path=str(shots / f"room-sources-not-read-{width}.png"))
            retry = sources_fold.get_by_role("button", name="Try again")
            _reachable_action(page, "#surface-project-memory [data-testid='room-fold-sources'] .surface-state[data-kind='error'] button", width, probes)
            page.evaluate("""() => {
              const selector="#surface-project-memory [data-testid='room-fold-sources'] .surface-state[data-kind='error'] button";
              const release=event=>{
                if (!event.target?.closest?.(selector)) return;
                window.__roomSourcesFaultActive=false;
                document.removeEventListener('click',release,true);
              };
              document.addEventListener('click',release,true);
            }""")
            fault["retry_armed"] = True
            retry.click()
            expect(sources_fold.get_by_text("Could not read the sources · Nothing changed · Try again")).to_have_count(0)
            expect(sources_fold.get_by_test_id("room-sources-not-read")).to_have_count(0)
            expect(sources_fold.locator("details").first).not_to_have_attribute("open", "")
            expect(room.get_by_test_id("room-add-sources")).to_have_count(0)
            assert fault["reads"] >= 1 and fault["real_reads"] >= 1, fault
            sources_fold.locator(".gadget-fold > summary").first.click()
            expect(room.get_by_test_id("room-add-source")).to_be_visible()
            expect(room.locator("[data-testid^='door-row-']")).to_have_count(0)
            page.screenshot(path=str(shots / f"room-sources-recovered-{width}.png"))
            if width == 393:
                assert not page.evaluate(TARGET_JS, "#surface-project-memory [data-testid='room-fold-files']")
                assert not page.evaluate(TARGET_JS, "#surface-project-memory [data-testid='room-fold-sources']")
            (shots / f"room-probes-{width}.json").write_text(json.dumps(probes, indent=2) + "\n")
            assert not errors, errors
            browser.close()
    finally:
        server.stop()


@pytest.mark.timeout(120)
@pytest.mark.parametrize("width", [1440, 393])
def test_components_filed_notes_uses_same_two_column_section_locally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from playwright.sync_api import expect, sync_playwright

    _ensure_build()
    server, base = _boot_isolated(tmp_path, monkeypatch)
    shots = evidence_dir(SHOTS)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": HEIGHT[width]},
                                    has_touch=width == 393, is_mobile=width == 393,
                                    reduced_motion="reduce")
            page.set_default_timeout(20_000)
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"{base}/design/components?token={TOKEN}", wait_until="load")
            _components_ready(page)
            pattern = page.get_by_role("navigation", name="Patterns").get_by_role("button", name="Lists", exact=True)
            if pattern.count():
                pattern.click()
            else:
                page.get_by_role("navigation", name="Patterns").get_by_role("button").click()
                page.locator("[role^='menuitem']").filter(has_text="Lists").first.click()
            page.get_by_role("combobox", name="Example state").select_option("filed-notes")
            specimen = page.get_by_test_id("reference-filed-notes")
            specimen.wait_for()
            requests: list[str] = []

            def observe(request: Any) -> None:
                # The host can read its own collections. This local specimen
                # cannot fetch its synthetic records, adopt, write, or infer.
                scoped_read = request.method == "GET" and any(part in request.url for part in (
                    "/api/projects/local-project", "/api/notes/review-record",
                    "/api/thoughts/for-note/review-record",
                ))
                # The Desk host may post its own ambient heartbeat while this
                # local specimen is open; that is not a specimen write.
                mutation = request.method != "GET" and (
                    "/api/" in request.url or "/v1/chat/completions" in request.url
                ) and not request.url.split("?", 1)[0].endswith("/api/desk/presence")
                if scoped_read or mutation:
                    requests.append(f"{request.method} {request.url}")

            page.on("request", observe)
            fold = specimen.get_by_test_id("room-fold-files")
            _reachable_action(page, "[data-testid='reference-filed-notes'] [data-testid='room-fold-files'] summary", width, {})
            fold.locator("summary").click()
            files = specimen.get_by_test_id("room-files")
            row = files.locator("[data-object-id='note:review-record']")
            expect(row).to_contain_text("Review record")
            columns = _columns(files)
            probes: dict[str, Any] = {"columns": columns}
            page.screenshot(path=str(shots / f"room-reference-files-{width}.png"))
            _reachable_action(page, "[data-testid='reference-filed-notes'] [data-object-id='note:review-record'] .object-list-open", width, probes)
            row.locator(".object-list-open").click()
            expect(files.get_by_test_id("room-files-open")).to_be_enabled()
            _reachable_action(page, "[data-testid='reference-filed-notes'] [data-testid='room-files-open']", width, probes)
            files.get_by_test_id("room-files-open").click()
            expect(specimen.locator(".reference-receipt[role='status']")).to_contain_text(
                "Opened locally · note:review-record · local-project")
            receipt = specimen.locator(".reference-receipt[role='status']")
            outcome = receipt.evaluate("""e => {
              const frame=e.closest('.desk-window');
              const body=frame?.querySelector('.desk-surface-body');
              const foot=frame?.querySelector('.surface-footer');
              const r=e.getBoundingClientRect(), b=body?.getBoundingClientRect(), f=foot?.getBoundingClientRect();
              const hit=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);
              const scroll=[];for(let n=e.parentElement;n&&n!==frame;n=n.parentElement){
                const s=getComputedStyle(n);if(/auto|scroll/.test(s.overflowY))
                  scroll.push({className:n.className,top:n.scrollTop,height:n.clientHeight,
                    scrollHeight:n.scrollHeight,box:n.getBoundingClientRect().toJSON()});}
              return {receipt:r.toJSON(),body:b?.toJSON(),footer:f?.toJSON(),
                frame:frame?.getBoundingClientRect().toJSON(),scroll,
                inViewport:r.top>=0&&r.bottom<=innerHeight,
                inBody:!!b&&r.top>=b.top&&r.bottom<=b.bottom,
                aboveFooter:!!f&&r.bottom<=f.top,
                hit:hit===e||e.contains(hit),hitName:hit?.className||hit?.tagName};
            }""")
            (shots / f"room-reference-outcome-{width}.json").write_text(json.dumps(outcome, indent=2) + "\n")
            page.screenshot(path=str(shots / f"room-reference-open-{width}.png"))
            assert outcome["inViewport"] and outcome["inBody"] and outcome["aboveFooter"] and outcome["hit"], outcome
            if width == 393:
                assert not page.evaluate(TARGET_JS, "[data-testid='reference-filed-notes']")
            (shots / f"room-reference-probes-{width}.json").write_text(json.dumps(probes, indent=2) + "\n")
            assert not requests, requests
            assert not errors, errors
            browser.close()
    finally:
        server.stop()
