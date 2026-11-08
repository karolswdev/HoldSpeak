// Parked 2026-11-08 (Lane W, "a feature with no way in"): eleven registry
// verbs that no menu, palette row, shortcut or live caller reached.
// - desk.new-thread: palette: false and no menu since Betterment Q4 ("kept
//   for old callers"); no caller remained.
// - thread.*: the ThreadComposer's slash commands (HS-153-02); every run was
//   a no-op and the composer was their only reader, parked in #1975.
// They were entries of VERBS in desk/verbRegistry.ts; kept here as text.
/* eslint-disable */
// @ts-nocheck
export const PARKED_VERBS = [
  // Betterment Q4: a new thread is a new Ask; the thread is kept when the
  // first question is answered. The registry verb remains for old callers,
  // but is parked from every menu face.
  {
    id: "desk.new-thread",
    label: "New Thread",
    scope: "floor",
    glyph: KIND_GLYPH.thread,
    palette: false,
    keywords: ["create", "chat", "conversation"],
    ghost: never,
    run: () => useDesk.getState().openAskThread(null),
  },
  // ── Thread slash verbs (HS-153-02) ─────────────────────────────────
  // These are the verb-ids for the ThreadComposer's / commands.
  // The composer owns the trigger; the pullout owns the handler.
  {
    id: "thread.keep",
    label: "Keep as note",
    scope: "thread",
    palette: false,
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.fork",
    label: "Fork from here",
    scope: "thread",
    palette: false,
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.stop",
    label: "Stop generation",
    scope: "thread",
    palette: false,
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.new",
    label: "New thread",
    scope: "thread",
    palette: false,
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.mode",
    label: "Switch mode",
    scope: "thread",
    palette: false,
    keywords: ["desk", "chase", "draft", "plan"],
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.prompt",
    label: "Insert prompt",
    scope: "thread",
    palette: false,
    keywords: ["saved", "template"],
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.tools",
    label: "Show tools",
    scope: "thread",
    palette: false,
    keywords: ["palette", "capabilities"],
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.todo",
    label: "Add todo",
    scope: "thread",
    palette: false,
    keywords: ["task", "action"],
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.compact",
    label: "Compact thread",
    scope: "thread",
    palette: false,
    keywords: ["summarize", "compress"],
    ghost: never,
    run: () => {},
  },
  {
    id: "thread.guardrail",
    label: "Toggle guardrail",
    scope: "thread",
    palette: false,
    keywords: ["guard", "safety"],
    ghost: never,
    run: () => {},
  },
];
