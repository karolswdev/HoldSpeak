import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../lib/api";
import type { RepoFile } from "../repository";

export interface RepositoryReadAdapter {
  tree(path: string): Promise<RepoFile[]>;
  file(path: string): Promise<string>;
}

export interface BrowserEntry {
  path: string;
  files: RepoFile[];
  loaded: boolean;
  selectedPath: string | null;
  inspection: { path: string; content: string; retained: boolean } | null;
}

export interface BrowserFailure {
  kind: "tree" | "file";
  path: string;
  message: string;
}

export interface RepositoryBrowserController {
  entry: BrowserEntry;
  busy: "tree" | "file" | null;
  failure: BrowserFailure | null;
  canBack: boolean;
  canForward: boolean;
  navigate(path: string): void;
  back(): void;
  forward(): void;
  inspect(path: string): void;
  closeInspection(): void;
  retry(): void;
  refresh(): void;
}

type BrowserModel = {
  entries: BrowserEntry[];
  index: number;
  busy: "tree" | "file" | null;
  failure: BrowserFailure | null;
};

const entryAt = (model: BrowserModel) => model.entries[model.index];
const emptyEntry = (path: string): BrowserEntry => ({ path, files: [], loaded: false, selectedPath: null, inspection: null });

/** A view-local read controller. A request owns the captured path and generation;
 * neither a late success nor a late refusal may change a newer view. */
export function useRepositoryBrowser(adapter: RepositoryReadAdapter, initialPath = ""): RepositoryBrowserController {
  const [model, setState] = useState<BrowserModel>(() => ({ entries: [emptyEntry(initialPath)], index: 0, busy: "tree", failure: null }));
  const modelRef = useRef(model);
  const generation = useRef(0);
  const alive = useRef(true);
  const setModel = (next: BrowserModel) => { modelRef.current = next; setState(next); };
  const update = (change: (current: BrowserModel) => BrowserModel) => setModel(change(modelRef.current));

  const readTree = (path: string, mode: "push" | "refresh") => {
    const request = ++generation.current;
    update((current) => ({ ...current, busy: "tree", failure: null,
      entries: mode === "refresh" ? current.entries.map((entry, index) => index === current.index && entry.inspection
        ? { ...entry, inspection: { ...entry.inspection, retained: true } } : entry) : current.entries,
    }));
    void adapter.tree(path).then((files) => {
      if (!alive.current || request !== generation.current) return;
      const inspectedPath = mode === "refresh" ? entryAt(modelRef.current).inspection?.path : null;
      const missingInspection = Boolean(inspectedPath && !files.some((file) => file.type === "file" && file.path === inspectedPath));
      update((current) => {
        const previous = entryAt(current);
        const nextEntry = mode === "refresh"
          ? { ...previous, files, loaded: true, selectedPath: files.some((file) => file.path === previous.selectedPath) ? previous.selectedPath : null }
          : { ...emptyEntry(path), files, loaded: true };
        const entries = mode === "refresh"
          ? current.entries.map((entry, index) => index === current.index ? nextEntry : entry)
          : [...current.entries.slice(0, current.index + 1), nextEntry];
        return { entries, index: mode === "refresh" ? current.index : entries.length - 1, busy: null,
          failure: missingInspection ? { kind: "file", path: inspectedPath!, message: `NOT FOUND · ${inspectedPath}` } : null };
      });
      if (inspectedPath && !missingInspection) inspect(inspectedPath);
    }).catch((error: unknown) => {
      if (!alive.current || request !== generation.current) return;
      update((current) => ({ ...current, busy: null, failure: { kind: "tree", path,
        message: `${error instanceof ApiError && error.status === 404 ? "NOT FOUND" : "READ REFUSED"} · ${path || "root"}` } }));
    });
  };

  useEffect(() => {
    alive.current = true;
    readTree(initialPath, "refresh");
    return () => { alive.current = false; generation.current += 1; };
    // The owner keys this controller by view identity. Adapter identity is stable.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const move = (index: number) => {
    const current = modelRef.current;
    if (index < 0 || index >= current.entries.length) return;
    generation.current += 1;
    setModel({ ...current, index, busy: null, failure: null });
    if (!current.entries[index].loaded) readTree(current.entries[index].path, "refresh");
  };
  const inspect = (path: string) => {
    const request = ++generation.current;
    update((current) => ({ ...current, busy: "file", failure: null,
      entries: current.entries.map((entry, index) => index === current.index && entry.inspection
        ? { ...entry, inspection: { ...entry.inspection, retained: true } } : entry),
    }));
    void adapter.file(path).then((content) => {
      if (!alive.current || request !== generation.current) return;
      update((current) => ({
        ...current, busy: null, failure: null,
        entries: current.entries.map((entry, index) => index === current.index
          ? { ...entry, selectedPath: path, inspection: { path, content, retained: false } }
          : entry),
      }));
    }).catch((error: unknown) => {
      if (!alive.current || request !== generation.current) return;
      update((current) => ({ ...current, busy: null, failure: { kind: "file", path,
        message: `${error instanceof ApiError && error.status === 404 ? "NOT FOUND" : "READ REFUSED"} · ${path}` } }));
    });
  };
  const entry = entryAt(model);
  return {
    entry,
    busy: model.busy,
    failure: model.failure,
    canBack: model.index > 0 || Boolean(model.failure?.kind === "tree" && model.failure.path !== entry.path),
    canForward: model.index < model.entries.length - 1,
    navigate: (path) => { if (path !== modelRef.current.entries[modelRef.current.index].path) readTree(path, "push"); },
    back: () => {
      const current = modelRef.current;
      if (current.failure?.kind === "tree" && current.failure.path !== entryAt(current).path) {
        update((state) => ({ ...state, failure: null }));
      } else move(current.index - 1);
    },
    forward: () => move(modelRef.current.index + 1),
    inspect,
    closeInspection: () => {
      generation.current += 1;
      update((current) => ({ ...current, busy: null, failure: null, entries: current.entries.map((item, index) => index === current.index ? { ...item, inspection: null } : item) }));
    },
    retry: () => {
      const failed = modelRef.current.failure;
      if (!failed) return;
      if (failed.kind === "tree") readTree(failed.path, failed.path === entryAt(modelRef.current).path ? "refresh" : "push");
      else inspect(failed.path);
    },
    refresh: () => readTree(entryAt(modelRef.current).path, "refresh"),
  };
}
