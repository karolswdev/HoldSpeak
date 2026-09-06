import { apiFetch } from "../lib/api";

export interface InterviewFact {
  id: string;
  section: string;
  text: string;
  basis: "stated" | "inferred";
  quote: string;
  source_message_id: string;
}

export interface InterviewSuggestion {
  id: string;
  section: string;
  title: string;
  benefit: string;
  behavior: string;
  basis: string;
  prerequisites: string;
  fact_ids: string[];
  feasibility: "manual" | "needs_input" | "needs_connection" | "unsupported_idea";
  disposition: "proposed" | "kept" | "deferred" | "dismissed" | "try" | "stale";
}

export interface InterviewState {
  thread_id: string;
  revision: number;
  section: string;
  status: string;
  facts: Record<string, InterviewFact>;
  suggestions: Record<string, InterviewSuggestion>;
  sections: Array<{ id: string; name: string; handoff: string }>;
}

export async function interviewCommand(state: InterviewState, event: Record<string, unknown>): Promise<InterviewState> {
  return apiFetch(`/api/threads/${encodeURIComponent(state.thread_id)}/interview`, {
    method: "POST",
    json: { command_id: crypto.randomUUID(), expected_revision: state.revision, event },
  });
}
