/** Artifact pullout content (HS-117-15).
 *
 *  W4-PHONE (2026-10-27, atlas pass 2 "two faces for one result"): the
 *  artifact on the reader grammar, as the Decision reader is (W1-TRUTH). A
 *  toolbar holds every verb (Open · Copy · Send… · Reveal); the result
 *  is the words on the window's paper (no card); Send… opens the one
 *  Send sheet in place of the words, and Cancel returns; Reveal shows
 *  where it is filed; the status bar says the kind as a dot and a
 *  word, the review state, and the receipt. */
import { useState } from "react";
import { useDesk } from "../store";
import { qualifiedRef } from "../api";
import { lineage } from "../lineage";
import { DeskFilingStrip } from "../components/DeskFilingStrip";
import { humanizeWireValue } from "../../lib/productLanguage";
import { Material } from "../surface/Material";
import type { PulloutContentProps } from "./types";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { Button } from "../../components/signal/Signal";
import { ArtifactSendWells } from "../documentSendsLazy";
import { ActionNotice, FoldGadget, StateChip, SurfaceState, SurfaceWell } from "../surface";
import { DotWord, StatusBar, ToolGlyph, Toolbar, type StatusBarItem } from "../surface/kit";
import { presentArtifact } from "./artifactPresentation";
import "./artifact-reading.css";

/** The kind of an artifact in plain words (`Automation result`). */
const KIND_WORDS: Record<string, string> = {
  workbench_output: "Automation result",
  run_output: "Run result",
  adr: "Decision record draft",
  requirements_doc: "Requirements",
};
export function artifactKindWord(type: string): string {
  const key = type.trim().toLowerCase();
  return KIND_WORDS[key] ?? (humanizeWireValue(key) || "Result");
}

