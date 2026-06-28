// ── HS-18 (web): the browser-mic dry-run capture widget ──────────────
//
// `/dictation` had only a typed dry-run. This adds an in-browser mic so you
// can SPEAK the utterance instead of typing it, then review the captured
// recording and the resolved preview + destination — exactly the
// preview-not-inject posture of the iPad teleprompter.
//
// HONESTY (why this is preview-only):
//   The hub exposes no dictation transcribe-preview route — the only
//   audio→text path (`/api/meetings/import`) builds a whole meeting, not a
//   throwaway preview. So we do NOT silently send your voice anywhere to be
//   transcribed. Instead the mic CAPTURE stays entirely in the browser (you
//   play it back to confirm what dictation would hear), and you confirm the
//   transcript text, which then runs through the SAME local `/api/dictation/
//   dry-run` the typed box uses. Nothing is injected; nothing is committed.
//
// EGRESS: the capture never leaves the machine, and the dry-run routes
// locally (lexical) unless intel is on — so the badge is the canonical
// `{scope:"local"}` chip, NEVER a privacy sentence (POSITIONING canon).
//
// All DOM ids read here are created by DryRunSection.astro; its styles for
// this widget are `is:global` (the standing Astro-scoped-CSS-on-JS-DOM rule
// does not bite static markup, but the recorder toggles classes at runtime).
import { runDryRun } from "./dryrun.js";

const micState = {
  supported:
    typeof navigator !== "undefined" &&
    !!navigator.mediaDevices &&
    typeof navigator.mediaDevices.getUserMedia === "function" &&
    typeof window !== "undefined" &&
    typeof window.MediaRecorder !== "undefined",
  recording: false,
  recorder: null,
  stream: null,
  chunks: [],
  blobUrl: null,
  startedAt: 0,
  timer: null,
};

function el(id) {
  return document.getElementById(id);
}

function setStatus(text, kind) {
  const node = el("mic-status");
  if (!node) return;
  node.textContent = text || "";
  node.classList.remove("is-recording", "is-error", "is-ready");
  if (kind) node.classList.add(kind);
}

function revokeBlob() {
  if (micState.blobUrl) {
    try {
      URL.revokeObjectURL(micState.blobUrl);
    } catch {
      /* no-op */
    }
    micState.blobUrl = null;
  }
}

function stopTracks() {
  if (micState.stream) {
    for (const track of micState.stream.getTracks()) {
      try {
        track.stop();
      } catch {
        /* no-op */
      }
    }
    micState.stream = null;
  }
}

function tickElapsed() {
  const node = el("mic-elapsed");
  if (!node) return;
  const secs = Math.max(0, Math.round((Date.now() - micState.startedAt) / 1000));
  const mm = String(Math.floor(secs / 60)).padStart(2, "0");
  const ss = String(secs % 60).padStart(2, "0");
  node.textContent = `${mm}:${ss}`;
}

