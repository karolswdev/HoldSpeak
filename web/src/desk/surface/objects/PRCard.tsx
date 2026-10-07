/** PHILO-14 B1 — PRCard and FilesChanged: the agent's work, inline in its
 *  lane (board A-4; C-4 puts them in the right column).
 *
 *  PRCard: the PR's sprite, `#413` and its title (primary step); then
 *  `CHECKS n OF m` as a lamp (fail when a check failed), `N RUNNING` when
 *  checks run, `REVIEW <word>`; then `branch → base` in mono. A raised
 *  plate: the card is the PR, the verb that opens it is the lane's
 *  (Open PR, in the footer, by the GITHUB.COM egress chip).
 *
 *  FilesChanged: the files the agent changed, one line each, the path in
 *  mono and its `+added −removed` counts; a zero count is not drawn.
 */
import { SurfaceSection } from "../Surface";
import { LampGadget } from "../gadgets";
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
}

export function PRCard({ number, title, checks, review, branch, base, sprite }: PRCardProps) {
  const failed = checks?.failed ?? 0;
  const running = checks?.running ?? 0;
  return (
    <article className="pr-card" aria-label={`Pull request #${number}: ${title}`}>
      <div className="pr-card-line">
        <img src={sprite ?? objectSprite("pr", `pr-${number}`)} alt="" draggable={false} />
        <span className="pr-card-title">
          #{number} {title}
        </span>
      </div>
      {checks || review ? (
        <div className="pr-card-line pr-card-facts">
          {checks && checks.total > 0 ? (
            <LampGadget
              label={`CHECKS ${checks.passed} OF ${checks.total}`}
              on
              tone={failed > 0 ? "fail" : "ok"}
            />
          ) : null}
          {failed > 0 ? <LampGadget label={`${failed} FAILED`} on tone="fail" /> : null}
          {running > 0 ? <LampGadget label={`${running} RUNNING`} on={false} /> : null}
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

export function FilesChanged({ files, label = "Files changed" }: { files: ChangedFile[]; label?: string }) {
  const shown = files.length;
  if (shown === 0) return null;
  return (
    <SurfaceSection label={`${label} · ${shown}`}>
      <ul className="files-changed">
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
