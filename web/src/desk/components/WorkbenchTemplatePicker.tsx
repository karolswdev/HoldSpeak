import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { useDesk } from "../store";
import { SurfaceSection, SurfaceState } from "../surface/Surface";
import { useRovingRows } from "../surface/roving";

interface Template {
  id: string;
  name: string;
  description: string;
  icon: string;
  recipe: { name: string; role: string };
  workbench: { schedule: string | null };
  starter_items: Array<{ title: string }>;
  skill_names?: string[];
}

export function WorkbenchTemplatePicker({
  onCreated,
}: {
  onCreated?: (workbenchId: string) => void;
}) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [createError, setCreateError] = useState("");
  const [readError, setReadError] = useState("");
  const [created, setCreated] = useState<{ id: string; name: string } | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  useRovingRows(gridRef, { selector: ".wb-picker-card" });

  const loadTemplates = useCallback(() => {
    setError(false);
    setLoading(true);
    return apiFetch<any>("/api/workbench-templates")
      .then((d) => setTemplates(d.templates || []))
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    void loadTemplates();
  }, [loadTemplates]);

  const refreshCreated = async (id: string, name: string) => {
    setBusy(true);
    setReadError("");
    try {
      await useDesk.getState().refresh();
      const error = useDesk.getState().error;
      if (error) throw new Error(error);
      onCreated?.(id);
    } catch (error) {
      setReadError(`${name} created · Workbench saved · Desk read failed · Retry · ${readableError(error)}`);
    } finally {
      setBusy(false);
    }
  };

  const create = async (templateId: string | null) => {
    if (busy || created) return;
    const name = templates.find((t) => t.id === templateId)?.name ?? "Blank";
    setSelected(templateId ?? "blank");
    setBusy(true);
    setCreateError("");
    try {
      const res = await apiFetch<any>(
        templateId ? `/api/workbench-templates/${templateId}/instantiate` : "/api/workbenches",
        {
          method: "POST",
          json: templateId ? {} : { name: "New Workbench" },
        },
      );
      const wbId = res.workbench?.id;
      if (wbId) {
        // The POST saved this object. Its window reads by ID, so a desk
        // refresh failure must not prevent opening or repeat the create.
        setCreated({ id: wbId, name });
        useDesk.getState().openWorkbenchWindow(wbId);
        await refreshCreated(wbId, name);
      } else {
        setCreateError(`${name} result missing · Reload workbenches`);
      }
    } catch (error) {
      setCreateError(`${name} not created · ${readableError(error)}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="wb-picker">
      {createError ? <SurfaceState error={createError} /> : null}
      {readError ? <SurfaceState error={readError} onRetry={busy || !created ? undefined : () => void refreshCreated(created.id, created.name)} /> : null}
      {created ? <Button dense variant="ghost" onClick={() => useDesk.getState().openWorkbenchWindow(created.id)}>Open workbench</Button> : null}
      <SurfaceSection label="START FROM A TEMPLATE">
        {error ? (
          <SurfaceState
            error="Templates failed to load. Current work is unchanged. Retry."
            onRetry={() => void loadTemplates()}
          />
        ) : loading ? (
          <SurfaceState loading />
        ) : (
          <>
          {!templates.length ? <SurfaceState empty emptyLabel="No templates · Start Blank" /> : null}
          <div ref={gridRef} className="wb-picker-grid">
            {templates.map((t) => (
              <Button
                key={t.id}
                variant="chrome"
                className="wb-picker-card"
                aria-pressed={selected === t.id}
                disabled={busy || Boolean(created)}
                onClick={() => void create(t.id)}
              >
                <span className="wb-picker-card-icon">{t.icon + "︎"}</span>
                <span className="wb-picker-card-name">{t.name}</span>
                <span className="wb-picker-card-desc">{t.description}</span>
                <span className="wb-picker-card-meta">
                  {t.workbench.schedule ? `⏱ ${t.workbench.schedule}` : "Manual"}
                  {t.starter_items.length ? ` · ${t.starter_items.length} items` : ""}
                  {t.skill_names?.length ? ` · ${t.skill_names.length} skills` : ""}
                </span>
              </Button>
            ))}
            <Button
              variant="chrome"
              className="wb-picker-card wb-picker-card-blank"
              aria-pressed={selected === "blank"}
              disabled={busy || Boolean(created)}
              onClick={() => void create(null)}
            >
              <span className="wb-picker-card-icon">○</span>
              <span className="wb-picker-card-name">Blank</span>
              <span className="wb-picker-card-desc">Start from scratch</span>
            </Button>
          </div>
          </>
        )}
      </SurfaceSection>
    </div>
  );
}
