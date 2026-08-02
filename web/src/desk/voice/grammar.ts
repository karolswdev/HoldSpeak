export interface VoiceIntentDef {
  id: string;
  patterns: RegExp[];
  requiresLLM: boolean;
  verbId: string | null;
  extract: (transcript: string) => Record<string, unknown>;
  ghost: (ctx: { hasSelection: boolean }) => string | null;
}

export interface VoiceGrammar {
  surfaceKind: string;
  intents: VoiceIntentDef[];
  dictationFallback: boolean;
}

export interface VoiceProposal {
  transcript: string;
  intentId: string;
  verbId: string | null;
  params: Record<string, unknown>;
  confidence: number;
  requiresLLM: boolean;
}
