import type { VoiceGrammar } from "../grammar";

export const workbenchVoiceGrammar: VoiceGrammar = {
  surfaceKind: "workbench",
  intents: [
    {
      id: "add-item",
      patterns: [
        /\b(?:add|new\s+item)\s+(.+?)(?:\s+priority\s+(\d))?$/i,
      ],
      requiresLLM: false,
      verbId: null,
      extract: (transcript) => {
        const m = transcript.match(
          /(?:add|new\s+item)\s+(.+?)(?:\s+priority\s+(\d))?$/i,
        );
        return {
          title: m?.[1]?.replace(/,?\s*priority\s+\d$/i, "").trim() ?? "",
          priority: m?.[2] ? Number(m[2]) : 3,
        };
      },
      ghost: () => null,
    },
    {
      id: "run",
      patterns: [
        /\b(?:run|run\s+this\s+workbench|go)\b/i,
      ],
      requiresLLM: false,
      verbId: null,
      extract: () => ({}),
      ghost: () => null,
    },
    {
      id: "dismiss",
      patterns: [/\bdismiss\s+(.+)/i],
      requiresLLM: false,
      verbId: null,
      extract: (transcript) => ({
        query: transcript.match(/dismiss\s+(.+)/i)?.[1]?.trim() ?? "",
      }),
      ghost: () => null,
    },
    {
      id: "set-agent",
      patterns: [/\bset\s+agent\s+(?:to\s+)?(.+)/i],
      requiresLLM: false,
      verbId: null,
      extract: (transcript) => ({
        agentName: transcript.match(/set\s+agent\s+(?:to\s+)?(.+)/i)?.[1]?.trim() ?? "",
      }),
      ghost: () => null,
    },
    {
      id: "set-schedule",
      patterns: [
        /\bset\s+schedule\s+(?:to\s+)?(.+)/i,
        /\bschedule\s+(.+)/i,
      ],
      requiresLLM: false,
      verbId: null,
      extract: (transcript) => ({
        preset: (
          transcript.match(/set\s+schedule\s+(?:to\s+)?(.+)/i)?.[1] ??
          transcript.match(/schedule\s+(.+)/i)?.[1] ?? ""
        ).trim(),
      }),
      ghost: () => null,
    },
    {
      id: "clear-done",
      patterns: [/\bclear\s+(?:done|completed|finished)\b/i],
      requiresLLM: false,
      verbId: null,
      extract: () => ({}),
      ghost: () => null,
    },
  ],
  dictationFallback: true,
};
