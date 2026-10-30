# Models and assignments

Use **Settings > Engines** to make a model destination available and assign it
to a capability. See [Models](MODELS.md) for the user procedure.

## Target, deployment, and assignment

- A model profile describes a provider, engine, model, endpoint, node, and
  secret slot.
- An Inference Target is the destination view used by routing. It is separate
  from the engine and the model name.
- An assignment selects one to four compatible targets for a capability or
  saved item.
- At run start, HoldSpeak freezes deployment revisions and the ordered route.
  A later Settings change affects later runs only.

The placement precedence is invocation, Workbench, agent or capability, then
the global `this_machine` default. The winning tier is recorded. HoldSpeak
does not choose a hidden fallback outside the frozen route.

## Destination kinds

| Target | Boundary | Readiness and execution |
| --- | --- | --- |
| `this_machine` | `same_device` | Needs a readable local model file. A missing frozen path refuses. |
| OpenAI-compatible private endpoint | `private_network` | Needs a valid URL and the profile's own key slot. |
| OpenAI-compatible external service | `external_service` | Uses the same checks. Data leaves the local network. |
| Paired device | `paired_device` | A manifest can be read, but execution is currently unsupported. |
| Mesh node | `private_mesh` | Needs a node id and an active worker poll. No local or cloud fallback occurs. |
| Cloud deployment | External cloud | Must be its own route leg and receipt boundary. |

`target_from_profile` can report `ready`, `unavailable`, `stale_manifest`,
`offline`, `unsupported`, or `needs_key`. An unknown target remains
unavailable. It never silently retargets to this machine.

## Credentials and boundaries

`secret_slot` identifies where the owner secret lives. The key value stays out
of target JSON, assignment heads, errors, logs, and Receipts. A configured
endpoint can still send the prompt and sources to its provider. Read the
boundary and host shown for the selected route.

CLI-engine presets use their installed CLI sign-in and can choose their own
provider configuration. A CLI engine is not the same as a launched coding
agent. See [Models](MODELS.md).

## Fallback and receipts

The fallback controller can reserve only the next leg in the frozen plan. A
same-device child cannot turn into cloud within one engine call. Cloud is a
separate route leg with a separate placement record.

The placement Receipt records the selected target, deployment revision,
boundary, model, host, attempted legs, and terminal result. Point-in-time
readiness does not promise run-time availability or model quality.

## See also

- [Execution destinations](EXECUTION_DESTINATIONS.md): destination contract.
- [Models](MODELS.md): Settings and CLI engine presets.
- [Security and privacy](SECURITY.md): data boundaries.
