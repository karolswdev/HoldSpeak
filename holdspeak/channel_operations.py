"""PHILO-10-01: the Send on the one declared contract (the descriptor rows).

One explicit row per operation (the Phase 7 settled method), carved beside
``holdspeak/operations.py`` (which imports this module into ``DESCRIPTORS``),
admitted BY EFFECT as the phase's admission table rules
(``pm/roadmap/holdspeak-philo/phase-10-the-channels/current-phase-status.md``):
the reads and the preview are exempt (XI.5); saving and removing a destination
change the allow-list (admitted, the owner's); prepare is admitted and
completes under the preparer's identity (the owner, or an agent he connected;
Q5); discard and send are admitted and the owner's (``owner_principal_required``
with a receipt for anyone else). Each row names its method on the hub's
``ChannelService``.

The words: the owner sends. An agent PREPARES a send; no description says an
agent can send, and none claims more than the channel's proof (a file written
and read back is the file channel's proof).
"""
from __future__ import annotations

from holdspeak.operations import _COMMAND_ID, _CONTRACT_REFUSALS, _ROOM_PRINCIPAL, Admission, OperationDescriptor

_READ = Admission("exempt", "A read: computation without effect (Article XI.5).")
_DESTINATION_ID = {"type": "string", "description": "Saved ID from channel.destinations."}
_DOCUMENT_REF = {"type": "string", "description": "Document ref <kind>:<id>. Kinds: project_update, monday_brief, "
                 "desk_decision, meeting_decision, decision_record, meeting_summary, meeting_digest, "
                 "meeting_followup, artifact. IDs come from source list/read views."}
_DOCUMENT_REF_FROM_PREVIEW = {"type": "string", "description": "The document ref from channel.preview."}
_SEND_ID = {"type": "string", "description": "The prepared send: send.id from channel.prepare, or sends[].id from "
                                            "channel.sends."}
_SEND_RESULT = ("{send: {id, document_ref, destination_id, destination_name, channel, badge, target, payload_digest, "
                "size, preview, prepared_by, state, reason, proof, file_path, ...}, outcome} and the receipt")
_OWNER_ONLY = "owner_principal_required: only the owner sends; an agent prepares"

