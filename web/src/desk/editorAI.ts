export const AI_VERBS = {
  rewrite: {
    label: "Rewrite",
    prompt: "Rewrite the following text more concisely while preserving its meaning:\n\n{text}",
  },
  expand: {
    label: "Expand",
    prompt: "Expand the following text with more detail and explanation:\n\n{text}",
  },
  summarize: {
    label: "Summarize",
    prompt: "Summarize the following text in 1-2 sentences:\n\n{text}",
  },
  continue: {
    label: "Continue",
    prompt: "Continue writing naturally from where this text leaves off:\n\n{text}",
  },
} as const;

export type EditorAIVerb = keyof typeof AI_VERBS;
