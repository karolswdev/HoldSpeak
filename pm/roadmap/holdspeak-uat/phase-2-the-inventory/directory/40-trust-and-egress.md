# Directory — Trust & Egress (the cross-cut)

> **Auto-derived** by the 8-agent inventory sweep (Opus 4.8, 2026-07-08) from the
> phase record, then to be **verified on real glass** by the sweep story. This is the
> *starting map*, not the final ledger: the ✅/❓/— marks are the record's claim, and
> every ❓ (and every contested ✅) is exactly what the human checks on the device.

every documented promise about what leaves the machine and every consent gate — pulled from SECURITY.md, POSITIONING, and the actuator/steering phases. These are must-test **regardless of domain**; a sweep that touches an egress point verifies its badge/gate here.

**24 capabilities** — 15 must-test, 4 should-test, 4 spot-check, 1 skip.

Surfaces: ✅ record says present · ❓ unknown, verify on device · — record says not on this surface.

| P | web | iPad | iPhone | Capability | Key | Phases | State recipe(s) |
|---|---|---|---|---|---|---|---|
| 🔴 | — | ❓ | ❓ | Safe schema upgrade: backup-then-apply older, refuse newer | `release.schema.safe_upgrade` | HS-50 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | Web runtime binds loopback by default; off-loopback binds refuse without an auth token | `trust.binding.loopback-token-gate` | HS-41,HS-50 | `fresh-desk` |
| 🔴 | ✅ | ✅ | ❓ | The egress badge names local vs the exact endpoint on every card | `trust.egress.badge-tells-truth` | HS-62,HS-58 | `seeded-desk`, `meeting-just-ended-open-actions` |
| 🔴 | ✅ | ❓ | ❓ | Cloud meeting intel egress only on explicit provider choice | `trust.egress.cloud-meeting-intel` | HS-61,HS-62 | `seeded-desk`, `intel-endpoint-dead` |
| 🔴 | ✅ | ✅ | ❓ | Desk GitHub issue files title+body through the user's own gh CLI on approval | `trust.egress.desk-github-issue` | HS-37,HS-49 | `meeting-just-ended-open-actions`, `proposal-pending-approval` |
| 🔴 | ✅ | ✅ | ❓ | Desk webhook connector sends previewed text to one configured endpoint on per-send approval | `trust.egress.desk-webhook-connector` | HS-37,HS-38 | `proposal-pending-approval` |
| 🔴 | ✅ | ✅ | ✅ | Mesh relay moves only prompt+result between hub and the node you named, no keys transit | `trust.egress.mesh-relay` | HS-85,HSM-25 | `mesh-node-alive`, `mesh-node-just-died` |
| 🔴 | ✅ | ✅ | ❓ | Send to Slack requires URL config plus per-send approval, URL never rides payloads | `trust.egress.send-to-slack-double-optin` | HS-61,HS-62 | `meeting-just-ended-open-actions`, `proposal-pending-approval` |
| 🔴 | ✅ | ❓ | ❓ | Egress badge on every actionable card | `trust.egress_badge` | HS-62 | `proposal-pending-approval`, `learned-correction-taught`, `meeting-just-ended-open-actions` |
| 🔴 | ✅ | ❓ | ❓ | No telemetry, crash reporting, or background beaconing anywhere | `trust.no-telemetry` | HS-58,HS-62 | `fresh-desk` |
| 🔴 | ✅ | ✅ | ✅ | Runtime profile keys never sync; a key supplied to any ingress never reappears on a read | `trust.secrets.profile-key-never-syncs` | HS-84,HSM-17 | `seeded-desk` |
| 🔴 | ✅ | ✅ | ❓ | Session steering requires an in-memory arming grant, TTL'd and pane-pinned; hub restart disarms | `trust.steering.arming-grant` | HS-87,HS-89 | `agent-pane-awaiting-input` |
| 🔴 | ✅ | ✅ | ❓ | Only allow-listed named keys reach tmux; an arbitrary string can never become a keystroke | `trust.steering.named-key-allowlist` | HS-89 | `agent-pane-awaiting-input` |
| 🔴 | ✅ | ✅ | ❓ | Cross-machine steering: the typing node owns the grant and audit; only command+node token cross | `trust.steering.relay-node-owns-grant` | HS-89,HS-90 | `mesh-node-alive`, `mesh-node-just-died` |
| 🔴 | ✅ | ✅ | ❓ | Session factory: spawn/rename name-allow-listed, kill gated exactly like a steer | `trust.steering.session-factory-gates` | HS-90 | `agent-pane-awaiting-input` |
| 🟡 | — | ❓ | ❓ | Back up and restore the whole HoldSpeak database from the CLI | `release.backup_restore.cli` | HS-50 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Paired device audio link authenticates with a constant-time PSK, same-LAN scope | `trust.device.psk-audio-link` | HS-53 | `seeded-desk` |
| 🟡 | ✅ | ✅ | ❓ | Mission-control belt is GET-only: reads open PRs via the user's own gh, composes nothing | `trust.egress.missioncontrol-receipts` | HS-88 | `seeded-desk` |
| 🟡 | ✅ | ❓ | ❓ | Wake-word enable triggers a one-time inbound model download, no audio ever egresses | `trust.egress.wake-model-download` | HS-60 | `first-run-no-model` |
| ⚪ | ❓ | ❓ | ❓ | doctor reports database + config health honestly | `release.doctor.database_check` | HS-50 | `seeded-desk` |
| ⚪ | ✅ | — | — | Connector CLI enrichment sends only entity IDs to the user's own gh/jira tools | `trust.egress.connector-cli-enrichment` | HS-38 | `seeded-desk` |
| ⚪ | ✅ | — | — | Deferred-intel failure webhook sends queue stats only, no transcript, opt-in | `trust.egress.deferred-intel-webhook` | HS-36 | `intel-endpoint-dead` |
| ⚪ | ❓ | ❓ | ❓ | The README/front-door pitch and comparison | `trust.positioning_readme` | HS-58,HS-64 | — |
| ⬛ | ❓ | ❓ | ❓ | The rendered architecture map | `trust.architecture_map` | HS-66 | — |

Priority: 🔴 must-test · 🟡 should-test · ⚪ spot-check · ⬛ skip.
