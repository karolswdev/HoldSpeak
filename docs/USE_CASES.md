# Use cases

Find the job you need.
Each row names the start, the result to check, the failure to tell apart, and the guide that owns the topic.

| Job | Start | Result to check | Failure to tell apart | Guide |
| --- | --- | --- | --- | --- |
| Dictate a coding request | Hold the hotkey | Text in the target app | A transcript that exists versus text that was delivered | [Dictation](DICTATION_ARCHITECTURE.md) |
| Correct and replay a phrase | An earlier journal entry | A correction and a new replay result | A stored correction versus a correction that fired | [Dictation](DICTATION_ARCHITECTURE.md) |
| Import an existing discussion | A recording or transcript file | A Meeting with its source material | An unsupported format versus failed intelligence | [Meetings](MEETING_ARCHITECTURE.md) |
| Review an architecture meeting | Meeting intelligence | A summary and typed artifacts linked to evidence | Queued or skipped work versus finished output | [Intelligence](MEETING_INTELLIGENCE.md) |
| Follow up a commitment | A reviewed meeting outcome | An updated action or a prepared external action | Extracting an action versus permission to send it | [Aftercare](MEETING_AFTERCARE.md) |
| Ask about project work | A Project or selected records | An answer with references | Matching context versus all project knowledge | [Agents and Threads](AGENTS_AND_THREADS.md) |
| Keep a useful answer | A model reply | A saved Artifact with its source | A temporary reply versus a kept record | [Domain model](DOMAIN_MODEL.md) |
| Continue a specialist conversation | An agent or a Thread | Saved turns, attachments, and results | The model choice versus the saved conversation | [Agents and Threads](AGENTS_AND_THREADS.md) |
| Reply to a coding agent | A waiting coder session | A delivered reply and its outcome | Watching a session versus permission to steer it | [Coder](CODER_INTEGRATION.md) |
| Review a held tool request | A Gate request | An allow or deny result for that request | Gate armed versus Gate installed but idle | [Gate](GATE.md) |
| Run a model on another machine | An execution destination | A run record that names the real destination | A saved destination versus the place the run happened | [Destinations](EXECUTION_DESTINATIONS.md) |
| Use a portable client | A paired device | Hub-backed work from the device | A paired device versus authority to act | [Companions](COMPANIONS_ARCHITECTURE.md) |
| Repair a broken installation | `holdspeak doctor` | A repaired dependency or a stated limit | One passing check versus a ready system | [Operations](OPERATIONS.md) |

## Record a meeting and find the result again

1. Start the hub and note which database it uses.
2. Record or import the meeting. Audio readiness and model readiness are separate.
3. Check the selected model destination before you run intelligence.
4. Read the job state: queued, running, finished, or failed.
5. Check that the result is useful and links to the right transcript.
6. Restart the hub. Find the same result again.

A queued job, a skipped job, or a failed request is not a summary.
The [meeting guide](MEETING_MODE_GUIDE.md) describes each step.

## Learning order

| Level | Learn | Stop when |
| --- | --- | --- |
| Start | Voice typing or one meeting | You see one useful result |
| Enhance | Model rewriting and project context | The output improves your job |
| Organize | Notes, Artifacts, and Projects | You can find a result again |
| Delegate | Threads, agents, coder, and destinations | You know what runs and where |
| Connect | Connectors, mesh, and devices | The connection works and its data boundary is clear |
| Govern | Control modes, Gate, and Receipts | You can explain who approved an action and what it did |

This order is advice. HoldSpeak does not enforce it.

## See also

- [What is HoldSpeak?](WHAT_IS_HOLDSPEAK.md): the short product model.
- [Capabilities](CAPABILITIES.md): precise coverage and limits.
- [Authority model](AUTHORITY_MODEL.md): how gestures, grants, and proposals differ.
