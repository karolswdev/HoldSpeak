/* PG-LANG LANG5 (PROGRAM-LANGUAGE-2026-10-31 §4.2): the Program window's
 * voice grammar. Its one intent is `shape`: a spoken change to the Program
 * in front ("program: put step 4 on Codex", or the change alone). The
 * Program window's shaping bar is the window's one mic authority; what it
 * hears goes to the hub's program.shape (POST …/shape) as a typed sentence
 * does, and the change rows are the proposal (Apply is the confirm; the
 * proposal strip is not used: "voice arms; it does not fire"). The words
 * are read by rule here: the leading "program" is the address, never part
 * of the sentence. The address is a closed form, so the router matches it
 * locally (no classification call); the shaping itself is the hub's engine. */
import type { VoiceGrammar } from "../grammar";

const ADDRESS = /^\s*(?:hey\s+)?program\b[\s,:;.\-–—]*/i;

/** The sentence of an utterance: "program: step 4 on Codex" → "step 4 on
 *  Codex"; an utterance with no address is the sentence itself. */
export function programSentence(transcript: string): string {
  return String(transcript ?? "").replace(ADDRESS, "").trim();
}

/** True when the utterance addresses the Program ("program: …"). */
export function addressesProgram(transcript: string): boolean {
  return ADDRESS.test(String(transcript ?? "")) && Boolean(programSentence(transcript));
}

export const programVoiceGrammar: VoiceGrammar = {
  surfaceKind: "program",
  intents: [
    {
      id: "shape",
      patterns: [/^\s*(?:hey\s+)?program\b[\s,:;.\-–—]+\S/i],
      requiresLLM: false,
      verbId: null,
      extract: (transcript) => ({ sentence: programSentence(transcript) }),
      ghost: () => "Say a change to the program",
    },
  ],
  dictationFallback: true,
};
