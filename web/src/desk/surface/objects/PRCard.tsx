/** PHILO-14 B1 — PRCard and FilesChanged: the agent's work, inline in its
 *  lane (board A-4; C-4 puts them in the right column).
 *
 *  PRCard: the PR's sprite, `#413` and its title (primary step); then
 *  `CHECKS n OF m` as a lamp (fail when a check failed), `N RUNNING` when
 *  checks run, `REVIEW <word>`; then `branch → base` in mono. A raised
 *  FLAT card (read-only facts): the verb that opens it is the lane's
 *  (Open PR, in the footer, by the GITHUB.COM egress chip).
 *
 *  FilesChanged: the files the agent changed, one line each, the path in
 *  mono and its `+added −removed` counts; a zero count is not drawn.
 */
import { SurfaceSection } from "../Surface";
import { LampGadget } from "../gadgets";
import { listSprite } from "../../sprites";
import { objectSprite } from "./kinds";
import "./objects.css";

export interface PRCardProps {
  number: number;
  title: string;
  checks?: { passed: number; total: number; failed?: number; running?: number };
  /** `NONE YET`, `APPROVED`, `CHANGES ASKED`. */
  review?: string;
  branch?: string;
  base?: string;
  sprite?: string;
  /** Pass-through data-testid for the root `article`. */
  "data-testid"?: string;
}

/** The checks as lamps, never a counter of zero (UX-CANON A.8):
 *  some passed → `CHECKS p OF t` (fail tone when one failed) + `N FAILED` +
 *  `N RUNNING`; none passed yet → `CHECKS · N RUNNING` / `CHECKS · N FAILED`
 *  / `CHECKS · N PENDING`, with no `0 OF`. */
function checkLamps(checks: NonNullable<PRCardProps["checks"]>) {
  const { passed, total } = checks;
  const failed = checks.failed ?? 0;
  const running = checks.running ?? 0;
  if (total <= 0) return [];
  const lamps: { label: string; on: boolean; tone: "ok" | "fail" | "info" }[] = [];
  if (passed > 0) {
    lamps.push({ label: `CHECKS ${passed} OF ${total}`, on: true, tone: failed > 0 ? "fail" : "ok" });
    if (failed > 0) lamps.push({ label: `${failed} FAILED`, on: true, tone: "fail" });
    if (running > 0) lamps.push({ label: `${running} RUNNING`, on: false, tone: "info" });
    return lamps;
  }
  if (failed > 0) lamps.push({ label: `CHECKS · ${failed} FAILED`, on: true, tone: "fail" });
  if (running > 0)
    lamps.push({ label: failed > 0 ? `${running} RUNNING` : `CHECKS · ${running} RUNNING`, on: false, tone: "info" });
  if (!lamps.length && total > 0) lamps.push({ label: `CHECKS · ${total} PENDING`, on: false, tone: "info" });
  return lamps;
}

export function PRCard({
  number,
  title,
  checks,
  review,
  branch,
  base,
  sprite,
  "data-testid": testId,
}: PRCardProps) {
  const lamps = checks ? checkLamps(checks) : [];
  return (
    <article className="pr-card" aria-label={`Pull request #${number}: ${title}`} data-testid={testId}>
      <div className="pr-card-line">
        <img src={listSprite(sprite ?? objectSprite("pr", `pr-${number}`))} alt="" draggable={false} />
        <span className="pr-card-title">
          #{number} {title}
        </span>
      </div>
      {lamps.length || review ? (
        <div className="pr-card-line pr-card-facts">
          {lamps.map((lamp) => (
            <LampGadget key={lamp.label} label={lamp.label} on={lamp.on} tone={lamp.tone} />
          ))}
          {review ? (
            <span className="pr-card-fact">
              REVIEW <b>{review.toUpperCase()}</b>
            </span>
          ) : null}
        </div>
      ) : null}
      {branch ? (
        <div className="pr-card-line">
          <code className="pr-card-branch">
            {branch}
            {base ? ` → ${base}` : ""}
          </code>
        </div>
      ) : null}
    </article>
  );
}

export interface ChangedFile {
  path: string;
  added?: number;
  removed?: number;
}

export function FilesChanged({
  files,
  label = "Files changed",
  "data-testid": testId,
}: {
  files: ChangedFile[];
  label?: string;
  /** Pass-through data-testid for the file list (`ul`). */
  "data-testid"?: string;
}) {
  const shown = files.length;
  if (shown === 0) return null;
  return (
    <SurfaceSection label={`${label} · ${shown}`}>
      <ul className="files-changed" data-testid={testId}>
        {files.map((file) => {
          const counts = [
            file.added ? `+${file.added}` : "",
            file.removed ? `−${file.removed}` : "",
          ].filter(Boolean);
          return (
            <li key={file.path} className="files-changed-row">
              <code>{file.path}</code>
              {counts.length ? <span className="files-changed-counts">{counts.join(" ")}</span> : <span />}
            </li>
          );
        })}
      </ul>
    </SurfaceSection>
  );
}
