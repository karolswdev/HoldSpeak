import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useDesk } from "../store";
import { CycleGadget } from "../surface/gadgets";
import { SurfaceSection, SurfaceState } from "../surface/Surface";

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
  const [busy, setBusy] = useState(false);
  const inferenceTargets = useDesk((s) => s.inferenceTargets);
  const [selectedTarget, setSelectedTarget] = useState("this_machine");

  useEffect(() => {
    void apiFetch<any>("/api/workbench-templates").then((d) =>
      setTemplates(d.templates || []),
    );
  }, []);

  const instantiate = async (templateId: string) => {
    setBusy(true);
    try {
      const res = await apiFetch<any>(
        `/api/workbench-templates/${templateId}/instantiate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            profile_id: selectedTarget !== "this_machine" ? selectedTarget : null,
          }),
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
          profile_id: selectedTarget !== "this_machine" ? selectedTarget : null,
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
      <SurfaceSection label="RUNS ON">
        <div className="wb-picker-target">
          <CycleGadget
            label="Runs on"
            value={selectedTarget}
            onChange={setSelectedTarget}
            options={[
              { value: "this_machine", label: "This device (local)" },
              ...inferenceTargets
                .filter((t) => t.id !== "this_machine" && t.readiness.available)
                .map((t) => ({ value: t.id, label: `${t.name} (${t.kind})` })),
            ]}
          />
        </div>
      </SurfaceSection>

      <SurfaceSection label="START FROM A TEMPLATE">
        {templates.length === 0 ? (
          <SurfaceState loading />
        ) : (
          <div className="wb-picker-grid">
            {templates.map((t) => (
              <button
                key={t.id}
                type="button"
                className="wb-picker-card"
                disabled={busy}
                onClick={() => void instantiate(t.id)}
              >
                <span className="wb-picker-card-icon">{t.icon}</span>
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
