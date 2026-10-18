/** Betterment A5 — About, in place under its line (DESIGN §4).
 *
 * The chips he chose (each named, each with Remove), then the one About
 * picker (`../about/AboutPicker`, the same picker Ask uses). A press adds
 * the pick and saves at once; the typed text stays. People come from the
 * People list (read once; no list when People is not set up).
 *
 * Betterment A10: when With is an agent engine (Claude Code, Codex), About
 * also offers a Folder: a repository on the desk, or a path he adds. The
 * agent works in that folder, read only. */
import { useEffect, useMemo, useState } from "react";
import { useDesk } from "../../store";
import { apiFetch, readableError } from "../../../lib/api";
import { registerRepository } from "../../repository";
import { StringGadget } from "../../surface/gadgets";
import { Button } from "../../../components/signal/Signal";
import { AboutPicker, aboutCandidates, type AboutCandidate } from "../about/AboutPicker";
import type { AutomationSource } from "./model";

/** The People list's names (the palette reads the same route). */
function usePeopleNames(): Array<{ id: string; name: string }> {
  const [people, setPeople] = useState<Array<{ id: string; name: string }>>([]);
  useEffect(() => {
    let live = true;
    void apiFetch<{ relationships?: Array<Record<string, unknown>> }>("/api/people/relationships")
      .then((answer) => {
        if (!live) return;
        setPeople((answer?.relationships ?? [])
          .map((row) => ({ id: String(row.id ?? ""), name: String(row.display_name ?? "") }))
          .filter((row) => row.id && row.name));
      })
      .catch(() => undefined); // People not set up: no people to find
    return () => { live = false; };
  }, []);
  return people;
}

export function AboutChips({
  sources,
  onRemove,
  busy = false,
}: {
  sources: AutomationSource[];
  onRemove?: (ref: string) => void;
  busy?: boolean;
}) {
  if (!sources.length) return null;
  return (
    <span className="automation-chips" data-testid="automation-about-chips">
      {sources.map((source) => {
        const name = source.missing ? "Missing source"
          : source.kind === "folder" ? `Folder ${source.label}` : source.label;
        return (
          <span key={source.ref} className="surface-token" data-chip=""
            data-tone={source.missing ? "warn" : undefined}>
            {name}
            {onRemove ? (
              <Button dense variant="ghost" className="automation-chip-remove" disabled={busy}
                aria-label={`Remove ${name}`} onClick={() => onRemove(source.ref)}>
                ✕
              </Button>
            ) : null}
          </span>
        );
      })}
    </span>
  );
}

/** A10: the folders an agent can work in: the desk's repositories, and a
 *  path he adds (it becomes a repository on the desk). */
function FolderPicker({
  picked,
  busy,
  onPick,
}: {
  picked: readonly string[];
  busy: boolean;
  onPick: (ref: string) => void;
}) {
  const repositories = useDesk((state) => state.items.repository ?? []);
  const [path, setPath] = useState("");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const offered = repositories.filter((repo) => !picked.includes(`repository:${repo.id}`));
  const add = async () => {
    setAdding(true);
    setError(null);
    try {
      const { repository } = await registerRepository({ path: path.trim() });
      setPath("");
      onPick(`repository:${repository.id}`);
    } catch (failure) {
      setError(readableError(failure));
    } finally {
      setAdding(false);
    }
  };
  return (
    <div className="automation-folders" data-testid="automation-folders">
      {offered.length ? (
        <span className="automation-folder-list">
          {offered.map((repo) => (
            <Button key={repo.id} dense variant="ghost" disabled={busy}
              aria-label={`Add folder ${repo.name}`} onClick={() => onPick(`repository:${repo.id}`)}
              data-testid="automation-folder">
              Folder {repo.name}
            </Button>
          ))}
        </span>
      ) : null}
      <span className="automation-folder-add">
        <StringGadget label="Folder" value={path} onChange={setPath}
          placeholder="A repository folder on this Mac" />
        <Button dense variant="secondary" disabled={!path.trim() || busy} loading={adding}
          onClick={() => void add()} data-testid="automation-folder-add">
          Add folder
        </Button>
      </span>
      {error ? <p className="automation-refusal" role="alert">{error}</p> : null}
    </div>
  );
}

export function AboutEditor({
  sources,
  busy,
  onChange,
  folders = false,
}: {
  sources: AutomationSource[];
  busy: boolean;
  onChange: (refs: string[]) => void;
  /** A10: With is an agent engine, so a folder can be a source. */
  folders?: boolean;
}) {
  const items = useDesk((state) => state.items);
  const people = usePeopleNames();
  const candidates = useMemo(() => aboutCandidates(items, people), [items, people]);
  const refs = sources.map((source) => source.ref);
  const add = (pick: AboutCandidate) => {
    if (!refs.includes(pick.ref)) onChange([...refs, pick.ref]);
  };
  return (
    <div className="automation-about-editor" data-testid="automation-about-editor">
      <AboutChips sources={sources} busy={busy} onRemove={(ref) => onChange(refs.filter((r) => r !== ref))} />
      <AboutPicker candidates={candidates} picked={refs} onPick={add} busy={busy} />
      {folders ? (
        <FolderPicker picked={refs} busy={busy}
          onPick={(ref) => { if (!refs.includes(ref)) onChange([...refs, ref]); }} />
      ) : null}
    </div>
  );
}
