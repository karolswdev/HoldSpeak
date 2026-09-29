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

from holdspeak.operations import _COMMAND_ID, _CONTRACT_REFUSALS, _ROOM_PRINCIPAL, _UPDATE_ID, Admission, OperationDescriptor

_READ = Admission("exempt", "A read: computation without effect (Article XI.5).")
_DESTINATION_ID = {"type": "string", "description": "The saved destination: destinations[].id from channel.destinations."}
_SEND_ID = {"type": "string", "description": "The prepared send: send.id from channel.prepare, or sends[].id from "
                                            "channel.sends."}
_SEND_RESULT = ("{send: {id, document_ref, destination_id, destination_name, channel, badge, target, payload_digest, "
                "size, preview, prepared_by, state, reason, proof, file_path, ...}, outcome} and the receipt")
_OWNER_ONLY = "owner_principal_required: only the owner sends; an agent prepares"

CHANNEL_DESTINATIONS = OperationDescriptor(
    name="channel.destinations",
    version=1,
    description="Where can I send? List your saved destinations (a folder today): each with its name, channel, "
                "target, badge (local, or cloud for a folder you marked synced) and state.",
    args_schema={
        "type": "object",
        "properties": {
            "include_parked": {"type": ["boolean", "null"],
                               "description": "Optional. Also list parked (removed or edited) destinations."},
        },
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="read",
    result="{destinations: [{id, name, channel, account, target, target_digest, synced, state, badge, created_at, parked_at}]}",
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
                "send). Mark it synced if a cloud client syncs that folder. Give replaces to edit one: the old "
                "destination is parked and this one is new.",
    args_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string", "maxLength": 120, "description": "Your name for it (120 characters at most)."},
            "channel": {"type": "string", "enum": ["file"], "description": "The channel: file (a folder)."},
            "folder": {"type": ["string", "null"], "description": "file: the absolute folder path."},
            "synced": {"type": ["boolean", "null"],
                       "description": "Optional, file: a cloud client syncs this folder (the badge says cloud)."},
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
                                   "destination_parked", "channel_unknown", "owner_principal_required"),
    completion="synchronous; channel.destinations lists it",
    exposure=("http:POST /api/channels/destinations", "mcp:channel.save_destination"),
    service="channel_service",
    method="save_destination",
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
    refusals=_CONTRACT_REFUSALS + ("destination_not_saved", "destination_parked", "owner_principal_required"),
    completion="synchronous; channel.destinations(include_parked) shows it parked",
    exposure=("http:DELETE /api/channels/destinations/{destination_id}", "mcp:channel.remove_destination"),
    service="channel_service",
    method="remove_destination",
    admission=Admission("admitted", "Changes the allow-list (XI.1); Remove parks, never deletes."),
)

CHANNEL_CHECK_DESTINATION = OperationDescriptor(
    name="channel.check_destination",
    version=1,
    description="Check a saved destination: a folder still resolves to the saved path, exists and is writable.",
    args_schema={
        "type": "object",
        "properties": {"destination_id": _DESTINATION_ID},
        "required": ["destination_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="read",
    result="{destination, check: {state: ready | changed | missing | not_writable | parked, resolved}}",
    refusals=_CONTRACT_REFUSALS + ("destination_not_saved",),
    completion="synchronous",
    exposure=("http:POST /api/channels/destinations/{destination_id}/check", "mcp:channel.check_destination"),
    service="channel_service",
    method="check_destination",
    admission=Admission("exempt", "A folder: a local check, no egress (the phase's table). The remote channels' "
                                  "account probe is admitted egress; it arrives with them (story 02, 03)."),
)

CHANNEL_PREVIEW = OperationDescriptor(
    name="channel.preview",
    version=1,
    description="See exactly what a destination would get for a published update: the readable preview, the "
                "size and the digest of the exact bytes. Nothing is sent. Pass the digest to channel.send.",
    args_schema={
        "type": "object",
        "properties": {"update_id": _UPDATE_ID, "destination_id": _DESTINATION_ID},
        "required": ["update_id", "destination_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="read",
    result="{document_ref, title, destination_id, channel, badge, payload_digest, size, preview: {text}}",
    refusals=_CONTRACT_REFUSALS + ("NotFound not_found: unknown update", "update_not_published",
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
    description="Prepare a send of a published update to a saved destination: \"send the update to <destination>\". "
                "It freezes the destination and the exact bytes (its preview) in a prepared send that waits for "
                "the owner. Nothing leaves the machine; only the owner sends it (or discards it).",
    args_schema={
        "type": "object",
        "properties": {"update_id": _UPDATE_ID, "destination_id": _DESTINATION_ID, "command_id": _COMMAND_ID},
        "required": ["update_id", "destination_id"],
        "additionalProperties": False,
    },
    principal=_ROOM_PRINCIPAL,
    effect="write",
    result=_SEND_RESULT + " (state prepared; prepared_by names who prepared it)",
    refusals=_CONTRACT_REFUSALS + ("NotFound not_found: unknown update", "update_not_published",
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
    admission=Admission("admitted", "Decides a prepared send (prepared -> discarded, one conditional write). "
                                    "The owner's."),
)

CHANNEL_SEND = OperationDescriptor(
    name="channel.send",
    version=1,
    description="The owner's Send: send a prepared send (send_id), or send a published update to a saved "
                "destination with the digest of the preview he saw (update_id, destination_id, preview_digest). "
                "The answer is the channel's proof (a folder: the file's path, sha256 and size, read back), a "
                "known failure, or unknown. HoldSpeak never sends again by itself: a repeat of the same command_id "
                "answers the first result. Only the owner sends; an agent prepares.",
    args_schema={
        "type": "object",
        "properties": {
            "send_id": {"type": ["string", "null"], "description": "The prepared send: send.id from channel.prepare."},
            "update_id": {"type": ["string", "null"], "description": "Inline form: the published update "
                                                                     "(updates[].id from project.list_updates)."},
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
                                   "payload_too_large:<channel>", "send_already_settled", "update_not_published",
                                   "path_outside_folder", "idempotency_conflict"),
    completion="synchronous; channel.sends and project.list_updates (deliveries) show it",
    exposure=("http:POST /api/channels/send", "mcp:channel.send"),
    service="channel_service",
    method="send",
    admission=Admission("admitted", "Crosses egress or files (XI.1): one terminal receipt -- succeeded (sent), "
                                    "failed, indeterminate (unknown), or refused before the dispatch boundary. "
                                    "The owner's press ('You, every time')."),
)

CHANNEL_SENDS = OperationDescriptor(
    name="channel.sends",
    version=1,
    description="What was sent: the sends of a published update (or one send, or the latest), each with its "
                "destination, state (prepared, dispatching, sent, failed, unknown, discarded), proof or reason, "
                "and the preview of its frozen bytes.",
    args_schema={
        "type": "object",
        "properties": {
            "update_id": {"type": ["string", "null"], "description": "Optional: one update's sends."},
            "send_id": {"type": ["string", "null"], "description": "Optional: one send."},
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

#: PHILO-10-01's rows, in export order.
CHANNEL_OPERATIONS: tuple[OperationDescriptor, ...] = (
    CHANNEL_DESTINATIONS, CHANNEL_SAVE_DESTINATION, CHANNEL_REMOVE_DESTINATION, CHANNEL_CHECK_DESTINATION,
    CHANNEL_PREVIEW, CHANNEL_PREPARE, CHANNEL_DISCARD, CHANNEL_SEND, CHANNEL_SENDS,
)
