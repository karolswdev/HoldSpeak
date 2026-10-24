import { useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import {
  checkout,
  commit,
  fetchBranches,
  fetchStatus,
  fetchFile,
  fetchTree,
  stageFiles,
  type RepoStatus,
} from "../repository";
import { usePrReceipts, type PrRow } from "../prReceipts";
import { SurfaceState } from "../surface/Surface";
import { SurfaceWings } from "../surface/wings";
import { CycleGadget, StringGadget } from "../surface/gadgets";
import { DeskSortableTable, type Column } from "./DeskSortableTable";
import { useRepositoryBrowser } from "./RepositoryBrowserController";
import { RepositoryBrowserView } from "./RepositoryBrowserView";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { DeskWindowFrame } from "./DeskWindow";
import "./RepoWindow.css";

const WINGS = [
  { id: "files", label: "Files" },
  { id: "prs", label: "PRs" },
  { id: "issues", label: "Issues" },
];

type PrSortKey = "number" | "title" | "state" | "ci" | "author";

export function RepoWindow({
  repositoryId,
  windowId,
  initialPath,
  origin,
}: {
  repositoryId: string;
  /** Full frame id; omitted by old callers for the default repository view. */
  windowId?: string;
  initialPath?: string;
  origin?: { x: number; y: number } | null;
}) {
  const frameId = windowId ?? `repository:${repositoryId}`;
  const repository = useDesk((s) => (s.items.repository || []).find((item) => item.id === repositoryId));
  const [wing, setWing] = useState("files");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [status, setStatus] = useState<RepoStatus | null>(null);
  const [branches, setBranches] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState<(() => void) | null>(null);
  const [prSort, setPrSort] = useState<{ key: PrSortKey; dir: "asc" | "desc" }>({ key: "number", dir: "desc" });
  const readAdapter = useMemo(() => ({
    tree: (path: string) => fetchTree(repositoryId, path),
    file: (path: string) => fetchFile(repositoryId, path),
  }), [repositoryId]);
  const browser = useRepositoryBrowser(readAdapter, initialPath ?? "");
  const prsLoaded = usePrReceipts((s) => s.loaded);
  const loadPrs = usePrReceipts((s) => s.load);
  const prSource = usePrReceipts((s) => s.sources.find((source) => source.source_id === repositoryId));

  const refreshMeta = async () => {
    setError("");
    setRetry(null);
    try {
      const [nextStatus, nextBranches] = await Promise.all([fetchStatus(repositoryId), fetchBranches(repositoryId)]);
      setStatus(nextStatus);
      setBranches(nextBranches);
    } catch {
      setError("Git status unavailable");
    }
  };

  useEffect(() => { void refreshMeta(); }, [repositoryId]);
  useEffect(() => { if (!prsLoaded) void loadPrs(); }, [prsLoaded, loadPrs]);
  useEffect(() => { setSelected(new Set()); }, [browser.entry.path]);

  const prs = useMemo(() => {
    const rows = [...(prSource?.prs || [])];
    const factor = prSort.dir === "asc" ? 1 : -1;
    return rows.sort((a, b) => {
      const av = String(a[prSort.key] ?? "");
      const bv = String(b[prSort.key] ?? "");
      return prSort.key === "number" ? factor * (Number(av) - Number(bv)) : factor * av.localeCompare(bv);
    });
  }, [prSource?.prs, prSort]);

  if (!repository) return null;
  const name = String(repository.name || "Repository");
  const location = browser.entry.path ? `/${browser.entry.path}` : "/";
  const branch = status?.branch || String(repository.branch || "detached");
  const toggleFile = (filePath: string) => setSelected((current) => {
    const next = new Set(current);
    if (next.has(filePath)) next.delete(filePath); else next.add(filePath);
    return next;
  });
  const stage = async () => {
    if (!selected.size) return;
    setBusy(true); setError("");
    try { await stageFiles(repositoryId, [...selected]); setSelected(new Set()); browser.refresh(); await refreshMeta(); }
    catch {
      setError("STAGE FAILED");
      setRetry(() => () => void stage());
    }
    finally { setBusy(false); }
  };
  const commitSelected = async () => {
    if (!message.trim()) return;
    setBusy(true); setError("");
    try { await commit(repositoryId, message); setMessage(""); setSelected(new Set()); browser.refresh(); await refreshMeta(); }
    catch {
      setError("COMMIT FAILED");
      setRetry(() => () => void commitSelected());
    }
    finally { setBusy(false); }
  };

  const prColumns: Column<PrRow>[] = [
    { key: "number", label: "PR", sortable: true, width: "56px", render: (pr) => `#${pr.number}` },
    { key: "title", label: "Title", sortable: true, render: (pr) => pr.title },
    { key: "state", label: "State", sortable: true, render: (pr) => <span className="repo-pr-state" data-state={pr.state}>{pr.state}</span> },
    { key: "ci", label: "CI", sortable: true, render: (pr) => <span className="repo-pr-ci" data-ci={pr.ci}>{pr.ci}</span> },
    { key: "author", label: "Author", sortable: true, render: (pr) => pr.author || "—" },
  ];

  return (
    <DeskWindowFrame
      id={frameId}
      glyph="▤"
      label={`${name} · ${location}`}
      title={<><span>{name}</span><span className="repo-location" title={location}>{location}</span><span className="repo-branch">{branch}</span>{status?.dirty ? <span className="repo-dirty">{status.dirty} dirty</span> : null}</>}
      icon={<img src={spriteUrl("repository", repositoryId)} alt="" width={30} height={30} />}
      minW={600}
      minH={390}
      open
      origin={origin}
      preserveInitialRect={frameId !== `repository:${repositoryId}`}
      onClose={() => useDesk.getState().closeRepositoryWindow(frameId.slice("repository:".length))}
      actions={<Button dense onClick={() => useDesk.getState().openNewRepositoryWindow(repositoryId, undefined, browser.entry.path, frameId)}>New window</Button>}
      wings={<SurfaceWings wings={WINGS} active={wing} onChange={setWing} />}
      className="desk-pullout desk-repo-window"
    >
      <div className="desk-repo-body desk-surface-body">
        {error ? <SurfaceState error={error} onRetry={retry ?? (() => void refreshMeta())} /> : null}
        {wing === "files" ? <>
          <RepositoryBrowserView browser={browser} checkedPaths={selected} onToggleChecked={toggleFile} trailingNavigation={branches.length > 1 ? (
              <CycleGadget
                label="Branch"
                value={branch}
                options={branches.map((item) => ({ value: item }))}
                onChange={(nextBranch) => {
                  setBusy(true);
                  void checkout(repositoryId, nextBranch)
                    .then((next) => {
                      setStatus(next);
                      browser.refresh();
                      return refreshMeta();
                    })
                    .catch(() => {
                      setError("BRANCH SWITCH FAILED");
                      setRetry(() => () => {
                        setBusy(true);
                        void checkout(repositoryId, nextBranch)
                          .then((next) => {
                            setStatus(next);
                            browser.refresh();
                            return refreshMeta();
                          })
                          .catch(() => setError("BRANCH SWITCH FAILED"))
                          .finally(() => setBusy(false));
                      });
                    })
                    .finally(() => setBusy(false));
                }}
              />
            ) : null} />
        </> : null}
        {wing === "prs" ? (
          prSource?.prs === null ? <SurfaceState empty emptyLabel={prSource.detail || "No PR receipt yet"} /> :
          <DeskSortableTable data={prs} columns={prColumns} sort={prSort} onSort={(key, dir) => setPrSort({ key: key as PrSortKey, dir })} rowKey={(pr) => String(pr.number)} rowLabel={(pr) => `PR ${pr.number}: ${pr.title}`} />
        ) : null}
        {wing === "issues" ? <SurfaceState empty emptyLabel="ISSUES UNAVAILABLE" emptyGlyph="○" /> : null}
      </div>
      <SurfaceFooter
        className="repo-footer-layout"
        fold={false}
        receipt={<span className="quiet">{browser.entry.files.length > 0 ? `${browser.entry.files.length} ${browser.entry.files.length === 1 ? "item" : "items"}` : browser.busy ? "Reading" : browser.failure ? "Unavailable" : "Empty"}{status?.ahead ? ` · ${status.ahead} ahead` : ""}{status?.behind ? ` · ${status.behind} behind` : ""}</span>}
        verbs={
          <div className="repo-footer-actions">
            <Button dense disabled={busy || !selected.size} onClick={() => void stage()}>
              Stage {selected.size || ""}
            </Button>
            <StringGadget
              label="Commit message"
              value={message}
              placeholder="Commit message"
              onChange={setMessage}
              onKeyDown={(event) => {
                if (event.key === "Enter") void commitSelected();
              }}
            />
            <Button
              dense
              disabled={busy || !message.trim()}
              title={message.trim() ? `Commit: ${message.trim()}` : "Enter a commit message"}
              onClick={() => void commitSelected()}
            >
              Commit
            </Button>
          </div>
        }
      />
    </DeskWindowFrame>
  );
}
