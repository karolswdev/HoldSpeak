# The Concierge glass, parked (PHILO-16 C)

`test_hs170_concierge_glass.py` as it was before the Models window became
Runs on (a Switchboard). It drove the retired face: the picker wells,
Adjust, `Use these`, Cancel. The live file at
`tests/e2e/test_hs170_concierge_glass.py` now drives Runs on. Nothing here
runs (`tests/_parked/conftest.py`).

## Parked with the port (second commit)

- `test_hs170_concierge_glass.py`: the Concierge face (picker wells, Adjust,
  Use these, Cancel). Intent (the Models window draws, holds the species
  laws, and fits 393) now lives in `tests/e2e/test_hs170_concierge_glass.py`
  on Runs on.
- `test_hs156_front_door_glass_retired.py`: `test_beauty_cards` and
  `test_beauty_candidate_picker`, already skipped (their front-door faces
  were retired by HS-170-03). Intent (engines as material objects, choosing
  an engine per job) now lives on the Runs on board:
  `tests/e2e/test_hs170_concierge_glass.py`. The live door tests stay in
  `tests/e2e/test_hs156_front_door_glass.py`.
- `live170_walk.py`: a standalone read-only walk of the owner's hub (never
  collected) that shot the Concierge's FOUND and SET rows. Intent (a
  read-only walk of the Models window on a real desk) is not ported: the
  Runs on window has no live walk yet.
