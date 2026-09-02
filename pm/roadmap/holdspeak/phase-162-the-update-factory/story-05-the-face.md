# HS-162-05 - The face: the Update room — claims that open their sources

- **Project:** holdspeak
- **Phase:** 162
- **Status:** in-progress
- **Depends on:** HS-162-04 (scaffold may start against 04's frozen wire)
- **Unblocks:** HS-162-07
- **Owner:** unassigned

## Problem

The immediately legible proof of value has to LOOK like value: an
editable update whose every claim opens its evidence — this is also
where 160's S-4 debt (source chips open their source) gets paid on
the surface that makes it matter.

## Scope

- **In:** in the project-room feature: the Update posture — draft
  list (lifecycle-honest), the editor (editable Markdown in-world,
  mic on the editor, NO modals), claim chips inline: hover/focus
  names the evidence, activation OPENS the source (paying 160 S-4 in
  this room); MARKED unverified spans visibly distinct (the owner
  sees what the model could not support); Draft/Regenerate/Save/
  Copy Markdown/Publish as separate controls with honest states
  (UPD-005) — Copy uses the markdown GET; the egress badge on the
  model-draft action (local+cloud at the point of decision);
  generator provenance visible (deterministic vs model — no
  masquerade). MOUNTED-PATH tests (the 161 lesson: prove the mount);
  fixtures mined from 04's integration tests. Then beauty + shots →
  THE OWNER'S VERDICT closes this story.
- **Out:** scheduling, Steward.

## Acceptance criteria

- [ ] Mounted-path proof: the posture reachable from the real Room by real clicks; the full draft→edit→publish walk through the mounted tree.
- [ ] Claim chips: every claim resolves on glass; activation opens the source; unverified spans marked; zero bare model prose presented as fact.
- [ ] The five verbs as separate honest controls; egress badge on model drafting; mic; no modals; no document listeners.
- [ ] check green; baseline zero branch-new; SHOTS + THE OWNER'S VERDICT recorded verbatim.

## Test plan

- **Web unit:** mounted walk, claim chips, verb states, marked spans. **Glass:** rides 06. **Manual:** the owner's verdict.

## The owner's verdict — round 1 (2026-09-02)

**BOUNCE**, verbatim: "For things like 02 · THE DRAFT - how do we
edit the content? Is this supposed to be editable? Becuase if so,
why aren't we using the component that we use for Notes, with a
'rich' text editor (well, I mean, it's still markdown but the
editor experience is at least a ton better. 03 · PUBLISHED, AND
EVERY CLAIM OPENS - I am really unhappy with how the interface
looks like... - you're not going to tell me that this is
acceptable. Also - I am not even sure what the frig am I looking
at, in this screenshot?"

Two findings: (1) the editor must be the house Notes markdown
editor, not a bare textarea; (2) the published view reads as a
claims dump — repetitive rows with buttons instead of the rendered
update itself. Consequence round chartered.

## The owner's verdict — round 2 (2026-09-02)

**BOUNCE (the list row)**, verbatim: "What does it mean? DRAFT
MOdel (, REV 1 just now. On this image #4..., I guess I'm confused
and also a little uglied-out by that." The draft-list row clipped
the generator label mid-parenthesis ("Model (") into a meaningless
fragment, and the row's fragments collide instead of reading as a
designed line. Micro-round chartered: the row becomes a designed
layout, provenance simplified to "Model draft"/"Deterministic
draft" in lists (assignment id to title/aria), no mid-token
clipping ever.

## The owner's verdict — round 3 (2026-09-02)

Two questions, verbatim: "Can you be clear to me - so what we just
sort of..., exposed via the editor. IS that actually meant to be
editable? Or no?" — answered YES by canon (UPD-001 editable
Markdown; UPD-005 Save; PV-H04 measures the edit-to-copy loop;
published freezes read-only). And: "How do I go from state 1 ...
to 02 ... is it after I double-clicked 01's Updates 1, ro
something? Because if that's the case, it's not obvious to me that
it is an interactable surface..." — a FINDING: the row opens on a
single click (SurfaceLedgerRow onToggle) but nothing signals
interactability. Affordance round chartered (hover, cursor,
chevron/hint the house way, keyboard).
