/* Programs (design §5, §9 item 4; canvas "The Gate fold, open"): the gate
 * of the selected step. The track in words, the check command, the verdict
 * the verifier read from the log (not the exit code), the sections as
 * DotWords, and Open log (the log in a Note pullout). */
import { Button } from "../../components/signal/Signal";
import { DotWord, FoldGadget, SurfaceCode } from "../surface";
import { stateWords } from "../surface/words";
import { openRef } from "../openObject";
import { stationsOf } from "./model";
import { StationTrack } from "./StationTrack";
import type { CheckSection, ProgramStep } from "./types";

function sectionTone(state: string) {
  if (state === "green") return "ok" as const;
  if (state === "red") return "fail" as const;
  return "idle" as const;
}

function sectionWord(section: CheckSection): string {
  const name = stateWords(section.name.charAt(0).toUpperCase() + section.name.slice(1));
  if (section.state === "green") return name;
  if (section.state === "red") return section.detail ? `${name} · ${section.detail}` : name;
  return `${name} · ${section.state || "not run"}`;
}

/** `Checked · green · 3 min · on 4c1e9a2`, `Check failed · 4 min · round 1 of 2`. */
export function verdictWords(step: ProgramStep): string {
  const check = step.check;
  if (check.running) return "Checking";
  if (!check.verdict) return "Not checked yet";
  const parts = [check.verdict === "green" ? "Checked · green" : "Check failed"];
  if (check.minutes != null) parts.push(`${check.minutes} min`);
  if (check.commit) parts.push(`on ${check.commit.slice(0, 7)}`);
  if (check.verdict !== "green" && step.rounds) parts.push(`round ${step.rounds} of 2`);
  return parts.join(" · ");
}

export function GateFold({ step, open, onToggle }: { step: ProgramStep; open?: boolean; onToggle?: (open: boolean) => void }) {
  const check = step.check;
  const tone = check.verdict === "green" ? "ok" : check.verdict ? "fail" : "idle";
  return (
    <FoldGadget className="pg-gate" title={<>Gate<span className="pg-fold-sub">{` · step ${step.ordinal}, ${step.title}`}</span></>} open={open} onToggle={onToggle}>
      <dl className="pg-gate-facts" data-testid="programs-gate">
        <dt>Track</dt>
        <dd><StationTrack form="words" stations={stationsOf(step)} data-testid="programs-gate-track" /></dd>
        {check.command ? (<><dt>Command</dt><dd><SurfaceCode>{check.command}</SurfaceCode></dd></>) : null}
        <dt>Verdict</dt>
        <dd><DotWord tone={tone} data-testid="programs-gate-verdict">{verdictWords(step)}</DotWord>
          {check.reasons.length ? <span className="pg-gate-reason"> · {check.reasons[0]}</span> : null}</dd>
        {check.sections.length ? (
          <>
            <dt>Sections</dt>
            <dd className="pg-gate-sections">
              {check.sections.map((section) => (
                <DotWord key={section.name} tone={sectionTone(section.state)} data-testid="programs-gate-section">{sectionWord(section)}</DotWord>
              ))}
            </dd>
          </>
        ) : null}
        {check.log ? (
          <>
            <dt className="pg-gate-blank" aria-hidden="true" />
            <dd>
              <Button dense variant="secondary" onClick={() => openRef(check.log!.startsWith("note:") ? check.log! : `note:${check.log}`)}
                data-testid="programs-open-log">Open log</Button>
            </dd>
          </>
        ) : null}
      </dl>
    </FoldGadget>
  );
}
