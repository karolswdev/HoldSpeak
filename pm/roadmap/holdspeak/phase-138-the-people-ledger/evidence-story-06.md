# Evidence - HS-138-06

- **Story:** HS-138-06 - The People walk
- **Status:** done
- **Date:** 2026-08-17

## Proof

### Captured run — 2026-08-17T23:57:45Z

- **Command:** `uv run python scripts/people_walk_full.py --attended`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0bbf234c8cace8594883adeb62961f7bd26d0011

```text

== ATTENDED MODE ==
  Owner must be watching for macOS Keychain prompts.
  HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-s3i7qqw0  port=54953
  PASS  walk keychain created + unlocked (isolated HOME)  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-s3i7qqw0/Library/Keychains/login.keychain-db
  hub pid=8249 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-s3i7qqw0 port=54953

== network proof: baseline-after-boot ==
  lsof snapshot (baseline-after-boot, pid=8249):
    COMMAND    PID  USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
    python3.1 8249 karol   15u  IPv4 0xe845a0ee8e7484c0      0t0  TCP localhost:54953 (LISTEN)
  PASS  all connections loopback-only (baseline-after-boot)
  PASS  pre-setup readiness  state=unconfigured

== ===== viewport 1440x900 (unconfigured) ===== ==

== readiness unconfigured @1440 ==
  PASS  readiness endpoint reachable  status=200
  PASS  readiness state is unconfigured  state=unconfigured
  PASS  degraded label 'Not set up' visible
  SHOT  people-unconfigured-1440.png  People surface: unconfigured before setup
  PASS  zero console errors  readiness unconfigured @1440  []

== ===== viewport 393x900 (unconfigured) ===== ==

== readiness unconfigured @393 ==
  PASS  readiness endpoint reachable  status=200
  PASS  readiness state is unconfigured  state=unconfigured
  PASS  degraded label 'Not set up' visible
  SHOT  people-unconfigured-393.png  People surface: unconfigured before setup
  PASS  zero console errors  readiness unconfigured @393  []

== setup: POST /api/people/setup (KEYCHAIN WRITE) ==

============================================================
  EXPECT A KEYCHAIN PROMPT -- CLICK 'ALWAYS ALLOW'
  (macOS will ask to allow HoldSpeak People Keychain access)
============================================================

  PASS  setup succeeded  status=200
  PASS  readiness now ready  state=ready

== seed: create relationship + 1:1 + request + notes ==
  PASS  create relationship  status=201
  PASS  create 1:1 session  status=201
  PASS  add shared-intent agenda item  status=201
  PASS  add leader-private agenda item  status=201
  PASS  create grounding note  status=201
  PASS  create request  status=201
  PASS  accept request -> commitment  status=200

== follow-through board proof ==
  PASS  follow-through board reachable  status=200
  PASS  commitment appears on Follow-through board  people_commitment cards in now lane: 1
  PASS  commitment appears exactly once  count=1
  PASS  card text matches request body  text=qT5bJ-sentinel-request-body-6Dz1x
  PASS  follow-through done verb  status=200
  PASS  follow-through reopen verb  status=200

== network proof: after-seed-and-follow-through ==
  lsof snapshot (after-seed-and-follow-through, pid=8249):
    COMMAND    PID  USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
    python3.1 8249 karol   15u  IPv4 0xe845a0ee8e7484c0      0t0  TCP localhost:54953 (LISTEN)
  PASS  all connections loopback-only (after-seed-and-follow-through)

== ===== viewport 1440x900 (populated) ===== ==

== people populated @1440 ==
  PASS  sentinel name visible in roster
  SHOT  people-roster-populated-1440.png  People roster: relationship with sentinel name
  PASS  zero console errors  people roster @1440  []
  SHOT  people-detail-now-lens-1440.png  Now lens: commitments, requests, next 1:1
  PASS  zero console errors  people detail now @1440  []
  SHOT  people-detail-one-on-ones-lens-1440.png  1:1s lens: session with shared and private agenda items
  PASS  zero console errors  people detail 1:1s @1440  []
  PASS  encrypted storage badge visible
  SHOT  people-detail-info-lens-1440.png  Info lens: metadata, storage facts, encrypted badge
  PASS  zero console errors  people detail info @1440  []

== send-to-workbench check @1440 ==
  PASS  Send-to-Workbench with egress badge  button=False badge=True
  SHOT  people-detail-send-to-workbench-1440.png  Send-to-Workbench action with egress badge
  PASS  zero console errors  send-to-workbench check @1440  []

== ===== viewport 393x900 (populated) ===== ==

== people populated @393 ==
  PASS  sentinel name visible in roster
  SHOT  people-roster-populated-393.png  People roster: relationship with sentinel name
  PASS  zero console errors  people roster @393  []
  SHOT  people-detail-now-lens-393.png  Now lens: commitments, requests, next 1:1
  PASS  zero console errors  people detail now @393  []
  SHOT  people-detail-one-on-ones-lens-393.png  1:1s lens: session with shared and private agenda items
  PASS  zero console errors  people detail 1:1s @393  []
  PASS  encrypted storage badge visible
  SHOT  people-detail-info-lens-393.png  Info lens: metadata, storage facts, encrypted badge
  PASS  zero console errors  people detail info @393  []

== RESTART LEG: stop + fresh boot on same HOME ==

============================================================
  KEYCHAIN READ -- macOS MAY prompt again
  (the fresh hub decrypts the store via the native key)
============================================================

  hub pid=8791 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-s3i7qqw0 port=55072
  PASS  readiness after restart  state=ready
  PASS  roster intact after restart  names=['Zara Quixote-Sentinel']

== MISSING-KEY SIMULATION ==
  key_id = people-key-v1:1020c505-7e52-4a71-a808-af2b2f0d2c4c

============================================================
  KEYCHAIN READ -- macOS MAY prompt
  (reading key value via `keyring get` for backup)
============================================================

  PASS  key value retrieved for backup

============================================================
  KEYCHAIN DELETE -- macOS MAY prompt
  (deleting key to simulate missing-key scenario)
============================================================

  PASS  keychain entry deleted
  hub pid=8803 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-s3i7qqw0 port=55083
  PASS  fail-closed: readiness is NOT ready  state=key_unavailable
  PASS  fail-closed: named state reported  state=key_unavailable
  PASS  fail-closed: content-free reason code  reason_code=people_store_key_unavailable
  PASS  fail-closed: roster inaccessible  status=503

============================================================
  KEYCHAIN WRITE -- macOS MAY prompt
  (restoring key after missing-key test)
============================================================

  PASS  keychain entry restored
  hub pid=8814 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-s3i7qqw0 port=55096
  PASS  recovery: readiness restored to ready  state=ready
  PASS  recovery: roster intact  names=['Zara Quixote-Sentinel']

== sentinel negative proof ==
  scanning 5 files for sentinel tokens
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-s3i7qqw0/.holdspeak/node_command_ledger.db
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-s3i7qqw0/.local/share/holdspeak/holdspeak.db
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-s3i7qqw0/.local/share/holdspeak/people.v1.sqlite3
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-s3i7qqw0/.local/share/holdspeak/people.v1.sqlite3-wal
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-s3i7qqw0/.local/share/holdspeak/people.v1.sqlite3-shm
  PASS  all sentinels absent from all scanned files

== cleanup ==

============================================================
  KEYCHAIN DELETE -- macOS MAY prompt
  (cleaning up the walk's Keychain entry)
============================================================

  PASS  walk Keychain entry deleted  key_id=people-key-v1:1020c505-7e52-4a71-a808-af2b2f0d2c4c
  PASS  temp HOME deleted  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-s3i7qqw0

== RESULT ==
  PASS x55   FAIL x0   FINDINGS x0   SHOTS x11

SHOTS:
  people-unconfigured-1440.png  (People surface: unconfigured before setup)
  people-unconfigured-393.png  (People surface: unconfigured before setup)
  people-roster-populated-1440.png  (People roster: relationship with sentinel name)
  people-detail-now-lens-1440.png  (Now lens: commitments, requests, next 1:1)
  people-detail-one-on-ones-lens-1440.png  (1:1s lens: session with shared and private agenda items)
  people-detail-info-lens-1440.png  (Info lens: metadata, storage facts, encrypted badge)
  people-detail-send-to-workbench-1440.png  (Send-to-Workbench action with egress badge)
  people-roster-populated-393.png  (People roster: relationship with sentinel name)
  people-detail-now-lens-393.png  (Now lens: commitments, requests, next 1:1)
  people-detail-one-on-ones-lens-393.png  (1:1s lens: session with shared and private agenda items)
  people-detail-info-lens-393.png  (Info lens: metadata, storage facts, encrypted badge)
```