async function startRecording() {
  if (micState.recording) return;
  const btn = el("mic-record-btn");
  setStatus("Requesting microphone…", null);
  try {
    micState.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (e) {
    const msg =
      e && e.name === "NotAllowedError"
        ? "Microphone permission denied. Allow it in the browser to capture, or type below."
        : `Could not open the microphone: ${e && e.message ? e.message : e}`;
    setStatus(msg, "is-error");
    return;
  }
  revokeBlob();
  micState.chunks = [];
  let recorder;
  try {
    recorder = new MediaRecorder(micState.stream);
  } catch (e) {
    stopTracks();
    setStatus(`Recorder unavailable: ${e && e.message ? e.message : e}`, "is-error");
    return;
  }
  micState.recorder = recorder;
  recorder.addEventListener("dataavailable", (ev) => {
    if (ev.data && ev.data.size > 0) micState.chunks.push(ev.data);
  });
  recorder.addEventListener("stop", onRecordingStopped);
  recorder.start();
  micState.recording = true;
  micState.startedAt = Date.now();
  micState.timer = window.setInterval(tickElapsed, 500);
  tickElapsed();
  if (btn) {
    btn.classList.add("is-recording");
    btn.setAttribute("aria-pressed", "true");
    const label = btn.querySelector(".mic-record-label");
    if (label) label.textContent = "Stop";
  }
  setStatus("Recording… speak your utterance, then Stop.", "is-recording");
}

function stopRecording() {
  if (!micState.recording || !micState.recorder) return;
  try {
    micState.recorder.stop();
  } catch {
    /* the stop handler still runs via the error path below */
  }
}

function onRecordingStopped() {
  micState.recording = false;
  if (micState.timer) {
    window.clearInterval(micState.timer);
    micState.timer = null;
  }
  stopTracks();
  const btn = el("mic-record-btn");
  if (btn) {
    btn.classList.remove("is-recording");
    btn.setAttribute("aria-pressed", "false");
    const label = btn.querySelector(".mic-record-label");
    if (label) label.textContent = "Record";
  }

  const type = (micState.recorder && micState.recorder.mimeType) || "audio/webm";
  const blob = new Blob(micState.chunks, { type });
  micState.chunks = [];
  if (!blob.size) {
    setStatus("No audio captured. Try again, or type the utterance below.", "is-error");
    return;
  }
  revokeBlob();
  micState.blobUrl = URL.createObjectURL(blob);

  const player = el("mic-playback");
  if (player) {
    player.src = micState.blobUrl;
    player.hidden = false;
  }
  const review = el("mic-review");
  if (review) review.hidden = false;
  setStatus(
    "Captured — play it back to confirm, then write what you said and run the preview.",
    "is-ready",
  );

  // Focus the transcript field so the next step (confirm the words) is obvious.
  // We never auto-fill it: nothing transcribed your voice, so claiming a
  // transcript would be dishonest. The user owns the words.
  const ta = el("dry-utterance");
  if (ta) {
    try {
      ta.focus({ preventScroll: false });
    } catch {
      ta.focus();
    }
  }
}

function onRecordClick() {
  if (micState.recording) stopRecording();
  else startRecording();
}

function onReviewRun() {
  const ta = el("dry-utterance");
  if (ta && !ta.value.trim()) {
    setStatus("Write what you said in the box first, then run the preview.", "is-error");
    ta.focus();
    return;
  }
  runDryRun();
}

function onDiscard() {
  revokeBlob();
  const player = el("mic-playback");
  if (player) {
    player.removeAttribute("src");
    player.hidden = true;
  }
  const review = el("mic-review");
  if (review) review.hidden = true;
  const elapsed = el("mic-elapsed");
  if (elapsed) elapsed.textContent = "00:00";
  setStatus("Discarded. Record again, or type below.", null);
}

/**
 * Wire the mic widget. Idempotent-ish: called once from init.js. When the
 * browser cannot do getUserMedia/MediaRecorder we hide the recorder and leave
 * the honest typed dry-run path fully intact.
 */
export function initMic() {
  const widget = el("mic-widget");
  if (!widget) return;

  if (!micState.supported) {
    const recordRow = el("mic-record-row");
    if (recordRow) recordRow.hidden = true;
    setStatus(
      "This browser can't capture mic audio here — type the utterance below to preview.",
      null,
    );
    return;
  }

  const btn = el("mic-record-btn");
  if (btn) btn.addEventListener("click", onRecordClick);
  const runBtn = el("mic-review-run");
  if (runBtn) runBtn.addEventListener("click", onReviewRun);
  const discardBtn = el("mic-discard");
  if (discardBtn) discardBtn.addEventListener("click", onDiscard);

  // Render the egress badge: the capture stays in the browser and the dry-run
  // routes locally — one structured chip, never a sentence.
  const badge = el("mic-egress");
  if (badge) {
    badge.textContent = "⌂ Local — stays in your browser";
    badge.className = "egress-badge is-local";
    badge.hidden = false;
  }
}
