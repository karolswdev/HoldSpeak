# Device dogfood runbook

This is the short, repeatable path for a Swift iPhone/iPad sitting. The full
policy is in [`CHARTER.md`](./CHARTER.md). Opening the guided site in a device
browser does not change the product target: React Safari and a Swift app on the
same iPad are different execution slots.

## Start and pair

```bash
cd /Users/karol/dev/tools/HoldSpeak
UAT_HOST=0.0.0.0 uv run python -m uat.conductor
```

1. Open the printed LAN URL in a browser to operate the guided UAT site.
2. Enable **Device sitting** before selecting a native pack.
3. Open the exact installed Swift target named by the scenario. In that app's
   connect card, enter the product pairing
   URL/token shown in the sitting. Test the connection.
4. In **Native device attestation**, register target, form factor, device name,
   OS, bundle ID, build number, and installation source; check **Pairing
   verified** only after the app has connected to this isolated run.
5. Record orientation/size class, permissions, audio route, inference
   mode/model, and network posture in the first relevant note.
6. Confirm the displayed slot matches the app: for example,
   `ios_flagship_swift:ipad`. Do not cast it from React, responsive mode, a
   simulator, another Swift root, or the desktop monitor.

The per-run token remains stable when a scenario changes decks. Verdicts poll
from the conductor so a result recorded in one guided-site browser appears in
the other. Native verdicts remain locked until the selected device attestation
matches both target and form factor and has pairing verified. This is structured
human attestation, not cryptographic device identity.

## Target and form-factor check

| What you are observing | Execution slot |
|---|---|
| React in desktop browser | `web_react:desktop` |
| React in Safari on physical iPad | `web_react:ipad_browser` |
| React under desktop responsive emulation | `web_react:tablet_viewport` |
| Production Swift app on iPad | `ios_flagship_swift:ipad` |
| Production Swift app on iPhone | `ios_flagship_swift:iphone` |
| Companion/classic Swift build | exact `ios_companion_swift:*` or `ios_classic_swift:*` |

No row in this table substitutes for another.

## Fast loops

| Time | Pack | Purpose |
|---|---|---|
| 20–30 min | `ios-flagship-deskos` | production-root arrival, native Desk read/CRUD/zones/free placement |
| 10–15 min | `ios-flagship-smoke` | pair/sync, record/reopen, iPad live intel, native steering/offline |
| 10 min | `smoke` on `web_react:desktop` | independent React Web Desk plumbing and cross-check |
| 15–20 min | `pack-d-honest-failure` | trust, setup, endpoint, schema and egress failures |
| focused | `pack-f-mobile` | broad mobile inventory; note each scenario's flagship/companion/classic target |

Do the fast native pack on both iPhone and iPad when its form factor is applicable.
The iPad-only diarization beat needs two speakers. Steering needs a real waiting
pane. Offline/on-device inference requires models downloaded before networking
is disabled.

## Capture quickly

- Use `pass` for a clean bar, `fail` for a miss, `partial` for a material split,
  `observe` for a bug-hunt note on otherwise accepted behavior, and `skip` only
  when no answer is possible.
- Speak notes with the microphone button when the run can transcribe; type when
  product transcription is deliberately unavailable.
- Attach one screenshot for visual/state ambiguity. The finding retains its
  note, screenshot path, real application-log slice, execution-slot split,
  protocol hash, and product commit.
- Finish, then triage every finding with a disposition. Generate the backlog
  block only after triage.

## Stop signals

Stop and record a fail rather than improvising when:

- the app target/build does not match the scenario;
- the target/form-factor slot does not match the app and device in hand;
- the device is paired to the live hub instead of the isolated run;
- the only available evidence is a resized browser, device browser, simulator,
  or different Swift root;
- a recipe/manual preflight or mid-step transition fails;
- a control cannot actually disable the claimed input;
- the expected screen is compiled but unreachable from the production root;
- a credential, key, transcript, or output egresses without explicit consent.
