import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch } from "../../lib/api";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import { boundaryEgressLamp } from "../inferenceEgress";
import { keepReply } from "../chat";
import {
  emptyGrounding,
  groundingIsEmpty,
  hubGrounding,
  type GroundingSelection,
} from "../grounding";
import { DeskWindowFrame } from "./DeskWindow";
import { DeskWindowFooter } from "./DeskWindowFooter";
import { AgentAvatar } from "./AgentAvatar";
import { GroundingSection } from "./GroundingSection";
import { MicButton } from "./MicButton";
import { RunsOnPicker } from "./RunsOnPicker";
import {
  CheckGadget,
  EgressChip,
  FoldGadget,
  LampGadget,
  LedMeter,
  PadGadget,
  StringGadget,
  TransportKey,
} from "../surface/gadgets";
import {
  ConfirmVerb,
  EditInPlace,
  SurfaceRows,
  SurfaceRow,
  SurfaceSection,
  SurfaceState,
} from "../surface/Surface";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
} from "../surface/Surface";
import { Material } from "../surface/Material";
import { SurfaceWings, type WingSpec } from "../surface/wings";
import { useRuntimeBus } from "../../runtime/RuntimeBus";
import { WorkbenchTemplatePicker } from "./WorkbenchTemplatePicker";
import { workbenchVoiceGrammar } from "../voice/grammars/workbench";
import type { VoiceProposal } from "../voice/grammar";
import { humanTime } from "../surface/format";

/* ── types ─────────────────────────────────────────────────────────── */

interface WorkbenchDetail {
  id: string;
  name: string;
  recipe_id: string | null;
  profile_id: string | null;
  schedule: string | null;
  schedule_enabled: boolean;
  items: WorkbenchItem[];
  item_count: number;
  pending_count: number;
  last_run: WorkbenchRun | null;
}

interface WorkbenchItem {
  id: string;
  title: string;
  body: string;
  priority: number;
  status: string;
  grounding: Record<string, unknown>;
  result: string | null;
  result_egress: { boundary?: string } | null;
  tokens_consumed: number;
  created_at: string;
  completed_at: string | null;
}

interface WorkbenchRun {
  id: string;
  started_at: string;
  completed_at: string | null;
  items_attempted: number;
  items_completed: number;
  items_failed: number;
  total_tokens: number;
  egress_boundary: string;
  model: string;
  status: string;
}

interface Skill {
  id: string;
  title: string;
  body: string;
  source: string;
  status: string;
  recipe_ids: string[];
  created_by: string;
}

interface MemoryEntry {
  run_id: string;
  timestamp: string;
  kind: string;
  content: string;
  item_title: string;
  provenance: { egress?: string; model?: string };
}

/* ── schedule presets ───────────────────────────────────────────────── */

const SCHEDULE_PRESETS: { label: string; cron: string | null }[] = [
  { label: "7 AM daily", cron: "0 7 * * *" },
  { label: "7 AM weekdays", cron: "0 7 * * 1-5" },
  { label: "2 AM nightly", cron: "0 2 * * *" },
  { label: "Every hour", cron: "0 * * * *" },
  { label: "Manual", cron: null },
];

function humanSchedule(cron: string | null): string {
  if (!cron) return "Manual";
  const preset = SCHEDULE_PRESETS.find((p) => p.cron === cron);
  if (preset) return preset.label;
  return cron;
}

/* ── item status ───────────────────────────────────────────────────── */

const STATUS_CHIPS: Record<string, { label: string; tone: string }> = {
  pending: { label: "PENDING", tone: "" },
  claimed: { label: "RUNNING", tone: "warn" },
  done: { label: "DONE", tone: "ok" },
  failed: { label: "FAILED", tone: "fail" },
  dismissed: { label: "DISMISSED", tone: "" },
};

const PRIORITY_LABELS = ["", "P1", "P2", "P3", "P4", "P5"];

/* ── config strip (collapsed) ──────────────────────────────────────── */

function ConfigStrip({
  recipe,
  target,
  lamp,
  schedule,
  scheduleEnabled,
  skillCount,
  onClick,
}: {
  recipe: any;
  target: any;
  lamp: { label: string; tone: string };
  schedule: string | null;
  scheduleEnabled: boolean;
  skillCount: number;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className="wb-config-strip"
      onClick={onClick}
      aria-label="Expand configuration"
    >
      {recipe ? (
        <span className="wb-config-strip-agent">
          <AgentAvatar
            avatar={String(recipe.avatar || "")}
            id={String(recipe.id)}
            kind="agent"
            size={16}
          />
          <span>{String(recipe.name || "Agent")}</span>
        </span>
      ) : (
        <span className="wb-config-strip-agent wb-config-strip-empty">
          No agent
        </span>
      )}
      <span className="wb-config-strip-sep" aria-hidden="true">
        ·
      </span>
      <LampGadget label={lamp.label} on={lamp.tone !== "fail"} tone={lamp.tone as "ok" | "warn" | "fail"} />
      {target ? (
        <span className="wb-config-strip-target">
          {String(target.name || "Target")}
        </span>
      ) : null}
      <span className="wb-config-strip-sep" aria-hidden="true">
        ·
      </span>
      <span className="wb-config-strip-schedule">
        {scheduleEnabled ? "⏱" : "⏸"} {humanSchedule(schedule)}
      </span>
      {skillCount > 0 ? (
        <span className="desk-chip wb-config-strip-skills">
          {skillCount} {skillCount === 1 ? "skill" : "skills"}
        </span>
      ) : null}
    </button>
  );
}

