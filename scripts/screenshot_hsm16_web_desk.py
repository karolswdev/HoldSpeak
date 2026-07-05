"""HSM-16-04 — the web desk slice, proven live (Playwright, real app, scratch DB).

Captures the resurrected recipe layer (rail + in-world editor) and the Ask AI
atom's full web arc: lasso → bundle bar → compose (honest egress for the picked
profile) → printed card → Keep (the artifact materializes on the desk wearing
the NEW beat). The intel engine is faked in-process so no model loads; the
/api/ask and /api/ask/keep routes run for real.
"""
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from playwright.sync_api import sync_playwright

from holdspeak.db import get_database, reset_database
from holdspeak.db.milestones import FIRST_DICTATION_SUCCESS
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OUT = Path("pm/roadmap/holdspeak-mobile/phase-16-the-desk-everywhere/screenshots")
OUT.mkdir(parents=True, exist_ok=True)

ANSWER = (
    "The mesh is real: the manifest is the wire's eleventh kind, the Ask atom "
    "carries its full lineage, and the web desk now runs both."
)


class _FakeIntel:
    active_provider = "cloud"

    def run_prompt(self, **kwargs):
        return ANSWER


def seed(db) -> None:
    db.milestones.mark(FIRST_DICTATION_SUCCESS)  # past the first-run guard
    db.notes.upsert(note_id="note_mesh", title="Mesh sync owner",
                    body_markdown="Karol owns the mesh sync review.")
    db.notes.upsert(note_id="note_walk", title="Couch queue",
                    body_markdown="17-06 plus the walk riders, one session.")
    db.plugins.record_artifact(
        artifact_id="artifact_q3", meeting_id="", artifact_type="plugin_output",
        title="Q3 summary", body_markdown="Ship the manifest. Prove the atom.",
    )
    db.recipes.upsert(recipe_id="recipe_scout", name="Scout", avatar="🦊",
                      role="Research scout",
                      system_prompt="You distill piles of context into one page.")
    db.profiles.upsert(profile_id="profile_lan", name="LAN box",
                       kind="openAICompatible",
                       base_url="http://192.168.1.43:8080/v1",
                       model="Qwen3.5-9B-Q6_K")


def main():
    tmp = Path(tempfile.mkdtemp())
    reset_database()
    db = get_database(tmp / "holdspeak.db")
    seed(db)
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=MagicMock(), on_stop=MagicMock(),
                            get_state=MagicMock(return_value={})),
        host="127.0.0.1")
    url = server.start()
    time.sleep(1.0)
    fake = _FakeIntel()
    try:
        with patch("holdspeak.intel.providers.build_meeting_intel_for_profile",
                   lambda **kw: fake), \
             patch("holdspeak.intel.providers.build_configured_meeting_intel",
                   lambda: fake), \
             sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.set_viewport_size({"width": 1280, "height": 800})
            # Arrange the desk deterministically (the legacy layout contract —
            # local-only, never synced) so no object sits under the conveyor.
            pg.add_init_script(
                'localStorage.setItem("hs.diorama.pos", JSON.stringify({'
                'recipe_scout: {x: 0.22, y: 0.34},'
                'note_mesh: {x: 0.44, y: 0.42},'
                'note_walk: {x: 0.62, y: 0.32},'
                'artifact_q3: {x: 0.8, y: 0.44}}))'
            )
            pg.goto(f"{url}/", wait_until="networkidle")
            pg.wait_for_selector(".desk-obj", timeout=6000)
            # The mission-control conveyor reads THIS machine's real rails —
            # off-topic for the story and it must not leak local project names
            # into committed shots.
            pg.add_style_tag(content=".desk-mc, .desk-mc-tab { display: none !important; }")
            pg.wait_for_timeout(700)

            # 1 — the resurrected recipe layer: Scout floats AND rides the rail.
            assert pg.query_selector(".desk-rail-avatar"), "recipe rail is empty"
            pg.screenshot(path=str(OUT / "hsm-16-04-desk-recipes.png"))

            # 2 — recipe authoring in-world: pull out Scout, then Edit.
            pg.click('.desk-obj[data-obj-id="recipe_scout"]')
            pg.wait_for_selector(".desk-pullout", timeout=4000)
            pg.click(".desk-pullout-foot .desk-chip:has-text('Edit')")
            pg.wait_for_selector(".desk-editor", timeout=4000)
            pg.click(".desk-editor-more")
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(OUT / "hsm-16-04-recipe-editor.png"))
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(300)

            # 3 — the lasso: rope the objects on the open desk → the bundle bar.
            pg.mouse.move(160, 200)
            pg.mouse.down()
            pg.mouse.move(1140, 560, steps=16)
            pg.mouse.up()
            pg.wait_for_selector(".desk-askbar", timeout=4000)
            n_selected = pg.eval_on_selector_all(".desk-obj.selected", "els => els.length")
            assert n_selected >= 2, f"lasso roped only {n_selected}"
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(OUT / "hsm-16-04-ask-selected.png"))

            # 4 — compose: the atelier posture (desk visible), lens grid,
            # the RUNS-ON pick names the LAN profile's honest egress.
            pg.click(".desk-askbar .desk-chip:has-text('Ask AI')")
            pg.wait_for_selector(".desk-ask", timeout=4000)
            pg.select_option(".desk-ask-runson", "profile_lan")
            pg.wait_for_timeout(300)
            badge = pg.inner_text(".desk-ask .egress-badge")
            assert "192.168.1.43" in badge, f"compose egress lies: {badge!r}"
            pg.screenshot(path=str(OUT / "hsm-16-04-ask-compose.png"))

            # 5 — the printed card: run through the (faked) engine; the badge
            # names where THIS run went (model · host), Bin / Keep offered.
            pg.click(".desk-pullout-foot .desk-chip:has-text('Ask')")
            pg.wait_for_selector(".desk-ask-card", timeout=6000)
            printed_badge = pg.inner_text(".desk-ask .egress-badge")
            assert "Qwen3.5-9B-Q6_K" in printed_badge, f"printed badge: {printed_badge!r}"
            pg.wait_for_timeout(400)
            pg.screenshot(path=str(OUT / "hsm-16-04-ask-printed.png"))

            # 6 — Keep: the kept ask lands on the desk wearing the NEW beat.
            pg.click(".desk-pullout-foot .desk-chip:has-text('Keep')")
            pg.wait_for_selector(".desk-obj.is-new", timeout=6000)
            pg.wait_for_timeout(500)
            pg.screenshot(path=str(OUT / "hsm-16-04-ask-kept.png"))
            b.close()

        kept = [a for a in db.plugins.list_run_artifacts() if a.plugin_id == "web.desk"]
        assert kept, "the kept ask never reached the store"
        prov = kept[0].structured_json.get("provenance") or {}
        assert prov.get("via_kind") == "ask" and prov.get("context_titles"), prov
        print(f"6 shots → {OUT}")
        print(f"kept ask: {kept[0].id} · {len(prov['context_titles'])} cards · via {prov['via_name']}")
    finally:
        server.stop()
        reset_database()


if __name__ == "__main__":
    main()
