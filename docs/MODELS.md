# Models: bring your own

HoldSpeak uses models you choose. **Model Library** is where you make a model
available. **Assignments** is where you choose the compatible ordered model list
for a kind of work. This guide gets you set up. Read the internal
[Intelligence Router architecture](internal/ARCHITECTURE_INTELLIGENCE_ROUTER.md)
when you need the execution mechanics.

> **Local-first.** Your model material and connection details stay on your hub.
> Model material leaves only for the model endpoint you choose. Read
> [Security & Privacy](SECURITY.md) for the complete egress boundary.

## Start here

1. Open **Settings, Models**.
2. In **Model Library**, add a model from the catalog, add a model file, connect
   a provider, or connect a paired device.
3. Check its readiness. A model that is present is not necessarily ready to run.
4. Open **Assignments** and choose the compatible model list for the work you
   want to run. Use **Use default** when the inherited choice is the right one.

Adding or connecting a model does not change an Assignment. Choosing or
clearing an Assignment does not alter the Model Library. Keep those two actions
separate when you repair setup.

## Model Library: make models available

The Model Library is the owner surface for availability. It can start a
catalog-pinned model acquisition, adopt a detected or uploaded model file,
connect a hosted provider, define an OpenAI-compatible endpoint, or connect an
existing paired device. A provider key is submitted through a separate
write-only field. The Library shows whether a required key is present, never its
value.

You can use three practical sources:

- **Local GGUF.** Install the `dictation-llama` extra when you want the local
  runtime, then add a supported GGUF model to the Library. HoldSpeak detects
  valid local artifacts and reports runtime readiness rather than treating a
  filename as proof that a model will run.
- **MLX on Apple Silicon.** Install the `dictation-mlx` extra for MLX text
  support. Model Library can detect MLX safetensors artifacts. Today they remain
  unavailable for Thoughts, even when the artifact is present, and stay useful
  only on the paths that support them.
- **A provider or another device.** Connect a hosted provider, define an
  OpenAI-compatible endpoint, or connect a paired device. Install
  `dictation-openai` when the dictation path needs an OpenAI-compatible
  endpoint. A keyless self-hosted endpoint needs no key.

For a provider draft, enter its label, model identity, and required connection
information in the Library. The Library creates the public model record,
private deployment material, binding, and current readiness observation as one
owner action. It reports an unavailable runtime honestly. For example, a stored
key does not make an unsupported provider runtime ready.

### Readiness is current, not a promise

Use **Check** or **Try again** after changing a local runtime, model file,
provider, key, endpoint, or paired machine. Readiness belongs to the exact
bound deployment revision. It can report an unavailable artifact, missing
credential, unreachable endpoint, unavailable runtime, or offline device.
Fix the named issue in Model Library, then check again.

Availability is not routing. A model can stay in your Library while you choose
another model list in Assignments. Removing or revising a model that is assigned
may require you to repair the dependent Assignment first.

## Assignments: choose where work runs

Assignments is the owner surface for selecting models for registered HoldSpeak
jobs. Choose a compatible ordered model list of one to four models. The list is
saved as a whole. HoldSpeak does not combine part of your new list with an
inherited one or silently remove an incompatible entry.

You can set a model list for a capability group, an individual capability, or an
eligible saved item. More specific scope wins. **Use default**
clears the current row and reveals the next complete compatible model list. The
editor previews compatibility before it saves. It can retain a valid choice
that is temporarily not ready, then name the repair when work starts.

You do not choose a model at the point of use. Saved work and meetings ask for
their capability. HoldSpeak resolves the applicable Assignment and freezes the
resulting route at admission. Later Library or Assignment edits affect later
work, not a run already in progress.

## Provider and runtime notes

HoldSpeak does not require a particular model family. Select a model that fits
your hardware and the capability's requirements. Structured output, tool use,
context size, supported modalities, runtime availability, and boundary are
checked against the capability before a model list can execute.

For local work, install only the optional runtime you use:

```bash
uv pip install -e '.[dictation-llama]'   # local GGUF runtime
uv pip install -e '.[dictation-mlx]'     # MLX text support on Apple Silicon
uv pip install -e '.[dictation-openai]'  # OpenAI-compatible dictation path
```

For a headless provider key, `HOLDSPEAK_PROFILE_<ID>_KEY` remains a fallback.
Use the Model Library for the ordinary owner workflow. It keeps secret material
out of model records, Library projections, receipts, and error messages.

## When a model will not run

| What you see | What to do |
|---|---|
| A model is listed but not ready | Open Model Library, read the readiness reason, fix it, then check again. |
| An Assignment needs attention | Choose a compatible, enabled model in Assignments or clear it with **Use default**. |
| A local artifact is detected but unavailable | Install the required runtime and verify the artifact and runtime again. |
| An endpoint is unavailable | Check the endpoint, required key, and network reachability, then run **Check**. |
| A capability cannot use your model | Use a model whose declared modalities, context, structured output, tools, and boundary meet that capability. |

## See also

- [Intelligence Router architecture](internal/ARCHITECTURE_INTELLIGENCE_ROUTER.md): capability, routing, freeze, execution, and receipt mechanics.
- [Security & Privacy](SECURITY.md): local custody and egress posture.
- [Dictation Pipeline Setup](DICTATION_PIPELINE_GUIDE.md): where a configured dictation model is used.
- [Meeting Mode Guide](MEETING_MODE_GUIDE.md): where a configured meeting model is used.
