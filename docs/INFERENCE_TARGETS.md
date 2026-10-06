# Models and assignments

Use the **Concierge** (**Settings > Models**) to make models available and to assign them to jobs. See [Models](MODELS.md) for the steps.

- Adding, downloading, or connecting a model makes it available. It does not give that model any work.
- An assignment chooses which available models do a job. The server checks the capability, the readiness, and the saved boundary before it saves an assignment.
- A missing key, an unsupported capability, or an unavailable model stays visible with a named repair. HoldSpeak never chooses another model for you.
- When work starts, HoldSpeak freezes the assignment into an immutable plan. A later edit affects the next run only.
- The Receipt records the frozen primary model, every attempt, the fallback reason, the model and host that served the work, and the result.
- Keys go in only through the owner-only secret field. Settings reads report whether a key is present, never its value. Keys do not appear in sync, API responses, Receipts, or the database.

Contributors: see [Model runtime](MODEL_RUNTIME.md).
