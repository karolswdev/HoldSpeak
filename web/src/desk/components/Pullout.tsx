// The pull-out (HS-73-04): tap an object and it opens HERE, on the stage —
// the port of the iPad's DioPullout + the meeting drawer (PR #196). The
// world stays alive behind it; "Open full" is the ONE navigation on the
// desk; Escape / click-elsewhere closes.
import { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
// @ts-ignore — shared ESM module (see ../sprites.d.ts)
import { spriteUrl } from "../sprites";
import { apiRequest } from "../../lib/api";
import { useDesk } from "../store";
import { parseLinearGraph, stepLabel } from "../graph";
import { MicButton } from "./MicButton";
import { lineage } from "../lineage";
import { useSteering } from "../steering";
import { objGlow, type WorldObject } from "../world";

const FILABLE = new Set([
  "meeting",
  "artifact",
  "note",
  "recipe",
  "chain",
  "workflow",
  "kb",
]);
const EDITABLE = new Set(["note", "kb", "recipe", "workflow"]);

interface MeetingDetail {
  intel?: { summary?: string; action_items?: any[]; topics?: string[] } | null;
  intel_status?: { state?: string } | null;
  [key: string]: unknown;
}

export function Pullout({ o }: { o: WorldObject }) {
  const items = useDesk((s) => s.items);
  const profiles = useDesk((s) => s.profiles);
  const backId = useDesk((s) => s.pulloutBackId);
  const {
    closePullout,
    openPullout,
    openEditor,
    fileIntoDir,
    removeFromDir,
    answerCoder,
    speakToCoder,
  } = useDesk.getState();
  const ref = useRef<HTMLDivElement | null>(null);
  const [detail, setDetail] = useState<MeetingDetail | null>(null);
  const [artifacts, setArtifacts] = useState<any[]>([]);
  const [runInput, setRunInput] = useState("");
  const [runBusy, setRunBusy] = useState(false);
  const [runOut, setRunOut] = useState("");
  const [runWarning, setRunWarning] = useState("");
  const [filing, setFiling] = useState(false);
  const [answered, setAnswered] = useState<
    "selected" | "sent" | "failed" | null
  >(null);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closePullout();
    };
    const onDown = (e: PointerEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node))
        closePullout();
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onDown);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onDown);
    };
  }, []);

  useEffect(() => {
    if (o.kind !== "meeting") return;
    // The detail payload nests intel_status (the repo's documented gotcha).
    apiRequest(`/api/meetings/${encodeURIComponent(o.id)}`)
      .then((r) => r.json())
      .then(setDetail)
      .catch(() => setDetail(null));
    apiRequest(`/api/meetings/${encodeURIComponent(o.id)}/artifacts`)
      .then((r) => r.json())
      .then((d) => setArtifacts(d.artifacts || []))
      .catch(() => setArtifacts([]));
  }, [o.kind, o.id]);

  const run = async () => {
    setRunBusy(true);
    setRunOut("");
    setRunWarning("");
    const result = await useDesk
      .getState()
      .runCapability(o.kind as "recipe" | "chain" | "workflow", o.id, runInput);
    setRunOut(result.output);
    // HSM-22-03 — the hub's honest refusal (graph ran as the prompt fallback)
    // reaches the reader instead of being dropped.
    setRunWarning(result.warning || "");
    setRunBusy(false);
  };

  const ir = o.ref as any;
  const zones = items.directory || [];
  const lin = lineage(items, ir.sources);
  const profile = profiles.find((p) => p.id === ir.profileId);
  const egress = profile
    ? (profile.kind || "onDevice") === "onDevice"
      ? { scope: "local", text: "⌂ On device" }
      : {
          scope: "cloud",
          text: `☁ ${
            String(profile.base_url || "endpoint")
              .replace(/^https?:\/\//, "")
              .split("/")[0]
          }`,
        }
    : null;

  const artifactRow = (a: any) => (
    <button
      key={a.id}
      type="button"
      className="desk-pullout-row"
      onClick={() => openPullout(a.id)}
    >
      <span className="desk-pullout-row-type">
        {a.artifact_type || a.artifactType}
      </span>
      <span className="desk-pullout-row-title">{a.title}</span>
    </button>
  );

  return (
    <motion.div
      ref={ref}
      className="desk-pullout"
      style={{ "--k": objGlow(o.kind) } as React.CSSProperties}
      initial={{ x: 60, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 30 }}
      onPointerDown={(e) => e.stopPropagation()}
    >
      <header className="desk-pullout-head">
        {backId && (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={() => openPullout(backId)}
          >
            ←
          </button>
        )}
        <img src={spriteUrl(o.kind, o.id)} alt="" width={30} height={30} />
        <span className="desk-pullout-title">{o.title}</span>
        {egress && (
          <span className={`egress-badge is-${egress.scope}`}>
            {egress.text}
          </span>
        )}
        {o.kind === "meeting" && (
          <a
            className="desk-chip quiet"
            href={`/history?meeting=${encodeURIComponent(o.id)}`}
          >
            Open full
          </a>
        )}
        {o.kind === "workflow" && (
          <a className="desk-chip quiet" href="/workbench">
            Open full
          </a>
        )}
        <button
          type="button"
          className="desk-pullout-close"
          onClick={closePullout}
          aria-label="Close"
        >
          ✕
        </button>
      </header>

      <div className="desk-pullout-body">
        {o.kind === "meeting" && (
          <>
            {detail?.intel?.summary ? (
              <section>
                <h3>Summary</h3>
                <p>{detail.intel.summary}</p>
              </section>
            ) : (
              <section>
                <h3>Intelligence</h3>
                <p className="quiet">
                  {detail?.intel_status?.state || "pending"}
                </p>
              </section>
            )}
            {detail?.intel?.action_items &&
              detail.intel.action_items.length > 0 && (
                <section>
                  <h3>Actions</h3>
                  <ul>
                    {detail.intel.action_items
                      .slice(0, 8)
                      .map((a: any, i: number) => (
                        <li key={i}>
                          {typeof a === "string"
                            ? a
                            : a.task || a.text || a.title || ""}
                        </li>
                      ))}
                  </ul>
                </section>
              )}
            {artifacts.length > 0 && (
              <section>
                <h3>Artifacts</h3>
                {artifacts.map(artifactRow)}
              </section>
            )}
          </>
        )}

        {o.kind === "artifact" && (
          <>
            <section>
              <h3>{String(ir.artifactType || "artifact")}</h3>
              <pre className="desk-pullout-md">
                {String(ir.bodyMarkdown || "")}
              </pre>
            </section>
            {lin.any && (
              <section>
                <h3>Lineage</h3>
                <div className="desk-pullout-lineage">
                  {lin.via && (
                    <span className="desk-chip quiet">via {lin.via.label}</span>
                  )}
                  {lin.from.map((f) => (
                    <button
                      key={f.ref}
                      type="button"
                      className="desk-chip quiet"
                      onClick={() => f.resolved && openPullout(f.ref)}
                    >
                      {f.label}
                    </button>
                  ))}
                </div>
              </section>
            )}
          </>
        )}

        {(o.kind === "note" || o.kind === "kb") && (
          <section>
            <pre className="desk-pullout-md">
              {String(
                ir.bodyMarkdown ||
                  (ir.memberIds || [])
                    .map((m: string) => `· ${m}`)
                    .join("\n") ||
                  "",
              )}
            </pre>
          </section>
        )}

        {o.kind === "recipe" && (
          <section>
            <p className="quiet">{String(ir.role || "")}</p>
            <pre className="desk-pullout-md">
              {String(ir.systemPrompt || "")}
            </pre>
          </section>
        )}

        {(o.kind === "chain" || o.kind === "workflow") && (
          <section>
            <h3>Steps</h3>
            <ul>
              {(
                (o.kind === "workflow" && ir.graphJson
                  ? (parseLinearGraph(ir.graphJson)?.map(stepLabel) ?? [
                      "Graphed on iPad",
                    ])
                  : null) ||
                (ir.steps as string[]) ||
                (ir.prompt ? [ir.prompt] : [])
              ).map((st, i) => (
                <li key={i}>{st}</li>
              ))}
            </ul>
          </section>
        )}

        {o.kind === "coder" && (
          <section>
            <p className="quiet">
              {String(ir.model || "")} · {String(ir.state || "")}
            </p>
            {ir.question ? (
              <pre className="desk-pullout-md">{String(ir.question)}</pre>
            ) : null}
            <div className="desk-coder-answer">
              <MicButton
                label="Hold to answer"
                onText={(t) => {
                  setAnswered(null);
                  void speakToCoder(
                    String(ir.agent || "claude"),
                    String(ir.sessionId || o.id),
                    t,
                  ).then((ok) => setAnswered(ok ? "sent" : "failed"));
                }}
              />
              <span className="quiet desk-coder-answer-state">
                {answered === "sent"
                  ? "Sent"
                  : answered === "failed"
                    ? "Retry"
                    : "Hold to answer"}
              </span>
              <button
                type="button"
                className="desk-chip quiet"
                onClick={() => {
                  void answerCoder(
                    String(ir.agent || "claude"),
                    String(ir.sessionId || o.id),
                  ).then((ok) => setAnswered(ok ? "selected" : "failed"));
                }}
              >
                {answered === "selected"
                  ? "Dictation target"
                  : "Use the hotkey"}
              </button>
              <button
                type="button"
                className="desk-chip quiet"
                onClick={() => {
                  closePullout();
                  useSteering
                    .getState()
                    .openSession(
                      `${String(ir.agent || "claude")}:${String(ir.sessionId || o.id)}`,
                    );
                }}
              >
                Watch live
              </button>
            </div>
          </section>
        )}

        {["recipe", "chain", "workflow"].includes(o.kind) && (
          <section>
            <div className="desk-pullout-run">
              <input
                value={runInput}
                placeholder="Ask"
                onChange={(e) => setRunInput(e.target.value)}
              />
              <button
                type="button"
                className="desk-chip"
                onClick={() => void run()}
                disabled={runBusy}
              >
                {runBusy ? "…" : "Run"}
              </button>
            </div>
            {runWarning && <p className="desk-run-warning">⚠ {runWarning}</p>}
            {runOut && <pre className="desk-pullout-md">{runOut}</pre>}
          </section>
        )}
      </div>

      <footer className="desk-pullout-foot">
        {EDITABLE.has(o.kind) && (
          <button
            type="button"
            className="desk-chip"
            onClick={() => openEditor(o.id)}
          >
            Edit
          </button>
        )}
        {FILABLE.has(o.kind) && zones.length > 0 && (
          <div className="desk-pullout-file">
            <button
              type="button"
              className="desk-chip quiet"
              onClick={() => setFiling((v) => !v)}
            >
              Move to…
            </button>
            {filing &&
              zones.map((z) => {
                const inZone = (
                  ((z as any).memberIds as string[]) || []
                ).includes(o.id);
                return (
                  <button
                    key={String(z.id)}
                    type="button"
                    className={"desk-chip quiet" + (inZone ? " in-zone" : "")}
                    onClick={() => {
                      setFiling(false);
                      void (inZone
                        ? removeFromDir(o.id, String(z.id))
                        : fileIntoDir(o.id, String(z.id)));
                    }}
                  >
                    {inZone ? "✓ " : ""}
                    {String(z.name || z.id)}
                  </button>
                );
              })}
          </div>
        )}
      </footer>
    </motion.div>
  );
}
