// Settings > Desk: sounds, presence and the voice (TTS). Moved out of SettingsCore.tsx.
import { CheckGadget, GadgetGroup, GadgetRow } from "../../../desk/surface/gadgets";
import { SurfaceColumns } from "../../../desk/surface";
import { toggleSfx } from "../../../lib/sfx";
import { useState, useEffect, useRef, useCallback } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import { EgressChip, FoldGadget, StateChip } from "../../../desk/surface";
import { Button } from "../../../components/signal/Signal";
import { CommandWell } from "../connections/ConnectionsPane";
import { WallpaperModule } from "./Wallpaper";
import { RecordingsSettings } from "../../../desk/recordings/RecordingsSettings";
import type { SettingsBindings } from "./bindings";

/* ── Sounds & Presence: desk sounds + presence + mascot ── */
function SoundsModule({ b }: { b: SettingsBindings }) {
  const { update, val, hl, check } = b;
        return (
          <SurfaceColumns variant="preferences" main={<>
              <GadgetGroup material="inset" label="Sounds">
                <GadgetRow
                  label="Desk sounds"
                  highlight={hl(["ui", "desk_sounds"])}
                  controlWidth="short"
                >
                  <CheckGadget
                    variant="state"
                    label="Desk sounds"
                    checked={Boolean(val(["ui", "desk_sounds"]) ?? true)}
                    onChange={(next) => {
                      update(["ui", "desk_sounds"], next);
                      toggleSfx(next);
                    }}
                  />
                </GadgetRow>
              </GadgetGroup>
              <GadgetGroup material="inset" label="Presence">
                {check(["presence", "enabled"], "Presence")}
                {check(["presence", "mascot"], "Mascot")}
              </GadgetGroup>
          </>} side={<TtsSettingsBlock />} />
        );
}

export function DeskSection({ b, focusHighlight }: { b: SettingsBindings; focusHighlight: string }) {
  return <>
    <SoundsModule b={b} />
    <WallpaperModule showFavorites highlight={focusHighlight} />
    <RecordingsSettings />
  </>;
}

/**
 * HS-154-01 — the TTS settings block.
 *
 * Browser voice availability comes from this browser. The server voice is
 * the Line's Pocket TTS (holdspeak[line]): the desk and a call speak with
 * one engine and one set of weights. When the extra is installed, shows the
 * licence note (MIT code, CC-BY-4.0 weights) + the weights download with
 * egress badge. When it is absent, shows ONE line with the install command.
 */

type TtsStatus = {
  installed: boolean;
  model_ready: boolean;
};

export function TtsSettingsBlock() {
  const [status, setStatus] = useState<TtsStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [receipt, setReceipt] = useState("");
  const [error, setError] = useState("");
  const mounted = useRef(true);
  const [readError, setReadError] = useState(false);
  const browserAvailable = typeof window.speechSynthesis !== "undefined";

  useEffect(
    () => {
      mounted.current = true;
      return () => { mounted.current = false; };
    },
    [],
  );

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch<TtsStatus>("/api/tts/status");
      if (mounted.current) { setStatus(data); setReadError(false); }
    } catch {
      if (mounted.current) setReadError(true);
    } finally { if (mounted.current) setLoading(false); }
  }, []);
  useEffect(() => { void reload(); }, [reload]);

  const handleDownload = async () => {
    setDownloading(true);
    setError("");
    setReceipt("");
    try {
      const result = await apiFetch<{
        receipt: { downloaded: boolean; elapsed_s: number };
        egress: { host: string; bytes_estimate: string };
      }>("/api/tts/download", { method: "POST" });
      if (mounted.current) {
        if (result.receipt?.downloaded) {
          setReceipt("Downloaded");
          setStatus({ installed: true, model_ready: true });
        } else {
          setError("Download did not complete");
        }
      }
    } catch (e) {
      if (mounted.current) setError(readableError(e));
    } finally {
      if (mounted.current) setDownloading(false);
    }
  };

  if (loading) return <GadgetGroup material="inset" label="Speech"><span aria-busy="true">Checking</span></GadgetGroup>;
  if (readError) return <GadgetGroup material="inset" label="Speech"><GadgetRow label="Server voice"><StateChip state="failure" label="Could not read" /><Button dense variant="secondary" onClick={() => void reload()}>Retry</Button></GadgetRow></GadgetGroup>;

  // Extra NOT installed: one-line install instruction, no dead switch.
  if (!status?.installed) {
    return (
      <GadgetGroup material="inset" label="Speech">
        <GadgetRow label="Browser voice">
          <span className="prefs-value">{browserAvailable ? "Available" : "Not available"}</span>
        </GadgetRow>
        <GadgetRow label="Server voice"><span className="prefs-value">Not installed</span></GadgetRow>
        <FoldGadget title="Details"><CommandWell hint="pip install 'holdspeak[line]'"/></FoldGadget>
      </GadgetGroup>
    );
  }

  // Extra installed.
  return (
    <GadgetGroup material="inset" label="Speech" actions={!status.model_ready || receipt || error ? <>
      {!status.model_ready ? (
        <>
          <EgressChip
            label="DOWNLOADS huggingface.co · ~226 MB"
            title="One-time model download from Hugging Face."
            scope="cloud"
          />
          <Button dense disabled={downloading} onClick={handleDownload}>
            {downloading ? "Downloading…" : "Download model"}
          </Button>
        </>
      ) : null}
      {receipt ? (
        <span className="gadget-fact" role="status">
          {receipt}
        </span>
      ) : null}
      {error ? (
        <span className="gadget-fact" data-tone="danger" role="alert">
          {error}
        </span>
      ) : null}
    </> : undefined}>
      <GadgetRow label="Browser voice">
        <span className="prefs-value">{browserAvailable ? "Available" : "Not available"}</span>
      </GadgetRow>
      <GadgetRow label="Server voice">
        <span className="prefs-value">
          {status.model_ready ? "Ready" : "Model needed"}
        </span>
      </GadgetRow>
      <FoldGadget title="Details">
        <span className="gadget-fact">
          Pocket TTS · MIT · weights CC-BY-4.0
        </span>
      </FoldGadget>
    </GadgetGroup>
  );
}
