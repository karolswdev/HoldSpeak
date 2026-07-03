# Evidence — HSM-19-02 — The faceted archive: search + facet chips

**Status:** done (2026-07-03), on `holdspeak-mobile/hsm-19-02-faceted-archive`. The
Wave-3 clients gain their surface: the desktop archive on the iPad is searchable and
faceted, narrowed server-side.

## 1. The filter row (`CompanionShellApp.swift`)

- On connect, `listFacets()` loads the hub's distinct speakers + tags; the chips render
  in the existing `FlowLayout` (compact-aware by construction). **Honest at N=0**: empty
  facets render no chip row.
- A **search field** (submit → `searchMeetings(query:)`), **speaker chips** (person icon)
  and **tag chips** (tag icon). A lit (filled) chip is the active filter; tapping it again
  clears it; the xmark clears everything. Speaker + tag + query combine — the hub
  intersects them.
- **Narrowing is server-side, never a client-side filter of a stale page:** any active
  filter swaps the list to the `searchMeetings` result; clearing returns to the plain
  `serverMeetings`. An active filter with no hits says "No meetings match."
- New screenshot-run affordances `HS_SHELL_FACET_SPEAKER` / `_TAG` — they call the same
  `toggleSpeaker/toggleTag` the chips call, so the screenshot run performs a REAL
  server-side search (not a seed).

## 2. The live-hub proof (real routes, scratch DB)

Three meetings with real transcript segments (speakers Alex/Dana/Karol) + tags:

```
1. facets           -> {'speakers': ['Alex', 'Dana', 'Karol'], 'tags': ['architecture', 'planning', 'standup']}
2. speaker=Dana     -> ['Architecture review', 'Team standup']
3. tag=standup      -> ['Team standup']
4. search=migration -> ['Team standup']          (a transcript-text hit)
5. speaker=Dana&tag=architecture -> ['Architecture review']   (filters intersect)
```

The connected simulator rendered that live hub, twice:

- [`hsm-19-02-live-hub-facets.png`](./screenshots/hsm-19-02-live-hub-facets.png) — the
  full archive (3 meetings) under the real chip row (all six facet values, unlit).
- [`hsm-19-02-live-hub-narrowed.png`](./screenshots/hsm-19-02-live-hub-narrowed.png) —
  `HS_SHELL_FACET_SPEAKER=Dana`: the **Dana chip lit**, the list narrowed by the hub to
  the two meetings Dana spoke in, the clear control visible. A real `searchMeetings`
  round trip, not a seed.

## Honest boundaries

- The hub's `date_from/date_to/has_open_actions` params stay unwired in the Swift client —
  named in the story as a follow-up, deliberately out.
- The chip **tap** itself rides the 19-07 walk (W2); the tap's exact code path
  (`toggleSpeaker`) is what the screenshot run executed live.

## Suites

`swift test` **425 passed / 8 skipped / 0 failures** (`FacetsClientTests` lock the query
mapping incl. `type→tag`) · companion-shell simulator build (iPad Air 13-inch M4)
**BUILD SUCCEEDED** — both after the change.