/* ── config panel (expanded) ───────────────────────────────────────── */

function ConfigPanel({
  detail,
  recipes,
  inferenceTargets,
  skills,
  lamp,
  onUpdateRecipe,
  onUpdateTarget,
  onUpdateSchedule,
  onToggleSchedule,
  onAttachSkill,
  onDetachSkill,
  onApproveSkill,
  onDismissSkill,
  onCollapse,
}: {
  detail: WorkbenchDetail;
  recipes: any[];
  inferenceTargets: any[];
  skills: Skill[];
  lamp: { label: string; tone: string };
  onUpdateRecipe: (id: string) => void;
  onUpdateTarget: (id: string) => void;
  onUpdateSchedule: (cron: string | null) => void;
  onToggleSchedule: (enabled: boolean) => void;
  onAttachSkill: (skillId: string) => void;
  onDetachSkill: (skillId: string) => void;
  onApproveSkill: (skillId: string) => void;
  onDismissSkill: (skillId: string) => void;
  onCollapse: () => void;
}) {
  const [agentSearch, setAgentSearch] = useState("");
  const [showSkillPicker, setShowSkillPicker] = useState(false);

  const recipe = recipes.find((r) => r.id === detail.recipe_id);
  const target = inferenceTargets.find((t) => t.id === detail.profile_id);

  const filteredRecipes = useMemo(() => {
    const q = agentSearch.toLowerCase().trim();
    if (!q) return recipes;
    return recipes.filter(
      (r) =>
        String(r.name || "").toLowerCase().includes(q) ||
        String(r.role || "").toLowerCase().includes(q),
    );
  }, [recipes, agentSearch]);

  const boundSkills = useMemo(
    () =>
      detail.recipe_id
        ? skills.filter((s) => s.recipe_ids.includes(detail.recipe_id!))
        : [],
    [skills, detail.recipe_id],
  );

  const unboundSkills = useMemo(
    () =>
      detail.recipe_id
        ? skills.filter(
            (s) =>
              s.status === "active" &&
              !s.recipe_ids.includes(detail.recipe_id!),
          )
        : [],
    [skills, detail.recipe_id],
  );

  return (
    <div className="wb-config-panel">
      {/* ── collapse affordance ─────────────────────────────────────── */}
      <button
        type="button"
        className="wb-config-collapse desk-chip quiet"
        onClick={onCollapse}
        aria-label="Collapse configuration"
      >
        ▴ Collapse
      </button>

      {/* ── agent ───────────────────────────────────────────────────── */}
      <SurfaceSection label="AGENT">
        {recipe ? (
          <div className="wb-config-current-agent">
            <AgentAvatar
              avatar={String(recipe.avatar || "")}
              id={String(recipe.id)}
              kind="agent"
              size={32}
            />
            <span className="wb-config-agent-info">
              <strong>{String(recipe.name || "Agent")}</strong>
              {recipe.role ? <small>{String(recipe.role)}</small> : null}
            </span>
          </div>
        ) : null}
        <div className="wb-config-agent-search">
          <StringGadget
            label="Search agents"
            value={agentSearch}
            onChange={setAgentSearch}
            placeholder="SEARCH AGENTS"
            mic={false}
          />
        </div>
        <SurfaceRows>
          {filteredRecipes.map((r) => (
            <SurfaceRow
              key={r.id}
              glyph={
                <AgentAvatar
                  avatar={String(r.avatar || "")}
                  id={String(r.id)}
                  kind="agent"
                  size={16}
                />
              }
              title={String(r.name || r.id)}
              detail={
                (String(r.role || "") +
                  (r.system_prompt
                    ? " · " + String(r.system_prompt).slice(0, 80)
                    : "")) ||
                undefined
              }
              selected={r.id === detail.recipe_id}
              onOpen={() => onUpdateRecipe(r.id)}
            />
          ))}
        </SurfaceRows>
        {filteredRecipes.length === 0 ? (
          <SurfaceState empty emptyLabel="No agents match" />
        ) : null}
      </SurfaceSection>

      {/* ── runs on ─────────────────────────────────────────────────── */}
      <SurfaceSection label="RUNS ON">
        <div className="wb-config-runs-on">
          <RunsOnPicker
            targets={inferenceTargets}
            selectedId={detail.profile_id || "this_machine"}
            onChange={onUpdateTarget}
          />
          <LampGadget
            label={lamp.label}
            on={lamp.tone !== "fail"}
            tone={lamp.tone as "ok" | "warn" | "fail"}
          />
        </div>
      </SurfaceSection>

      {/* ── schedule ────────────────────────────────────────────────── */}
      <SurfaceSection label="SCHEDULE">
        <div className="wb-schedule-row">
          {SCHEDULE_PRESETS.map((preset) => (
            <button
              key={preset.label}
              type="button"
              className="desk-chip"
              aria-pressed={
                (preset.cron === null && !detail.schedule) ||
                preset.cron === detail.schedule
              }
              onClick={() => onUpdateSchedule(preset.cron)}
            >
              {preset.label}
            </button>
          ))}
          <span className="wb-schedule-toggle">
            <CheckGadget
              label="Schedule enabled"
              checked={detail.schedule_enabled}
              onChange={onToggleSchedule}
              disabled={!detail.schedule}
            />
          </span>
        </div>
      </SurfaceSection>

      {/* ── skills ──────────────────────────────────────────────────── */}
      <SurfaceSection
        label="SKILLS"
        actions={
          boundSkills.length > 0 ? (
            <span className="wb-config-skill-count">
              {boundSkills.length}
            </span>
          ) : null
        }
      >
        {boundSkills.length > 0 ? (
          <SurfaceRows>
            {boundSkills.map((s) => (
              <SurfaceRow
                key={s.id}
                title={s.title}
                detail={s.body.slice(0, 60) || undefined}
                meta={
                  s.status === "draft" ? (
                    <span className="desk-chip" data-tone="warn">
                      DRAFT
                    </span>
                  ) : null
                }
                verbs={
                  <>
                    {s.status === "draft" ? (
                      <>
                        <button
                          type="button"
                          className="desk-chip"
                          onClick={() => onApproveSkill(s.id)}
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          className="desk-chip quiet"
                          onClick={() => onDismissSkill(s.id)}
                        >
                          Dismiss
                        </button>
                      </>
                    ) : (
                      <button
                        type="button"
                        className="desk-chip quiet"
                        onClick={() => onDetachSkill(s.id)}
                      >
                        Remove
                      </button>
                    )}
                  </>
                }
              />
            ))}
          </SurfaceRows>
        ) : (
          <SurfaceState empty emptyLabel="No skills attached" emptyGlyph="◇" />
        )}
        {detail.recipe_id ? (
          showSkillPicker ? (
            <div className="wb-skill-picker">
              <SurfaceRows>
                {unboundSkills.map((s) => (
                  <SurfaceRow
                    key={s.id}
                    title={s.title}
                    detail={s.body.slice(0, 60) || undefined}
                    onOpen={() => onAttachSkill(s.id)}
                  />
                ))}
              </SurfaceRows>
              {unboundSkills.length === 0 ? (
                <SurfaceState empty emptyLabel="All skills attached" />
              ) : null}
              <button
                type="button"
                className="desk-chip quiet"
                onClick={() => setShowSkillPicker(false)}
              >
                Done
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="gadget-table-add"
              onClick={() => setShowSkillPicker(true)}
            >
              + ATTACH SKILL
            </button>
          )
        ) : null}
      </SurfaceSection>

      {/* ── workspace path ──────────────────────────────────────────── */}
      <div className="wb-workspace-path">
        ~/.holdspeak/workbenches/{detail.id}/
      </div>
    </div>
  );
}

