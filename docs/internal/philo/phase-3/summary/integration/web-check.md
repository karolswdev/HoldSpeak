# PHILO-3-02 — final web check

Astra ran `npm --prefix web run check` through Delivery Workbench with an isolated HOME and Node 22.21.0 after the phone 44 px control correction. The retained capture is `evidence-story-02.md`, 2026-09-23T16:19:31Z, exit 0.

TypeScript, all **303 files / 2,800 tests**, production Vite build, and bundle gate passed. Test duration: 87.99 seconds. Bundle: Desk JS **1,319,310 B**, CSS **317,774 B**, source maps **0**. Built index: `index-CT6RwACn.js`; index SHA-256 `f62b3024c816370eb1a72e8660eb4d2bd94330505795cdd75f442e948e2b16a3`. The usual Vite large-chunk notice is not a failing gate.

The earlier 15:56:37Z full check also passed but preceded the phone CSS correction. The final capture retains up to 1,000,000 output bytes so its complete build and gate tail are present. No worker edited during either full check.

## Integrated A1 build — 2026-09-23

After merging main `7b2c2b2a`, Astra repeated the full check in a quiet tree. DW capture **2026-09-23T16:49:18Z**, exit **0**: **306 files / 2,806 tests passed**, 97.49 seconds; TypeScript, Vite and bundle gate passed. Desk JS **1,320,308 B**, CSS **319,048 B**, source maps **0**. Index `index-EPIMRzZ0.js`, SHA-256 `f7df17ed5696e8a501abac65ba23f861455e1a0c4506142eeeb259d8c6087642`. This is the build used for the post-integration actual-atlas runs.

Final check after the read-failure correction: DW capture **2026-09-23T19:08:27Z**, exit 0. **306 files / 2,806 tests**, typecheck, tokens/architecture, build and bundle gate green. Desk JS **1,320,404 B**, CSS **319,048 B**, no source maps. Full output: [full-web-final.raw.log](full-web-final.raw.log). The initial test-option typecheck failure is retained in [full-web-fallout-first.raw.log](full-web-fallout-first.raw.log).
