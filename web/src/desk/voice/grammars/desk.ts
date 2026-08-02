import type { VoiceGrammar } from "../grammar";

export const deskVoiceGrammar: VoiceGrammar = {
  surfaceKind: "desk",
  intents: [
    {
      id: "open",
      patterns: [/\bopen\s+(.+)/i],
      requiresLLM: false,
      verbId: "desk.open",
      extract: (transcript) => ({
        query: transcript.match(/open\s+(.+)/i)?.[1]?.trim() ?? "",
      }),
      ghost: () => null,
    },
    {
      id: "create-note",
      patterns: [/\b(create|new)\s+(a\s+)?note\b/i],
      requiresLLM: false,
      verbId: "desk.new-note",
      extract: () => ({}),
      ghost: () => null,
    },
    {
      id: "attention",
      patterns: [/\bwhat.s\s+(on\s+fire|urgent|attention)\b/i],
      requiresLLM: false,
      verbId: "desk.attention",
      extract: () => ({}),
      ghost: () => null,
    },
  ],
  dictationFallback: false,
};
