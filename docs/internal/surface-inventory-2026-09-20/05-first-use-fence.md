# 05 — The first-use fence

[The smoke](../../../tests/e2e/test_hs202_first_use_smoke.py) runs one fixture
walk at 1440×900 and 393×852 on a real hub in a temporary HOME.

1. **Speak:** Chromium supplies the fixture WAV through a fake audio device.
   The real dictation WebSocket sends nonzero PCM to a transcriber stub.
   The sentence must appear; Keep as Note must open the kept text.
2. **Meeting to summary:** import the WAV from the face. Require its
   transcript and no automatic summary. Compare the host beside Run summary
   with planned_route, then the admitted selection hash and run_receipt.
   Require the completed summary and actual host without a reload.
3. **Write and save:** check Write a thought's destination. Create a note
   through the real command, write title and body, verify persistence, and
   require a new visible Kept receipt in that editor before Save closes it.
   The editor autosaves; after Save, verify closure and the exact saved text.
4. **Find it again:** restart the in-process hub on the same HOME and database. In a
   fresh tab, find the note body and meeting summary in two navigation
   gestures each: open Search with its button, then select the exact result.
   Query typing is not navigation. The hub must retain the same run receipt.
5. **Set up an engine:** use Add an engine, Check, and Use this for summaries
   against a localhost stub. Require the setup row to clear without reload.
   Only the speech adapter is assigned by the fixture.

The dock and four desktop menus are checked. At 393, Go must carry New Note
and the Object and Window entries, with no inaccessible separate menu titles
announced. New Note uses Go at that width. Dock doors must fit;
Search needs an owned, visible pointer target. Each surface must load its
own content marker. Recovery after a recorded failure is labelled and
cannot make that check pass.

The normal run stays RED. HS202_EXPECTED_FAILURES=1 runs the same assertions
and requires the exact named failure set. Unexpected or healed defects fail
that mode. Setup, loading, HTTP, persistence, engine, and route errors are
never expected failures. The unchanged source-button ratchet remains the
only such gate; this adds no census gate.

Two findings are precise: Notes highlights an unrelated program and Enter
executes it, while exact-title search works; the imported transcript loads
but its stale row withholds Run summary. The fixture releases transcription
after the importing row loads to make this order deterministic. The latter
check is named import-refresh and belongs to HS-202-02.

With dependencies installed, run on macOS:

~~~sh
browser_cache="$HOME/Library/Caches/ms-playwright"
HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH="$browser_cache" \
  uv run pytest -q -s tests/e2e/test_hs202_first_use_smoke.py
~~~

Set browser_cache for other systems. Add HS202_EXPECTED_FAILURES=1 for
verification. Shots stay in the test's temporary directory unless
HS202_EXPORT_SHOTS=1 is set for a named evidence run.
[Story evidence](../../../pm/roadmap/holdspeak/phase-202-the-coherent-face/evidence-story-01.md)
holds both runs and shots.

The rig has no owner lock: its drainer is OFF (NOT DRAINING on glass).
The test drains the real queue and calls the production completion callback.
The summary adapter is FakeIntel; receipt hosts are route-derived, not proof
of network contact. Engine Check uses real localhost HTTP. Restart replaces
the server, database singleton and browser context; Python module state remains.

This cannot prove the owner's voice, microphone permissions, external-app
dictation, model quality, or Tuesday judgment. Those remain the sitting's
exits. The rig does not use the printed startup URL, so its tokenless nudge
is outside this fence. The phase still requires normal GREEN after repairs.