/* ── item card ─────────────────────────────────────────────────────── */

function WorkbenchItemCard({
  item,
  expanded,
  recipeId,
  workbenchId,
  workbenchName,
  onToggle,
  onReload,
}: {
  item: WorkbenchItem;
  expanded: boolean;
  recipeId: string | null;
  workbenchId: string;
  workbenchName: string;
  onToggle: () => void;
  onReload: () => void;
}) {
  const chip = STATUS_CHIPS[item.status] || STATUS_CHIPS.pending;
  const egressLamp = item.result_egress?.boundary
    ? boundaryEgressLamp(item.result_egress.boundary)
    : null;
  const hasResult = !!(item.result && (item.status === "done" || item.status === "failed"));
  const hasGrounding =
    item.grounding &&
    typeof item.grounding === "object" &&
    Object.keys(item.grounding).length > 0;

  const updateItem = async (fields: Record<string, unknown>) => {
    try {
      await apiFetch<any>(
        `/api/workbenches/${workbenchId}/items/${item.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(fields),
        },
      );
      onReload();
    } catch { /* */ }
  };

  const deleteItem = async () => {
    try {
      await apiFetch<any>(
        `/api/workbenches/${workbenchId}/items/${item.id}`,
        { method: "DELETE" },
      );
      onReload();
    } catch { /* */ }
  };

  const rerunItem = () => void updateItem({ status: "pending", result: null, result_egress: null, tokens_consumed: 0, completed_at: null });
  const dismissItem = () => void updateItem({ status: "dismissed" });

  const [keeping, setKeeping] = useState(false);
  const handleKeep = async () => {
    if (!recipeId || !item.result) return;
    setKeeping(true);
    try {
      const artifactId = await keepReply(recipeId, item.title, item.result);
      if (artifactId) void useDesk.getState().refresh();
    } catch { /* */ }
    setKeeping(false);
  };

  return (
    <div className="wb-card" data-status={item.status}>
      {/* ── head line ──────────────────────────────────────────── */}
      <button
        type="button"
        className="wb-card-head"
        onClick={onToggle}
        aria-expanded={expanded}
      >
        <span className="desk-chip wb-item-priority">
          {PRIORITY_LABELS[item.priority] || "P3"}
        </span>
        <span className="wb-card-title">{item.title}</span>
        {item.status === "claimed" ? (
          <LedMeter label="WORKING" value={0} scanning />
        ) : null}
        <span className="desk-chip" data-tone={chip.tone}>
          {chip.label}
        </span>
      </button>

      {/* ── collapsed result preview ───────────────────────────── */}
      {!expanded && hasResult ? (
        <p className="wb-card-preview">
          {item.result!.slice(0, 120)}
          {item.result!.length > 120 ? "…" : ""}
        </p>
      ) : null}

      {/* ── expanded detail ────────────────────────────────────── */}
      {expanded ? (
        <div className="wb-card-detail">
          {/* body (editable) */}
          <div className="wb-card-body-edit">
            <PadGadget
              label="Item body"
              value={item.body || ""}
              onChange={(next) => void updateItem({ body: next })}
              placeholder="Add details…"
              rows={2}
              autoGrow
            />
          </div>

          {/* grounding chips */}
          {hasGrounding ? (
            <div className="wb-card-grounding">
              {Object.entries(item.grounding).map(([key, val]) =>
                val ? (
                  <span key={key} className="desk-chip quiet">
                    ▣ {String(typeof val === "object" && val !== null && "title" in val ? (val as any).title : key)}
                  </span>
                ) : null,
              )}
            </div>
          ) : null}

          {/* result + egress */}
          {hasResult ? (
            <div className="wb-card-result">
              <div className="wb-card-result-head">
                <span className="wb-card-result-label">RESULT</span>
                {egressLamp ? (
                  <EgressChip
                    label={`⌂ ${egressLamp.label}`}
                    scope={
                      egressLamp.tone === "ok"
                        ? "local"
                        : egressLamp.tone === "fail"
                          ? "cloud"
                          : "mixed"
                    }
                  />
                ) : null}
              </div>
              <div className="wb-card-result-body">
                <Material>{item.result!}</Material>
              </div>
            </div>
          ) : null}

          {/* meta */}
          {item.tokens_consumed ? (
            <span className="wb-item-tokens">
              {item.tokens_consumed.toLocaleString()} tokens
              {item.completed_at ? ` · ${humanTime(item.completed_at)}` : ""}
            </span>
          ) : null}

          {/* verbs */}
          <div className="wb-card-verbs">
            {item.status === "done" && item.result && recipeId ? (
              <button
                type="button"
                className="desk-chip"
                disabled={keeping}
                onClick={() => void handleKeep()}
              >
                {keeping ? "Keeping…" : "Keep ▸"}
              </button>
            ) : null}
            {item.status === "done" || item.status === "failed" ? (
              <button
                type="button"
                className="desk-chip"
                onClick={rerunItem}
              >
                Re-run
              </button>
            ) : null}
            {item.status === "pending" ? (
              <button
                type="button"
                className="desk-chip quiet"
                onClick={dismissItem}
              >
                Dismiss
              </button>
            ) : null}
            {item.status !== "claimed" ? (
              <button
                type="button"
                className="desk-chip quiet"
                onClick={() => void deleteItem()}
              >
                Remove
              </button>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}

/* ── main component ────────────────────────────────────────────────── */

export function WorkbenchWindow({
  workbenchId,
  origin,
}: {
  workbenchId: string;
  origin?: { x: number; y: number } | null;
}) {
  const wb = useDesk(
    (s) => (s.items.workbench || []).find((w) => w.id === workbenchId),
  );
  const inferenceTargets = useDesk((s) => s.inferenceTargets);
  const recipes = useDesk((s) => s.items.recipe);
  const [detail, setDetail] = useState<WorkbenchDetail | null>(null);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [configOpen, setConfigOpen] = useState<boolean | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [newBody, setNewBody] = useState("");
  const [newPriority, setNewPriority] = useState(3);
  const [grounding, setGrounding] = useState<GroundingSelection>(emptyGrounding);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const [runProgress, setRunProgress] = useState<{ index: number; total: number } | null>(null);
  const [runs, setRuns] = useState<WorkbenchRun[]>([]);
  const [memoryEntries, setMemoryEntries] = useState<MemoryEntry[]>([]);
  const [activeWing, setActiveWing] = useState("items");
  const [openRunId, setOpenRunId] = useState<string | null>(null);
  const [voiceProposal, setVoiceProposal] = useState<VoiceProposal | null>(null);
  const [dropHover, setDropHover] = useState(false);
  const configAutoExpanded = useRef(false);

  const recipe = recipes.find(
    (r) => r.id === (detail?.recipe_id || (wb as any)?.recipeId),
  );
  const target = inferenceTargets.find(
    (t) => t.id === (detail?.profile_id || (wb as any)?.profileId),
  );
  const lamp = boundaryEgressLamp(target?.boundary);

  /* ── data loading ──────────────────────────────────────────────── */

  const load = useCallback(async () => {
    try {
      const res = await apiFetch<any>(`/api/workbenches/${workbenchId}`);
      setDetail(res.workbench);
      setError("");
    } catch {
      setError("Workbench unavailable");
    }
  }, [workbenchId]);

  const loadSkills = useCallback(async () => {
    try {
      const res = await apiFetch<any>("/api/skills");
      setSkills(res.skills || []);
    } catch {
      /* skills are auxiliary — silent fail */
    }
  }, []);

  const loadRuns = useCallback(async () => {
    try {
      const res = await apiFetch<any>(`/api/workbenches/${workbenchId}/runs`);
      setRuns(res.runs || []);
    } catch { /* */ }
  }, [workbenchId]);

  const loadMemory = useCallback(async () => {
    try {
      const res = await apiFetch<any>(`/api/workbenches/${workbenchId}/memory`);
      setMemoryEntries(res.entries || []);
    } catch { /* */ }
  }, [workbenchId]);

  useEffect(() => {
    void load();
    void loadSkills();
    void loadRuns();
    void loadMemory();
  }, [load, loadSkills, loadRuns, loadMemory]);

  useEffect(() => {
    if (detail && configOpen === null && !configAutoExpanded.current) {
      configAutoExpanded.current = true;
      setConfigOpen(!detail.recipe_id);
    }
  }, [detail, configOpen]);

  /* ── WebSocket subscription for live run feedback ─────────────── */

  const bus = useRuntimeBus();

  useEffect(() => {
    const d = (frame: { data: unknown }) => frame.data as Record<string, any> | undefined;
    const unsubs = [
      bus.subscribe("workbench.run_start", (frame) => {
        const ev = d(frame);
        if (ev?.workbench_id !== workbenchId) return;
        setRunning(true);
        setRunProgress({ index: 0, total: ev.item_count || 0 });
      }),
      bus.subscribe("workbench.item_claimed", (frame) => {
        const ev = d(frame);
        if (ev?.workbench_id !== workbenchId) return;
        setRunProgress({ index: ev.index || 0, total: ev.total || 0 });
        void load();
      }),
      bus.subscribe("workbench.item_done", (frame) => {
        const ev = d(frame);
        if (ev?.workbench_id !== workbenchId) return;
        void load();
      }),
      bus.subscribe("workbench.item_failed", (frame) => {
        const ev = d(frame);
        if (ev?.workbench_id !== workbenchId) return;
        void load();
      }),
      bus.subscribe("workbench.run_complete", (frame) => {
        const ev = d(frame);
        if (ev?.workbench_id !== workbenchId) return;
        setRunning(false);
        setRunProgress(null);
        void load();
        void loadRuns();
        void loadMemory();
      }),
    ];
    return () => unsubs.forEach((u) => u());
  }, [bus, workbenchId, load, loadRuns, loadMemory]);

  // Reconnect-safe: detect in-progress run from item states
  useEffect(() => {
    if (!detail) return;
    const hasClaimed = detail.items.some((i) => i.status === "claimed");
    if (hasClaimed && !running) setRunning(true);
    if (!hasClaimed && running && !runProgress) setRunning(false);
  }, [detail, running, runProgress]);

  /* ── mutations ──────────────────────────────────────────────────── */

  const updateField = async (fields: Record<string, unknown>) => {
    try {
      await apiFetch<any>(`/api/workbenches/${workbenchId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(fields),
      });
      void load();
      void useDesk.getState().refresh();
    } catch {
      /* honest failure on next refresh */
    }
  };

  const updateName = (name: string) => void updateField({ name });
  const updateRecipe = (id: string) => void updateField({ recipe_id: id });
  const updateTarget = (id: string) => void updateField({ profile_id: id });
  const updateSchedule = (cron: string | null) =>
    void updateField({
      schedule: cron,
      schedule_enabled: cron !== null,
    });
  const toggleSchedule = (enabled: boolean) =>
    void updateField({ schedule_enabled: enabled });

  const updateSkillBinding = async (
    skillId: string,
    recipeIds: string[],
    extraFields?: Record<string, unknown>,
  ) => {
    try {
      await apiFetch<any>(`/api/skills/${skillId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipe_ids: recipeIds, ...extraFields }),
      });
      void loadSkills();
    } catch {
      /* */
    }
  };

  const attachSkill = (skillId: string) => {
    const skill = skills.find((s) => s.id === skillId);
    if (!skill || !detail?.recipe_id) return;
    void updateSkillBinding(skillId, [...skill.recipe_ids, detail.recipe_id]);
  };

  const detachSkill = (skillId: string) => {
    const skill = skills.find((s) => s.id === skillId);
    if (!skill || !detail?.recipe_id) return;
    void updateSkillBinding(
      skillId,
      skill.recipe_ids.filter((id) => id !== detail.recipe_id),
    );
  };

  const approveSkill = async (skillId: string) => {
    try {
      await apiFetch<any>(`/api/skills/${skillId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "active" }),
      });
      void loadSkills();
    } catch { /* */ }
  };

  const dismissSkill = async (skillId: string) => {
    try {
      await apiFetch<any>(`/api/skills/${skillId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "dismissed" }),
      });
      void loadSkills();
    } catch { /* */ }
  };

  /* ── item actions ──────────────────────────────────────────────── */

  const addItem = async () => {
    const title = newTitle.trim();
    if (!title) return;
    const payload: Record<string, unknown> = {
      title,
      body: newBody.trim(),
      priority: newPriority,
    };
    if (!groundingIsEmpty(grounding)) {
      payload.grounding = hubGrounding(grounding);
    }
    try {
      await apiFetch<any>(`/api/workbenches/${workbenchId}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setNewTitle("");
      setNewBody("");
      setNewPriority(3);
      setGrounding(emptyGrounding());
      void load();
    } catch {
      /* refresh will show honest state */
    }
  };

  const triggerRun = async () => {
    setRunning(true);
    const pendingCount = detail?.items.filter((i) => i.status === "pending").length || 0;
    setRunProgress({ index: 0, total: pendingCount });
    try {
      await apiFetch<any>(`/api/workbenches/${workbenchId}/run`, {
        method: "POST",
      });
      void load();
      void loadRuns();
    } catch {
      /* */
    }
    setRunning(false);
    setRunProgress(null);
  };

  /* ── voice command handler ─────────────────────────────────────── */

  const handleVoiceProposal = async (proposal: VoiceProposal) => {
    const p = proposal.params as Record<string, any>;
    switch (proposal.intentId) {
      case "add-item": {
        const title = String(p.title || "").trim();
        if (!title) return;
        try {
          await apiFetch<any>(`/api/workbenches/${workbenchId}/items`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title, priority: p.priority || 3 }),
          });
          void load();
        } catch { /* */ }
        break;
      }
      case "run":
        void triggerRun();
        break;
      case "clear-done": {
        const doneItems = (detail?.items || []).filter(
          (i) => i.status === "done" || i.status === "dismissed",
        );
        for (const item of doneItems) {
          try {
            await apiFetch<any>(
              `/api/workbenches/${workbenchId}/items/${item.id}`,
              { method: "DELETE" },
            );
          } catch { /* */ }
        }
        void load();
        break;
      }
      case "set-schedule": {
        const presetLabel = String(p.preset || "").toLowerCase();
        const SCHEDULE_MAP: Record<string, string | null> = {
          "7 am daily": "0 7 * * *", daily: "0 7 * * *",
          "7 am weekdays": "0 7 * * 1-5", weekdays: "0 7 * * 1-5",
          "2 am nightly": "0 2 * * *", nightly: "0 2 * * *",
          "every hour": "0 * * * *", hourly: "0 * * * *",
          manual: null,
        };
        const cron = SCHEDULE_MAP[presetLabel];
        if (cron !== undefined) {
          void updateField({ schedule: cron, schedule_enabled: cron !== null });
        }
        break;
      }
    }
    setVoiceProposal(null);
  };

  /* ── drop-to-work handler ─────────────────────────────────────── */

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDropHover(false);
    const text = e.dataTransfer.getData("application/x-desk-item");
    if (!text) return;
    try {
      const items: Array<{ kind: string; id: string; title: string; body?: string }> =
        JSON.parse(text);
      for (const item of items) {
        const payload: Record<string, unknown> = {
          title: item.title || `${item.kind}: ${item.id}`,
          body: item.body || "",
          priority: 3,
        };
        if (item.kind === "meeting") {
          payload.grounding = { meeting_ids: [item.id] };
        } else if (item.kind === "artifact" || item.kind === "note") {
          payload.grounding = { artifact_ids: [item.id] };
        }
        await apiFetch<any>(`/api/workbenches/${workbenchId}/items`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      }
      void load();
    } catch {
      /* invalid drop data — ignore */
    }
  };

  /* ── render ─────────────────────────────────────────────────────── */

  if (!wb) return null;
  const name = String((wb as any).name || "Workbench");
  const items = detail?.items || [];
  const lastRun = detail?.last_run;
  const isConfigured = !!detail?.recipe_id;
  const showConfig = configOpen ?? !isConfigured;
  const boundSkillCount = detail?.recipe_id
    ? skills.filter((s) => s.recipe_ids.includes(detail.recipe_id!)).length
    : 0;

  const WINGS: WingSpec[] = [
    { id: "items", label: "Items" },
    { id: "runs", label: "Runs" },
    { id: "memory", label: "Memory" },
  ];

  const runButtonLabel = running && runProgress
    ? `Running ${runProgress.index}/${runProgress.total}`
    : running
      ? "Running…"
      : "▸ Run";

  return (
    <DeskWindowFrame
      id={`workbench:${workbenchId}`}
      glyph="⚙"
      label={name}
      title={
        <EditInPlace
          value={name}
          onCommit={updateName}
          label="Workbench name"
          className="wb-title-edit"
        />
      }
      icon={
        recipe ? (
          <AgentAvatar
            avatar={String(recipe.avatar || "")}
            id={String(recipe.id)}
            kind="agent"
            size={32}
          />
        ) : (
          <img
            src={spriteUrl("workbench", workbenchId)}
            alt=""
            width={30}
            height={30}
          />
        )
      }
      wings={
        <SurfaceWings
          wings={WINGS}
          active={activeWing}
          onChange={setActiveWing}
        />
      }
      actions={
        <button
          type="button"
          className="desk-chip"
          data-tone={running ? "warn" : undefined}
          disabled={running || !detail?.recipe_id}
          onClick={() => void triggerRun()}
          title="Run this workbench now"
        >
          {runButtonLabel}
        </button>
      }
      minW={480}
      minH={340}
      open
      origin={origin}
      onClose={() => useDesk.getState().closeWorkbenchWindow(workbenchId)}
      className="desk-pullout desk-workbench-window"
    >
      <div
        className={`desk-surface-body wb-body${dropHover ? " wb-drop-hover" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDropHover(true); }}
        onDragEnter={(e) => { e.preventDefault(); setDropHover(true); }}
        onDragLeave={() => setDropHover(false)}
        onDrop={handleDrop}
      >
        {dropHover ? (
          <div className="wb-drop-zone">Drop to add</div>
        ) : null}
        {error ? <SurfaceState error={error} /> : null}

        {/* ── head scanning indicator ─────────────────────────────── */}
        {running ? (
          <div className="wb-head-scan">
            <LedMeter label="RUNNING" value={0} scanning />
          </div>
        ) : null}

        {/* ── config strip / panel ────────────────────────────────── */}
        {detail && !showConfig ? (
          <ConfigStrip
            recipe={recipe}
            target={target}
            lamp={lamp}
            schedule={detail.schedule}
            scheduleEnabled={detail.schedule_enabled}
            skillCount={boundSkillCount}
            onClick={() => setConfigOpen(true)}
          />
        ) : null}

        {detail && showConfig ? (
          <ConfigPanel
            detail={detail}
            recipes={recipes}
            inferenceTargets={inferenceTargets}
            skills={skills}
            lamp={lamp}
            onUpdateRecipe={updateRecipe}
            onUpdateTarget={updateTarget}
            onUpdateSchedule={updateSchedule}
            onToggleSchedule={toggleSchedule}
            onAttachSkill={attachSkill}
            onDetachSkill={detachSkill}
            onApproveSkill={approveSkill}
            onDismissSkill={dismissSkill}
            onCollapse={() => setConfigOpen(false)}
          />
        ) : null}

        {/* ── items wing ─────────────────────────────────────────── */}
        {activeWing === "items" ? (
          <>
            <div className="wb-items">
              {items.length === 0 && !error && !detail?.recipe_id ? (
                <WorkbenchTemplatePicker onCreated={() => void load()} />
              ) : items.length === 0 && !error ? (
                <SurfaceState
                  empty
                  emptyLabel="No items yet"
                  emptyGlyph="○"
                />
              ) : null}

              {items.map((item) => (
                <WorkbenchItemCard
                  key={item.id}
                  item={item}
                  expanded={expanded === item.id}
                  recipeId={detail?.recipe_id || null}
                  workbenchId={workbenchId}
                  workbenchName={name}
                  onToggle={() =>
                    setExpanded(expanded === item.id ? null : item.id)
                  }
                  onReload={load}
                />
              ))}
            </div>

            {/* ── voice proposal strip ───────────────────────────────── */}
            {voiceProposal ? (
              <div className="wb-proposal-strip">
                <span className="wb-proposal-text">
                  {voiceProposal.intentId === "add-item"
                    ? `Add: "${(voiceProposal.params as any).title}" P${(voiceProposal.params as any).priority || 3}`
                    : voiceProposal.intentId === "run"
                      ? "Run this workbench"
                      : voiceProposal.intentId === "clear-done"
                        ? "Clear done items"
                        : voiceProposal.transcript}
                </span>
                <button
                  type="button"
                  className="desk-chip"
                  onClick={() => void handleVoiceProposal(voiceProposal)}
                >
                  Confirm
                </button>
                <button
                  type="button"
                  className="desk-chip quiet"
                  onClick={() => setVoiceProposal(null)}
                >
                  Cancel
                </button>
              </div>
            ) : null}

            {/* ── composer ──────────────────────────────────────────── */}
            <div className="wb-composer">
              <GroundingSection
                meetings={(useDesk.getState().items.meeting || []).map(
                  (m: any) => ({
                    id: m.id,
                    title: String(m.title || "Untitled meeting"),
                    startedAt: m.startedAt,
                  }),
                )}
                selection={grounding}
                onChange={setGrounding}
                limitTokens={8192}
                meter={false}
              />
              <div className="wb-composer-row">
                <MicButton
                  draftScope={`workbench:${workbenchId}`}
                  grammar={workbenchVoiceGrammar}
                  onText={(t) => setNewTitle((v) => (v ? v + " " + t : t))}
                  onProposalConfirm={(p) => setVoiceProposal(p)}
                />
                <input
                  type="text"
                  className="wb-composer-input"
                  placeholder="Add an item…"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") void addItem();
                  }}
                  aria-label="New item title"
                />
                <button
                  type="button"
                  className="desk-chip wb-priority-cycle"
                  onClick={() => setNewPriority((p) => (p >= 5 ? 1 : p + 1))}
                  title={`Priority ${newPriority} — click to cycle`}
                >
                  P{newPriority}
                </button>
                <TransportKey
                  compact
                  label="ADD"
                  glyph="＋"
                  disabled={!newTitle.trim()}
                  onClick={() => void addItem()}
                />
              </div>
              <FoldGadget title="Body" token={newBody ? `${newBody.length}` : undefined}>
                <PadGadget
                  label="Item body"
                  value={newBody}
                  onChange={setNewBody}
                  placeholder="Optional details…"
                  rows={3}
                  autoGrow
                />
              </FoldGadget>
            </div>
          </>
        ) : null}

        {/* ── runs wing ────────────────────────────────────────────── */}
        {activeWing === "runs" ? (
          <div className="wb-runs-wing">
            <SurfaceLedger
              count={`${runs.length} RUNS`}
            >
              {runs.length === 0 ? (
                <SurfaceState empty emptyLabel="No runs yet" emptyGlyph="○" />
              ) : null}
              {runs.map((run) => {
                const runLamp = boundaryEgressLamp(run.egress_boundary);
                const statusChip = run.status === "completed"
                  ? { label: "COMPLETED", tone: "ok" }
                  : run.status === "running"
                    ? { label: "RUNNING", tone: "warn" }
                    : { label: "FAILED", tone: "fail" };
                return (
                  <SurfaceLedgerRow
                    key={run.id}
                    time={humanTime(run.started_at)}
                    primary={
                      <>
                        {run.items_completed}/{run.items_attempted} done
                        {run.items_failed ? ` · ${run.items_failed} failed` : ""}
                        {" · "}
                        {runLamp.label}
                        {run.model ? ` · ${run.model}` : ""}
                      </>
                    }
                    cells={
                      <span className="desk-chip" data-tone={statusChip.tone}>
                        {statusChip.label}
                      </span>
                    }
                    open={openRunId === run.id}
                    onToggle={() =>
                      setOpenRunId(openRunId === run.id ? null : run.id)
                    }
                  >
                    <div className="wb-run-detail">
                      <dl className="surface-facts">
                        <div><dt>egress</dt><dd>{runLamp.label}</dd></div>
                        <div><dt>model</dt><dd>{run.model || "—"}</dd></div>
                        <div><dt>tokens</dt><dd>{run.total_tokens.toLocaleString()}</dd></div>
                        {run.completed_at ? (
                          <div><dt>completed</dt><dd>{humanTime(run.completed_at)}</dd></div>
                        ) : null}
                      </dl>
                    </div>
                  </SurfaceLedgerRow>
                );
              })}
            </SurfaceLedger>
          </div>
        ) : null}

        {/* ── memory wing ──────────────────────────────────────────── */}
        {activeWing === "memory" ? (
          <div className="wb-memory-wing">
            <SurfaceLedger
              count={`${memoryEntries.length} MEMORIES`}
              controls={
                memoryEntries.length > 0 ? (
                  <ConfirmVerb
                    label="Clear"
                    confirmLabel="Clear all?"
                    onConfirm={async () => {
                      try {
                        await apiFetch<any>(`/api/workbenches/${workbenchId}/memory`, { method: "DELETE" });
                        void loadMemory();
                      } catch { /* */ }
                    }}
                  />
                ) : null
              }
            >
              {memoryEntries.length === 0 ? (
                <SurfaceState empty emptyLabel="No memories yet" emptyGlyph="◇" />
              ) : null}
              {memoryEntries.map((entry, i) => {
                const kindBadge = entry.kind === "lesson" ? "LESSON" : entry.kind === "preference" ? "PREF" : "OBS";
                return (
                  <SurfaceLedgerRow
                    key={`${entry.run_id}-${i}`}
                    time={humanTime(entry.timestamp)}
                    primary={entry.content}
                    cells={
                      <>
                        <span className="desk-chip" style={{ fontSize: "9px", height: "18px", padding: "0 6px" }}>
                          {kindBadge}
                        </span>
                        {entry.provenance?.model ? (
                          <span className="wb-memory-model">{entry.provenance.model}</span>
                        ) : null}
                      </>
                    }
                    open={openRunId === `mem-${i}`}
                    onToggle={() => setOpenRunId(openRunId === `mem-${i}` ? null : `mem-${i}`)}
                  >
                    <div className="wb-memory-detail">
                      <p className="wb-memory-content">{entry.content}</p>
                      {entry.item_title ? (
                        <span className="wb-memory-source">from: {entry.item_title}</span>
                      ) : null}
                      <div className="wb-memory-verbs">
                        <button
                          type="button"
                          className="desk-chip"
                          onClick={async () => {
                            try {
                              await apiFetch<any>(
                                `/api/workbenches/${workbenchId}/memory/${i}/promote`,
                                { method: "POST" },
                              );
                              void loadSkills();
                            } catch { /* */ }
                          }}
                        >
                          Promote to skill
                        </button>
                      </div>
                    </div>
                  </SurfaceLedgerRow>
                );
              })}
            </SurfaceLedger>
          </div>
        ) : null}
      </div>

      <DeskWindowFooter
        status={
          <span className="wb-footer-status">
            {items.length} {items.length === 1 ? "item" : "items"}
            {lastRun
              ? ` · last run ${humanTime(lastRun.completed_at || lastRun.started_at)}`
              : ""}
            {lastRun?.total_tokens
              ? ` · ${lastRun.total_tokens.toLocaleString()} tok`
              : ""}
          </span>
        }
      />
    </DeskWindowFrame>
  );
}
