# Choose a HoldSpeak workflow

Use one row to define the result you need. These workflows describe the research
snapshot, not a guarantee that your hardware or model is ready.

| Job | Start | Result and inspection | Main failure to distinguish | Contract |
| --- | --- | --- | --- | --- |
| Dictate a coding request | Hold the configured hotkey | Text in the target app; inspect the journal when it differs | Transcript success versus delivery failure | [Dictation](DICTATION_ARCHITECTURE.md) |
| Correct and replay a phrase | An earlier dictation entry | A correction and a new replay result | A stored correction is not proof it was applied | [Dictation](DICTATION_ARCHITECTURE.md) |
| Import an existing discussion | A supported recording or transcript | A meeting with source material | Unsupported format versus failed intelligence | [Meetings](MEETING_ARCHITECTURE.md) |
| Review an architecture meeting | Meeting intelligence | Summary and typed artifacts linked to evidence | Queued or skipped work versus completed output | [Intelligence](MEETING_INTELLIGENCE.md) |
| Follow up a commitment | Reviewed meeting outcome | An updated action or a prepared external action | Extraction versus authority to send | [Aftercare](MEETING_AFTERCARE.md) |
| Ask about retained project work | Project context or selected records | Answer and relevant references | Matching context versus all project knowledge | [Agents and Threads](AGENTS_AND_THREADS.md) |
| Keep a useful answer | A model reply | Saved Artifact and provenance | Transient reply versus retained object | [Domain model](DOMAIN_MODEL.md) |
| Continue a specialist conversation | An Agent or Thread | Persisted turns, attachments and results | Model selection versus the saved conversation identity | [Agents and Threads](AGENTS_AND_THREADS.md) |
| Reply to a coding agent | A waiting Coder session | A delivered reply and outcome | Observation versus steering authority | [Coder](CODER_INTEGRATION.md) |
| Review a held tool request | Gate request | Allow or deny result for that request | Gate armed versus Gate installed but inactive | [Gate](GATE.md) |
| Move inference to another machine | An execution destination | Run evidence naming the actual destination | Configured destination versus reachable executor | [Destinations](EXECUTION_DESTINATIONS.md) |
| Use a portable client | A paired companion | Hub-backed work from the client | Implemented client versus a released app | [Companions](COMPANIONS_ARCHITECTURE.md) |
| Recover a failed installation | Doctor and the named fault | Repaired dependency or an explicit limit | Passing one probe versus whole-system readiness | [Operations](OPERATIONS.md) |

## Meet, then find the result again

The first vertical slice has six checks:

1. Identify the hub build and database used for the test.
2. Capture or import a meeting without confusing model readiness with audio readiness.
3. Identify the selected destination before requesting intelligence.
4. Distinguish admission, queueing, execution and terminal output.
5. Review whether the result is useful and linked to the right transcript.
6. Restart the same isolated hub and find the same retained result.

An isolated automated fixture can prove parts of this path. It cannot establish
whether a real summary is useful to the owner. Record those two verdicts separately.

## Learning order

| Level | Learn | Stop when |
| --- | --- | --- |
| Start | Dictation or a first meeting | One useful result is visible |
| Enhance | Model transformation and relevant context | The output improves the chosen job |
| Organize | Notes, Artifacts and Projects | You can find the result again |
| Delegate | Threads, Agents, Coder and destinations | You understand what will run and where |
| Connect | External integrations, mesh or companions | The specific connection works and its boundary is clear |
| Govern | Control modes, Gate and receipts | You can explain the authority and result of an action |

This table is guidance, not six mandatory setup screens.

## See also

- [What is HoldSpeak?](WHAT_IS_HOLDSPEAK.md): the short product model.
- [Capabilities](CAPABILITIES.md): precise coverage and evidence.
- [Authority](AUTHORITY_MODEL.md): how gestures, grants and proposals differ.
