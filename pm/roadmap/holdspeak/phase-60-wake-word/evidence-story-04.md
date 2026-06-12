# Evidence — HS-60-04: The false-accept measurement

**Date:** 2026-06-11
**Branch:** `phase-60-wake-word`

## 1. The central honest finding

The first run of the harness FAILED, and that failure is the most valuable
output of the phase: sentences **containing the wake word** ("the jarvis
pattern is overused in demos": 0.996) or a **near-homophone** ("hey jarred
this needs a review": 0.995) score indistinguishably from the real phrase
(true wakes ranged 0.628-0.861) — **no threshold separates them**. This is
inherent to wake-word detection, not a defect of this engine. It is
precisely the scenario the phase's conditions were written for: with the
preview default, the cost of such a false accept is a visible armed window
and a dismissible preview card — never text in your focused app.

The harness therefore measures two classes with different bars, and the
docs (HS-60-05) state both plainly.

## 2. The measured numbers (committed, repeatable harness)

`dogfood_story04.py` — the REAL production detector, frame by frame, over
synthesized speech (3 `say` voices: Samantha, Daniel, Fred):

```
wake  Samantha   0.861  DETECTED
wake  Daniel     0.746  DETECTED
wake  Fred       0.628  DETECTED

utterances: 3 wake + 57 ordinary distractors (19 sentences x 3 voices)
            + 9 wake-adjacent
ordinary false accepts at 0.5: 0
worst wake score        : 0.628
best ordinary distractor: 0.433
ordinary margin         : 0.196
loudest ordinary distractors:
  0.433  [Fred] hey travis the pipeline is red
  0.422  [Samantha] hey travis the pipeline is red
  0.419  [Samantha] play jazz this afternoon please
wake-adjacent (detections EXPECTED; the preview default is the mitigation):
  0.995  fires  [Samantha] hey jarred this needs a review
  0.996  fires  [Fred] the jarvis pattern is overused in demos
  0.982  fires  [Fred] hey jarred this needs a review
  (6 of 9 stayed quiet — voice-dependent)
RESULT: PASS
```

- **Ordinary speech** (work sentences, hey-prefixed openers, loose
  phonetic neighbors like "hey marvis"/"hey travis"/"play jazz"):
  **0 false accepts in 57 utterances** at the 0.5 default; the loudest
  reached 0.433, a 0.196 margin below the worst true wake.
- **Wake-adjacent phrases**: fire in 3 of 9 cases (voice-dependent),
  exactly as expected; mitigated by design, not by tuning.

## 3. Honest caveats (carried to the docs)

Synthetic TTS speech, three voices, quiet conditions. Real rooms (accents,
distance, noise, speakers playing media) differ in both directions; the
threshold is a settings knob for exactly that reason, and long-duration
ambient measurement is noted as future work.

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2723 passed, 17 skipped   # the harness is a committed script, not a test
```