### Captured run — 2026-08-18T00:07:17Z

- **Command:** `uv run python scripts/people_walk_full.py --attended`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 0bbf234c8cace8594883adeb62961f7bd26d0011

```text

== ATTENDED MODE ==
  Owner must be watching for macOS Keychain prompts.
  HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-anqvlcr8  port=55420
  PASS  walk keychain created + unlocked (isolated HOME)  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-anqvlcr8/Library/Keychains/login.keychain-db
  hub pid=12361 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-anqvlcr8 port=55420

== network proof: baseline-after-boot ==
  lsof snapshot (baseline-after-boot, pid=12361):
    COMMAND     PID  USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
    python3.1 12361 karol   13u  IPv4 0xf1b5d08c92c3b5b8      0t0  TCP localhost:55420 (LISTEN)
  PASS  all connections loopback-only (baseline-after-boot)
  PASS  pre-setup readiness  state=unconfigured

== ===== viewport 1440x900 (unconfigured) ===== ==

== readiness unconfigured @1440 ==
  PASS  readiness endpoint reachable  status=200
  PASS  readiness state is unconfigured  state=unconfigured
  PASS  degraded label 'Not set up' visible
  SHOT  people-unconfigured-1440.png  People surface: unconfigured before setup
  PASS  zero console errors  readiness unconfigured @1440  []

== ===== viewport 393x900 (unconfigured) ===== ==

== readiness unconfigured @393 ==
  PASS  readiness endpoint reachable  status=200
  PASS  readiness state is unconfigured  state=unconfigured
  PASS  degraded label 'Not set up' visible
  SHOT  people-unconfigured-393.png  People surface: unconfigured before setup
  PASS  zero console errors  readiness unconfigured @393  []

== setup: POST /api/people/setup (KEYCHAIN WRITE) ==

============================================================
  EXPECT A KEYCHAIN PROMPT -- CLICK 'ALWAYS ALLOW'
  (macOS will ask to allow HoldSpeak People Keychain access)
============================================================

  PASS  setup succeeded  status=200
  PASS  readiness now ready  state=ready

== seed: create relationship + 1:1 + request + notes ==
  PASS  create relationship  status=201
  PASS  create 1:1 session  status=201
  PASS  add shared-intent agenda item  status=201
  PASS  add leader-private agenda item  status=201
  PASS  create grounding note  status=201
  PASS  create request  status=201
  PASS  accept request -> commitment  status=200

== follow-through board proof ==
  PASS  follow-through board reachable  status=200
  PASS  commitment appears on Follow-through board  people_commitment cards in now lane: 1
  PASS  commitment appears exactly once  count=1
  PASS  card text matches request body  text=qT5bJ-sentinel-request-body-6Dz1x
  PASS  follow-through done verb  status=200
  PASS  follow-through reopen verb  status=200

== network proof: after-seed-and-follow-through ==
  lsof snapshot (after-seed-and-follow-through, pid=12361):
    COMMAND     PID  USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
    python3.1 12361 karol   13u  IPv4 0xf1b5d08c92c3b5b8      0t0  TCP localhost:55420 (LISTEN)
  PASS  all connections loopback-only (after-seed-and-follow-through)

== ===== viewport 1440x900 (populated) ===== ==

== people populated @1440 ==
  PASS  sentinel name visible in roster
  SHOT  people-roster-populated-1440.png  People roster: relationship with sentinel name
  PASS  zero console errors  people roster @1440  []
  SHOT  people-detail-now-lens-1440.png  Now lens: commitments, requests, next 1:1
  PASS  zero console errors  people detail now @1440  []
  SHOT  people-detail-one-on-ones-lens-1440.png  1:1s lens: session with shared and private agenda items
  PASS  zero console errors  people detail 1:1s @1440  []
  PASS  encrypted storage badge visible
  SHOT  people-detail-info-lens-1440.png  Info lens: metadata, storage facts, encrypted badge
  PASS  zero console errors  people detail info @1440  []

== send-to-workbench check @1440 ==
  FAIL  Send-to-Workbench button + Workbench-model egress badge  button=False badge=False
  SHOT  people-detail-no-workbench-btn-1440.png  Detail view without visible Send-to-Workbench inspector
  PASS  zero console errors  send-to-workbench check @1440  []

== ===== viewport 393x900 (populated) ===== ==

== people populated @393 ==
  PASS  sentinel name visible in roster
  SHOT  people-roster-populated-393.png  People roster: relationship with sentinel name
  PASS  zero console errors  people roster @393  []
  SHOT  people-detail-now-lens-393.png  Now lens: commitments, requests, next 1:1
  PASS  zero console errors  people detail now @393  []
  SHOT  people-detail-one-on-ones-lens-393.png  1:1s lens: session with shared and private agenda items
  PASS  zero console errors  people detail 1:1s @393  []
  PASS  encrypted storage badge visible
  SHOT  people-detail-info-lens-393.png  Info lens: metadata, storage facts, encrypted badge
  PASS  zero console errors  people detail info @393  []

== RESTART LEG: stop + fresh boot on same HOME ==

============================================================
  KEYCHAIN READ -- macOS MAY prompt again
  (the fresh hub decrypts the store via the native key)
============================================================

  hub pid=12784 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-anqvlcr8 port=55525
  PASS  readiness after restart  state=ready
  PASS  roster intact after restart  names=['Zara Quixote-Sentinel']

== MISSING-KEY SIMULATION ==
  key_id = people-key-v1:e9d920b7-230b-47bc-a198-de23c8bd510e

============================================================
  KEYCHAIN READ -- macOS MAY prompt
  (reading key value via `keyring get` for backup)
============================================================

  PASS  key value retrieved for backup

============================================================
  KEYCHAIN DELETE -- macOS MAY prompt
  (deleting key to simulate missing-key scenario)
============================================================

  PASS  keychain entry deleted
  hub pid=12791 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-anqvlcr8 port=55536
  PASS  fail-closed: readiness is NOT ready  state=key_unavailable
  PASS  fail-closed: named state reported  state=key_unavailable
  PASS  fail-closed: content-free reason code  reason_code=people_store_key_unavailable
  PASS  fail-closed: roster inaccessible  status=503

============================================================
  KEYCHAIN WRITE -- macOS MAY prompt
  (restoring key after missing-key test)
============================================================

  PASS  keychain entry restored
  hub pid=12801 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-anqvlcr8 port=55549
  PASS  recovery: readiness restored to ready  state=ready
  PASS  recovery: roster intact  names=['Zara Quixote-Sentinel']

== sentinel negative proof ==
  scanning 5 files for sentinel tokens
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-anqvlcr8/.holdspeak/node_command_ledger.db
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-anqvlcr8/.local/share/holdspeak/holdspeak.db
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-anqvlcr8/.local/share/holdspeak/people.v1.sqlite3
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-anqvlcr8/.local/share/holdspeak/people.v1.sqlite3-wal
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-anqvlcr8/.local/share/holdspeak/people.v1.sqlite3-shm
  PASS  all sentinels absent from all scanned files

== cleanup ==

============================================================
  KEYCHAIN DELETE -- macOS MAY prompt
  (cleaning up the walk's Keychain entry)
============================================================

  PASS  walk Keychain entry deleted  key_id=people-key-v1:e9d920b7-230b-47bc-a198-de23c8bd510e
  PASS  temp HOME deleted  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-anqvlcr8

== RESULT ==
  PASS x54   FAIL x1   FINDINGS x0   SHOTS x11

FAILURES:
  - Send-to-Workbench button + Workbench-model egress badge  button=False badge=False

SHOTS:
  people-unconfigured-1440.png  (People surface: unconfigured before setup)
  people-unconfigured-393.png  (People surface: unconfigured before setup)
  people-roster-populated-1440.png  (People roster: relationship with sentinel name)
  people-detail-now-lens-1440.png  (Now lens: commitments, requests, next 1:1)
  people-detail-one-on-ones-lens-1440.png  (1:1s lens: session with shared and private agenda items)
  people-detail-info-lens-1440.png  (Info lens: metadata, storage facts, encrypted badge)
  people-detail-no-workbench-btn-1440.png  (Detail view without visible Send-to-Workbench inspector)
  people-roster-populated-393.png  (People roster: relationship with sentinel name)
  people-detail-now-lens-393.png  (Now lens: commitments, requests, next 1:1)
  people-detail-one-on-ones-lens-393.png  (1:1s lens: session with shared and private agenda items)
  people-detail-info-lens-393.png  (Info lens: metadata, storage facts, encrypted badge)
```

