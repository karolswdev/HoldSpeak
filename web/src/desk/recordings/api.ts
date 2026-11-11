/* Recordings' typed reads and writes. ListApp reconciles the window's rows;
 * useRecordingFrames keeps the shared capture lamp current on every view. */
import { useEffect } from "react";
import { apiFetch } from "../../lib/api";
import { useListApp } from "../surface";
import { authToken } from "../../lib/auth";
import { useOptionalRuntimeBus } from "../../runtime/RuntimeBus";
import { applyRecording } from "./capture";
import type { Recording, RecordingStateFrame, RecordingsPayload } from "./types";

export const EMPTY_PAYLOAD: RecordingsPayload = {
  recordings: [],
  usage: { bytes: 0, keep_days: 30 },
  links: { tailnet: null, local: null },
  encoder: "ffmpeg",
  folder: "",
};

export async function readRecordings(): Promise<RecordingsPayload> {
  const body = await apiFetch<RecordingsPayload>("/api/recordings");
  if (!body || !Array.isArray(body.recordings)) throw new Error("The recordings list could not be read");
  return body;
}

function post<T>(path: string): Promise<T> {
  return apiFetch<T>(path, { method: "POST", json: {} });
}

const at = (id: string) => `/api/recordings/${encodeURIComponent(id)}`;
export const retryRecording = (id: string) => post<Recording>(`${at(id)}/retry`);
export const shareRecording = (id: string) => post<Recording>(`${at(id)}/share`);
export const unshareRecording = (id: string) => post<Recording>(`${at(id)}/unshare`);
export const parkRecording = (id: string) => post<{ id: string; parked: boolean }>(`${at(id)}/park`);
export const openRecordingsFolder = () => post<{ opened: boolean }>("/api/recordings/folder/open");

/** The desk's own Play: the hub's video with the owner token (a `<video>`
 *  cannot send a header). */
export function videoUrl(id: string): string {
  const token = authToken();
  return `${at(id)}/video${token ? `?token=${encodeURIComponent(token)}` : ""}`;
}

export function posterUrl(id: string): string {
  const token = authToken();
  return `${at(id)}/poster${token ? `?token=${encodeURIComponent(token)}` : ""}`;
}

/** `1.2 GB`, `38 MB`, `640 KB`. */
export function sizeWords(bytes: number): string {
  const value = Math.max(0, Number(bytes) || 0);
  if (value >= 1e9) return `${(value / 1e9).toFixed(1)} GB`;
  if (value >= 1e6) return `${Math.round(value / 1e6)} MB`;
  if (value >= 1e3) return `${Math.round(value / 1e3)} KB`;
  return `${value} B`;
}

/** `0:42`, `12:05`, `1:02:10`. */
export function lengthWords(seconds: number): string {
  const whole = Math.max(0, Math.floor(Number(seconds) || 0));
  const h = Math.floor(whole / 3600);
  const m = Math.floor((whole % 3600) / 60);
  const s = String(whole % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${s}` : `${m}:${s}`;
}

const recordingKey = (row: Recording) => row.id;
const findRecording = (row: Recording, query: string) => `${row.title} ${new Date(row.started_ts * 1000).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}`.toLocaleLowerCase().includes(query);
const readList = async () => { const payload = await readRecordings(); return { ...payload, rows: payload.recordings }; };

export function useRecordings() {
  const app = useListApp({ initialPage: { ...EMPTY_PAYLOAD, rows: [] as Recording[] }, read: readList, keyOf: recordingKey, search: findRecording });
  const subscribe = useOptionalRuntimeBus()?.subscribe;
  useEffect(() => { app.rows.forEach(applyRecording); }, [app.page]);
  useEffect(() => subscribe?.("recording_state", frame => {
    const data = frame.data as RecordingStateFrame | undefined;
    if (!data?.recording?.id) return;
    if (data.reason === "parked") app.drop(data.recording.id); else app.apply(data.recording);
  }), [subscribe, app.apply, app.drop]);
  return { ...app, payload: { ...(app.page ?? EMPTY_PAYLOAD), recordings: app.rows } };
}

/** Every view: another view's live recording reaches the capture store, from
 *  the first read and from each `recording_state` frame. */
export function useRecordingFrames(): void {
  const bus = useOptionalRuntimeBus();
  const subscribe = bus?.subscribe;
  useEffect(() => {
    let alive = true;
    void readRecordings()
      .then((body) => { if (alive) body.recordings.filter((row) => row.state === "recording").forEach(applyRecording); })
      .catch(() => undefined);
    return () => { alive = false; };
  }, []);
  useEffect(() => {
    if (!subscribe) return;
    return subscribe("recording_state", (frame) => {
      applyRecording((frame.data as RecordingStateFrame | undefined)?.recording);
    });
  }, [subscribe]);
}
