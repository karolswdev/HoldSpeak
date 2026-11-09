/* The People app's hub calls (the native face, 2026-11-08): every read and
 * write the face makes, one typed function each. People's verbs are
 * declared operations (holdspeak/people_operations.py) or the people
 * routes that still stand by hand (holdspeak/web/routes/people.py); the
 * PR that made this file lists each one. Writes are the owner's; agents
 * read People over MCP (owner ruling 2026-10-06). */
import { apiFetch } from "../../lib/api";

const P = "/api/people";
const person = (id: string) => `${P}/relationships/${encodeURIComponent(id)}`;
const commitment = (id: string) => `${P}/commitments/${encodeURIComponent(id)}`;
const post = <T = unknown>(path: string, json: unknown = {}) => apiFetch<T>(path, { method: "POST", json });
const remove = <T = unknown>(path: string, json?: unknown) => apiFetch<T>(path, { method: "DELETE", ...(json === undefined ? {} : { json }) });

/* ── reads ── */
export const readReadiness = <T>() => apiFetch<T>(`${P}/readiness`);
/** PHILO-17 (MUST 4): each row carries its owed counts. */
export const readRoster = <T>() => apiFetch<{ relationships?: T[] }>(`${P}/relationships?counts=1`);
export const readSuggestions = <T>() => apiFetch<{ suggestions?: T[] }>(`${P}/suggestions`);
export const readPerson = <T>(id: string) => apiFetch<{ relationship: T }>(person(id));
export const readOneOnOnes = <T>(id: string) => apiFetch<{ one_on_ones: T[] }>(`${person(id)}/one-on-ones`);
export const readBrief = <T>(id: string) => apiFetch<{ brief: T }>(`${person(id)}/brief`);
export const readExecution = <T>(id: string) => apiFetch<{ items?: T[] }>(`${commitment(id)}/execution`);
/** The Door's upcoming calendar rows (the next 1:1, the series picker). */
export const readUpcoming = <T>() => apiFetch<{ upcoming?: T[] }>("/api/door");
export const readProjects = <T>() => apiFetch<{ projects?: T[] }>("/api/projects");
export const readWorkbenches = <T>() => apiFetch<{ workbenches?: T[] }>("/api/workbenches");

/* ── writes (the owner's) ── */
export const setupPeople = () => post(`${P}/setup`);
export const createPerson = (display_name: string, relationship_kind: string) => post(`${P}/relationships`, { display_name, relationship_kind });
export const addSuggestion = (key: string) => post(`${P}/suggestions/add`, { key });
export const hideSuggestion = (key: string) => post(`${P}/suggestions/hide`, { key });
export const archivePerson = (id: string) => post(`${person(id)}/archive`);
export const createOneOnOne = <T>(id: string) => post<{ one_on_one: T }>(`${person(id)}/one-on-ones`, { visibility: "shared_intent" });
export const addAgendaItem = (sessionId: string, body: string) =>
  post(`${P}/one-on-ones/${encodeURIComponent(sessionId)}/agenda`, { body, visibility: "shared_intent", state: "open", source: { kind: "manual" } });
export const removeAgendaItem = (id: string) => post(`${P}/agenda/${encodeURIComponent(id)}/transition`, { to: "removed" });
export const createRequest = <T>(id: string, body: string) =>
  post<T>(`${person(id)}/requests`, { body, visibility: "shared_intent", source: { kind: "manual" } });
export const acceptRequest = <T>(id: string) => post<T>(`${P}/requests/${encodeURIComponent(id)}/accept`);
export const createOwed = (id: string, body: string) => post(`${person(id)}/owed`, { body, visibility: "shared_intent" });
export const commitmentDone = (id: string) => post(`${commitment(id)}/transition`, { verb: "done" });
export const sendToWorkbench = (id: string, workbench_id: string) => post(`${commitment(id)}/workbench`, { workbench_id });
export const satisfyCommitment = (id: string, rationale: string) => post(`${commitment(id)}/satisfy`, { rationale });
export const createNote = (id: string, note: { topic: string; body: string; visibility: string }) => post(`${person(id)}/notes`, note);
export const linkProject = (id: string, projectId: string) => post(`${person(id)}/projects/${encodeURIComponent(projectId)}`);
export const unlinkProject = (id: string, projectId: string) => remove(`${person(id)}/projects/${encodeURIComponent(projectId)}`);
export const linkSeries = (id: string, uid: string, source_id: string, label: string) => post(`${person(id)}/calendar-links`, { uid, source_id, label });
export const unlinkSeries = (id: string, uid: string, source_id: string) => remove(`${person(id)}/calendar-links`, { uid, source_id });
export const linkAlias = (id: string, alias: string) => post(`${person(id)}/owner-aliases`, { alias });
export const unlinkAlias = (id: string, alias: string) => remove(`${person(id)}/owner-aliases`, { alias });
/** A meeting action's Done (the follow-through card). */
export const completeAction = (cardId: string) => post("/api/follow-through/complete", { card_id: cardId, verb: "done", payload: {} });
/** Nudge keeps the drafted message as a note; he presses Send. */
export const keepNudge = (title: string, body_markdown: string) =>
  post<{ note?: { id?: string } }>("/api/notes", { title, body_markdown, tags: ["nudge"] });