export function ArtifactPullout({ object: o }: PulloutContentProps) {
  const items = useDesk((s) => s.items);
  const { openPullout } = useDesk.getState();
  const [sending, setSending] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const [filed, setFiled] = useState("");
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  if (o.ref.kind !== "artifact") return null;
  const ir = o.ref;
  const resourceRef = qualifiedRef(o.kind, o.id);
  const title = String(ir.title || o.title || "Artifact");
  const type = String(ir.artifactType || "artifact");
  const body = String(ir.bodyMarkdown || "");
  const presentation = presentArtifact({ title, artifactType: type, bodyMarkdown: body, sources: ir.sources, items });
  const read = ir.sourceRead;
  const hasMaterial = read?.hasMaterial !== false;
  const hasReadingMaterial = hasMaterial && !presentation.isEmptyResult;
  const reviewState = ir.status === "pending-review" ? { tone: "warn" as const, label: "Awaiting review" }
    : ir.status === "rejected" ? { tone: "fail" as const, label: "Rejected" } : null;
  const meeting = ir.meetingId ? lineage(items, [{ source_type: "meeting", source_ref: ir.meetingId }]).from[0] : null;
  const openMeeting = meeting?.resolved
    ? () => openPullout(meeting.actionRef ?? qualifiedRef("meeting", String(ir.meetingId)))
    : undefined;
  // Open: what the result came from (its meeting, else its first known source).
  const source = meeting?.resolved ? meeting : presentation.sources.find((entry) => entry.resolved) ?? null;
  const openSource = source ? () => openPullout(source.actionRef ?? source.ref) : undefined;
  const sheet = sending && hasReadingMaterial;

  const statusItems: Array<StatusBarItem | null> = [
    hasMaterial ? { key: "kind", text: <DotWord tone="info" data-testid="artifact-kind">{artifactKindWord(type)}</DotWord> } : null,
    reviewState ? { key: "review", text: <span aria-label={reviewState.label}><DotWord tone={reviewState.tone}>{reviewState.label}</DotWord></span> } : null,
    filed ? { key: "filed", text: `Filed in: ${filed}`, testId: "artifact-filed" } : null,
    copyReceipt ? { key: "receipt", text: copyReceipt } : null,
  ];

  return (
    <>
      <div className="desk-pullout-body desk-surface-body artifact-window" data-interior="editor" data-testid="artifact-reader">
        {hasMaterial && !sheet ? (
          <Toolbar label="Result" className="artifact-toolbar" data-testid="artifact-toolbar">
            {openSource ? (
              <Button dense variant="secondary" title={`Open ${source!.label}`} onClick={openSource} data-testid="artifact-open">
                <ToolGlyph kind="open" />Open
              </Button>
            ) : null}
            <Button dense variant="secondary" onClick={() => void copy(body)} data-testid="artifact-copy">
              <ToolGlyph kind="copy" />Copy
            </Button>
            {hasReadingMaterial ? (
              <Button dense variant="secondary" aria-expanded={sheet} onClick={() => { setRevealed(false); setSending(true); }} data-testid="artifact-send">
                <ToolGlyph kind="send" />Send…
              </Button>
            ) : null}
            <Button dense variant="ghost" aria-expanded={revealed} onClick={() => { setSending(false); setRevealed((open) => !open); }} data-testid="artifact-reveal">
              <ToolGlyph kind="project" />Reveal
            </Button>
          </Toolbar>
        ) : null}
        {sheet ? (
          <div className="artifact-send-sheet" data-testid="artifact-send-sheet">
            <ArtifactSendWells id={o.id} title={title} type={type} onBack={() => setSending(false)} />
          </div>
        ) : (
        <article className="artifact-reader" aria-label={title}>
        {read ? <ActionNotice role="alert" tone="danger" action={{ label: "Retry read", onClick: () => void useDesk.getState().refresh() }}>
          <StateChip state={read.state === "unavailable" ? "unreachable" : "failure"} label={read.state === "unavailable" ? "Source unavailable" : "Read failed"} />
          {hasMaterial ? <StateChip state="warning" label="Last read" /> : null}
          {read.state === "failed" ? <span>{humanizeWireValue(read.message)}</span> : null}
        </ActionNotice> : null}
        {hasMaterial ? (
          <>
            {revealed ? (
              <div className="artifact-filing" data-testid="artifact-filing">
                <DeskFilingStrip objectRef={resourceRef} objectKind={o.kind} objectId={o.id} bare onSummary={setFiled} />
              </div>
            ) : null}
            <section className="artifact-reading-section">
              <div className="artifact-reading">
                {presentation.isEmptyResult
                  ? <SurfaceState empty emptyGlyph="" emptyLabel={presentation.emptyLabel} onAction={openMeeting} actionLabel={openMeeting ? "Open meeting" : undefined} />
                  : <SurfaceWell><Material>{presentation.body}</Material></SurfaceWell>}
              </div>
            </section>
            {presentation.sources.length > 0 ? (
              <FoldGadget title="Sources" className="artifact-sources-fold">
                <div className="artifact-sources" data-testid="artifact-sources">
                  {presentation.sources.map((entry) => entry.resolved ? (
                    <Button key={`${entry.type}:${entry.ref}`} dense variant="ghost" onClick={() => openPullout(entry.actionRef ?? entry.ref)}>
                      {entry.via ? `via ${entry.label}` : entry.label}
                    </Button>
                  ) : (
                    <span key={`${entry.type}:${entry.ref}`} className="artifact-source-unresolved" data-testid="artifact-source-unresolved">
                      {entry.via ? `via ${entry.label}` : entry.label}
                    </span>
                  ))}
                </div>
              </FoldGadget>
            ) : null}
          </>
        ) : null}
        </article>
        )}
        {hasMaterial && !revealed ? (
          <span hidden aria-hidden="true">
            <DeskFilingStrip objectRef={resourceRef} objectKind={o.kind} objectId={o.id} bare onSummary={setFiled} />
          </span>
        ) : null}
      </div>
      <StatusBar data-testid="artifact-status" items={statusItems} />
    </>
  );
}
