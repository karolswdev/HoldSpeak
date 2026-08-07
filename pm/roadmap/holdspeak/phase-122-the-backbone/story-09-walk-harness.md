# HS-122-09 — Walk harness

- **Project:** holdspeak
- **Phase:** 122
- **Status:** done
- **Depends on:** HS-122-07 (MCP server — MCP drives, Playwright captures)
- **Unblocks:** HS-122-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

The desk needs a first-class walk harness: seed state programmatically,
drive actions via MCP, capture what the UI renders via Playwright.
Today walks are ad-hoc scripts; the harness makes them repeatable
and evidence-grade.

When this ships:

### Isolated hub fixture
- Start FastAPI with a test database and known owner token.
- Wait for `/health`.
- Seed via `DeskService.seed()` or MCP `desk.create`.
- Tear down after the test.

### Page objects (Python Playwright)
Four page objects using ARIA-first locators:
- **DeskPage** — wait for ready, open palette, keyboard shortcuts,
  inspect open windows.
- **Palette** — open, search, assert combobox, choose via Enter.
- **WorkbenchWindow** — find by identity, toolbar, footer slots,
  snap/close.
- **Pullout** — open by reference, assert content, edit, close.

### Screenshot manifest
Named states captured at 1440px and 393px:
```
00-desk-ready
01-palette-open
02-workbench-with-items
03-undo-receipt-active
04-copy-receipt
05-empty-state-action
06-pullout-open
07-websocket-reconnecting
08-error-recovery
```

### Assertion helpers
- `assert_surface_footer(surface)` — footer exists, three slots.
- `assert_empty_state_actionable(surface)` — action button present.
- `assert_combobox(locator)` — role, activedescendant.
- `assert_no_silent_failure(page)` — no console errors, no failed
  requests.

## Acceptance criteria

- [ ] Hub fixture starts, seeds, and tears down in <10 seconds.
- [ ] Four page objects exercised in at least one walk script.
- [ ] Screenshot manifest captures all listed states at both widths.
- [ ] Assertion helpers catch real failures (verified by intentionally
      breaking a surface).
- [ ] Walk script runs headless in CI-compatible mode.

## Files in scope

- New: `scripts/desk_walk/fixtures.py`
- New: `scripts/desk_walk/pages/desk.py`
- New: `scripts/desk_walk/pages/palette.py`
- New: `scripts/desk_walk/pages/workbench_window.py`
- New: `scripts/desk_walk/pages/pullout.py`
- New: `scripts/desk_walk/assertions.py`
- New: `scripts/desk_walk/walk_phase_122.py`
