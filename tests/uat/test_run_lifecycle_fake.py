"""The run state machine, driven by a fake product (no real boot).

Proves the honest lifecycle — booting→up, failed-with-log-tail, restart
tears the old process down first, teardown leaves no live process — without
paying for a real HoldSpeak boot. The real boot is exercised (marked,
self-skipping) in ``test_run_lifecycle_real.py``.
"""

from __future__ import annotations

import pytest

from uat.conductor import paths


def test_create_run_boots_up_under_isolated_home(manager):
    run = manager.create_run()
    assert run.status == "up"
    assert run.pid is not None
    # The config + HOME live under uat/_runs, never the real ~.
    home = paths.run_home(run.id)
    assert home.exists()
    assert (home / ".config" / "holdspeak" / "config.json").exists()
    assert str(paths.runs_root()) in str(home)
    # Loopback by default; no LAN token.
    assert run.product_host == "127.0.0.1"
    assert run.lan is False
    assert run.to_public()["pairing"]["url"].startswith("http://127.0.0.1:")


def test_failed_boot_reports_log_tail_not_hang(manager, fake_products):
    fake_products.boot_ok = False
    run = manager.create_run()
    assert run.status == "failed"
    assert run.error and "endpoint refused" in run.error
    assert run.pid is None
    # The failing product was stopped, not left to orphan.
    assert fake_products.instances[-1].stopped is True


def test_restart_tears_down_old_then_boots_new(manager, fake_products):
    run = manager.create_run(config={"model": {"warm_on_start": False}})
    first = fake_products.instances[-1]
    run2 = manager.restart(run.id, config={"meeting": {"intel_enabled": False}})
    assert run2.id == run.id
    assert run2.status == "up"
    # The first product process was stopped before the second booted.
    assert first.stopped is True
    assert len(fake_products.instances) == 2
    assert fake_products.instances[-1] is not first


def test_teardown_marks_down_and_removes_live_process(manager, fake_products):
    run = manager.create_run()
    prod = fake_products.instances[-1]
    torn = manager.teardown(run.id)
    assert torn.status == "down"
    assert torn.pid is None
    assert prod.stopped is True
    # Still queryable from the DB after teardown, still 'down'.
    again = manager.get(run.id)
    assert again.status == "down"


def test_lan_run_gets_own_token_and_lan_pairing(manager):
    run = manager.create_run(lan=True)
    assert run.status == "up"
    assert run.product_host == "0.0.0.0"
    assert run.token  # a per-run web auth token was minted
    pub = run.to_public()
    assert pub["pairing"]["lan"] is True
    assert f"token={run.token}" in pub["pairing"]["url"]
    # The token was written into the overlay the product booted with.
    assert run.config["meeting"]["web_auth_token"] == run.token


def test_lan_token_survives_deck_restart(manager):
    run = manager.create_run(lan=True, deck="golden-local")
    token = run.token
    pairing = run.pairing_url
    restarted = manager.restart(run.id, deck="bad-endpoint")
    assert restarted.token == token
    assert f"token={token}" in restarted.pairing_url
    assert restarted.pairing_url.split("?", 1)[0] == pairing.split("?", 1)[0]


def test_get_reflects_a_crashed_product_as_down(manager, fake_products):
    run = manager.create_run()
    prod = fake_products.instances[-1]
    prod._alive = False  # simulate the product dying after a healthy boot
    got = manager.get(run.id)
    assert got.status == "down"


def test_list_runs_returns_all(manager):
    a = manager.create_run()
    b = manager.create_run()
    ids = {r.id for r in manager.list_runs()}
    assert {a.id, b.id} <= ids
