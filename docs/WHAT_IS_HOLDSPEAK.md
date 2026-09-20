# What is HoldSpeak?

HoldSpeak puts voice typing, meetings, saved context and agent work on one Desk.
The Desk is the place to open records and tools. The hub runs the work and stores
its results. A model can run on your machine or at a destination you configure.

This guide describes source commit `675401a8`. It does not certify that each
workflow works on your installation. The project is still before first-use
acceptance. A package label such as Beta does not change that limit.

## Start with one result

Choose the job you need today. You do not need to configure every subsystem.

| Your job | What you use | Result to check |
| --- | --- | --- |
| Put spoken words into another app | Dictation | The intended text appears in the intended field |
| Find the useful parts of a meeting | Meetings and intelligence | A saved transcript and a useful result linked to it |
| Think through material you already have | Notes, Projects, Ask or a Thread | An answer whose selected sources you can inspect |
| Ask software to act for you | An applicable command or proposal | The intended action and its recorded outcome |

These are four ways to understand the product. They are not four separate apps.
An action can move between them. For example, a meeting result can become context
for a Thread, and the Thread can help prepare a follow-up.

## The words you need first

| Word | Meaning |
| --- | --- |
| Desk | The workspace of objects and windows |
| Meeting | A saved conversation and its transcript |
| Note | Text you keep and edit |
| Artifact | A saved output that you can return to |
| Project | A scope for related work and sources |
| Thread | A conversation with saved turns and context |
| Model | The engine that generates or transforms a result |
| Destination | Where a particular operation runs |
| Receipt | A record of an operation's outcome |

The [domain model](DOMAIN_MODEL.md) distinguishes stored entities from visual
objects and service concepts. You do not need that detail to start a meeting.

## Your first meeting result

Use the [meeting guide](MEETING_MODE_GUIDE.md) to prepare audio and open Meetings.
The source has controls for recording, import and intelligence. Capture and
intelligence are separate stages. Having a transcript does not mean a summary
has been generated.

Before a model run, check the selected destination. After the run, inspect the
result and its source meeting. Return to the result after a hub restart. That
last step tests whether the result is durable and findable.

The first meeting-result acceptance remains open at this snapshot. A missing model, queued job or
failed request is not a successful summary. The
[meeting architecture](MEETING_ARCHITECTURE.md) explains those states.

## Add tools when the job needs them

Start with capture. Add model rewriting or meeting intelligence when it saves
work. Use Notes and Projects to retain context. Add Threads or coding-agent
integration for work that needs a conversation. Configure external tools or
companions only when you need their specific action.

This is a suggested learning order. It is not an implemented onboarding wizard.
The complete [capability reference](CAPABILITIES.md) records the larger surface,
including developer-only and platform-limited paths.

## Know what an action permits

An owner gesture can supply approval. A separate confirmation is not required
for every operation. Delegated work and proposed external actions have their
own authority checks. Read [Control modes](AUTHORITY.md) before enabling them.

Models, connectors, companion devices and external actions can transfer data.
Local storage does not make every configured operation local. Check the
destination and the [security model](SECURITY_MODEL.md).

## See also

- [Getting Started](GETTING_STARTED.md): install and capture a sentence.
- [Use cases](USE_CASES.md): choose a job and inspect its result.
- [System architecture](SYSTEM_ARCHITECTURE.md): how the parts work together.
- [Capabilities](CAPABILITIES.md): implementation, evidence and limits.
- [Troubleshooting](TROUBLESHOOTING.md): follow a specific failure path.
