# Evidence — HS-82-04 — Sessions and events ride the belt

**Status:** done (2026-07-04).

## The move

The belt gains its live layer. Sessions: `on_story` sessions pin
to their story chips (`sessionsByStory`), with `awaiting_response`
the loudest signal on the desk (a pulsing warn pin, the question's
first 200 chars in the tooltip) and `stale` visibly dimmed, never
dropped. Every other correlation outcome stays off the belt in its
honest bucket (`offBeltSessions`): `ambiguous` never guesses a pin,
`off_rails` / `idle_on_rails` / `unreadable` render as themselves.
The collapsed tab shows the awaiting count so a blocked agent is
visible even with mission control folded away.

Events: a ticker under the belts (`formatEvent`), newest first,
`gate_refusal` first-class in the danger color with its rule id
verbatim — the rails' words, not ours. The documents carry no
transcript content by the counterpart's consent stance, and the
Desk adds none back.

## Proof

- `npm run test:desk` — **28 passed**, including the live-layer
  suite: pinning only `on_story` sessions, ambiguous kept off the
  belt (unknown beats guessed), and the refusal line formatted
  with `rule=story-evidence` verbatim.
- `npx astro build` — clean.
- Live check on this desk: deferred to HS-82-05's joint proof,
  where the real registry sessions and the real delivery-workbench
  events render together — recorded there rather than duplicated
  here.
