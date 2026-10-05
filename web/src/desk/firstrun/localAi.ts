/* First run C1 — the "Set up local AI" client.
 *
 * The contract is PR #856's (holdspeak/services/local_ai_setup_service.py
 * there): GET/POST /api/setup/local-ai and POST /api/setup/local-ai/cancel.
 * The fields this face reads: `state`, `files[].key|label|size_bytes|
 * on_device|url`, `bytes_total`, `bytes_done`, `egress.destination`,
 * `error`, `error_code`. Every file `key: "whisper"` on the device is the
 * moment the First words card lights: #856 recomputes `on_device` from the
 * disk on every read and downloads in plan order (whisper, embed, starter),
 * so the speech model lands first. */
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import type { PlanStep } from "../surface";

export type LocalAiState =
  | "not_started"
  | "downloading"
  | "failed"
  | "ready"
  | "needs_runtime";

export interface LocalAiFile {
  key: string;
  label: string;
  filename?: string;
  url?: string;
  size_bytes: number;
  on_device: boolean;
}

export interface LocalAiStatus {
  state: LocalAiState;
  files: LocalAiFile[];
  bytes_total: number;
  bytes_done: number;
  percent?: number;
  egress?: { destination: string; files?: number; bytes?: number } | null;
  error?: string;
  error_code?: string;
}

export const LOCAL_AI_PATH = "/api/setup/local-ai";

/** The three groups of the face, in download order. */
export const GROUPS = [
  { key: "whisper", glyph: "◖", name: "Speech" },
  { key: "embed", glyph: "≋", name: "Meaning search" },
  { key: "starter", glyph: "◆", name: "Chat" },
] as const;

export interface LocalAiGroup {
  key: string;
  glyph: string;
  name: string;
  model: string;
  bytes: number;
  onDevice: boolean;
}

/** `142 MB`, `2.7 GB` (decimal units, as the download sizes are stated). */
export function formatBytes(bytes: number): string {
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
  return `${Math.max(1, Math.round(bytes / 1e6))} MB`;
}

/** The groups the face shows: one row per key, every file of it summed. */
export function groupsOf(status: LocalAiStatus | null): LocalAiGroup[] {
  const files = status?.files ?? [];
  const known = GROUPS.map((group): LocalAiGroup | null => {
    const own = files.filter((file) => file.key === group.key);
    if (!own.length) return null;
    return {
      key: group.key,
      glyph: group.glyph,
      name: group.name,
      model: own[0].label,
      bytes: own.reduce((sum, file) => sum + (file.size_bytes || 0), 0),
      onDevice: own.every((file) => file.on_device),
    };
  });
  return known.filter((group): group is LocalAiGroup => group !== null);
}

/** Speech is on this device: the First words card lights. */
export function speechReady(status: LocalAiStatus | null): boolean {
  const speech = (status?.files ?? []).filter((file) => file.key === "whisper");
  return speech.length > 0 && speech.every((file) => file.on_device);
}

/** Bytes still to download (the size on the one press). */
export function missingBytes(status: LocalAiStatus | null): number {
  return (status?.files ?? [])
    .filter((file) => !file.on_device)
    .reduce((sum, file) => sum + (file.size_bytes || 0), 0);
}

/** The host the files come from, upper case (the egress chip). */
export function sourceHost(status: LocalAiStatus | null): string {
  const named = status?.egress?.destination;
  if (named) return named.toUpperCase();
  const file = (status?.files ?? []).find((item) => item.url);
  try {
    return file?.url ? new URL(file.url).host.toUpperCase() : "";
  } catch {
    return "";
  }
}

/** The ProgressPlan steps of a run (or a stopped run).
 *
 * `bytes_done` counts every byte this run fetched, the finished files too.
 * The finished files are `on_device` now, so the bytes of the file in
 * progress are `bytes_done` less what already landed in this run. */
