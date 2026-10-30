# Use cases

Start with the job. Check the result that the Desk records. Keep a failed
request separate from a result that was never produced.

| Job | Start | Result to check | Failure to tell apart | Guide |
| --- | --- | --- | --- | --- |
| Dictate a coding request | Hold the hotkey | Text in the focused app | A transcript exists versus text was delivered | [Dictation](DICTATION_ARCHITECTURE.md) |
| Correct and replay a phrase | An earlier journal entry | A correction and a new replay result | A stored correction versus a correction that fired | [Dictation](DICTATION_ARCHITECTURE.md) |
| Import an existing discussion | A supported recording or transcript | A Meeting with source material | Unsupported format versus failed intelligence | [Meetings](MEETING_ARCHITECTURE.md) |
| Review an architecture meeting | Meeting intelligence | A summary and typed outputs linked to evidence | Queued, skipped, or failed work versus finished output | [Intelligence](MEETING_INTELLIGENCE.md) |
| Follow up a commitment | A reviewed Meeting outcome | An updated action or prepared external action | Extracting an action versus permission to send it | [Aftercare](MEETING_AFTERCARE.md) |
| Ask about project work | Ask, a Project Room, or selected records | An answer or brief with references | About starting context versus Project service scope | [Project Rooms](PROJECT_ROOMS.md) |
| Keep a useful answer | A model reply | A saved Note or Artifact with its source | Temporary reply versus retained record | [The Desk](WEB_DESK.md#ask-about-your-work) |
| Continue a specialist conversation | Ask or a Thread | Saved turns, references, and tool results | Engine route versus saved conversation | [Threads](AGENTS_AND_THREADS.md) |
| Run a multi-step goal | Programs, a goal, and its steps | Checkpoints, handoffs, and owner decisions | A read-only prepared procedure versus an executable Program | [User Guide](USER_GUIDE.md#programs) |
| Call the Desk | A configured Calls adapter and phone line | Call record, transcript, and receipt | Adapter status versus an answered call | [Calls](calls.md) |
| Reach the owner by phone | Phone reach rules and a configured number or future paired client | Message or call state and receipt | Pairing service token versus a delivered phone client | [Phone](phone.md) |
| Review a held tool request | A tool call in Ask | Allow or deny result | Tool support versus execution authority | [Control modes](AUTHORITY.md) |
| Hand work to a coding agent | A Desk item and configured repository | An agent session in its worktree | Agent persona or CLI inference route versus live coding session | [Coder](CODER_INTEGRATION.md) |
| Run a model on another machine | An engine endpoint | A receipt naming the actual host | Saved endpoint versus where the request ran | [Destinations](EXECUTION_DESTINATIONS.md) |
| Use a portable client | A paired device | Hub-backed work from that device | Paired device versus authority to act | [Companions](COMPANIONS_ARCHITECTURE.md) |
| Repair a broken installation | `holdspeak doctor` | A repaired dependency or stated limit | One passing check versus a ready system | [Operations](OPERATIONS.md) |

## Record a meeting and find the result again

1. Start the hub and note which database it uses.
2. Record or import the meeting.
3. Check audio readiness and model readiness as separate conditions.
4. Read the job state: queued, running, finished, or failed.
5. Check that the output cites the correct transcript.
6. Restart the hub and find the same retained result again.

A queued job, skipped job, or failed request is not a summary. The source
record, job state, result, and receipt are separate evidence. See [Meeting
mode](MEETING_MODE_GUIDE.md) for the current capture and intelligence flow.

## Learning order

| Level | Learn | Stop when |
| --- | --- | --- |
| Start | Voice typing or one Note | You see one useful result in the target app or Desk |
| Ask | Ask and a short Thread | You can inspect its sources and tool result |
| Organize | Notes, Meetings, Artifacts, and Projects | You can find the result again |
| Delegate | Threads, personas, coding agents, and destinations | You know which process runs and where |
| Connect | Project sources, MCP, and paired devices | The data boundary is clear |
| Govern | Control modes and receipts | You can explain who approved an effect |

This order is advice. HoldSpeak does not enforce it.

## See also

- [What is HoldSpeak?](WHAT_IS_HOLDSPEAK.md): the short product model.
- [Capabilities](CAPABILITIES.md): coverage and limits.
- [The Desk](WEB_DESK.md): records, windows, Ask, and navigation.
- [Authority model](AUTHORITY_MODEL.md): grants, gestures, and proposals.
