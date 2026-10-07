/** PHILO-14 C4 — Get Info on a Conductor member: a window of its own (the
 *  drawer's Get Info, board A-2 right).
 *
 *  A ready agent: VERSION, HOOKS, SIGN-IN (the agents read), with Install
 *  hooks or Copy install. A launched agent: the item, the Project, the
 *  branch, LAUNCHED and CONTROL from the lane route's `launch` block
 *  (`GET /api/agent/launches/{id}/lane`, lane C0), with Open, Answer, Stop.
 */
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { DeskWindowFrame } from "../components/DeskWindow";
import { GetInfo, SurfaceFooter, type GetInfoFacts } from "../surface";
import { windowName } from "../windowName";
import { madeWord } from "../drawer/members";
import { MemberReceipt, MemberVerbs } from "./ConductorWindow";
import { readyMember, type ConductorMember } from "./members";
import { conductorInfoId, useConductor } from "./store";

interface LaunchBlock {
  branch?: string | null;
  launched_at?: string | null;
  control_mode?: string | null;
}

const CONTROL_WORD: Record<string, string> = { safe: "SECURE", secure: "SECURE", normal: "NORMAL", yolo: "YOLO" };

/** The launch facts the lane route holds, added to the member's own. */
export function launchFacts(base: GetInfoFacts, launch: LaunchBlock | null, now: Date = new Date()): GetInfoFacts {
  if (!launch) return base;
  const control = String(launch.control_mode ?? "").toLowerCase();
  return {
    ...base,
    branch: launch.branch || base.branch,
    made: undefined,
    more: [
      ...(base.more ?? []),
      { key: "launched", word: "Launched", value: madeWord(launch.launched_at, now) },
      { key: "control", word: "Control", value: CONTROL_WORD[control] ?? control.toUpperCase() },
    ],
  };
}

export function ConductorInfoWindow({ member }: { member: ConductorMember }) {
  const live = useConductor((s) => s.detect?.agents.find((a) => a.id === member.detect?.id));
  const [launch, setLaunch] = useState<LaunchBlock | null>(null);
  const [launchFailed, setLaunchFailed] = useState(false);
  useEffect(() => {
    if (!member.launchId) return;
    let alive = true;
    apiFetch<{ launch?: LaunchBlock } | null>(
      `/api/agent/launches/${encodeURIComponent(member.launchId)}/lane?after=0&limit=1`,
    )
      .then((body) => {
        if (alive) setLaunch(body?.launch ?? null);
      })
      .catch(() => {
        if (alive) setLaunchFailed(true);
      });
    return () => {
      alive = false;
    };
  }, [member.launchId]);

  // A ready agent re-reads its own row (Install hooks changes it).
  const current: ConductorMember = live ? readyMember(live) : member;
  const facts = launchFacts(current.facts, launch);
  const title = windowName({ kind: "info", name: member.name });
  return (
    <DeskWindowFrame
      id={conductorInfoId(member.ref)}
      title={title}
      label={title}
      glyph="ⓘ"
      icon={<img className="drawer-winicon" src={member.sprite} alt="" />}
      className="desk-pullout drawer-info-window conductor-info-window"
      minW={300}
      minH={240}
      defaultW={520}
      defaultH={420}
      open
      onClose={() => useConductor.getState().closeInfo(member.ref)}
    >
      <div className="desk-pullout-body drawer-body" data-testid="conductor-info">
        <div className="drawer-scroll">
          <GetInfo
            id={member.id}
            kind={member.kind}
            name={member.name}
            kindWord={member.kindWord}
            sprite={member.sprite}
            facts={facts}
          />
        </div>
      </div>
      <SurfaceFooter
        className="cw-footer"
        receipt={
          launchFailed ? (
            <span className="drawer-receipt" data-tone="fail" role="status">
              LAUNCH · NOT READ
            </span>
          ) : (
            <MemberReceipt member={current} />
          )
        }
        verbs={<MemberVerbs member={current} />}
      />
    </DeskWindowFrame>
  );
}
