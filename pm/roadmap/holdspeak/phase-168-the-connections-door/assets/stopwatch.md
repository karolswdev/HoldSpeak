# HS-168-05 Stopwatch: BEFORE vs AFTER

**Runner:** `tests/e2e/live168_walk.py` (isolated leg, real HOME, real gh + acli)
**BEFORE:** `assets/audit-today.md` (HS-168-01 audit, same method)
**AFTER:** `assets/story-05-walk/transcript-{1440,393}.json`

## Connected condition

| Metric | BEFORE 1440 | BEFORE 393 | AFTER 1440 | AFTER 393 |
|--------|-------------|------------|------------|-----------|
| New Project to tested GitHub Watch | 9 clicks, 10.5s | 9 clicks, 10.6s | **7 clicks, 11.7s** | **7 clicks, 11.6s** |
| New Project to second tested GH Watch (known-scope) | n/a (scope per proposal) | n/a | **11 clicks, 16.6s** | **11 clicks, 17.3s** |
| New Project to tested Jira Watch | 15 clicks, 28.2s (Test gated on Preview) | 15 clicks, 28.3s | **15 clicks, 29.4s** | **15 clicks, 30.7s** |
| New Project to Review | n/a | n/a | **17 clicks, 30.2s** | **17 clicks, 31.5s** |
| New Project to Activate (Room lands) | n/a | n/a | **18 clicks, 34.0s** | **18 clicks, 35.4s** |
| Total steps recorded | 18 | 18 | **22** | **22** |

### Click accounting (connected, New Project to first tested GH Watch)

| Step | BEFORE (audit) | AFTER (walk) |
|------|---------------|--------------|
| Open interview | 1 (click Settings + navigate) | 1 (open interview) |
| Outcome answered | 1 | 1 |
| Signals answered | 1 | 1 |
| Sources appear | 0 (auto) | 0 (auto) |
| Click GH card | 1 | 1 |
| Pick repo (discovery) | 1 | 1 |
| Test this Watch | 1 | 1 |
| **Subtotal to tested GH Watch** | **7 clicks from Sources** (9 from desk) | **7 clicks from Sources** |

The before audit counted 3 additional clicks navigating Settings before the interview (Settings open, Integrations, Meetings), adding 3 to reach 9. The after walk opens the interview directly.

### Second GH Watch (scope carries)

| Step | BEFORE | AFTER |
|------|--------|-------|
| Click second GH card | n/a (scope per proposal) | 1 click |
| Use this repo (known-scope) | n/a | 1 click |
| Test this Watch | n/a | 1 click |
| Use this Watch | n/a | 1 click |
| **Subtotal** | **n/a** | **4 clicks from first GH done** |

### Jira Watch

| Step | BEFORE | AFTER |
|------|--------|-------|
| Click Jira card | 1 | 1 |
| Account step | 1 (select account) | 0 (skipped: 1 connection) |
| Choose project | 1 | 0 (scope step direct) |
| Select KAN | 1 | 1 |
| Preview (scope clarify) | 1 | 0 (not needed) |
| Test this Watch | 1 (disabled in before) | 1 |
| Exit | 1 | 1 |
| **Subtotal** | **6 clicks** (Test was disabled) | **4 clicks** |

## Cold condition

| Metric | BEFORE | AFTER |
|--------|--------|-------|
| Cold > first GitHub on the face | dead end at 6 clicks (SILENT -- no card, no hint) | **"Connect GitHub" visible in TOOLS row at step 3 (4 clicks)** |
| Cold > dead end? | YES (no path forward) | **NO (Connect verb opens Connections face)** |
| Cold > terminal visits | 0 (no path to a command) | 0 (Connect opens Connections; `gh auth login` shown in Connections, not Sources) |

## Sentences on screen

| Face | BEFORE | AFTER |
|------|--------|-------|
| GitHub wizard | 2 ("GitHub is ready. Choose a repository to watch." + "Repository scoped. Ready to test.") | **0** (zero-sentence law: only labels and chips) |
| Jira wizard | (not measured) | **0** |
| Sources TOOLS row | (not present) | **0** |

## Terminal visits (per tool)

| Tool | BEFORE | AFTER |
|------|--------|-------|
| GitHub | `gh auth login` embedded in wizard (F5) | 0 from Sources; `gh auth login` shown ONLY in Settings > Connections face (step 01) |
| Jira | `acli` recovery embedded in wizard | 0 from Sources; `acli` shown ONLY in Settings > Connections face |
| **Max per tool** | **1 (embedded in wizard, not a visit)** | **0 from Sources; 1 from Connections face (separate window)** |
