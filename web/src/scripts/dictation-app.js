// ── The dictation cockpit entry ──────────────────────────────────────
// The page behavior lives in single-concern ES modules under ./dictation/:
//
//   core.js            shared state, api, utils, the section switcher
//   blocks.js          intent blocks: list, templates, editor, CRUD
//   readiness.js       the readiness snapshot cards + next actions
//   knowledge.js       Project Facts (kb) + Project Context (.hs/) + guided setup
//   runtime.js         the pipeline/runtime config editor + copilot depth
//   memory.js          corrections memory + the "What HoldSpeak learned" digest
//   journal.js         the dictation journal + replay
//   dryrun.js          the dry-run trace + the moment-of-truth correction ritual
//   agent.js           agent context/hooks + the project-root override
//   discovery-nudge.js the HS-47-04 project-knowledge discovery nudge
//   activity-nudges.js the HS-53-04 activity pre-briefing cards + pin
//   init.js            event wiring + the page-load sequence
//
// Importing init.js pulls in the rest and runs the wiring (the page emits
// this entry as a deferred type="module" script, so the DOM is ready).
import "./dictation/init.js";
