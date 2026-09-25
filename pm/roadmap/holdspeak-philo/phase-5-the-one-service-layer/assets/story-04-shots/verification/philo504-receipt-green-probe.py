"""Reopen run 4's isolated hub and inspect its Codex-produced brief only."""
import json
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
from scripts import graph_walk as gw
from scripts import philo5_his_words as driver

run = Path('.tmp/philo5-04-runs/20260925T000518Z-his-words-real')
out = Path('.tmp/philo504-receipt-green')
out.mkdir(exist_ok=True)
original = json.loads((run / 'hub-proof.json').read_text())
home = Path(original['home'])
hub = gw.Hub(home, token=driver.TOKEN, producer_clock=True,
             record_rehearsal=True, transcript_path=home / 'receipt-green.jsonl').start()
try:
    proof = driver._hub_proof(hub, home)
    assert proof['db_path'] == original['db_path']
    driver._json_dump(out / 'hub-proof.json', proof)
    provenance = gw.base_provenance(engine_mode='real')
    brief = driver._read_op(gw, hub, 'brief.latest', {}, provenance)
    assert brief['response']['id'] == 'brief-a14b28b8fbbd4f89b9026a0b34b95167'
    driver._json_dump(out / 'brief-read.json', brief)
    with sync_playwright() as play:
        browser = play.chromium.launch(headless=True)
        pages = tuple(browser.new_page(viewport={'width': w, 'height': h})
                      for w, h in ((1440, 900), (393, 852)))
        try:
            observed = driver._reopen_stage(pages, hub, out, 'brief', 'intelligence:desk')
            assert len(observed['pages']) == 2
            assert all(p['receipt_present'] is True for p in observed['pages'])
            assert all(p['receipt_text'].startswith('Brief ready · 5 items') for p in observed['pages'])
            assert all(p['row_texts'] for p in observed['pages'])
            print('PASS: same saved Codex brief, both widths show its receipt without Generate.')
        finally:
            browser.close()
finally:
    hub.stop()
    driver._write_text(out / 'hub.log', '\n'.join(hub.lines) + '\n')
    shutil.copy2(hub.transcript_path, out / 'rehearsal-transcript.jsonl')
