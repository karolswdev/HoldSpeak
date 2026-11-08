// The Room's row marks: the lifecycle chip and each source's object glyph.
import { Token } from "../../../desk/surface/Token";
import { lifecycleLabel } from "../model";

export function LifecycleChip({ row }: { row: Record<string, unknown> }) {
  const lifecycle = String(row.lifecycle || "recorded");
  const tone =
    lifecycle === "accepted"
      ? "ok"
      : lifecycle === "rejected"
        ? "danger"
        : undefined;
  return (
    <Token className="surface-token" data-tone={tone}>
      {lifecycleLabel(row)}
    </Token>
  );
}

export function DecisionPromotionSlot({
  decision,
  onOpenArtifact,
}: {
  decision: Record<string, unknown>;
  onOpenArtifact?(artifactId: string): void;
}) {
  if (String(decision.lifecycle) !== "accepted") return null;
  return null;
}

/* ── provider emblems ── */

const PROVIDER_EMBLEM: Record<string, string> = {
  github: "GH",
  jira: "J",
  confluence: "C",
  meeting: "MTG",
  proposal: "MTG",
  delta: "◇",
  room: "▣",
};

export function emblemFor(source: string): string {
  const key = source.toLowerCase();
  return PROVIDER_EMBLEM[key] || source.slice(0, 2).toUpperCase();
}

/** PHILO-17 refit: a row's object as its pixel sprite (the desk's own
 *  icons); the short word stays for a source with no sprite. */
const SPRITES = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/32/`;
const SOURCE_SPRITE: Record<string, string> = {
  github: "pull-request",
  jira: "action-item",
  confluence: "note",
  meeting: "meeting",
  proposal: "meeting",
  item: "action-item",
  decision: "decision",
};

export function RowSprite({ source, kind }: { source: string; kind?: string }) {
  const sprite = SOURCE_SPRITE[source.toLowerCase()] ?? (kind === "decision" ? "decision" : null);
  if (!sprite) return <>{emblemFor(source)}</>;
  return (
    <span className="room-row-sprite" title={emblemFor(source)}>
      <img src={`${SPRITES}${sprite}.png`} alt="" draggable={false} />
    </span>
  );
}

/** A source's object glyph (GitHub a pull request, Jira an action item),
 *  for the Room window's Sources (W3-B: no `GH`/`J` plates). */
export const SourceGlyph = RowSprite;
