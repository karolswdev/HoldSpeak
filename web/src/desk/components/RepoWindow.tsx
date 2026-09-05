import { useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import {
  checkout,
  commit,
  fetchBranches,
  fetchStatus,
  fetchTree,
  stageFiles,
  type RepoFile,
  type RepoStatus,
} from "../repository";
import { usePrReceipts, type PrRow } from "../prReceipts";
import { humanTime } from "../surface/format";
import { SurfaceState } from "../surface/Surface";
import { SurfaceWings } from "../surface/wings";
import { CheckGadget, CycleGadget, StringGadget } from "../surface/gadgets";
import { DeskSortableTable, type Column } from "./DeskSortableTable";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { DeskWindowFrame } from "./DeskWindow";
import "./RepoWindow.css";

const WINGS = [
  { id: "files", label: "Files" },
  { id: "prs", label: "PRs" },
  { id: "issues", label: "Issues" },
];

type SortKey = "name" | "type" | "modified";
type PrSortKey = "number" | "title" | "state" | "ci" | "author";

function statusMark(status: RepoFile["status"]) {
  return <span className="repo-status" data-status={status || "clean"}>{status || "·"}</span>;
}

function extension(file: RepoFile) {
  if (file.type === "dir") return "folder";
  const dot = file.name.lastIndexOf(".");
  return dot > 0 ? file.name.slice(dot + 1) : "file";
}

export function RepoWindow({
  repositoryId,
  origin,
}: {
  repositoryId: string;
  origin?: { x: number; y: number } | null;
}) {
  const repository = useDesk((s) => (s.items.repository || []).find((item) => item.id === repositoryId));
  const [wing, setWing] = useState("files");
  const [files, setFiles] = useState<RepoFile[]>([]);
  const [path, setPath] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [status, setStatus] = useState<RepoStatus | null>(null);
  const [branches, setBranches] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState<(() => void) | null>(null);
  const [sort, setSort] = useState<{ key: SortKey; dir: "asc" | "desc" }>({ key: "name", dir: "asc" });
  const [prSort, setPrSort] = useState<{ key: PrSortKey; dir: "asc" | "desc" }>({ key: "number", dir: "desc" });
  const prsLoaded = usePrReceipts((s) => s.loaded);
  const loadPrs = usePrReceipts((s) => s.load);
  const prSource = usePrReceipts((s) => s.sources.find((source) => source.source_id === repositoryId));

  const refresh = async (nextPath = path) => {
    setError("");
    setRetry(null);
    try {
      const [nextFiles, nextStatus, nextBranches] = await Promise.all([
        fetchTree(repositoryId, nextPath),
        fetchStatus(repositoryId),
        fetchBranches(repositoryId),
      ]);
      setFiles(nextFiles);
      setStatus(nextStatus);
      setBranches(nextBranches);
    } catch {
      setError("Repository unavailable");
    }
  };

  useEffect(() => { void refresh(""); }, [repositoryId]);
  useEffect(() => { if (!prsLoaded) void loadPrs(); }, [prsLoaded, loadPrs]);

  const sortedFiles = useMemo(() => {
    const factor = sort.dir === "asc" ? 1 : -1;
    return [...files].sort((a, b) => {
      if (a.type !== b.type) return a.type === "dir" ? -1 : 1;
      const av = sort.key === "type" ? extension(a) : sort.key === "modified" ? a.modified || "" : a.name;
      const bv = sort.key === "type" ? extension(b) : sort.key === "modified" ? b.modified || "" : b.name;
      return factor * av.localeCompare(bv);
    });
  }, [files, sort]);

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
  const branch = status?.branch || String(repository.branch || "detached");
  const breadcrumb = path ? path.split("/") : [];
  const toggleFile = (filePath: string) => setSelected((current) => {
    const next = new Set(current);
    if (next.has(filePath)) next.delete(filePath); else next.add(filePath);
    return next;
  });
  const descend = (directory: RepoFile) => {
    setPath(directory.path);
    setSelected(new Set());
    setSelectedFile(null);
    void refresh(directory.path);
  };
  const ascend = (index: number) => {
    const nextPath = breadcrumb.slice(0, index).join("/");
    setPath(nextPath);
    setSelected(new Set());
    setSelectedFile(null);
    void refresh(nextPath);
  };
  const stage = async () => {
    if (!selected.size) return;
    setBusy(true); setError("");
    try { await stageFiles(repositoryId, [...selected]); setSelected(new Set()); await refresh(); }
    catch {
      setError("STAGE FAILED");
      setRetry(() => () => void stage());
    }
    finally { setBusy(false); }
  };
  const commitSelected = async () => {
    if (!message.trim()) return;
    setBusy(true); setError("");
    try { await commit(repositoryId, message); setMessage(""); setSelected(new Set()); await refresh(); }
    catch {
      setError("COMMIT FAILED");
      setRetry(() => () => void commitSelected());
    }
    finally { setBusy(false); }
  };

  const fileColumns: Column<RepoFile>[] = [
    { key: "select", label: "", width: "32px", render: (file) => file.type === "file" ? (
      <span onClick={(event) => event.stopPropagation()}>
        <CheckGadget
          label={`Select ${file.name}`}
          checked={selected.has(file.path)}
          onChange={() => toggleFile(file.path)}
        />
      </span>
    ) : null },
    { key: "status", label: "", width: "28px", render: (file) => statusMark(file.status) },
    { key: "name", label: "Name", sortable: true, render: (file) => <span className={file.type === "dir" ? "repo-folder" : ""}>{file.type === "dir" ? "▸ " : ""}{file.name}</span> },
    { key: "type", label: "Type", sortable: true, render: extension },
    { key: "modified", label: "Modified", sortable: true, render: (file) => <span className="quiet">{file.modified ? humanTime(file.modified) : "—"}</span> },
  ];
  const prColumns: Column<PrRow>[] = [
    { key: "number", label: "PR", sortable: true, width: "56px", render: (pr) => `#${pr.number}` },
    { key: "title", label: "Title", sortable: true, render: (pr) => pr.title },
    { key: "state", label: "State", sortable: true, render: (pr) => <span className="repo-pr-state" data-state={pr.state}>{pr.state}</span> },
    { key: "ci", label: "CI", sortable: true, render: (pr) => <span className="repo-pr-ci" data-ci={pr.ci}>{pr.ci}</span> },
    { key: "author", label: "Author", sortable: true, render: (pr) => pr.author || "—" },
  ];

  return (
    <DeskWindowFrame
      id={`repository:${repositoryId}`}
      glyph="▤"
      label={name}
      title={<><span>{name}</span><span className="repo-branch">{branch}</span>{status?.dirty ? <span className="repo-dirty">{status.dirty} dirty</span> : null}</>}
      icon={<img src={spriteUrl("repository", repositoryId)} alt="" width={30} height={30} />}
      minW={600}
      minH={390}
      open
      origin={origin}
      onClose={() => useDesk.getState().closeRepositoryWindow(repositoryId)}
      wings={<SurfaceWings wings={WINGS} active={wing} onChange={setWing} />}
      className="desk-repo-window"
    >
      <div className="desk-repo-body desk-surface-body">
        {error ? <SurfaceState error={error} onRetry={retry ?? (() => void refresh())} /> : null}
        {!error && wing === "files" ? <>
          <nav className="repo-breadcrumb" aria-label="Repository path">
            <Button dense variant="ghost" onClick={() => ascend(0)} disabled={!path}>root</Button>
            {breadcrumb.map((part, index) => <Button dense variant="ghost" key={`${part}-${index}`} onClick={() => ascend(index + 1)} disabled={index === breadcrumb.length - 1}>{part}</Button>)}
            {branches.length > 1 ? (
              <CycleGadget
                label="Branch"
                value={branch}
                options={branches.map((item) => ({ value: item }))}
                onChange={(nextBranch) => {
                  setBusy(true);
                  void checkout(repositoryId, nextBranch)
                    .then((next) => {
                      setStatus(next);
                      return refresh();
                    })
                    .catch(() => {
                      setError("BRANCH SWITCH FAILED");
                      setRetry(() => () => {
                        setBusy(true);
                        void checkout(repositoryId, nextBranch)
                          .then((next) => {
                            setStatus(next);
                            return refresh();
                          })
                          .catch(() => setError("BRANCH SWITCH FAILED"))
                          .finally(() => setBusy(false));
                      });
                    })
                    .finally(() => setBusy(false));
                }}
              />
            ) : null}
          </nav>
          <DeskSortableTable
            className="desk-repo-files"
            data={sortedFiles}
            columns={fileColumns}
            sort={sort}
            onSort={(key, dir) => setSort({ key: key as SortKey, dir })}
            rowKey={(file) => file.path}
            selectedKey={selectedFile}
            rowLabel={(file) => file.path}
            onRowClick={(file) => file.type === "dir" ? descend(file) : setSelectedFile(file.path)}
          />
        </> : null}
        {!error && wing === "prs" ? (
          prSource?.prs === null ? <SurfaceState empty emptyLabel={prSource.detail || "No PR receipt yet"} /> :
          <DeskSortableTable data={prs} columns={prColumns} sort={prSort} onSort={(key, dir) => setPrSort({ key: key as PrSortKey, dir })} rowKey={(pr) => String(pr.number)} rowLabel={(pr) => `PR ${pr.number}: ${pr.title}`} />
        ) : null}
        {!error && wing === "issues" ? <SurfaceState empty emptyLabel="ISSUES UNAVAILABLE" emptyGlyph="○" /> : null}
      </div>
      <SurfaceFooter
        receipt={<span className="quiet">{files.length > 0 ? `${files.length} ${files.length === 1 ? "item" : "items"}` : "Empty"}{status?.ahead ? ` · ${status.ahead} ahead` : ""}{status?.behind ? ` · ${status.behind} behind` : ""}</span>}
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
