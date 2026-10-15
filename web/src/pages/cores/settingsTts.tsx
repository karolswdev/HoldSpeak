/**
 * HS-154-01 — the TTS settings block.
 *
 * Browser voice availability comes from this browser. When the holdspeak[tts] extra is
 * installed, shows the GPL-3.0 note (phonemizer /
 * espeak-ng) + the weights download with egress badge. When the extra
 * is absent, shows ONE line with the install command — no dead switch.
 */
import { useState, useEffect, useRef, useCallback } from "react";
import { apiFetch, readableError } from "../../lib/api";
import {
  EgressChip,
  GadgetGroup,
  GadgetRow,
  FoldGadget,
  StateChip,
} from "../../desk/surface";
import { Button } from "../../components/signal/Signal";
import { CommandWell } from "./connections/ConnectionsPane";

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
        <FoldGadget title="Details"><CommandWell hint="pip install 'holdspeak[tts]'"/></FoldGadget>
      </GadgetGroup>
    );
  }

  // Extra installed.
  return (
    <GadgetGroup material="inset" label="Speech" actions={!status.model_ready || receipt || error ? <>
      {!status.model_ready ? (
        <>
          <EgressChip
            label="DOWNLOADS huggingface.co · ~90 MB"
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
          GPL-3.0 · phonemizer + espeak-ng
        </span>
      </FoldGadget>
    </GadgetGroup>
  );
}
