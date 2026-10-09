"""Parked from tests/e2e/test_hs156_front_door_glass.py (PHILO-16 C).

Two already-skipped tests of retired front-door faces. Not runnable here:
the helpers they call stay in the live file.
"""
# ruff: noqa

def test_beauty_cards(hub: dict) -> None:
    """HS-156-08: pack cards as OBJECTS — tier row, summary anchor, folded detail.

    HS-170: RETIRED -- the front-door pack cards (.front-door-cards, surface-choice-card)
    are PARKED (HS-170-03, settled-design-four-faces.md Face 3); the pack-card
    recommender is replaced by the Concierge's FOUND engine rows + picker wells
    (ConciergeCore.tsx, own window open-concierge).
    """
    pytest.skip(
        "HS-170: front-door pack cards PARKED (HS-170-03); "
        "capability now at the Concierge's FOUND section (ConciergeCore.tsx)"
    )
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    _api_direct(url, "POST", "/api/desk/seed")
    _api_direct(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    # A reachable stub endpoint so the recommender ALWAYS offers packs,
    # even on runners with no local inference runtime (CI).
    stub, stub_port = _start_stub_endpoint()
    _seed_endpoint_profile(
        hub["db"], "hs156-beauty-stub", "Qwen server (stub)",
        f"http://127.0.0.1:{stub_port}", "glass-stub-model",
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 1000})
            _open_models_module(page, url, width)
            page.wait_for_selector("[data-testid='front-door-cards']", timeout=20000)
            _save_shot_08(page, "cards", width)

            # The recommended pack, selected: presence, not just a corner tag
            recommended = page.locator(".surface-choice-card[data-recommended]").first
            recommended.wait_for(state="visible", timeout=20000)
            recommended.click()
            page.wait_for_timeout(300)
            _save_shot_08(page, "cards-selected", width)

            # One fold open: per-job detail grouped by what serves them
            cards_count = page.locator(".surface-choice-card").count()
            folds = page.locator(
                ".surface-choice-card-fold .surface-disclosure-trigger"
            )
            assert cards_count >= 1 and folds.count() == cards_count, (
                "every pack card carries a fold"
            )
            folds.first.click()
            page.wait_for_timeout(300)
            _save_shot_08(page, "cards-fold-open", width)

            # No horizontal overflow
            body_w = page.evaluate("document.body.scrollWidth")
            viewport_w = page.evaluate("window.innerWidth")
            assert body_w <= viewport_w + 1, (
                f"Horizontal overflow at {width}: body={body_w}, viewport={viewport_w}"
            )

            page.close()

        browser.close()
    stub.shutdown()


def test_beauty_candidate_picker(hub: dict) -> None:
    """HS-156-08: candidates are material cards (name, boundary, health), never raw rows.

    HS-170: RETIRED -- the front-door candidate picker (.assignment-candidates)
    is PARKED (HS-170-03, settled-design-four-faces.md Face 3); the picker is
    replaced by the Concierge's per-group ChoiceCard picker wells
    (ConciergeCore.tsx PickerWell, concierge-picker-well-{group} testid).
    """
    pytest.skip(
        "HS-170: front-door candidate picker PARKED (HS-170-03); "
        "capability now at the Concierge's picker ChoiceCards (ConciergeCore.tsx)"
    )
    from playwright.sync_api import sync_playwright

    url = hub["url"]
    db = hub["db"]

    _api_direct(url, "POST", "/api/desk/seed")
    _api_direct(url, "PUT", "/api/setup/onboarding", {"disposition": "completed"})
    _seed_profile_and_assign(db)
    # Stub-backed endpoint profiles: a LAN address here would stall the
    # recommender's reachability probes on CI (3 s each, no LAN).
    stub, stub_port = _start_stub_endpoint()
    _seed_endpoint_profile(
        db, "hs156-beauty-lan", "Qwen server on .43",
        f"http://127.0.0.1:{stub_port}", "qwen3.5-9b",
    )
    _seed_endpoint_profile(
        db, "hs156-beauty-mlx", "Qwen3.5 9B (MLX)",
        f"http://127.0.0.1:{stub_port}", "qwen3.5-9b-mlx",
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        for width in (1440, 393):
            page = browser.new_page(viewport={"width": width, "height": 1000})
            _open_models_module(page, url, width)

            # The configured desk shows the strip; wait for it, then the fold
            page.wait_for_selector("[data-testid='front-door-strip']", timeout=25000)
            advanced = page.locator("text=Advanced")
            assert advanced.count() > 0, "the strip carries the Advanced fold"
            advanced.first.click()
            page.wait_for_timeout(1000)
            table_tab = page.get_by_role("tab", name="Table")
            if table_tab.count() > 0:
                table_tab.first.click()
                page.wait_for_timeout(1500)

            # Open the first assignment editor
            page.locator(".capability-assignment-row button").first.click()
            page.wait_for_selector(".assignment-candidates", timeout=15000)
            page.locator(".assignment-candidates").scroll_into_view_if_needed()
            page.wait_for_timeout(300)

            # Material cards, not raw rows: name + chips + chain state
            cards = page.locator(".assignment-candidates > button")
            assert cards.count() >= 1, "the editor lists candidate cards"
            assert page.locator(".assignment-candidate-chips").count() >= 1

            _save_shot_08(page, "candidate-picker", width)

            # No horizontal overflow
            body_w = page.evaluate("document.body.scrollWidth")
            viewport_w = page.evaluate("window.innerWidth")
            assert body_w <= viewport_w + 1, (
                f"Horizontal overflow at {width}: body={body_w}, viewport={viewport_w}"
            )

            page.close()

        browser.close()
    stub.shutdown()
