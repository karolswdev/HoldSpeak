/** Agents uses the same grouped selection list as the other Desk apps. */
import { useState, useRef, type ReactNode } from "react";
import { ListPane, ListView, StringGadget, type ObjectListRow, type ListVerb } from "../surface";
import { agentWord, memberTitle, agoWord } from "./AgentPane";
import { useCompactViewport } from "../useCompactViewport";
import { useWindowBack, useHasWindowBack } from "../surface/back";
import type { ConductorMember } from "./members";

export interface RailSection {
  id: "asks" | "running" | "ended" | "installed";
  word: string;
  rows: Array<{ member: ConductorMember; group: string; helperOf?: string }>;
}
export function AgentRail({
  sections,
  picked,
  paneOpen,
  onBack,
  pillOf,
  onPick,
  onSelect,
  verbs,
  children,
}: {
  sections: readonly RailSection[];
  picked: string | null;
  paneOpen: boolean;
  onBack(): void;
  pillOf(member: ConductorMember): { word: string; tone: string };
  onPick(id: string): void;
  onSelect(id: string): void;
  verbs: readonly ListVerb[];
  children: ReactNode;
}) {
  const compact = useCompactViewport(),
    hosted = useHasWindowBack();
  const back = useRef(onBack);
  back.current = onBack;
  useWindowBack(compact && paneOpen ? { label: "Back", testId: "agents-back", onBack: () => back.current() } : null, [
    compact,
    paneOpen,
  ]);
  const [query, setQuery] = useState("");
  const [finding, setFinding] = useState(false);
  const all = sections.flatMap((section, group) =>
    section.rows.map(({ member, helperOf, group: kind }) => {
      const pill = pillOf(member);
      const tone: NonNullable<ObjectListRow["state"]>["tone"] =
        member.live === "pr"
          ? "info"
          : pill.tone === "danger"
            ? "fail"
            : pill.tone === "warn"
              ? "ask"
              : pill.tone === "ok"
                ? "ok"
                : pill.tone === "info"
                  ? "info"
                  : "idle";
      return {
        id: member.id,
        kind: "agent",
        name: memberTitle(member),
        group,
        detail: [
          helperOf
            ? `Helper of ${helperOf}`
            : member.role === "ready"
              ? ""
              : String(member.facts.where || agentWord(member)),
          member.deskAnswer?.state === "answered" && member.deskAnswer.isNew ? "The desk answered · New" : "",
        ]
          .filter(Boolean)
          .join(" · "),
        leadingLamp: {
          state:
            tone === "info"
              ? "working"
              : tone === "ask"
                ? "waiting"
                : tone === "ok"
                  ? "done"
                  : tone === "fail"
                    ? "failed"
                    : "off",
          label: pill.word,
        },
        cells: { agent: member.role === "ready" ? "" : agentWord(member) },
        when: agoWord(member.when),
        state: { label: pill.word, tone, testId: "conductor-pill" },
        member,
        rowKind: kind,
        helperOf,
      } satisfies ObjectListRow & {
        member: ConductorMember;
        rowKind: string;
        helperOf?: string;
      };
    }),
  );
  const rows: ObjectListRow[] = all.filter((row) =>
    `${row.name} ${row.detail} ${row.cells.agent} ${row.state.label}`.toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <ListPane
      deck
      hostBack={compact && hosted}
      open={paneOpen && (!picked || rows.some((row) => row.id === picked))}
      onBack={onBack}
      onReveal={() => {
        if (picked) onPick(picked);
      }}
      label="Selected agent"
      listTestId="agents-list"
      previewTestId="agents-pane"
      list={
        <ListView
          label="Agents"
          selection
          ordered
          rows={rows}
          selectedId={picked}
          onSelect={onSelect}
          onOpen={onPick}
          columns={[
            { key: "name", word: "Session", track: "minmax(160px, 2fr)" },
            { key: "agent", word: "Agent", priority: 1, minWidth: 144 },
            { key: "state", word: "State", priority: 2, minWidth: 112 },
            { key: "when", word: "Since", minWidth: 88 },
          ]}
          groups={sections.map((section, id) => ({ id, label: section.word }))}
          verbs={[
            ...verbs,
            {
              id: "find",
              label: finding ? "Close Find" : "Find",
              enabled: () => true,
              run: () => {
                setFinding(!finding);
                setQuery("");
              },
            },
          ]}
          toolbar={{
            trailing: finding ? (
              <StringGadget label="Find a session" value={query} onChange={setQuery} placeholder="Find a session" />
            ) : undefined,
          }}
          rowProps={(row) => ({
            "data-testid": "conductor-row",
            "data-group": all.find((item) => item.id === row.id)?.rowKind,
            "data-helper": all.find((item) => item.id === row.id)?.helperOf ? "" : undefined,
          })}
        />
      }
    >
      {picked && !rows.some((row) => row.id === picked) ? null : children}
    </ListPane>
  );
}
