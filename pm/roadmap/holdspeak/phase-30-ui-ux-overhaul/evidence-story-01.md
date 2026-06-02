# HS-30-01 Evidence — UX audit + IA redesign

**Date:** 2026-06-01.
**Story:** [story-01-ux-audit-and-ia.md](./story-01-ux-audit-and-ia.md).

## Implementation Evidence

Docs-only story. Three deliverables landed under `evidence/`, all grounded in the
**running** built front-end (not source-reading alone) and in the `ui-ux-pro-max`
skill:

- `evidence/ux-audit.md` — 12 named problems across the shell + IA + per route,
  each tied to a screenshot and/or a skill `ux` guideline. Top finding: the
  saturated-blue / white-panel / VT323-pixel / hard-hairline grammar gives no
  hierarchy, and **global Settings is buried as tab 6 of 6 inside History**.
- `evidence/ia-spec.md` — the redesigned IA + the shared global patterns (nav
  model, page header, panel grammar, rail, one status/empty/loading/error system)
  and a per-route layout intention for all five routes. Scope-guarded: **no new
  routes** — Settings is relocated to a global drawer, not a new page. Ends with a
  problem→fix traceability table.
- `evidence/before/before-*.png` — 1440×900 screenshots of all five routes + the
  `/design/components` gallery, the "before" baseline for the per-page stories.

### Skill grounding (captured)

`ui-ux-pro-max` `product` search classes HoldSpeak as **Developer Tool / IDE**
(→ *Dark Mode (OLED) + Minimalism*, dashboard *Real-Time Monitor + Terminal*) and
**Productivity Tool** (→ *Flat Design + Micro-interactions*, *clear hierarchy +
functional colours*) — both validate the dark, minimal, real-time-monitor "Signal"
direction over the current Workbench skin. `ux` search surfaced the guidelines the
audit cites: *Heading Hierarchy* (Medium), *Color Only* (High), *Sticky
Navigation* (Medium), *Font Size Scale* (Medium).

```bash
python3 .claude/skills/ui-ux-pro-max/scripts/search.py \
  "desktop productivity app navigation information architecture, hierarchy, density, dashboard, dark theme" \
  --domain ux -f markdown --max-results 5
python3 .claude/skills/ui-ux-pro-max/scripts/search.py \
  "local-first desktop productivity tool, meeting transcription dashboard, developer tool" \
  --domain product -f markdown --max-results 3
```

## Tests

No code changed, so no unit suite applies. Verification = the current front-end
builds clean and is serveable for the capture:

```bash
cd web && npm run build
# 23:10:30 [build] ✓ Completed in 4.32s — 8 page(s) built. (green)

npm run preview   # astro preview → http://127.0.0.1:4321/_built/
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:4321/_built/   # 200
```

Before-screenshot capture (puppeteer via the transitively-installed browser, idle
no-backend state — the chrome/IA/visual grammar is what's audited):

```text
shot runtime <- http://127.0.0.1:4321/_built/
shot dictation <- http://127.0.0.1:4321/_built/dictation/
shot history <- http://127.0.0.1:4321/_built/history/
shot activity <- http://127.0.0.1:4321/_built/activity/
shot companion <- http://127.0.0.1:4321/_built/companion/
shot design-components <- http://127.0.0.1:4321/_built/design/components/
done
```

Backend sweep not required for this docs-only chunk (no Python touched); it is the
exit gate on the foundation story (HS-30-03) where the served output changes.

## Result

The audit + IA spec are the contract for the rest of the phase. **Next: HS-30-02**
— derive the "Signal" design language with the skill and get Karol's sign-off
(hard gate before any token is written).
