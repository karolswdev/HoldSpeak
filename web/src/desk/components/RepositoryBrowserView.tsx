import { useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { humanTime } from "../surface/format";
import { CheckGadget } from "../surface/gadgets";
import { ScrollHint, SurfaceState, SurfaceWell } from "../surface/Surface";
import type { RepoFile } from "../repository";
import { DeskSortableTable, type Column } from "./DeskSortableTable";
import type { RepositoryBrowserController } from "./RepositoryBrowserController";
import "./RepositoryBrowserView.css";

type SortKey = "name" | "type" | "modified";

function extension(file: RepoFile) {
  if (file.type === "dir") return "folder";
  const dot = file.name.lastIndexOf(".");
  return dot > 0 ? file.name.slice(dot + 1) : "file";
}

function statusMark(status: RepoFile["status"]) {
  return <span className="repo-status" data-status={status || "clean"}>{status || "·"}</span>;
}

export function RepositoryBrowserView({
  browser,
  checkedPaths = new Set<string>(),
  onToggleChecked,
  trailingNavigation,
}: {
  browser: RepositoryBrowserController;
  checkedPaths?: ReadonlySet<string>;
  onToggleChecked?: (path: string) => void;
  trailingNavigation?: ReactNode;
}) {
  const [sort, setSort] = useState<{ key: SortKey; dir: "asc" | "desc" }>({ key: "name", dir: "asc" });
  const previewRef = useRef<HTMLPreElement>(null);
  const collectionRef = useRef<HTMLDivElement>(null);
  const { entry } = browser;
  const breadcrumb = entry.path ? entry.path.split("/") : [];
  const sortedFiles = useMemo(() => {
    const factor = sort.dir === "asc" ? 1 : -1;
    return [...entry.files].sort((a, b) => {
      if (a.type !== b.type) return a.type === "dir" ? -1 : 1;
      const av = sort.key === "type" ? extension(a) : sort.key === "modified" ? a.modified || "" : a.name;
      const bv = sort.key === "type" ? extension(b) : sort.key === "modified" ? b.modified || "" : b.name;
      return factor * av.localeCompare(bv);
    });
  }, [entry.files, sort]);
  const columns: Column<RepoFile>[] = [
    { key: "select", label: "", width: "32px", render: (file) => file.type === "file" && onToggleChecked ? (
      <span onClick={(event) => event.stopPropagation()}>
        <CheckGadget label={`Select ${file.name} for Git`} checked={checkedPaths.has(file.path)} onChange={() => onToggleChecked(file.path)} />
      </span>
    ) : null },
    { key: "status", label: "", width: "28px", render: (file) => statusMark(file.status) },
    { key: "name", label: "Name", sortable: true, render: (file) => <span className={`repo-file-name${file.type === "dir" ? " repo-folder" : ""}`}>
      <span>{file.type === "dir" ? "▸ " : ""}{file.name}</span>
      <span className="repo-file-fold">{extension(file)}{file.modified ? ` · ${humanTime(file.modified)}` : ""}</span>
    </span> },
    { key: "type", label: "Type", sortable: true, render: extension },
    { key: "modified", label: "Modified", sortable: true, render: (file) => <span className="quiet">{file.modified ? humanTime(file.modified) : "—"}</span> },
  ];
  const inspection = entry.inspection;
  const hasMaterial = entry.files.length > 0 || inspection !== null;

  return <section className="repo-browser" data-inspecting={Boolean(inspection)} aria-label="Repository files">
    <nav className="repo-breadcrumb" aria-label="Repository path">
      <Button dense variant="ghost" onClick={browser.back} disabled={!browser.canBack}>Back</Button>
      <Button dense variant="ghost" onClick={browser.forward} disabled={!browser.canForward}>Forward</Button>
      <span className="repo-breadcrumb-path">
        <Button dense variant="ghost" onClick={() => browser.navigate("")} disabled={!entry.path}>root</Button>
        {breadcrumb.map((part, index) => <span className="repo-crumb" key={`${part}-${index}`}>
          <span className="repo-crumb-separator" aria-hidden="true">/</span>
          <Button dense variant="ghost" onClick={() => browser.navigate(breadcrumb.slice(0, index + 1).join("/"))} disabled={index === breadcrumb.length - 1}>{part}</Button>
        </span>)}
      </span>
      {trailingNavigation}
    </nav>
    {browser.failure ? <SurfaceState error={browser.failure.message} onRetry={browser.retry} retryLabel="Retry" /> : null}
    {browser.busy ? <div className="repo-browser-loading" role="status" aria-busy="true">Reading {browser.busy === "tree" ? "folder" : "file"}…</div> : null}
    <div className="repo-browser-content">
      <ScrollHint axis="y" scrollRef={collectionRef} className="repo-browser-collection-hint"><div ref={collectionRef} className="repo-browser-collection">
        {browser.busy === "tree" && !hasMaterial && !browser.failure ? <SurfaceState loading /> :
          browser.failure && !hasMaterial ? null :
          <DeskSortableTable
            className="desk-repo-files"
            data={sortedFiles}
            columns={columns}
            sort={sort}
            onSort={(key, dir) => setSort({ key: key as SortKey, dir })}
            rowKey={(file) => file.path}
            selectedKey={entry.selectedPath}
            rowLabel={(file) => file.path}
            emptyLabel="Folder empty"
            foldColumns={["type", "modified"]}
            onRowClick={(file) => file.type === "dir" ? browser.navigate(file.path) : browser.inspect(file.path)}
          />}
      </div></ScrollHint>
      {inspection ? <div className="repo-browser-inspection" aria-label={`File inspection: ${inspection.path}`}>
        <Button className="repo-browser-detail-back" dense variant="ghost" onClick={browser.closeInspection}>Back to files</Button>
        <SurfaceWell head={<span className="repo-browser-file-path">{inspection.path} · {inspection.retained ? "RETAINED COPY" : "READ ONLY"}</span>}>
          <ScrollHint axis="y" scrollRef={previewRef}>
            <pre ref={previewRef} className="repo-browser-file-content" data-testid="repo-file-content">{inspection.content}</pre>
          </ScrollHint>
        </SurfaceWell>
      </div> : null}
    </div>
  </section>;
}