### Captured run — 2026-08-18T00:09:56Z

- **Command:** `uv run python scripts/people_walk_full.py --attended`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 0bbf234c8cace8594883adeb62961f7bd26d0011

```text

== ATTENDED MODE ==
  Owner must be watching for macOS Keychain prompts.
  HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-2tt7ltdt  port=55650
  PASS  walk keychain created + unlocked (isolated HOME)  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-2tt7ltdt/Library/Keychains/login.keychain-db
  hub pid=13501 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-2tt7ltdt port=55650

== network proof: baseline-after-boot ==
  lsof snapshot (baseline-after-boot, pid=13501):
    COMMAND     PID  USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
    python3.1 13501 karol   15u  IPv4 0x5720b9e3f6adbc2b      0t0  TCP localhost:55650 (LISTEN)
  PASS  all connections loopback-only (baseline-after-boot)
  PASS  pre-setup readiness  state=unconfigured

== ===== viewport 1440x900 (unconfigured) ===== ==

== readiness unconfigured @1440 ==
  PASS  readiness endpoint reachable  status=200
  PASS  readiness state is unconfigured  state=unconfigured
  PASS  degraded label 'Not set up' visible
  SHOT  people-unconfigured-1440.png  People surface: unconfigured before setup
  PASS  zero console errors  readiness unconfigured @1440  []

== ===== viewport 393x900 (unconfigured) ===== ==

== readiness unconfigured @393 ==
  PASS  readiness endpoint reachable  status=200
  PASS  readiness state is unconfigured  state=unconfigured
  PASS  degraded label 'Not set up' visible
  SHOT  people-unconfigured-393.png  People surface: unconfigured before setup
  PASS  zero console errors  readiness unconfigured @393  []

== setup: POST /api/people/setup (KEYCHAIN WRITE) ==

============================================================
  EXPECT A KEYCHAIN PROMPT -- CLICK 'ALWAYS ALLOW'
  (macOS will ask to allow HoldSpeak People Keychain access)
============================================================

  PASS  setup succeeded  status=200
  PASS  readiness now ready  state=ready

== seed: create relationship + 1:1 + request + notes ==
  PASS  create relationship  status=201
  PASS  create 1:1 session  status=201
  PASS  add shared-intent agenda item  status=201
  PASS  add leader-private agenda item  status=201
  PASS  create grounding note  status=201
  PASS  create request  status=201
  PASS  accept request -> commitment  status=200

== follow-through board proof ==
  PASS  follow-through board reachable  status=200
  PASS  commitment appears on Follow-through board  people_commitment cards in now lane: 1
  PASS  commitment appears exactly once  count=1
  PASS  card text matches request body  text=qT5bJ-sentinel-request-body-6Dz1x
  PASS  follow-through done verb  status=200
  PASS  follow-through reopen verb  status=200

== network proof: after-seed-and-follow-through ==
  lsof snapshot (after-seed-and-follow-through, pid=13501):
    COMMAND     PID  USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
    python3.1 13501 karol   15u  IPv4 0x5720b9e3f6adbc2b      0t0  TCP localhost:55650 (LISTEN)
  PASS  all connections loopback-only (after-seed-and-follow-through)

== ===== viewport 1440x900 (populated) ===== ==

== people populated @1440 ==
  PASS  sentinel name visible in roster
  SHOT  people-roster-populated-1440.png  People roster: relationship with sentinel name
  PASS  zero console errors  people roster @1440  []
  SHOT  people-detail-now-lens-1440.png  Now lens: commitments, requests, next 1:1
  PASS  zero console errors  people detail now @1440  []
  SHOT  people-detail-one-on-ones-lens-1440.png  1:1s lens: session with shared and private agenda items
  PASS  zero console errors  people detail 1:1s @1440  []
  PASS  encrypted storage badge visible
  SHOT  people-detail-info-lens-1440.png  Info lens: metadata, storage facts, encrypted badge
  PASS  zero console errors  people detail info @1440  []

== send-to-workbench check @1440 ==
  PASS  Send-to-Workbench button + Workbench-model egress badge  button=True badge=True
  SHOT  people-detail-send-to-workbench-1440.png  Commitment inspector: Send-to-Workbench with Workbench-model egress badge
  PASS  zero console errors  send-to-workbench check @1440  []

== ===== viewport 393x900 (populated) ===== ==

== people populated @393 ==
  PASS  sentinel name visible in roster
  SHOT  people-roster-populated-393.png  People roster: relationship with sentinel name
  PASS  zero console errors  people roster @393  []
  SHOT  people-detail-now-lens-393.png  Now lens: commitments, requests, next 1:1
  PASS  zero console errors  people detail now @393  []
  SHOT  people-detail-one-on-ones-lens-393.png  1:1s lens: session with shared and private agenda items
  PASS  zero console errors  people detail 1:1s @393  []
  PASS  encrypted storage badge visible
  SHOT  people-detail-info-lens-393.png  Info lens: metadata, storage facts, encrypted badge
  PASS  zero console errors  people detail info @393  []

== RESTART LEG: stop + fresh boot on same HOME ==

============================================================
  KEYCHAIN READ -- macOS MAY prompt again
  (the fresh hub decrypts the store via the native key)
============================================================

  hub pid=13861 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-2tt7ltdt port=55745
  PASS  readiness after restart  state=ready
  PASS  roster intact after restart  names=['Zara Quixote-Sentinel']

== MISSING-KEY SIMULATION ==
  key_id = people-key-v1:6a96b688-8520-4991-a687-b48e4551c00e

============================================================
  KEYCHAIN READ -- macOS MAY prompt
  (reading key value via `keyring get` for backup)
============================================================

  PASS  key value retrieved for backup

============================================================
  KEYCHAIN DELETE -- macOS MAY prompt
  (deleting key to simulate missing-key scenario)
============================================================

  PASS  keychain entry deleted
  hub pid=13873 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-2tt7ltdt port=55756
  PASS  fail-closed: readiness is NOT ready  state=key_unavailable
  PASS  fail-closed: named state reported  state=key_unavailable
  PASS  fail-closed: content-free reason code  reason_code=people_store_key_unavailable
  PASS  fail-closed: roster inaccessible  status=503

============================================================
  KEYCHAIN WRITE -- macOS MAY prompt
  (restoring key after missing-key test)
============================================================

  PASS  keychain entry restored
  hub pid=13892 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-2tt7ltdt port=55767
  PASS  recovery: readiness restored to ready  state=ready
  PASS  recovery: roster intact  names=['Zara Quixote-Sentinel']

== sentinel negative proof ==
  scanning 5 files for sentinel tokens
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-2tt7ltdt/.holdspeak/node_command_ledger.db
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-2tt7ltdt/.local/share/holdspeak/holdspeak.db
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-2tt7ltdt/.local/share/holdspeak/people.v1.sqlite3
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-2tt7ltdt/.local/share/holdspeak/people.v1.sqlite3-wal
    /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-2tt7ltdt/.local/share/holdspeak/people.v1.sqlite3-shm
  PASS  all sentinels absent from all scanned files

== cleanup ==

============================================================
  KEYCHAIN DELETE -- macOS MAY prompt
  (cleaning up the walk's Keychain entry)
============================================================

  PASS  walk Keychain entry deleted  key_id=people-key-v1:6a96b688-8520-4991-a687-b48e4551c00e
  PASS  temp HOME deleted  /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/people-walk-138-attended-2tt7ltdt

== RESULT ==
  PASS x55   FAIL x0   FINDINGS x0   SHOTS x11

SHOTS:
  people-unconfigured-1440.png  (People surface: unconfigured before setup)
  people-unconfigured-393.png  (People surface: unconfigured before setup)
  people-roster-populated-1440.png  (People roster: relationship with sentinel name)
  people-detail-now-lens-1440.png  (Now lens: commitments, requests, next 1:1)
  people-detail-one-on-ones-lens-1440.png  (1:1s lens: session with shared and private agenda items)
  people-detail-info-lens-1440.png  (Info lens: metadata, storage facts, encrypted badge)
  people-detail-send-to-workbench-1440.png  (Commitment inspector: Send-to-Workbench with Workbench-model egress badge)
  people-roster-populated-393.png  (People roster: relationship with sentinel name)
  people-detail-now-lens-393.png  (Now lens: commitments, requests, next 1:1)
  people-detail-one-on-ones-lens-393.png  (1:1s lens: session with shared and private agenda items)
  people-detail-info-lens-393.png  (Info lens: metadata, storage facts, encrypted badge)
```

## Capture provenance note

Three captures above, kept deliberately: (1) the first walk PASSED its
send-to-workbench check on a false positive (the global desk-chrome badge
satisfied an OR-assertion; shot byte-identical to the Now lens) — caught by
the fresh close counsel (S1); (2) the strict AND-assertion then honestly
FAILED (unscoped click landed on the Chair's Follow-Through card behind the
window); (3) the scoped click (You-owe section → surface-row-open) opened the
real Commitment inspector: button=True badge=True, 55 PASS / 0 FAIL, and the
shot shows the WORKBENCH MODEL badge at the point of decision.
