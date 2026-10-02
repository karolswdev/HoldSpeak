# Check — Astra (Codex `gpt-6-astra`, xhigh): PHILO-13-11 canvases, round 5

Session `01a0fa73-d58f-73c0-9c7e-93ab9a42a262`. Verbatim.

VERDICT: RATIFY

FINDINGS:
1. R4’s sticky mutant condition is paid: `shoot.py:387-397` creates an absolute-position button inside the Room’s Ask bar and records its computed position and nearest bar; `shoot.py:620-623` fails the proof if those values are wrong. The rig serves the product app against a real hub (`harness/rig.py:1-6,98-116`). The proof records `absolute`, the sticky Ask bar, and a caught `Clear here / MUTANT A` pair (`shots/mutation-proof.json:5-22`).
2. The broad-versus-narrow comparison is paid: `OVERLAP_BROAD` matches the earlier broad fence, and `shoot.py:603-616` runs both fences against each injected overlap. All three broad checks miss and all three narrowed checks catch (`shots/mutation-proof.json:12-14,26-30,44-49`; `README.md:32-40`).
3. The boards remain unchanged from round 3d; the changed paths are the README, harness code, and mutation proof. The Park/Restore phone shots remain legible: `C1-5a-meeting-selected-park-393.png`, `C1-5b-meeting-parked-receipt-393.png`, and `C1-5d-meeting-restored-393.png`.

CONDITIONS: None for the r4 conditions. Ready for the owner’s ratification.

MISSED: Low cost: `README.md:7` omits `shots/mutation-proof.json` from the generated-measurements inputs, though `harness/build_review.py:87-101` reads it. Also, the sticky proof’s `target` field is empty (`shots/mutation-proof.json:15`); the caught pair is recorded, but the selected row label is not.

TUESDAY: Yes, at canvas level: Park is visible, then `PARKED` and a separate Restore button appear; the restored item returns marked in the list (C1-5a/b/d, 393).

UNKNOWN: The Park and Restore behavior is a harness stand-in that sends no request, and the owner has not been observed using the built C1 flow (`README.md:143`).