CHANNEL_DESTINATIONS = OperationDescriptor(
    name="channel.destinations",
    version=1,
    description="Where can I send? This lists saved destinations: folders, GitHub issues or pull requests, Jira work items, Confluence spaces and email. Each result has a name, channel, account, target, badge (local or cloud), state and connection state.",
    args_schema={
        "type": "object",
        "properties": {
            "include_parked": {"type": ["boolean", "null"],
                               "description": "Also include parked destinations."},
        },
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="read",
    result="{destinations: [{id, name, channel, account, target, target_digest, synced, state, badge, created_at, "
           "parked_at, connection: {id, state, last_checked_at} or null for a folder}]}",
    refusals=_CONTRACT_REFUSALS,
    completion="synchronous",
    exposure=("http:GET /api/channels/destinations", "mcp:channel.destinations"),
    service="channel_service",
    method="destinations",
    admission=_READ,
)

CHANNEL_SAVE_DESTINATION = OperationDescriptor(
    name="channel.save_destination",
    version=1,
    description="Save a destination you send to: a folder (an absolute path; HoldSpeak writes a new file there per "
                "send), a GitHub issue or pull request (a comment per send; the gh login is saved with it), one "
                "Jira work item (a comment per send), a Confluence space (a blog post per send), or email through "
                "a provider (SendGrid or Resend): your verified sender, the name of the saved key, and the To and Cc "
                "addresses. Mark a folder synced if a cloud client syncs it. Give replaces to edit one: the old "
                "destination is parked and this one is new.",
    args_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "maxLength": 120, "description": "Your name for it (120 characters at most)."},
            "channel": {"type": "string", "enum": ["file", "github", "jira", "confluence", "email", "slack"],
                        "description": "The channel: file (a folder), github, jira, confluence, email or Slack."},
            "folder": {"type": ["string", "null"], "description": "file: the absolute folder path."},
            "synced": {"type": ["boolean", "null"],
                       "description": "Optional, file: a cloud client syncs this folder (the badge says cloud)."},
            "host": {"type": ["string", "null"], "description": "github: the host (github.com if not given)."},
            "repo": {"type": ["string", "null"], "description": "github: owner/repo."},
            "kind": {"type": ["string", "null"], "enum": ["issue", "pr", None],
                     "description": "github: issue or pr (a pull request)."},
            "number": {"type": ["integer", "null"], "minimum": 1, "description": "github: the issue or pull request number."},
            "site": {"type": ["string", "null"], "description": "jira, confluence: the Atlassian site (name.atlassian.net)."},
            "email": {"type": ["string", "null"], "description": "jira, confluence: the email of the acli account."},
            "key": {"type": ["string", "null"], "description": "jira: ONE work item key, like ABC-123."},
            "space_id": {"type": ["string", "null"], "description": "confluence: the space id (digits)."},
            "provider": {"type": ["string", "null"],
                         "description": "email: the provider, sendgrid or resend (sendgrid if not given)."},
            "channel_label": {"type": ["string", "null"], "maxLength": 120,
                              "description": "slack: your label for the incoming-webhook channel, for example #leads."},
            "from_email": {"type": ["string", "null"],
                           "description": "email: the sender address (a sender the provider verified)."},
            "from_name": {"type": ["string", "null"], "maxLength": 120, "description": "email: the sender's name."},
            "key_ref": {"type": ["string", "null"], "description": "email: the name of the saved provider key; "
                                                                  "slack: the key_ref returned by channel.save_slack_webhook. Never the secret."},
            "to": {"type": ["array", "null"], "items": {"type": "string"}, "maxItems": 20,
                   "description": "email: the To addresses (at least one)."},
            "cc": {"type": ["array", "null"], "items": {"type": "string"}, "maxItems": 20,
                   "description": "email: the Cc addresses (To and Cc together: 20 at most)."},
            "replaces": {"type": ["string", "null"],
                         "description": "Optional. Edit: the destination id this one replaces (it is parked)."},
            "command_id": _COMMAND_ID,
        },
        "required": ["name", "channel"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{destination: {...as channel.destinations}, replaced} and the receipt",
    refusals=_CONTRACT_REFUSALS + ("folder_not_absolute", "folder_missing", "destination_name_invalid",
                                   "destination_parked", "channel_unknown", "github_target_invalid",
                                   "github_not_logged_in", "jira_key_not_single", "jira_key_invalid",
                                   "atlassian_email_invalid", "confluence_space_invalid", "email_provider_unknown",
                                   "email_address_invalid", "email_key_ref_invalid", "email_recipients_missing",
                                   "email_recipients_too_many", "email_recipient_duplicate",
                                   "slack_webhook_invalid", "slack_key_ref_invalid", "slack_channel_label_invalid",
                                   "slack_webhook_missing",
                                   "slack_key_store_not_native", "slack_key_store_locked",
                                   "destination_builtin", "owner_principal_required"),
    completion="synchronous; channel.destinations lists it",
    exposure=("http:POST /api/channels/destinations", "mcp:channel.save_destination"),
    service="channel_service",
    method="save_destination",
    blocking_io=True,  # GitHub: gh api user --hostname (the concrete login)
    owner_press=True,
    admission=Admission("admitted", "Changes where the owner's documents may go: the allow-list (XI.1). "
                                    "The owner's; Edit parks the old row."),
)

