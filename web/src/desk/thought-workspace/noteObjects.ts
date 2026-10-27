/* Note canvas A, step 4 (owner pick 2026-10-27): the objects a note names in
   its text. livePreview.ts draws them (glyph + ink, a peek card on hover,
   press opens the window); this module answers what the desk knows about
   each one, and offers the people and Projects for the @ and # completion.
   The note keeps plain Markdown (`[@Priya](person:<id>)`), so it stays
   portable; nothing here writes. */
import { apiFetch } from "../../lib/api";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";

export type NoteObjectKind = "person" | "project" | "decision" | "meeting" | "note" | "pr" | "jira";

export interface NoteObjectToken {
  kind: NoteObjectKind;
  /** The words in the text (`@Priya`, `#Payments`, `PR #1482`, `PAY-311`). */
  label: string;
  /** The desk ref (`person:p1`) or the outside url that the press opens. */
  href: string | null;
}

/** The peek card: the name, the kind word, one fact (a state or a date). */
export interface NoteObjectPeek {
  name: string;
  kind: string;
  fact?: string;
}

export interface NoteObjectChoice {
  id: string;
  name: string;
  detail?: string;
}

/** What the live preview asks of the desk. Tests pass their own. */
export interface NoteObjects {
  peek(token: NoteObjectToken): NoteObjectPeek;
  people(): Promise<NoteObjectChoice[]>;
  projects(): NoteObjectChoice[];
  /** Resolves when a slow read (the People roster) is in, so the peeks can
   *  draw again with its facts. */
  ready?(): Promise<unknown>;
}

const KIND_WORD: Record<NoteObjectKind, string> = {
  person: "Person",
  project: "Project",
  decision: "Decision",
  meeting: "Meeting",
  note: "Note",
  pr: "Pull request",
  jira: "Jira issue",
};

const RELATIONSHIP_WORD: Record<string, string> = {
  direct_report: "Direct report", peer: "Peer", manager: "Manager", skip: "Skip level", stakeholder: "Stakeholder",
};

/** The glyph of a kind, at 20 px (the canvas's 14 px ink glyph). */
export function objectGlyph(kind: NoteObjectKind): string {
  const sprite = kind === "jira" ? "action" : kind;
  return spriteUrl(sprite, `note-object-${kind}`, "rest", null, 20);
}

/** The kind of a desk ref the note links to, or null. */
export function refKind(href: string): NoteObjectKind | null {
  const prefix = /^([a-z_]+):\S/i.exec(href)?.[1]?.toLowerCase();
  switch (prefix) {
    case "person": case "people": return "person";
    case "project": return "project";
    case "decision": case "desk_decision": case "decision_record": return "decision";
    case "meeting": return "meeting";
    case "note": return "note";
    default: return null;
  }
}

const PR_URL = /^https?:\/\/(?:www\.)?github\.com\/([\w.-]+)\/([\w.-]+)\/pull\/(\d+)(?:[/?#]\S*)?$/i;

/** A GitHub pull request url: its repo and number. */
export function pullRequestOf(url: string): { repo: string; number: string } | null {
  const match = PR_URL.exec(url.trim());
  return match ? { repo: `${match[1]}/${match[2]}`, number: match[3] } : null;
}

function shortDate(value: string | null | undefined): string | undefined {
  if (!value) return undefined;
  const at = new Date(value);
  if (Number.isNaN(at.getTime())) return undefined;
  return at.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

const STATUS_WORD: Record<string, string> = {
  proposed: "Proposed", accepted: "Accepted", superseded: "Superseded", rejected: "Rejected", deprecated: "Deprecated",
};

let peopleRows: Array<{ id: string; name: string; kind?: string }> | null = null;
let peopleRead: Promise<Array<{ id: string; name: string; kind?: string }>> | null = null;

function readPeople(): Promise<Array<{ id: string; name: string; kind?: string }>> {
  if (peopleRows) return Promise.resolve(peopleRows);
  if (!peopleRead) {
    peopleRead = apiFetch<{ relationships?: Array<Record<string, unknown>> }>("/api/people/relationships")
      .then((answer) => {
        peopleRows = (answer?.relationships ?? [])
          .map((row) => ({ id: String(row.id ?? ""), name: String(row.display_name ?? ""), kind: typeof row.relationship_kind === "string" ? row.relationship_kind : undefined }))
          .filter((row) => row.id && row.name);
        return peopleRows;
      })
      .catch(() => {
        // People not set up: no people to offer. A later @ reads again.
        peopleRead = null;
        return [];
      });
  }
  return peopleRead;
}

/** Test seam: forget the People roster read. */
export function resetNoteObjectPeople(): void {
  peopleRows = null;
  peopleRead = null;
}

function idOf(href: string | null): string {
  return href ? href.slice(href.indexOf(":") + 1) : "";
}

/** The desk's own answers (the store, and the People roster). */
export const deskObjects: NoteObjects = {
  peek(token) {
    const kind = KIND_WORD[token.kind];
    const id = idOf(token.href);
    const desk = useDesk.getState();
    const plain = token.label.replace(/^[@#]/, "");
    switch (token.kind) {
      case "person": {
        const row = peopleRows?.find((person) => person.id === id);
        return { name: row?.name || plain, kind, fact: row?.kind ? RELATIONSHIP_WORD[row.kind] : undefined };
      }
      case "project": {
        const project = desk.projects.find((row) => row.id === id);
        if (!project) return { name: plain, kind };
        const changed = shortDate(project.updated_at);
        return { name: project.name || plain, kind, fact: project.is_archived ? "Archived" : changed ? `Changed ${changed}` : undefined };
      }
      case "meeting": {
        const meeting = (desk.items.meeting ?? []).find((row) => row.id === id);
        return { name: meeting?.title || plain, kind, fact: shortDate(meeting?.startedAt) };
      }
      case "decision": {
        const decision = (desk.items.decision ?? []).find((row) => row.id === id);
        return { name: decision?.title || plain, kind, fact: decision ? STATUS_WORD[decision.status] : undefined };
      }
      case "note": {
        const note = (desk.items.note ?? []).find((row) => row.id === id);
        return { name: note?.title || plain, kind, fact: shortDate(note?.createdAt) };
      }
      case "pr": {
        const pr = token.href ? pullRequestOf(token.href) : null;
        return { name: token.label, kind, fact: pr ? pr.repo : undefined };
      }
      case "jira":
        return { name: token.label, kind };
    }
  },
  people: () => readPeople().then((rows) => rows.map((row) => ({
    id: row.id, name: row.name, detail: row.kind ? RELATIONSHIP_WORD[row.kind] : undefined,
  }))),
  projects: () => useDesk.getState().projects
    .filter((project) => !project.is_archived && project.name)
    .map((project) => ({ id: project.id, name: project.name, detail: "Project" })),
  ready: () => readPeople(),
};
