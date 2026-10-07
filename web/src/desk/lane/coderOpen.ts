/** PHILO-14 C2 — a coder object that belongs to a launch opens the agent's
 * lane, not the coder card. The lane module answers first (registered when
 * the lane host mounts); with no answer the card opens as before. No imports:
 * the store reads this without a cycle. */
type Answer = (coder: { agent?: string | null; sessionId?: string | null; id: string }) => boolean;

let answer: Answer | null = null;

export function answerCoderOpenFirst(fn: Answer): () => void {
  answer = fn;
  return () => {
    if (answer === fn) answer = null;
  };
}

/** True when the lane took the open. */
export function coderOpenFirst(coder: { agent?: string | null; sessionId?: string | null; id: string }): boolean {
  return answer ? answer(coder) : false;
}
