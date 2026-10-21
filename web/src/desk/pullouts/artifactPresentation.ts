import { lineage, type LineageEntry } from "../lineage";
import type { Items } from "../api";

const SYNTHESIS_FOOTER = /(?:^|\n)- Source windows: ([^\r\n]*)\r?\n- Source plugin runs: ([^\r\n]*)\s*$/;
const LEADING_HEADING = /^\ufeff?[ \t]*#{1,6}[ \t]+([^\r\n]+?)[ \t]*#*[ \t]*\r?\n(?:\r?\n)?/;
const ADR_EMPTY = /^adr_drafter:[ \t]*no architectural decisions found\.?$/i;

type SourceRecord = { source_type?: unknown; source_ref?: unknown; type?: unknown; ref?: unknown; source?: unknown; id?: unknown };

function sourceSets(sources: unknown): { windows: Set<string>; pluginRuns: Set<string> } {
  const windows = new Set<string>();
  const pluginRuns = new Set<string>();
  for (const raw of Array.isArray(sources) ? sources : []) {
    if (!raw || typeof raw !== "object") continue;
    const source = raw as SourceRecord;
    const type = String(source.source_type ?? source.type ?? "").trim().toLowerCase();
    const ref = String(source.source_ref ?? source.ref ?? source.source ?? source.id ?? "").trim();
    if (!ref) continue;
    if (type === "intent_window") windows.add(ref);
    if (type === "plugin_run") pluginRuns.add(ref);
  }
  return { windows, pluginRuns };
}

/** Remove only the synthesis footer when both lines match this artifact's own
 * source rows. Authored text with the same shape stays visible. */
export function withoutSynthesisFraming(body: string, sources: unknown): string {
  const { windows, pluginRuns } = sourceSets(sources);
  if (!windows.size && !pluginRuns.size) return body;
  const candidate = body.replace(/\r\n/g, "\n").replace(/\r/g, "\n").replace(/\n+$/, "");
  const match = SYNTHESIS_FOOTER.exec(candidate);
  if (!match) return body;
  const expectedWindows = windows.size ? [...windows].sort().join(", ") : "none";
  const expectedPluginRuns = pluginRuns.size ? [...pluginRuns].sort().join(", ") : "none";
  if (match[1] !== expectedWindows || match[2] !== expectedPluginRuns) return body;
  return candidate.slice(0, match.index).replace(/\n$/, "");
}

/** Remove one duplicate title heading. A normal body heading or any other
 * first line remains byte-for-byte intact. */
export function withoutDuplicateHeading(body: string, title: string): string {
  if (!title.trim()) return body;
  const match = LEADING_HEADING.exec(body);
  if (!match || match[1].trim() !== title.trim()) return body;
  return body.slice(match[0].length);
}

export interface ArtifactSourcePresentation extends LineageEntry {
  via: boolean;
}

export interface ArtifactPresentation {
  body: string;
  isEmptyResult: boolean;
  emptyLabel: string;
  sources: ArtifactSourcePresentation[];
}

/** Shared reading presentation. `bodyMarkdown` remains the source of truth for
 * Copy and Send; this body is only the quiet reader view. */
export function presentArtifact({
  title,
  artifactType,
  bodyMarkdown,
  sources,
  items,
}: {
  title: string;
  artifactType: string;
  bodyMarkdown: string;
  sources: unknown;
  items: Items;
}): ArtifactPresentation {
  const framed = withoutSynthesisFraming(bodyMarkdown, sources);
  const body = withoutDuplicateHeading(framed, title);
  const adrEmpty = artifactType.trim().toLowerCase() === "adr" && ADR_EMPTY.test(body.trim());
  const isEmptyResult = adrEmpty || body.trim().length === 0;
  const lin = lineage(items, sources);
  const sourceEntries = [
    ...(lin.via ? [{ ...lin.via, via: true }] : []),
    ...lin.from.map((entry) => ({ ...entry, via: false })),
  ];
  return {
    body: adrEmpty ? "" : body,
    isEmptyResult,
    emptyLabel: adrEmpty ? "No architecture decisions found" : "No material recorded",
    sources: sourceEntries,
  };
}
