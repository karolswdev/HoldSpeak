/* RECIPE LINE-6: the Engines window's "Phone speech" group: the Line's two
 * speech models (Parakeet in, Pocket TTS out), each with its licences, its
 * size and its readiness word, and Download through the concierge's path
 * (`POST /api/concierge/download`, the Line's own fetch into its model
 * folder). `GET /api/concierge/speech` is the one state `holdspeak line
 * models` also says. Ready = every pinned file is there and its SHA-256
 * matches. Kit only: the ListView species (a captioned group, rows with a
 * glyph, the name, quiet meta, a dot and a word, the row's verb). */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { ListDay, ListRow, ListView } from "../../desk/surface/objects/ListView";
import type { ObjectTone } from "../../desk/surface/objects/kinds";
import { spriteUrl } from "../../desk/sprites";
import { stateWords } from "../../desk/surface/words";
import { formatBytes } from "../../desk/firstrun/localAi";

export type SpeechModelState = "ready" | "missing" | "partial" | "downloading" | "failed";

/** One row of `GET /api/concierge/speech` (`line/models.py` `model_row`). */
export interface SpeechModelRow {
  id: string;
  role: "stt" | "tts";
  label: string;
  summary: string;
  bytes: number;
  license: string;
  code_license: string;
  attribution: string;
  host: string;
  revision: string;
  state: SpeechModelState;
  received?: number;
  total?: number;
  reason?: string;
}

const POLL_MS = 750;

export function speechStateWord(row: SpeechModelRow): { label: string; tone: ObjectTone | "idle" } {
  switch (row.state) {
    case "ready":
      return { label: stateWords("READY"), tone: "ok" };
    case "downloading": {
      const total = row.total || row.bytes;
      const pct = total ? Math.min(100, Math.floor(((row.received ?? 0) * 100) / total)) : 0;
      return { label: `Downloading · ${pct}%`, tone: "info" };
    }
    case "partial":
      return { label: "Part downloaded", tone: "warn" };
    case "failed":
      return { label: "Download stopped", tone: "fail" };
    default:
      return { label: "Not downloaded", tone: "idle" };
  }
}

export function licenceWords(row: SpeechModelRow): string {
  return `Weights ${row.license} · code ${row.code_license}`;
}

/** The rows, read once and again every POLL_MS while one downloads. */
export function useSpeechModels() {
  // undefined: the first read is in flight (the window stays aria-busy).
  const [rows, setRows] = useState<SpeechModelRow[] | null | undefined>(undefined);
  const [pressed, setPressed] = useState("");
  const alive = useRef(true);
  const read = useCallback(async () => {
    try {
      const answer = await apiFetch<{ rows?: SpeechModelRow[] } | null>("/api/concierge/speech");
      if (alive.current) setRows(Array.isArray(answer?.rows) ? answer!.rows : null);
    } catch {
      if (alive.current) setRows(null);
    }
  }, []);
  useEffect(() => {
    alive.current = true;
    void read();
    return () => {
      alive.current = false;
    };
  }, [read]);
  const downloading = (rows ?? []).some((row) => row.state === "downloading");
  useEffect(() => {
    if (!downloading) return;
    const timer = window.setInterval(() => void read(), POLL_MS);
    return () => window.clearInterval(timer);
  }, [downloading, read]);
  const download = async (id: string) => {
    setPressed(id);
    try {
      const answer = await apiFetch<{ row?: SpeechModelRow } | null>("/api/concierge/download", { method: "POST", json: { presetId: id } });
      const row = answer?.row;
      if (row && alive.current) setRows((current) => (current ?? []).map((item) => (item.id === row.id ? row : item)));
    } catch {
      await read();
    } finally {
      if (alive.current) setPressed("");
    }
  };
  return { rows, download, pressed, reading: rows === undefined };
}

export type SpeechModels = ReturnType<typeof useSpeechModels>;

export function PhoneSpeech({ models }: { models: SpeechModels }) {
  const { rows, download, pressed } = models;
  if (!rows?.length) return null;
  return (
    <ListView label="Phone speech" className="runson-phone-speech" data-testid="runson-phone-speech">
      <ListDay label="Phone speech">
        {rows.map((row) => {
          const state = speechStateWord(row);
          const canDownload = row.state === "missing" || row.state === "partial" || row.state === "failed";
          return (
            <ListRow
              key={row.id}
              data-testid={`runson-speech-${row.id}`}
              glyph={spriteUrl("model", row.id, "rest", null, 20)}
              name={row.label}
              nameTestId={`runson-speech-name-${row.role}`}
              meta={<span title={row.attribution}>{`${formatBytes(row.bytes)} · ${licenceWords(row)}`}</span>}
              state={{ word: state.label, tone: state.tone, testId: `runson-speech-state-${row.role}` }}
              verbs={canDownload ? (
                <Button dense variant="secondary" loading={pressed === row.id} disabled={Boolean(pressed)}
                  title={`Downloads ${formatBytes(row.bytes)} from ${row.host}`}
                  data-testid={`runson-speech-download-${row.role}`} onClick={() => void download(row.id)}>
                  {row.state === "failed" ? "Try again" : "Download"}
                </Button>
              ) : null}
            />
          );
        })}
      </ListDay>
    </ListView>
  );
}
