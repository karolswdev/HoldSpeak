"""Parked by Betterment daily D4 (Today is one page): leg 3 of
tests/e2e/test_desk_glass.py's footer-receipt walk, the Brief wing's footer
(Acknowledge refused). The wing is parked in
web/src/desk/pullouts/_parked/BriefWing.tsx. Not collected (_parked).

The leg, verbatim:

        # 3. a footer receipt (the Brief view's SurfaceFooter)
        # The module shares a hub across widths. Each sitting owns a named
        # record, and its source id must survive selection and return.
        receipt_title = f"Receipt hit material at {width}"
        status, made = receipt_hub.api("POST", "/api/decisions", {"title": receipt_title, "status": "proposed"})
        assert status == 201
        decision_id = made["decision"]["id"]
        # the brief is made through the hub's own route (the Chair's Generate
        # is J10's case; at 393 the open Thread sheet covers the Chair here)
        status, _ = receipt_hub.api("POST", "/api/brief/generate", {})
        assert status in (200, 201), status
        _search(page, "Show today's brief", "[id='desk-palette-option-desk.intelligence-brief']")
        # PHILO-17 summaries (#1064): a setup row ("No engine for summaries")
        # can lead the list; select the decision's own row.
        page.locator("[data-testid=brief-sf-row] .intelligence-brief-sf-primary",
                     has_text=receipt_title).click()
        # The row opens the decision in its own window (PHILO-13-06 B1); at
        # 393 that window is the front sheet. Bring the Brief back to the
        # front from its Dock tile: its footer is the receipt under test.
        source = page.locator(f"[id='pullout:decision:{decision_id}']")
        source.wait_for(timeout=15000)
        assert source.get_attribute("aria-label") == receipt_title
        page.locator(".desk-dock [data-app='intelligence:desk']").click()
        today = page.locator("[id='pullout:intelligence:desk'].is-front")
        today.wait_for(timeout=15000)
        assert today.get_by_role("group", name="Intelligence view", exact=True).filter(visible=True).get_by_role(
            "button", name="Brief", exact=True).get_attribute("aria-pressed") == "true", (
                "Returning to Today must keep the selected Brief view and its triage row"
            )
        assert today.get_by_test_id("brief-sf-row").filter(
            has_text=receipt_title).get_attribute("data-selected") == "true"
        _fault(page, "POST", "/api/brief/items/")
        today.get_by_role("button", name="Acknowledge", exact=True).click()
        _probe(page, ".surface-footer-receipt", "brief-footer", width, failures)
"""
