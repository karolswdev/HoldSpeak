# How to turn my dictation into a coding-agent task

When I dictate a request, rewrite it as a precise task for a coding agent
working in this repo. Always:

- Name the concrete files/modules to touch (use the paths in context.md).
- State the change as an imperative spec, not a paraphrase of my rambling.
- Add a short **Acceptance criteria** checklist the agent can verify.
- Call out the invariants in memory.md that the change must not break.
- Prefer a new ledger entry over mutating an existing row — entries are
  append-only.
- If money can be double-counted, say so explicitly and require a test.

Keep it tight. No preamble, no "Sure, here's…". Just the task.
