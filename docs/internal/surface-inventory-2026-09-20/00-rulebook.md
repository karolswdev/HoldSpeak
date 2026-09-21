# The rulebook — what every surface is measured against (2026-09-20)

One list, cited by every lane of the surface inventory. A finding names the
rule it fails. Rules come from the Seven Tenets and the Constitution first,
UX-CANON and DESIGN_SYSTEM second, and the UI/UX review skill third (only
where it does not contradict the canon).

## A. Canon (fails here outrank everything)

| Id | Rule | Source |
|---|---|---|
| T1 | Not over-engineered for safety: ceremony only where it buys a receipt, provenance or undo | Tenet 1 |
| T2 | Serves the creator's first real use, not a release | Tenet 2 |
| T3 | One obvious move per job; no unnecessary interface; no vague instruction | Tenet 3 |
| T4 | ASD-STE100: short common words, one meaning, short sentences | Tenet 4 |
| T5 | Composed from the component framework (the surface library); nothing reinvented | Tenet 5 |
| T6 | Workbench 2.0+: windows, icons, drawers, tools; direct, dense, calm | Tenet 6 |
| T7 | A Senior Software Architect's job, in his words | Tenet 7 |
| A3 | Honest egress at the point of decision: the badge before the click, the receipt after | Article III |
| A6 | Honest by construction: no state the screen shows that the machine does not hold | Article VI |
| A7 | The interface serves, it does not speak: no prose, no narration | Article VII, UX-CANON A.3 |
| U1 | Every verb is the library Button; a raw button is a bounce | UX-CANON A.1 |
| U2 | No modals; edit in-world | UX-CANON A |
| U3 | No counters of zero | UX-CANON A.8 |
| U4 | One filled primary per window | UX-CANON / HS-200-15 |
| U5 | Errors never overlap UI; no mixed-era rooms | owner ruling |
| U6 | One name per thing across faces; canonical names render | POSITIONING |
| D1 | Tokens only: no raw hex, no raw px sizes outside the token scale | DESIGN_SYSTEM |
| D2 | The interior type scale; one body face, one mono face, used by role | DESIGN_SYSTEM |

## B. Measured (the walk asserts these with numbers)

| Id | Rule | Threshold |
|---|---|---|
| M1 | No horizontal overflow: window and document scrollWidth ≤ clientWidth | 0 px at 1440 and 393 |
| M2 | No hidden text: no element whose text is cut (scrollWidth > clientWidth with overflow hidden or ellipsis) unless its full text is reachable in-world | 0 |
| M3 | Every verb inside its window's bounds and the viewport | 0 outside |
| M4 | No content reachable only through a tab, fold or scroll that the surface does not signal | 0 |
| M5 | No empty heading, no empty section, no label with no value | 0 |
| M6 | Nothing stated twice on one screen (same fact, two elements) | 0 |
| M7 | Body text ≥ 12 px; touch targets ≥ 44 px at 393 | per skill §1/§2 |
| M8 | Text contrast ≥ 4.5:1 (large ≥ 3:1) | WCAG AA |
| M9 | Zero console errors, zero 4xx/5xx on load | 0 |
| M10 | At most two font families per surface (body + mono), used by role | 2 |
| M11 | Spacing on the 4/8 rhythm; no arbitrary gaps | skill §5 |
| M12 | Prefers-reduced-motion respected; no animation > 400 ms | skill §7 |

## C. Coherence (read, then counted)

| Id | Rule |
|---|---|
| C1 | The same job has the same verb label on every face (a verb inventory) |
| C2 | The same thing has one name on every face (a noun inventory vs product-language.json) |
| C3 | Every surface has a door a stranger can find in one move (Go, dock, a row's verb) |
| C4 | Every surface's states (empty, working, failed, done) exist and say what is true |
| C5 | The face matches the Philo SRS requirement that describes it, or the SRS is wrong |
