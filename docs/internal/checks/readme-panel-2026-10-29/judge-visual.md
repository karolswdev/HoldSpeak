# Visual judge — 2026-10-29

## Scores

| Criterion | Score | Reason |
| --- | ---: | --- |
| Modernity | 8/10 | Strong GitHub hierarchy, useful jump links, current transparency, and a clear first fold. The long feature catalogue and mixed image treatments keep it just below polished product-README level. |
| Verbosity | 6/10 | The opening is well judged, but seven flow sections repeat a paragraph-plus-links pattern across 245 lines. It retains useful context at the cost of a short first read. |
| Attractiveness | 8/10 | The screenshots are cohesive, high-contrast, and distinctive. The starfield, blue window chrome, and dock make the product memorable without needing decorative marketing art. |
| Potential | 8/10 | The page shows a believable chain from thought and meeting to project, agent, Program, and recurring work. The breadth is implemented-looking, though the number of nouns can obscure the one core loop. |

## Ranked findings

1. **The hero communicates the product, but not the first job quickly enough on a phone.** The desktop preview makes the 1440px hero compelling; at the supplied 393px preview, the Desk text is too small to read and occupies a tall block (`.tmp/readme-preview/phone-top.png`; `README.md:9-13`). Add a one-line core loop or three short actions immediately below the opening (for example, “Capture a thought → ask with sources → hand off the next task”) and let the image be proof, not the only explanation. Keep the hero.

2. **The middle reads as a catalogue before it reads as a journey.** “From a thought…” through “Make useful work repeat” contains several dense paragraphs, each with its own link row (`README.md:41-143`). Replace each section’s second paragraph with 2–3 outcome bullets, or group the sections under one compact “Core flows” table. Put implementation caveats in the linked guides. This would improve scan speed without removing coverage.

3. **Screenshot sizing is inconsistent.** The two 1440×900 JPEG/PNG captures fill the content column, while `agents.png` (794×568) and `project.png` (848×570) are smaller window crops; the paired 320px phone images form a separate visual rhythm (`README.md:59`, `75`, `94`, `115`, `147-150`). Standardize desktop screenshots to one presentation width and keep the phone pair explicitly grouped. Do not upscale the small crops until higher-resolution captures exist.

4. **The sample-workspace disclosure arrives too late.** Captions and alt text are good and specific (`README.md:9`, `59`, `75`, `94`, `115`, `148-149`), but the fixture/sample note is at `README.md:163`, after all galleries. Move a short disclosure beside the first screenshot or just before the first flow gallery; retain the precise Program-fixture wording.

## Concrete edits

- Add the one-line core loop below the opening and keep the hero/caption pair.
- Compress each flow to one outcome sentence plus bullets and its existing guide links.
- Normalize desktop image presentation and keep phone images side by side/stacked as a deliberate mobile example.
- Move the screenshot disclosure near the first image; retain all truthful alt text.

## Retain

Retain the Workbench framing (`README.md:25-28`), the agentic-first definition (`README.md:22-24`), the useful flow table (`README.md:31-39`), local-versus-cloud limits (`README.md:165-186`), quick start/platform limits (`README.md:200-232`), and the honest fixture note. These make the visual promise credible rather than generic.

## Proposed opening (65 words)

HoldSpeak is a local, agentic-first Desk for turning spoken thoughts, meetings, and project questions into reviewed work. It connects Notes, Meetings, Projects, People, and coding agents in one browser surface. Start with a Note or an Ask; inspect sources, prepare the next action, then hand the work to an agent. It runs on your machine, with local, network, or cloud engines chosen per job.

## Tuesday

Yes, after the proposed core-loop line and flow compression: a software architect can recognize the Desk, understand the useful path, and find Quick start without reading the catalogue.

## Unknowns

I did not run GitHub’s renderer or a live product walk. The supplied previews approximate GitHub styling; exact image scaling, intrinsic-width behavior, and link wrapping may differ in production.

## Final assessment

**VERDICT: RATIFY**

| Criterion | Score |
| --- | ---: |
| Modernity | 9/10 |
| Verbosity | 8/10 |
| Attractiveness | 8/10 |
| Potential | 8/10 |

The revision materially improves the first fold: the local/cloud boundary and core loop are visible before the hero (`README.md:5-17`), Quick start is reachable immediately (`README.md:19-41`), and the sample disclosure now sits beside the hero. The desktop preview has a clean, intentional opening; the phone preview remains readable even with the loop and links wrapping (`.tmp/readme-preview/desktop-top.png`, `phone-top.png`). The four desktop flow captures now share a centered 780px treatment without enlarging the small source assets (`README.md:51-105`), which makes the gallery feel coherent. The shorter middle keeps useful product proof while reducing catalogue drag (`README.md:49-125`).

No material visual issue remains. The second phone capture falls below the supplied 1000px gallery crop because the two 320px images stack on a 393px viewport (`.tmp/readme-preview/phone-gallery.png`; `README.md:127-134`); this is expected responsive pacing, not a defect. Exact GitHub wrapping remains unverified because these are approximate previews. The Workbench styling stays distinctive and deliberate, not a modernization problem.
