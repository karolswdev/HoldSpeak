// Parked: wave 13 replaces the Agents cards with kit selection and inspection.
import { Button } from "../../components/signal/Signal";
import { Rail, ToolGlyph } from "../surface";
import { listSprite } from "../sprites";
import { agentWord, memberTitle, spineTone } from "./AgentPane";
import type { ConductorMember } from "./members";

export interface RailSection {
  id: "asks" | "running" | "ended" | "installed";
  word: string;
  rows: Array<{ member: ConductorMember; group: string; helperOf?: string }>;
}

export function AgentRail({ sections, picked, starting, paneOpen, onBack, pillOf, onPick, onStart }: {
  sections: readonly RailSection[]; picked: string | null; starting: boolean; paneOpen: boolean; onBack(): void;
  pillOf(member: ConductorMember): { word: string }; onPick(id: string): void; onStart(): void;
}) {
  return <Rail label="Agents" data-testid="agents-rail" picked={picked} onPick={onPick}
    paneOpen={paneOpen} onBack={onBack}
    head={<Button dense variant="primary" aria-expanded={starting} onClick={onStart} data-testid="conductor-start"><ToolGlyph kind="new" />Start an agent</Button>}
    groups={sections.map((section) => ({
      id: section.id, label: section.word, testId: "conductor-list", labelTestId: "conductor-section",
      items: section.rows.map(({ member, group, helperOf }) => ({
        id: member.id, label: memberTitle(member), accessibleLabel: memberTitle(member),
        glyph: <img src={listSprite(member.sprite ?? "")} alt="" draggable={false} />,
        state: <span data-testid="conductor-pill">{pillOf(member).word}</span>,
        facts: <>{helperOf ? `Helper of ${helperOf}` : member.role === "ready" ? "" : agentWord(member)}
          {member.deskAnswer?.state === "answered" && member.deskAnswer.isNew ? <> · <span data-testid="agents-tile-new">The desk answered · New</span></> : null}</>,
        spine: { tone: spineTone(member) },
        rowData: { "data-object-id": member.id, "data-testid": "conductor-row", "data-group": group, "data-helper": helperOf ? "" : undefined },
      })),
    }))} />;
}
