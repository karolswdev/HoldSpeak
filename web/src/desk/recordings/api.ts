/* Recordings (RECORDINGS-DESIGN-2026-10-28 §4): the faces' reads and writes.
 *
 * `useRecordings` holds the window's copy; a `recording_state` frame replaces
 * the row it names (a parked row leaves). `useRecordingFrames` keeps the
 * capture store's view of another view's live recording: the menu-bar lamp
 * mounts it on every view. */
import { useCallback, useEffect, useState } from "react";
import { ApiError, apiFetch, readableError } from "../../lib/api";
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
  try {
    const body = await apiFetch<RecordingsPayload>("/api/recordings");
    return body && Array.isArray(body.recordings) ? body : EMPTY_PAYLOAD;
  } catch (error) {
    // A hub without the Recordings slice: nothing recorded yet.
    if (error instanceof ApiError && error.status === 404) return EMPTY_PAYLOAD;
    throw error;
  }
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

export interface RecordingsState {
  loading: boolean;
  error: string;
  payload: RecordingsPayload;
  reload(): Promise<void>;
  apply(row: Recording): void;
  drop(id: string): void;
}

export function useRecordings(): RecordingsState {
  const bus = useOptionalRuntimeBus();
  const subscribe = bus?.subscribe;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [payload, setPayload] = useState<RecordingsPayload>(EMPTY_PAYLOAD);

  const reload = useCallback(async () => {
    try {
      const next = await readRecordings();
      setPayload(next);
      setError("");
      next.recordings.forEach(applyRecording);
    } catch (failure) {
      setError(readableError(failure));
    } finally {
      setLoading(false);
    }
  }, []);

  const apply = useCallback((row: Recording) => {
    setPayload((now) => {
      const known = now.recordings.some((item) => item.id === row.id);
      const recordings = known
        ? now.recordings.map((item) => (item.id === row.id ? row : item))
        : [row, ...now.recordings];
      return { ...now, recordings };
    });
  }, []);

  const drop = useCallback((id: string) => {
    setPayload((now) => ({ ...now, recordings: now.recordings.filter((item) => item.id !== id) }));
  }, []);

  useEffect(() => { void reload(); }, [reload]);
  useEffect(() => {
    if (!subscribe) return;
    return subscribe("recording_state", (frame) => {
      const data = frame.data as RecordingStateFrame | undefined;
      const row = data?.recording;
      if (!row?.id) return;
      if (data?.reason === "parked") drop(row.id);
      else apply(row);
    });
  }, [subscribe, apply, drop]);

  return { loading, error, payload, reload, apply, drop };
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
