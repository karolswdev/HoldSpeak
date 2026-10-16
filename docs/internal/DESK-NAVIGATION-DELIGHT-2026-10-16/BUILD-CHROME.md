# Phone menu targets

Root reviewed the source diagnosis and gave GO for this surgical layout fix.
The current 393 product frames supplied the existing direction; the painted
separator stays in the same 44 px screen bar.

Source proof: `styles/global.css:31` sets border-box. The menubar uses
`--wb-screen-h` at `desk/components/chrome-menus.css:664`; the phone token is
44 px at `desk/components/pullout.css:624`. Its 1 px bottom border at
`chrome-menus.css:672` consumed one pixel of that height while phone controls
remained 44 px high and `overflow: hidden` clipped the bottom points.
HoldSpeak and Go are existing chrome Buttons, so their strip must provide the
target; this is UX-CANON C and Seven Tenets 3, 5 and 6.

The phone menubar rule at `chrome-menus.css:1060` now removes the layout
border and paints the same ink/steel separator with two inset shadows. The
outer screen bar remains 44 px. No token, work area, Dock, menu flow or global
Button rule changed.

Focused collection and both runs used `.tmp/navigation/locked.py`, its isolated
HOME, isolation switches and the machine lock. The only case was:

```
tests/e2e/test_desk_sweep.py::test_every_window_holds_the_fences[desk-393]
```

Collection: `.tmp/navigation/chrome393-collect.log`, exit 0:

```
tests/e2e/test_desk_sweep.py::test_every_window_holds_the_fences[desk-393]
1 test collected in 0.06s
```

The first run retained the old known-red entries to prove healing before their
removal. `.tmp/navigation/chrome393-healed.log`, expected exit 1, reported:

```
AssertionError: desk at 393: healed, remove from KNOWN_REDS
  target: the menu bar's HoldSpeak menu title owns under 44 px at 393 (the bar is shorter)
  target: the menu bar's Go menu title owns under 44 px at 393 (the bar is shorter)
[glass_infra] web bundle rebuilt in 3.9s
1 failed in 10.90s
```

The actual assertion named both obsolete target entries and no new red. Only
the `("desk", 393)` entries were then removed; the palette's prior healing,
other debt, fences and ceilings were retained.

The same exact case then passed without an exception.
`.tmp/navigation/chrome393-green.log`, exit 0:

```
.                                                                        [100%]
1 passed in 6.90s
```

The sweep's target fence reads all nine ownership points through
`elementFromPoint`; this run also holds its other desk fences. Shot:
`.tmp/evidence-shots/desk-sweep/desk-393.png`. This lane ran no broader cases
or new tests. Root owns the final production pointer proof, shots and quick
check.

Status: HOLD FOR SHIP — no staging or commit.