CHANNEL_REMOVE_DESTINATION = OperationDescriptor(
    name="channel.remove_destination",
    version=1,
    description="Remove a saved destination: it is parked, its history is kept, and a send prepared to it is "
                "refused.",
    args_schema={
        "type": "object",
        "properties": {"destination_id": _DESTINATION_ID, "command_id": _COMMAND_ID},
        "required": ["destination_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{destination: {... state: parked}} and the receipt",
    refusals=_CONTRACT_REFUSALS + ("destination_not_saved", "destination_parked", "destination_builtin",
                                   "owner_principal_required"),
    completion="synchronous; channel.destinations(include_parked) shows it parked",
    exposure=("http:DELETE /api/channels/destinations/{destination_id}", "mcp:channel.remove_destination"),
    service="channel_service",
    method="remove_destination",
    owner_press=True,
    admission=Admission("admitted", "Changes the allow-list (XI.1); Remove parks, never deletes."),
)

CHANNEL_CHECK_DESTINATION = OperationDescriptor(
    name="channel.check_destination",
    version=1,
    description="Check a saved destination: a folder still resolves to the saved path, exists and is writable; a "
                "GitHub, Jira or Confluence destination shows the stored state of its connection; an email "
                "destination's key is in the OS keychain, then its sender's verification as the provider last "
                "answered a send from it (no call to the provider).",
    args_schema={
        "type": "object",
        "properties": {"destination_id": _DESTINATION_ID},
        "required": ["destination_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="read",
    result="{destination, check: {state: ready | changed | missing | not_writable | parked | connected | "
           "never_checked | owner_action_required | unavailable | degraded | email_key_missing | "
           "email_key_store_not_native | email_key_store_locked | sender_accepted | sender_not_verified | "
           "key_changed, resolved, answered_at (email: when the provider gave that answer)}}",
    refusals=_CONTRACT_REFUSALS + ("destination_not_saved",),
    completion="synchronous",
    exposure=("http:POST /api/channels/destinations/{destination_id}/check", "mcp:channel.check_destination"),
    service="channel_service",
    method="check_destination",
    blocking_io=True,  # email: the OS keychain read (it may wait on the owner's unlock); Codex Astra r2 on #696
    admission=Admission("exempt", "A folder: a local check, no egress (the phase's table). A remote channel: the "
                                  "stored connection state, no probe (connection.recheck probes, admitted)."),
)

CHANNEL_PREVIEW = OperationDescriptor(
    name="channel.preview",
    version=1,
    description="Preview exact bytes for a stored document at a saved destination. Returns text, size, digest; sends nothing. Pass digest to channel.send.",
    args_schema={
        "type": "object",
        "properties": {"document_ref": _DOCUMENT_REF, "destination_id": _DESTINATION_ID},
        "required": ["document_ref", "destination_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="read",
    result="{document_ref, title, destination_id, channel, badge, payload_digest, size, preview: {text} "
           "(confluence: {title, text})}",
    refusals=_CONTRACT_REFUSALS + ("document_kind_unknown", "document_not_found", "artifact_body_missing", "artifact_not_text", "not_published", "no_summary",
                                   "destination_not_saved", "destination_parked", "payload_too_large:<channel>"),
    completion="synchronous",
    exposure=("http:POST /api/channels/preview", "mcp:channel.preview"),
    service="channel_service",
    method="preview",
    admission=Admission("exempt", "Computation: a render per channel, nothing leaves (XI.5)."),
)

CHANNEL_PREPARE = OperationDescriptor(
    name="channel.prepare",
    version=1,
    description="Prepare a send of a stored document using \"send the update to <destination>\" or \"send this artifact to <destination>\". The prepared send freezes its destination and exact preview bytes. Nothing leaves the machine. Only the owner can send or discard it.",
    args_schema={
        "type": "object",
        "properties": {"document_ref": _DOCUMENT_REF_FROM_PREVIEW, "destination_id": _DESTINATION_ID, "command_id": _COMMAND_ID},
        "required": ["document_ref", "destination_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result=_SEND_RESULT + " (state prepared; prepared_by names who prepared it)",
    refusals=_CONTRACT_REFUSALS + ("document_kind_unknown", "document_not_found", "artifact_body_missing", "artifact_not_text", "not_published", "no_summary",
                                   "destination_not_saved", "destination_parked", "payload_too_large:<channel>"),
    completion="synchronous; channel.sends lists it prepared until the owner sends or discards it",
    exposure=("http:POST /api/channels/sends", "mcp:channel.prepare"),
    service="channel_service",
    method="prepare",
    admission=Admission("admitted", "Records a prepared send under the preparer's identity: the owner, or an "
                                    "agent he connected (Q5). Nothing leaves."),
)

CHANNEL_DISCARD = OperationDescriptor(
    name="channel.discard",
    version=1,
    description="Discard a prepared send: it will never be sent. The owner's; against a Send at the same time, "
                "one wins.",
    args_schema={
        "type": "object",
        "properties": {"send_id": _SEND_ID, "command_id": _COMMAND_ID},
        "required": ["send_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result=_SEND_RESULT + " (state discarded)",
    refusals=_CONTRACT_REFUSALS + ("NotFound not_found: unknown send", "send_already_settled", _OWNER_ONLY),
    completion="synchronous",
    exposure=("http:POST /api/channels/sends/{send_id}/discard", "mcp:channel.discard"),
    service="channel_service",
    method="discard",
    owner_press=True,
    admission=Admission("admitted", "Decides a prepared send (prepared -> discarded, one conditional write). "
                                    "The owner's."),
)

CHANNEL_SEND = OperationDescriptor(
    name="channel.send",
    version=1,
    description="The owner's Send: send a prepared send (send_id), or send a stored document to a saved "
                "destination with the digest of the preview he saw (document_ref, destination_id, preview_digest). "
                "The answer is the channel's proof (a folder: the file's path, sha256 and size, read back; GitHub: "
                "the comment URL; Jira and Confluence: the id acli gives; email: the provider's message id, "
                "ACCEPTED BY SENDGRID or ACCEPTED BY RESEND -- accepted for processing, not delivered), a known failure with its code, or "
                "unknown. HoldSpeak never sends again by itself: a repeat of the same command_id answers the first "
                "result. Only the owner sends; an agent prepares.",
    args_schema={
        "type": "object",
        "properties": {
            "send_id": {"type": ["string", "null"], "description": "The prepared send: send.id from channel.prepare."},
            "document_ref": {"type": ["string", "null"], "description": "Inline form: the stored document "
                                                                       "(<kind>:<source id>)."},
            "destination_id": {"type": ["string", "null"], "description": "Inline form: the saved destination "
                                                                          "(destinations[].id)."},
            "preview_digest": {"type": ["string", "null"], "description": "Inline form: payload_digest from "
                                                                          "channel.preview (what he saw)."},
            "command_id": _COMMAND_ID,
        },
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result=_SEND_RESULT + ": outcome sent (proof), failed (reason) or unknown (reason)",
    refusals=_CONTRACT_REFUSALS + (_OWNER_ONLY, "NotFound not_found: unknown send", "destination_not_saved",
                                   "destination_parked", "destination_changed", "preview_changed", "payload_changed",
                                   "payload_too_large:<channel>", "send_already_settled", "document_kind_unknown",
                                   "document_not_found", "artifact_body_missing", "artifact_not_text", "not_published", "no_summary",
                                   "path_outside_folder", "github_identity_changed", "github_not_logged_in",
                                   "github_identity_unverified", "atlassian_not_signed_in",
                                   "atlassian_switch_failed", "atlassian_identity_unverified", "lock_timeout",
                                   "email_provider_unknown", "email_key_missing",
                                   "email_key_store_not_native", "email_key_store_locked",
                                   "email_recipients_too_many", "idempotency_conflict"),
    completion="synchronous; channel.sends and project.list_updates (deliveries) show it",
    exposure=("http:POST /api/channels/send", "mcp:channel.send"),
    service="channel_service",
    method="send",
    blocking_io=True,  # gh / acli children; the email egress (a SendGrid or Resend call up to 30 s)
    owner_press=True,
    admission=Admission("admitted", "Crosses egress or files (XI.1): one terminal receipt -- succeeded (sent), "
                                    "failed, indeterminate (unknown), or refused before the dispatch boundary. "
                                    "The owner's press ('You, every time')."),
)

CHANNEL_SENDS = OperationDescriptor(
    name="channel.sends",
    version=1,
    description="What was sent? List document sends by destination and state. Each result includes proof or reason and the frozen preview.",
    args_schema={
        "type": "object",
        "properties": {
            "document_ref": {"type": ["string", "null"], "description": "Optional document ref."},
            "send_id": {"type": ["string", "null"], "description": "Optional send ID."},
        },
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="read",
    result="{sends: [" + _SEND_RESULT.split(" and the receipt")[0] + "]}",
    refusals=_CONTRACT_REFUSALS + ("NotFound not_found: unknown send",),
    completion="synchronous",
    exposure=("http:GET /api/channels/sends", "mcp:channel.sends"),
    service="channel_service",
    method="sends",
    admission=_READ,
)

CHANNEL_SAVE_EMAIL_KEY = OperationDescriptor(
    name="channel.save_email_key",
    version=1,
    description="Save your email provider's key (a SendGrid or Resend API key) in the OS keychain under a name and "
                "the provider; an email destination names that key. The key is sent in the request body, is never an argument, and is "
                "never shown again.",
    args_schema={
        "type": "object",
        "properties": {
            "key_ref": {"type": "string", "description": "The key's name (from the path)."},
            "provider": {"type": ["string", "null"], "description": "Optional: the provider, sendgrid or resend (sendgrid if not given)."},
            "command_id": _COMMAND_ID,
        },
        "required": ["key_ref"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{key_ref, provider, saved} and the receipt (never the key)",
    refusals=_CONTRACT_REFUSALS + ("owner_required", "email_key_ref_invalid", "email_key_invalid",
                                   "email_provider_unknown", "email_key_store_not_native", "email_key_store_locked"),
    completion="synchronous; channel.check_destination of an email destination answers ready",
    exposure=("http:PUT /api/channels/email-keys/{key_ref}",),
    service="channel_service",
    method="save_email_key",
    held=("api_key",),
    owner_only=True,
    owner_press=True,
    blocking_io=True,  # the OS keychain (it may wait on the owner's unlock)
    admission=Admission("admitted", "Config: the owner's email key in the OS keychain (#694's table: config, "
                                    "his press, HTTP only, in no palette). The key is held by the transport, "
                                    "never an argument, never journaled."),
)

CHANNEL_SAVE_SLACK_WEBHOOK = OperationDescriptor(
    name="channel.save_slack_webhook",
    version=1,
    description="Save a Slack incoming-webhook URL in the native keychain. The URL is held by HTTP, never an "
                "argument or result; the returned key_ref is consumed by channel.save_destination.",
    args_schema={
        "type": "object",
        "properties": {
            "command_id": _COMMAND_ID,
        },
        "required": [],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result="{key_ref, saved} and the receipt (never the URL)",
    refusals=_CONTRACT_REFUSALS + ("owner_required", "slack_webhook_invalid", "slack_key_ref_invalid",
                                   "slack_webhook_missing",
                                   "slack_key_store_not_native", "slack_key_store_locked"),
    completion="synchronous; channel.save_destination consumes key_ref to create the destination",
    exposure=("http:POST /api/channels/slack-webhooks",),
    service="channel_service",
    method="save_slack_webhook",
    held=("webhook_url",),
    owner_only=True,
    owner_press=True,
    blocking_io=True,
    admission=Admission("admitted", "Config: the owner's Slack webhook in the native keychain, HTTP only, in no palette. "
                                    "The URL is held by the transport and never journaled."),
)

#: PHILO-10-01's rows, in export order.
CHANNEL_OPERATIONS: tuple[OperationDescriptor, ...] = (
    CHANNEL_DESTINATIONS, CHANNEL_SAVE_DESTINATION, CHANNEL_REMOVE_DESTINATION, CHANNEL_CHECK_DESTINATION,
    CHANNEL_PREVIEW, CHANNEL_PREPARE, CHANNEL_DISCARD, CHANNEL_SEND, CHANNEL_SENDS, CHANNEL_SAVE_EMAIL_KEY,
    CHANNEL_SAVE_SLACK_WEBHOOK,
)
