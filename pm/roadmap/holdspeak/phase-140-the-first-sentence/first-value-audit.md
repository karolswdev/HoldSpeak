# Phase 140 first-value audit

**Date:** 2026-08-18
**Mode:** read-only, three independent Terra reviews on merged `main`

## What the cold owner saw

A fresh isolated HOME reached the runtime quickly, then landed on a Chair with
roughly twenty competing nouns and actions and no instruction for first use.
Ask AI produced no visible result in that condition. Speak exposed Aim,
Rehearse, Deliver, Grounding, target, pipeline, and budget before a first
dictation could become useful. Models became an apparent prerequisite. The
Floor also discovered repository roadmap objects from the development tree.

The product was running; the value was not findable.

## What already works

The existing `FirstWords` composition already provides the right small loop:

1. click to speak;
2. click to stop;
3. receive a non-empty transcript;
4. edit it;
5. Copy or Keep as Note;
6. load pending audio for retry when capture has actually retained it;
7. record content-free journey mechanics and outcome.

The retention receiving seam exists, but the live first-value stream does not
currently pass `retainScope: "first-words"` to `startStreamSession`. The current
“audio is retained” failure copy is therefore false until HS-140-03 wires and
proves the real stream failure → reload → retry path.

Setup status already knows whether arrival is required. The structural bug is
that `DeskApp` renders this composition only inside `EmptyDesk`, and
`EmptyDesk` is rendered only on the Floor. The actual `/` front door is Chair.

## Complexity census

The census found 21 canonical product nouns, four destination classes, three
postures, 30 lifecycle states, 15 windowed surfaces, 13 launcher programs, 51
registered verbs, and four home lanes. These may be legitimate capabilities.
They are not a legitimate first impression.

## Tuesday ruling

**Do not build Dashboard Door.** Scheduled recording already exists; upcoming
meetings lacks an honest calendar source; a TODO kanban would introduce a new
task model. That proposal adds another place and more nouns before the product
has proven its simplest value.

Build The First Sentence: one temporary first-value composition on the Chair,
then disclose the existing product after success or explicit defer.

## Diagnostic captures

- `/tmp/holdspeak-cold-authorized-landing.png`
- `/tmp/holdspeak-cold-speak-authorized.png`
- `/tmp/holdspeak-cold-models.png`
- `/tmp/holdspeak-cold-floor.png`

These are inputs, not closeout evidence. HS-140-05 must capture a fresh,
committed both-width walk after implementation.
