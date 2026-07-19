// HS-101 B7 — the desk accepts files through the glass: a transcript
// or audio file dropped anywhere imports a Meeting through the real
// import route. The veil lights BEFORE the drop; refusals name why.
import { useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import { openSurfaceOr } from "../shell";
import { glassFileKind, glassFileRefusal } from "../glassDrop";

type DropState =
  | { phase: "idle" }
  | { phase: "armed" }
  | { phase: "importing"; name: string }
  | { phase: "imported"; name: string; meetingId: string }
  | { phase: "refused"; reason: string };

export function GlassDropLayer() {
  const [state, setState] = useState<DropState>({ phase: "idle" });
  const depth = useRef(0);

  useEffect(() => {
    const hasFiles = (event: DragEvent) =>
      Boolean(event.dataTransfer?.types.includes("Files"));
    const onEnter = (event: DragEvent) => {
      if (!hasFiles(event)) return;
      event.preventDefault();
      depth.current += 1;
      setState((s) => (s.phase === "idle" || s.phase === "armed" ? { phase: "armed" } : s));
    };
    const onOver = (event: DragEvent) => {
      if (!hasFiles(event)) return;
      event.preventDefault();
    };
    const onLeave = (event: DragEvent) => {
      if (!hasFiles(event)) return;
      depth.current = Math.max(0, depth.current - 1);
      if (depth.current === 0) {
        setState((s) => (s.phase === "armed" ? { phase: "idle" } : s));
      }
    };
    const onDrop = (event: DragEvent) => {
      if (!hasFiles(event)) return;
      event.preventDefault();
      depth.current = 0;
      const file = event.dataTransfer?.files?.[0];
      if (!file) {
        setState({ phase: "idle" });
        return;
      }
      if (!glassFileKind(file.name)) {
        setState({ phase: "refused", reason: glassFileRefusal(file.name) });
        return;
      }
      setState({ phase: "importing", name: file.name });
      const body = new FormData();
      body.append("file", file);
      body.append("title", file.name.replace(/\.[^.]+$/, ""));
      if (file.lastModified) {
        body.append("started_at_ms", String(file.lastModified));
      }
      void apiFetch<{ meeting_id?: string }>("/api/meetings/import", {
        method: "POST",
        body,
      })
        .then((result) =>
          setState({
            phase: "imported",
            name: file.name,
            meetingId: String(result.meeting_id ?? ""),
          }),
        )
        .catch((error) =>
          setState({ phase: "refused", reason: readableError(error) }),
        );
    };
    document.addEventListener("dragenter", onEnter);
    document.addEventListener("dragover", onOver);
    document.addEventListener("dragleave", onLeave);
    document.addEventListener("drop", onDrop);
    return () => {
      document.removeEventListener("dragenter", onEnter);
      document.removeEventListener("dragover", onOver);
      document.removeEventListener("dragleave", onLeave);
      document.removeEventListener("drop", onDrop);
    };
  }, []);

  if (state.phase === "idle") return null;

  return (
    <div
      className={
        "desk-glassdrop" + (state.phase === "armed" ? " is-armed" : "")
      }
      role={state.phase === "refused" ? "alert" : "status"}
    >
      <div className="desk-glassdrop-card">
        {state.phase === "armed" ? (
          <>
            <strong>Drop to import a Meeting</strong>
            <small>.vtt · .srt · .txt · audio</small>
          </>
        ) : null}
        {state.phase === "importing" ? (
          <>
            <strong>Importing {state.name}</strong>
            <small>Transcribing runs on this device</small>
          </>
        ) : null}
        {state.phase === "imported" ? (
          <>
            <strong>Meeting created</strong>
            <small>{state.name}</small>
            <span className="desk-glassdrop-verbs">
              <button
                type="button"
                onClick={() => {
                  setState({ phase: "idle" });
                  openSurfaceOr("review-meetings", "/history");
                }}
              >
                Open Meetings
              </button>
              <button
                type="button"
                className="is-quiet"
                onClick={() => setState({ phase: "idle" })}
              >
                Dismiss
              </button>
            </span>
          </>
        ) : null}
        {state.phase === "refused" ? (
          <>
            <strong>{state.reason}</strong>
            <span className="desk-glassdrop-verbs">
              <button
                type="button"
                className="is-quiet"
                onClick={() => setState({ phase: "idle" })}
              >
                Dismiss
              </button>
            </span>
          </>
        ) : null}
      </div>
    </div>
  );
}
