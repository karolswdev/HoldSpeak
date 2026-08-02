import { runAsk } from "../ask";
import type { VoiceGrammar, VoiceIntentDef, VoiceProposal } from "./grammar";

export interface VoiceRouteInput {
  transcript: string;
  surfaceKind: string;
  selectionState: { hasSelection: boolean };
  grammar: VoiceGrammar;
}

const DICTATION: Omit<VoiceProposal, "transcript"> = {
  intentId: "dictation",
  verbId: null,
  params: {},
  confidence: 0,
  requiresLLM: false,
};

function proposalFor(
  transcript: string,
  intent: VoiceIntentDef,
  confidence: number,
): VoiceProposal {
  return {
    transcript,
    intentId: intent.id,
    verbId: intent.verbId,
    params: intent.extract(transcript),
    confidence,
    requiresLLM: intent.requiresLLM,
  };
}

function matches(transcript: string, intent: VoiceIntentDef) {
  return intent.patterns.some((pattern) => {
    pattern.lastIndex = 0;
    return pattern.test(transcript);
  });
}

function parseClassification(output: string): {
  intentId?: string;
  confidence?: number;
} | null {
  const json = output.match(/\{[\s\S]*\}/)?.[0];
  if (!json) return null;
  try {
    const parsed = JSON.parse(json) as Record<string, unknown>;
    return {
      intentId: typeof parsed.intentId === "string" ? parsed.intentId : undefined,
      confidence: typeof parsed.confidence === "number" ? parsed.confidence : undefined,
    };
  } catch {
    return null;
  }
}

/**
 * Stateless voice classifier. Local commands never leave the device. An LLM
 * is consulted only for an explicitly LLM-backed grammar candidate; it never
 * executes an action and its result remains an armed proposal.
 */
export async function routeVoiceIntent({
  transcript,
  surfaceKind,
  selectionState,
  grammar,
}: VoiceRouteInput): Promise<VoiceProposal> {
  const spoken = transcript.trim();
  if (!spoken || grammar.surfaceKind !== surfaceKind) {
    return { transcript, ...DICTATION };
  }

  const candidates = grammar.intents.filter((intent) => matches(spoken, intent));
  const local = candidates.find((intent) => !intent.requiresLLM);
  if (local) return proposalFor(spoken, local, 0.9);

  const llmCandidates = candidates.filter((intent) => intent.requiresLLM);
  if (!llmCandidates.length) return { transcript, ...DICTATION };

  const result = await runAsk({
    lens: "Voice intent",
    context: [],
    prompt: [
      "Classify this voice command for the current DeskOS surface.",
      `Surface: ${surfaceKind}`,
      `Text selected: ${selectionState.hasSelection ? "yes" : "no"}`,
      `Transcript: ${spoken}`,
      "Allowed intent IDs: " + llmCandidates.map((intent) => intent.id).join(", "),
      'Reply with JSON only: {"intentId":"allowed ID or dictation","confidence":0 to 1}.',
      "Choose dictation when no allowed action is clear.",
    ].join("\n"),
  });
  if (!result.ok) return { transcript, ...DICTATION };

  const classified = parseClassification(result.output);
  const intent = llmCandidates.find((candidate) => candidate.id === classified?.intentId);
  const confidence = Math.max(0, Math.min(1, Number(classified?.confidence) || 0));
  return intent && confidence >= 0.5
    ? proposalFor(spoken, intent, confidence)
    : { transcript, ...DICTATION };
}
