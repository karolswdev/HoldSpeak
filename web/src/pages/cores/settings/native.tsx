/* Settings in the language (2026-11-11; the Programs, People and Agents
 * pattern): the section's MAST (its sprite, its name, the one facts line),
 * the PLATE (the one thing that matters now in the section, with its one
 * verb) and the LEDGER (the section's settings as rows: label, value in
 * mono, one verb each; a row's editor opens under it in place). */
import type { ReactNode } from "react";
import { Mast } from "../../../desk/surface/patterns/Mast";
import { SurfaceLedger, SurfaceLedgerRow } from "../../../desk/surface";
import { spriteUrl } from "../../../desk/sprites";
import type { SettingsSectionId } from "./prefs";
import { ShowMe } from "../../../desk/walk/ShowMe";

const SPRITES = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/settings/`;
const WORLD: Partial<Record<SettingsSectionId, { kind: string; id: string; agent?: string }>> = {
  you: { kind: "person", id: "settings-you" },
  meetings: { kind: "meeting", id: "settings-meetings" },
  agents: { kind: "agent", id: "settings-agents", agent: "codex" },
};

/** The section's sprite: the desk's own sprite where the section is an
 *  object of the desk, the settings mold elsewhere. */
export function sectionSprite(id: SettingsSectionId, sprite: string): string {
  const world = WORLD[id];
  return world ? spriteUrl(world.kind, world.id, "rest", world.agent, 32) : `${SPRITES}${sprite}.png`;
}

export function SectionMast({ id, label, sprite, facts, children }: {
  id: SettingsSectionId;
  label: string;
  sprite: string;
  facts?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <Mast kind="settings" glyph={sectionSprite(id, sprite)} className="settings-mast" data-testid={`settings-mast-${id}`}
      title={<span id={`settings-section-title-${id}`}>{label}</span>} facts={facts || undefined}>
      {children}

    </Mast>
  );
}

export type PlateTone = "moss" | "brass" | "coral" | "steel";

/** The one raised thing of a section: its head (title, facts in mono), its
 *  body and its verbs. The meaning colour is the top edge, never a fill. */
export function SettingsPlate({ tone, title, facts, verbs, children, testId }: {
  tone: PlateTone;
  title: ReactNode;
  facts?: ReactNode;
  verbs?: ReactNode;
  children?: ReactNode;
  testId: string;
}) {
  return (
    <article className="settings-plate" data-tone={tone} data-testid={testId}>
      <header className="settings-plate-head">
        <h3 className="settings-plate-title">{title}</h3>
        {facts ? <span className="settings-plate-facts">{facts}</span> : null}
      </header>
      {children}
      {verbs ? <div className="settings-plate-verbs">{verbs}</div> : null}
    </article>
  );
}

/** The section's settings, one row each. */
export function SettingsLedger({ label, children }: { label: string; children: ReactNode }) {
  return (
    <section className="settings-ledger" aria-label={label}>
      <SurfaceLedger cols="settings-rows" label={label}>{children}</SurfaceLedger>
    </section>
  );
}

/** One setting: its label, its value (mono) and its one verb. With
 *  `children` and `open`, the row's editor stands under it in place. */
export function SettingLine({ label, value, verb, open, children, testId }: {
  label: string;
  value?: ReactNode;
  verb?: ReactNode;
  open?: boolean;
  children?: ReactNode;
  testId?: string;
}) {
  return (
    <SurfaceLedgerRow
      primary={label}
      cells={value != null && value !== "" ? <span className="settings-line-value">{value}</span> : <span />}
      trailing={verb ?? undefined}
      expands={false}
      open={open}
      data-testid={testId}
    >
      {children}
    </SurfaceLedgerRow>
  );
}
