# README panel: decisions and result

Owner request: three judges assess modernity, verbosity, attractiveness, and potential, then apply the findings and merge a PR. Base: `09cbe18c2`. Branch: `docs/readme-panel`. Delivery: [PR #1613](https://github.com/karolswdev/HoldSpeak/pull/1613).

## Method and scores

Three separate `gpt-5.6-luna` contexts at `xhigh` reviewed independently. Each inspected the README and its screenshots, filed a baseline, then gave one bounded final assessment. They did not read each other's reports. All criteria use 1–10, higher is better; verbosity means useful concision. These are subjective agent judgments, not user testing or Muad'Dib's review.

| Judge | Modernity, before → after | Concision, before → after | Attractiveness, before → after | Potential, before → after |
| --- | --- | --- | --- | --- |
| [Product](judge-product.md) | 8 → 8 | 7 → 7 | 8 → 8 | 9 → 9 |
| [Editorial](judge-editorial.md) | 8 → 9 | 6 → 8 | 8 → 8 | 9 → 9 |
| [Visual](judge-visual.md) | 8 → 9 | 6 → 8 | 8 → 8 | 8 → 8 |
| Mean | 8.0 → 8.7 | 6.3 → 7.7 | 8.0 → 8.0 | 8.7 → 8.7 |

Editorial and Visual ratified the revision. Product found no remaining material content error and conditioned its verdict on fresh rendering verification. Its scores remain unchanged; no score increase was required.

## Applied decisions

- Put the context → Ask → task → agent → review loop above the hero. State local storage and selectable local, network, or cloud engines there too.
- Move the Quick start heading from line 200 to line 19, with requirements, installation, and a first Note/Ask flow. The jump link is now above the hero.
- Remove the duplicate introductory section and feature table. Keep concrete flows, shorten their explanations, and link advanced Program and integration details to the guides.
- Add one architect example: develop a migration idea, extract tasks, hand one off, review the change, then use the Project's records for an update.
- Retain seven screenshots. Center the four middle desktop images at a common 780px display width, below their native widths. Keep the large hero and paired phone gallery. Move the sample disclosure to the hero; retain adjacent Program fixture captions and useful alt text.
- Keep installation, platform and dependency limits, incomplete iPhone transport status, engine boundaries, and live-guarded plugin/tool counts.

The whitespace word count falls from 1,923 to about 1,320 (31%). All seven product screenshots are reused without editing their pixels. Their provenance remains in the earlier core-docs refresh record. The product's deliberate Workbench appearance remains the visual identity.

Not every suggestion was copied literally. The feature table was removed because the editorial and visual findings identified duplicated catalogue structure. A new table would restore that repetition. The product judge's proposed line about repeating a checked workflow with either a Program or Automation was not adopted: those are distinct execution paths. The hero remains before Quick start to show the product before the install commands; a first-fold jump link gives direct access.

## Render condition

The product judge reported seeing stale previews. Root regenerated the preview from the current README in this worktree, with its absolute source path, SHA-256, word count, and generation time in `.tmp/readme-preview/source.json`. Root inspected the new opening at 1440 and 393 pixels: it shows the new core loop, navigation above the hero, and Quick start immediately after it. The old opening does not appear. The machine report confirms seven decoded images, one H1, and no page overflow at either width. This satisfies the rendering condition without changing the judge's original assessment.

The preview uses approximate GitHub styling. It does not establish exact GitHub wrapping, a live product walk, install success, model quality, or owner aesthetic acceptance.

## Fixes found by the required quick check

The first local attempt stopped because the shared old web dependency set lacked Mermaid. Dependencies were installed from the existing lockfile into this worktree's ignored `web/node_modules`, without changing the main checkout's dependency directory.

The next check passed build, affected tests, and the 124-case desk sweep. Its documentation guards found a raw relative link in the editorial proposal, retired terminology in the README and five core guides, one stale documentation debt entry, and a notification phrase caught by the delivery wording guard. The raw proposal is now fenced as source. Public wording now uses Engines and Modes, preserves code identifiers, and separates host notifications from paired delivery. The obsolete debt row was removed as the existing ratchet requires. No new exemption or test assertion was added.

The earlier remote DeskOS Web Quality failure was traced to the token gate reporting 184 raw CSS values in existing product files. This PR changes no product source. That separate CI issue is retained as open work in the status file.

## Final validation

The required `scripts/quick_check.sh origin/main` is GREEN, using the machine-wide lock and an isolated HOME. Its stages report:

- Web build passed. No changed web source required a related Vitest run.
- Affected documentation tests: **60 passed in 3.48s**.
- Desk sweep at desktop and phone widths: **124 passed in 66.73s**.
- Canon guards: **27 passed in 5.28s**.
- Repository guards: **1,156 passed in 32.92s**.

The earlier focused run of the repaired documentation guards reports **47 passed in 3.73s**. Public navigation reports **73 documents checked**. `git diff --check` passes.

The fresh preview was generated at `2026-10-29T19:07:27Z` from README SHA-256 `7d1fb35e8dfa20f855a66ead45c4154ed171272da87951fdb744e413de19694a`. Root inspected the opening and phone gallery after generation. Both widths decode seven images without page overflow. The current README hash still matches the render record.

Render outputs are under `.tmp/readme-preview/`; successful quick-check logs are under `.tmp/readme-panel-quick-check-green/`. No test assertion or product source changed. The debt fixture change removes one fixed documentation entry and adds no exemption.
