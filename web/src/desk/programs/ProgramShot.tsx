/* Programs PG-REQ §9, §16 (REQ12): the shot pullout
 * `pullout:program-shot:<program>:<requirement>`, an image frame. The
 * desk had no image window; a Shot requirement's Open shot opens this one.
 *
 * Window grammar: title bar ("R2 · people at 393") → Toolbar (Open program)
 * → the image, whole, on the window's well → the StatusBar (the state word,
 * the commit it was judged on, the sweep's result line). The image is read
 * through the hub's evidence route (this desk only). */
import { Button } from "../../components/signal/Signal";
import { DotWord, StatusBar, SurfaceState, Toolbar, type StatusBarItem } from "../surface";
import { useWindowInterior } from "../surface/interior";
import { useWindowTitle } from "../surface/title";
import { useProgram } from "./api";
import { requirementTone, requirementWord } from "./model";
import { openProgram } from "./open";
import { useEvidenceImage } from "./Requirements";
import "./programs.css";

/** `<program>:<requirement>` → its two ids. */
export function shotIds(id: string): { programId: string; requirementId: string } {
  const at = id.lastIndexOf(":");
  return at > 0 ? { programId: id.slice(0, at), requirementId: id.slice(at + 1) } : { programId: "", requirementId: id };
}

export function ProgramShotBody({ id }: { id: string }) {
  const { programId, requirementId } = shotIds(id);
  const { loading, error, program, reload } = useProgram(programId);
  useWindowInterior("list");
  const row = program
    ? [...(program.requirements ?? []), ...program.steps.flatMap((step) => step.requirements ?? [])].find((item) => item.id === requirementId) ?? null
    : null;
  const where = row ? `${row.evidence.case ?? row.spec.case ?? ""} at ${row.evidence.width ?? row.spec.width ?? ""}`.trim() : "";
  useWindowTitle(row ? `${row.label} · ${where}` : null, [row?.label, where]);
  const image = useEvidenceImage(row?.evidence.url);
  if (loading || (error && !program)) {
    return <SurfaceState loading={loading} error={error ? "The shot did not load. Nothing changed. Try again." : undefined} onRetry={() => void reload()} />;
  }
  if (!row) return <SurfaceState empty emptyKind="program" emptyLabel="This requirement is not on the program any more" />;
  const step = program?.steps.find((candidate) => candidate.id === row.step_id);
  const commit = row.evidence.commit ?? row.judged_commit;
  const status: StatusBarItem[] = [
    { key: "state", lamp: requirementTone(row) === "idle" ? undefined : (requirementTone(row) as StatusBarItem["lamp"]), text: requirementWord(row), testId: "program-shot-state" },
    step ? { key: "step", text: `Step ${step.ordinal} · ${step.title}` } : { key: "step", text: "The program" },
    commit ? { key: "commit", text: <span>{`on ${commit.slice(0, 7)}`}</span> } : null,
    row.evidence.line ? { key: "line", text: <span>{row.evidence.line}</span> } : null,
  ].filter(Boolean) as StatusBarItem[];
  return (
    <div className="pg-window pg-shot" data-testid="program-shot-window" data-req={row.id}>
      <Toolbar label="Shot">
        <Button dense variant="ghost" onClick={() => openProgram(programId)} data-testid="program-shot-open-program">Open program</Button>
      </Toolbar>
      <div className="pg-shot-frame" data-testid="program-shot-frame">
        {image.src ? (
          <img className="pg-shot-image" src={image.src} alt={`${row.label} · ${row.text}`} data-testid="program-shot-image" />
        ) : image.failed ? (
          <DotWord tone="warn">The shot is not there any more</DotWord>
        ) : <span className="pg-shot-wait" aria-hidden="true" />}
      </div>
      <StatusBar data-testid="program-shot-status" items={status} />
    </div>
  );
}

/** The pullout content: `pullout:program-shot:<program>:<requirement>`. */
export function ProgramShotPullout({ object }: { object: { id: string } }) {
  return <ProgramShotBody id={object.id} />;
}

export default ProgramShotPullout;
