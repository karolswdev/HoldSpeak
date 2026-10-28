/** PHILO-14 B1 — PRCard and FilesChanged: the agent's work, inline in its
 *  lane (board A-4; C-4 puts them in the right column).
 *
 *  PRCard: the PR's sprite, `#413` and its title (primary step); then
 *  `Checks n of m` as a dot + words (fail when a check failed), `N running`
 *  when checks run, `Review <word>` (W6-H words: sentence case, sans); then
 *  `branch → base` in mono. A raised
 *  FLAT card (read-only facts): the verb that opens it is the lane's
 *  (Open PR, in the footer, by the GITHUB.COM egress chip).
 *
 *  FilesChanged: the files the agent changed, one line each, the path in
 *  mono and its `+added −removed` counts; a zero count is not drawn.
 */
import { SurfaceSection } from "../Surface";
import { DotWord } from "../kit";
import { listSprite } from "../../sprites";
import { objectSprite } from "./kinds";
import "./objects.css";

export interface PRCardProps {
  number: number;
  /** The PR's own title (GitHub's). */
  title: string;
  /** PHILO-15 B50: the desk item the PR is for, as the second line. */
  item?: string;
  checks?: { passed: number; total: number; failed?: number; running?: number };
  /** `none yet`, `approved`, `changes asked` (any case; drawn lower case). */
  review?: string;
  branch?: string;
  base?: string;
  sprite?: string;
  /** Pass-through data-testid for the root `article`. */
  "data-testid"?: string;
}

/** The checks as dot + words, never a counter of zero (UX-CANON A.8):
 *  some passed → `Checks p of t` (fail tone when one failed) + `N failed` +
 *  `N running`; none passed yet → `Checks · N running` / `Checks · N failed`
 *  / `Checks · N pending`, with no `0 of`. */
function checkLamps(checks: NonNullable<PRCardProps["checks"]>) {
  const { passed, total } = checks;
  const failed = checks.failed ?? 0;
  const running = checks.running ?? 0;
  if (total <= 0) return [];
  const lamps: { label: string; tone: "ok" | "fail" | "info" | "idle" }[] = [];
  if (passed > 0) {
    lamps.push({ label: `Checks ${passed} of ${total}`, tone: failed > 0 ? "fail" : "ok" });
    if (failed > 0) lamps.push({ label: `${failed} failed`, tone: "fail" });
    if (running > 0) lamps.push({ label: `${running} running`, tone: "info" });
    return lamps;
  }
  if (failed > 0) lamps.push({ label: `Checks · ${failed} failed`, tone: "fail" });
  if (running > 0)
    lamps.push({ label: failed > 0 ? `${running} running` : `Checks · ${running} running`, tone: "info" });
  if (!lamps.length && total > 0) lamps.push({ label: `Checks · ${total} pending`, tone: "idle" });
  return lamps;
}

export function PRCard({
  number,
  title,
  item,
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
      {item && item !== title ? (
        <div className="pr-card-line">
          <span className="pr-card-item" data-testid={testId ? `${testId}-item` : undefined}>
            {item}
          </span>
        </div>
      ) : null}
      {lamps.length || review ? (
        <div className="pr-card-line pr-card-facts">
          {lamps.map((lamp) => (
            <DotWord key={lamp.label} tone={lamp.tone}>{lamp.label}</DotWord>
          ))}
          {review ? (
            <span className="pr-card-fact">
              Review <b>{review.toLowerCase()}</b>
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
