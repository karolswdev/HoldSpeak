# Models and assignments

**Settings, Models** is where HoldSpeak keeps intelligence available. Adding,
downloading, or connecting a model makes it available. It does not choose work
for that model.

**Settings, Assignments** is where the owner chooses which available models do
HoldSpeak jobs. The server checks the capability, readiness, and saved boundary
before an assignment can be saved. A missing key, unsupported capability, or
unavailable model stays visible with a named repair. HoldSpeak never silently
chooses another model.

When work starts, HoldSpeak freezes the selected assignment into an immutable
plan. Editing an assignment affects the next run only. The receipt records the
frozen primary, every attempt, any fallback reason, the actual model and
boundary, and the terminal result without consulting today's settings.

Keys are written only through the owner-only secret subresource. Settings reads
report whether a key is present, never its value. Keys do not appear in sync,
ordinary API responses, receipts, or the database.
