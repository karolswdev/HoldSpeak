/**
 * HS-154-01 — the TTS settings block.
 *
 * Browser voice always available. When the holdspeak[tts] extra is
 * installed, shows the enable toggle + the GPL-3.0 note (phonemizer /
 * espeak-ng) + the weights download with egress badge. When the extra
 * is absent, shows ONE line with the install command — no dead switch.
 */
import { useState, useEffect, useRef } from "react";
import { apiFetch, readableError } from "../../lib/api";
import {
  EgressChip,
  GadgetGroup,
  GadgetRow,
} from "../../desk/surface/gadgets";
import { Button } from "../../components/signal/Signal";

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

  useEffect(
    () => () => {
      mounted.current = false;
    },
    [],
  );

  useEffect(() => {
    void (async () => {
      try {
        const data = await apiFetch<TtsStatus>("/api/tts/status");
        if (mounted.current) {
          setStatus(data);
          setLoading(false);
        }
      } catch {
        if (mounted.current) {
          setStatus({ installed: false, model_ready: false });
          setLoading(false);
        }
      }
    })();
  }, []);

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
          setReceipt("DOWNLOADED");
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

  if (loading) return null;

  // Extra NOT installed: one-line install instruction, no dead switch.
  if (!status?.installed) {
    return (
      <GadgetGroup label="Speech">
        <GadgetRow wide label="BROWSER VOICE">
          <span className="gadget-fact">ACTIVE</span>
        </GadgetRow>
        <div className="prefs-egress-line">
          <span className="gadget-fact">
            SERVER VOICE · pip install &apos;holdspeak[tts]&apos;
          </span>
        </div>
      </GadgetGroup>
    );
  }

  // Extra installed.
  return (
    <GadgetGroup label="Speech">
      <GadgetRow wide label="BROWSER VOICE">
        <span className="gadget-fact">ACTIVE</span>
      </GadgetRow>
      <GadgetRow wide label="SERVER VOICE">
        <span className="gadget-fact">
          {status.model_ready ? "READY" : "WEIGHTS NEEDED"}
        </span>
      </GadgetRow>
      {!status.model_ready ? (
        <div className="prefs-egress-line">
          <EgressChip
            label="DOWNLOADS huggingface.co · ~90 MB"
            title="One-time model download from Hugging Face."
            scope="cloud"
          />
          <Button dense disabled={downloading} onClick={handleDownload}>
            {downloading ? "DOWNLOADING..." : "DOWNLOAD WEIGHTS"}
          </Button>
        </div>
      ) : null}
      {receipt ? (
        <div className="prefs-egress-line">
          <span className="gadget-fact" role="status">
            {receipt}
          </span>
        </div>
      ) : null}
      {error ? (
        <div className="prefs-egress-line">
          <span className="gadget-fact" data-tone="danger" role="alert">
            {error}
          </span>
        </div>
      ) : null}
      <div className="prefs-egress-line">
        <span className="gadget-fact">
          GPL-3.0 · phonemizer + espeak-ng
        </span>
      </div>
    </GadgetGroup>
  );
}
