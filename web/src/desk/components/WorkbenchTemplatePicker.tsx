import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
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
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  const gridRef = useRef<HTMLDivElement>(null);
  useRovingRows(gridRef, { selector: ".wb-picker-card" });

  const loadTemplates = useCallback(() => {
    setError(false);
    return apiFetch<any>("/api/workbench-templates")
      .then((d) => setTemplates(d.templates || []))
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    void loadTemplates();
  }, [loadTemplates]);

  const instantiate = async (templateId: string) => {
    setBusy(true);
    try {
      const res = await apiFetch<any>(
        `/api/workbench-templates/${templateId}/instantiate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        },
      );
      await useDesk.getState().refresh();
      const wbId = res.workbench?.id;
      if (wbId) {
        useDesk.getState().openWorkbenchWindow(wbId);
        onCreated?.(wbId);
      }
    } catch { /* honest failure on next refresh */ }
    setBusy(false);
  };

  const createBlank = async () => {
    setBusy(true);
    try {
      const res = await apiFetch<any>("/api/workbenches", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "New Workbench",
        }),
      });
      await useDesk.getState().refresh();
      const wbId = res.workbench?.id;
      if (wbId) {
        useDesk.getState().openWorkbenchWindow(wbId);
        onCreated?.(wbId);
      }
    } catch { /* */ }
    setBusy(false);
  };

  return (
    <div className="wb-picker">
      <SurfaceSection label="START FROM A TEMPLATE">
        {error ? (
          <SurfaceState
            error="Templates failed to load. Current work is unchanged. Retry."
            onRetry={() => void loadTemplates()}
          />
        ) : templates.length === 0 ? (
          <SurfaceState loading />
        ) : (
          <div ref={gridRef} className="wb-picker-grid">
            {templates.map((t) => (
              <button
                key={t.id}
                type="button"
                className="wb-picker-card"
                disabled={busy}
                onClick={() => void instantiate(t.id)}
              >
                <span className="wb-picker-card-icon">{t.icon + "︎"}</span>
                <span className="wb-picker-card-name">{t.name}</span>
                <span className="wb-picker-card-desc">{t.description}</span>
                <span className="wb-picker-card-meta">
                  {t.workbench.schedule ? `⏱ ${t.workbench.schedule}` : "Manual"}
                  {t.starter_items.length ? ` · ${t.starter_items.length} items` : ""}
                  {t.skill_names?.length ? ` · ${t.skill_names.length} skills` : ""}
                </span>
              </button>
            ))}
            <button
              type="button"
              className="wb-picker-card wb-picker-card-blank"
              disabled={busy}
              onClick={() => void createBlank()}
            >
              <span className="wb-picker-card-icon">○</span>
              <span className="wb-picker-card-name">Blank</span>
              <span className="wb-picker-card-desc">Start from scratch</span>
            </button>
          </div>
        )}
      </SurfaceSection>
    </div>
  );
}