export function planSteps(status: LocalAiStatus, rate: string | null): PlanStep[] {
  const groups = groupsOf(status);
  const remaining = groups.filter((g) => !g.onDevice).reduce((s, g) => s + g.bytes, 0);
  const landed = Math.max(0, (status.bytes_total || 0) - remaining);
  const current = Math.max(0, (status.bytes_done || 0) - landed);
  const runningKey = groups.find((g) => !g.onDevice)?.key;
  const failed = status.state === "failed";
  return groups.map((group) => {
    if (group.onDevice) {
      return { id: group.key, label: group.name, status: "done", progress: 1, rate: formatBytes(group.bytes) };
    }
    if (group.key === runningKey && failed) {
      // A stopped run reads no byte count (#856 reports bytes only while it
      // downloads): the step says it stopped and how big it is.
      return { id: group.key, label: group.name, status: "failed", rate: formatBytes(group.bytes) };
    }
    if (group.key === runningKey) {
      const progress = group.bytes ? Math.min(1, current / group.bytes) : 0;
      // The amount done in the unit of the whole: `1.1 / 2.7 GB`, `40 / 142 MB`.
      const done = group.bytes >= 1e9 ? (current / 1e9).toFixed(1) : String(Math.round(current / 1e6));
      const amount = `${done} / ${formatBytes(group.bytes)}`;
      return {
        id: group.key,
        label: group.name,
        status: "running",
        progress,
        rate: rate ? `${amount} · ${rate}` : amount,
      };
    }
    return { id: group.key, label: group.name, status: "queued", rate: formatBytes(group.bytes) };
  });
}

/** `46 MB/s` from two reads of `bytes_done`. */
export function rateOf(prev: { at: number; done: number } | null, at: number, done: number): string | null {
  if (!prev || at <= prev.at || done <= prev.done) return null;
  const perSecond = ((done - prev.done) / (at - prev.at)) * 1000;
  return `${Math.max(1, Math.round(perSecond / 1e6))} MB/s`;
}

export type LocalAiRead =
  | { kind: "loading" }
  | { kind: "ok"; status: LocalAiStatus }
  | { kind: "unread"; reason: string };

const POLL_MS = 1000;

/** The Local AI card's state: one read, a poll while it downloads. */
export function useLocalAi() {
  const [read, setRead] = useState<LocalAiRead>({ kind: "loading" });
  const [rate, setRate] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [finishedAt, setFinishedAt] = useState<string | null>(null);
  const last = useRef<{ at: number; done: number } | null>(null);
  const sawRun = useRef(false);
  const mounted = useRef(true);

  const accept = useCallback((status: LocalAiStatus) => {
    if (!mounted.current) return;
    const now = Date.now();
    if (status.state === "downloading") {
      sawRun.current = true;
      const next = rateOf(last.current, now, status.bytes_done || 0);
      if (next) setRate(next);
      last.current = { at: now, done: status.bytes_done || 0 };
    } else {
      last.current = null;
      setRate(null);
      if (status.state === "ready" && sawRun.current) {
        sawRun.current = false;
        setFinishedAt(
          new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false }),
        );
      }
    }
    setRead({ kind: "ok", status });
  }, []);

  const refresh = useCallback(async () => {
    try {
      accept(await apiFetch<LocalAiStatus>(LOCAL_AI_PATH));
    } catch (error) {
      if (mounted.current) setRead({ kind: "unread", reason: readableError(error) });
    }
  }, [accept]);

  const act = useCallback(
    async (path: string) => {
      setBusy(true);
      try {
        accept(await apiFetch<LocalAiStatus>(path, { method: "POST" }));
      } catch {
        // A refusal (no runtime, no disk) is stored on the hub: the next
        // read names it on the card.
        await refresh();
      } finally {
        if (mounted.current) setBusy(false);
      }
    },
    [accept, refresh],
  );

  useEffect(() => {
    mounted.current = true;
    void refresh();
    return () => {
      mounted.current = false;
    };
  }, [refresh]);

  const downloading = read.kind === "ok" && read.status.state === "downloading";
  useEffect(() => {
    if (!downloading) return;
    const timer = window.setInterval(() => void refresh(), POLL_MS);
    return () => window.clearInterval(timer);
  }, [downloading, refresh]);

  return {
    read,
    rate,
    busy,
    finishedAt,
    refresh,
    start: () => act(LOCAL_AI_PATH),
    cancel: () => act(`${LOCAL_AI_PATH}/cancel`),
  };
}
