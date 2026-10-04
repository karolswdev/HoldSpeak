import "./workbench-config.css";
import {
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
} from "react";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import type {
  WorkbenchDetail,
  WorkbenchItem,
  Skill,
  WorkbenchAutomation,
  ResourcefulPolicy,
} from "../detail-types";
import {
  fetchWorkbenchDetail,
  fetchWorkbenchRuns,
  fetchWorkbenchMemory,
  fetchSkills,
  fetchWorkbenchAutomations,
  fetchResourcefulPolicy,
  updateResourcefulPolicy,
  setWorkbenchAutomationEnabled,
  updateWorkbenchField,
  addWorkbenchItem,
  updateWorkbenchItem,
  parkWorkbenchItem,
  parkWorkbenchItems,
  restoreWorkbenchItems,
  fetchParkedWorkbenchItems,
  triggerWorkbenchRun,
  clearWorkbenchMemory,
  promoteMemoryToSkill,
  retryMint,
} from "../api";
import { usePrimitiveDetail } from "../hooks/usePrimitiveDetail";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { useWriteReceipt, type WriteAttempt } from "../hooks/useWriteReceipt";
import { boundaryEgressLamp } from "../inferenceEgress";
import { ApiError, apiRequest } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import {
  ParkReceipt,
  ParkedStrip,
  parkClock,
  parkedOutcome,
  restoredOutcome,
  restoreFailedOutcome,
  notParkedOutcome,
  type ParkOutcome,
  type ParkedRow,
} from "../surface";

/** HS-151-07: inlined from the retired chat.ts — recipe keep is not a thread
 * operation; the /api/recipes/{id}/keep route lives on independently. */
async function keepReply(
  recipeId: string,
  question: string,
  output: string,
): Promise<string | null> {
  try {
    const res = await apiRequest(
      `/api/recipes/${encodeURIComponent(recipeId)}/keep`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, output }),
      },
    );
    if (!res.ok) return null;
    const data = await res.json().catch(() => ({}));
    return data.artifact_id ? String(data.artifact_id) : null;
  } catch {
    return null;
  }
}
import {
  emptyGrounding,
  groundingIsEmpty,
  hubGrounding,
  type GroundingSelection,
} from "../grounding";
import type { ResolvedRef } from "../../lib/drawerResolver";
import { resolveDrawerNames } from "../../lib/drawerResolver";
import { resolveVoiceReferences } from "../api";
import { DeskWindowFrame } from "./DeskWindow";
import { SurfaceFooter } from "../surface/SurfaceFooter";
import { AgentAvatar } from "./AgentAvatar";
import { WhyControl } from "./WhyControl";
import { GroundingSection } from "./GroundingSection";
import { MicButton } from "./MicButton";
import type { MicState } from "./MicButton";
import { ContextualAssignment } from "../../pages/cores/ContextualAssignment";
import { openSurfaceOr } from "../shell";
import { onReturnToTask, rememberTaskFocus } from "../returnToTask";
import {
  CheckGadget,
  EgressChip,
  FoldGadget,
  LampGadget,
  LedMeter,
  PadGadget,
  StringGadget,
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
import { useRuntimeBus, type RuntimeFrame } from "../../runtime/RuntimeBus";
import { workbenchVoiceGrammar } from "../voice/grammars/workbench";
import type { VoiceProposal } from "../voice/grammar";
import { humanTime } from "../surface/format";
import {
  InletAutocomplete,
  findAtTrigger,
  filterZones,
  zoneToRef,
  removeAtSpan,
} from "./InletAutocomplete";
import { WorkbenchAutomations } from "./WorkbenchAutomations";
import { WorkbenchResourceful } from "./WorkbenchResourceful";
import {
  WORKBENCH_RUN_FRAME_TYPES,
  initialWorkbenchRunState,
  isWorkbenchRunActive,
  planWorkbenchRunFrame,
  workbenchRunReducer,
  workbenchRunRequestFailure,
} from "./workbench/runLifecycle";
import { WorkbenchRunsWing } from "./workbench/WorkbenchRunsWing";
import { countLabel, countToken } from "../surface";

/* ── schedule presets ───────────────────────────────────────────────── */

const SCHEDULE_PRESETS: { label: string; cron: string | null }[] = [
  { label: "7 AM daily", cron: "0 7 * * *" },
  { label: "7 AM weekdays", cron: "0 7 * * 1-5" },
  { label: "2 AM nightly", cron: "0 2 * * *" },
  { label: "Every hour", cron: "0 * * * *" },
  { label: "Manual", cron: null },
];

/** The hub's named Run refusal for a workbench with no usable engine
 *  (`holdspeak/web/routes/primitives/workbenches.py`, HTTP 409). */
function isNoEngineRefusal(cause: unknown): boolean {
  if (!(cause instanceof ApiError) || cause.status !== 409) return false;
  const code = (cause.payload as { code?: unknown } | null)?.code;
  return code === "no_assignment" || code === "no_compatible_assignment";
}

function humanSchedule(cron: string | null): string {
  if (!cron) return "Manual";
  const preset = SCHEDULE_PRESETS.find((p) => p.cron === cron);
  if (preset) return preset.label;
  return cron;
}

/* ── item status ───────────────────────────────────────────────────── */

const STATUS_CHIPS: Record<string, { label: string; tone: string }> = {
  pending: { label: "NEEDS REVIEW", tone: "" },
  claimed: { label: "RUNNING", tone: "warn" },
  done: { label: "DONE", tone: "ok" },
  failed: { label: "FAILED", tone: "fail" },
  dismissed: { label: "DISMISSED", tone: "" },
};

const PRIORITY_LABELS = ["", "P1", "P2", "P3", "P4", "P5"];

/* ── config strip (collapsed) ──────────────────────────────────────── */

function ConfigStrip({
  recipe,
  schedule,
  scheduleEnabled,
  startSummary,
  skillCount,
  onClick,
}: {
  recipe: any;
  schedule: string | null;
  scheduleEnabled: boolean;
  startSummary: string | null;
  skillCount: number;
  onClick: () => void;
}) {
  return (
    <Button
      variant="chrome"
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
      <span className="wb-config-strip-schedule">
        {startSummary || `${scheduleEnabled ? "⏱" : "⏸"} ${humanSchedule(schedule)}`}
      </span>
      {skillCount > 0 ? (
        <span className="desk-chip wb-config-strip-skills">
          {skillCount} {skillCount === 1 ? "skill" : "skills"}
        </span>
      ) : null}
      <span className="wb-config-strip-chevron" aria-hidden="true">▾</span>
    </Button>
  );
}

/* ── config panel (expanded) ───────────────────────────────────────── */

function ConfigPanel({
  detail,
  recipes,
  skills,
  onUpdateRecipe,
  onUpdateSchedule,
  onToggleSchedule,
  workbenchId,
  write,
  automations,
  resourcefulPolicy,
  onAutomationsChanged,
  onResourcefulChanged,
  onCollapse,
  onEngineChanged,
}: {
  /** The RUNS ON assignment was saved: the window reads its engine again. */
  onEngineChanged?: () => void;
  detail: WorkbenchDetail;
  recipes: any[];
  skills: Skill[];
  onUpdateRecipe: (id: string) => void;
  onUpdateSchedule: (cron: string | null) => void;
  onToggleSchedule: (enabled: boolean) => void;
  workbenchId: string;
  write: WriteAttempt;
  automations: WorkbenchAutomation[];
  resourcefulPolicy: ResourcefulPolicy | null;
  onAutomationsChanged: () => void;
  onResourcefulChanged: () => void;
  onCollapse: () => void;
}) {
  const [agentSearch, setAgentSearch] = useState("");
  const activeAutomationCount = automations.filter((automation) => automation.enabled).length;
  const [startMode, setStartMode] = useState<"manual" | "schedule" | "event" | "idle">(
    resourcefulPolicy?.enabled
      ? "idle"
      : activeAutomationCount
        ? "event"
        : detail.schedule_enabled && detail.schedule ? "schedule" : "manual",
  );
  const [startModeTouched, setStartModeTouched] = useState(false);

  useEffect(() => {
    if (startModeTouched) return;
    if (resourcefulPolicy?.enabled) setStartMode("idle");
    else if (activeAutomationCount && !detail.schedule_enabled) setStartMode("event");
  }, [activeAutomationCount, detail.schedule_enabled, resourcefulPolicy?.enabled, startModeTouched]);

  const selectStartMode = (mode: "manual" | "schedule" | "event" | "idle") => {
    setStartModeTouched(true);
    setStartMode(mode);
    if (mode !== "schedule" && detail.schedule_enabled) onToggleSchedule(false);
    if (mode !== "event" && activeAutomationCount > 0) {
      void write("PAUSE EVENT STARTS", async () => {
        await Promise.all(
          automations
            .filter((automation) => automation.enabled)
            .map((automation) => setWorkbenchAutomationEnabled(
              workbenchId, automation.id, false,
            )),
        );
        onAutomationsChanged();
      });
    }
    if (mode !== "idle" && resourcefulPolicy?.enabled) {
      void write("PAUSE RESOURCEFULNESS", async () => {
        await updateResourcefulPolicy(workbenchId, {
          enabled: false,
          idle_after_minutes: resourcefulPolicy.idle_after_minutes,
          cooldown_hours: resourcefulPolicy.cooldown_hours,
          nightly_target: resourcefulPolicy.nightly_target,
          night_only: resourcefulPolicy.night_only,
          night_start_hour: resourcefulPolicy.night_start_hour,
          night_end_hour: resourcefulPolicy.night_end_hour,
          routines: resourcefulPolicy.routines,
        });
        onResourcefulChanged();
      });
    }
  };

  const recipe = recipes.find((r) => r.id === detail.recipe_id);

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
        {filteredRecipes.length === 0 && recipes.length === 0 ? (
          <SurfaceState
            empty
            emptyLabel="No agents yet"
            emptyGlyph="+"
            actionLabel="New Agent"
            onAction={() =>
              void useDesk.getState().createPrimitive("recipe")
            }
          />
        ) : filteredRecipes.length === 0 ? (
          <SurfaceState empty emptyLabel="No agents match" />
        ) : null}
      </SurfaceSection>

      {/* ── assignments ───────────────────────────────────────────── */}
      <SurfaceSection label="RUNS ON">
        <ContextualAssignment
          label="Item assignment"
          capabilityId="workbench.item"
          onChanged={onEngineChanged}
          scope={{
            kind: "subject",
            subject_kind: "workbench",
            subject_id: workbenchId,
            capability_id: "workbench.item",
          }}
        />
      </SurfaceSection>

      <SurfaceSection label="RESOLVES WITH">
        <ContextualAssignment
          label="Reference assignment"
          capabilityId="voice.reference_resolve"
          scope={{
            kind: "subject",
            subject_kind: "workbench",
            subject_id: workbenchId,
            capability_id: "voice.reference_resolve",
          }}
        />
      </SurfaceSection>

      {/* ── start condition ───────────────────────────────────────── */}
      <SurfaceSection label="STARTS WHEN">
        <div className="wb-start-mode" role="radiogroup" aria-label="Workbench start condition">
          <button
            type="button"
            role="radio"
            aria-checked={startMode === "manual"}
            className="desk-chip"
            onClick={() => selectStartMode("manual")}
          >
            Manual
          </button>
          <button
            type="button"
            role="radio"
            aria-checked={startMode === "schedule"}
            className="desk-chip"
            onClick={() => selectStartMode("schedule")}
          >
            Schedule
          </button>
          <button
            type="button"
            role="radio"
            aria-checked={startMode === "event"}
            className="desk-chip"
            onClick={() => selectStartMode("event")}
          >
            Event
          </button>
          <button
            type="button"
            role="radio"
            aria-checked={startMode === "idle"}
            className="desk-chip"
            onClick={() => selectStartMode("idle")}
          >
            Idle
          </button>
        </div>
        {startMode === "manual" ? (
          <p className="wb-start-mode-copy">Starts only when you press Run.</p>
        ) : null}
        {startMode === "schedule" ? (
          <div className="wb-schedule-row">
            {SCHEDULE_PRESETS.filter((preset) => preset.cron !== null).map((preset) => (
              <button
                key={preset.label}
                type="button"
                className="desk-chip"
                aria-pressed={preset.cron === detail.schedule}
                onClick={() => onUpdateSchedule(preset.cron)}
              >
                {preset.label}
              </button>
            ))}
            {/* HS-132-07 — a disabled control names why (AC 4). */}
            <span className="wb-schedule-toggle" title={detail.schedule ? undefined : "Pick a schedule first"}>
              <CheckGadget
                label="Schedule enabled"
                checked={detail.schedule_enabled}
                onChange={onToggleSchedule}
                disabled={!detail.schedule}
              />
            </span>
          </div>
        ) : null}
        {startMode === "event" ? <WorkbenchAutomations workbenchId={workbenchId} write={write} onChanged={onAutomationsChanged} /> : null}
        {startMode === "idle" ? (
          <WorkbenchResourceful
            workbenchId={workbenchId}
            policy={resourcefulPolicy}
            write={write}
            onChanged={onResourcefulChanged}
          />
        ) : null}
      </SurfaceSection>

      {/* ── skills (read-only, inherited from the bound agent) ─────── */}
      <SurfaceSection
        label="SKILLS"
        actions={
          countToken(boundSkills.length, "INHERITED") ? (
            <span className="wb-config-skill-count">
              {countToken(boundSkills.length, "INHERITED")}
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
              />
            ))}
          </SurfaceRows>
        ) : detail.recipe_id ? (
          <SurfaceState
            empty
            emptyLabel="Agent has no skills yet"
            emptyGlyph="◇"
          />
        ) : (
          <SurfaceState
            empty
            emptyLabel="Skills appear when an agent is bound"
            emptyGlyph="◇"
          />
        )}
        {detail.recipe_id ? (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={() =>
              useDesk.getState().openPullout("recipe:" + detail.recipe_id)
            }
          >
            Edit in Agent
          </button>
        ) : null}
      </SurfaceSection>

      {/* ── workspace path ──────────────────────────────────────────── */}
      <div className="wb-workspace-path">
        ~/.holdspeak/workbenches/{detail.id}/
      </div>
    </div>
  );
}

/* ── drop-target grammar (HS-132-07) ───────────────────────────────── */

/** What this workbench will REALLY do with the payload under the cursor.
 * The old overlay promised ADD ITEM for every drag while the handler took
 * desk items only, so a dropped file silently minted a Meeting instead. */
export interface DropIntent {
  /** The honest verb, in label grammar. */
  verb: string;
  /** True when the workbench takes the payload; false names a refusal. */
  accepted: boolean;
}

export function dropTypes(transfer: DataTransfer | null | undefined): string[] {
  const types = transfer?.types;
  return types ? Array.from(types as ArrayLike<string>) : [];
}

export function workbenchDropVerb(types: readonly string[]): DropIntent {
  if (types.includes("application/x-desk-item"))
    return { verb: "ADD ITEM", accepted: true };
  // Files never stop here: the desk's glass layer imports them (HS-101 B7).
  if (types.includes("Files"))
    return { verb: "IMPORT AS MEETING", accepted: false };
  return { verb: "NOT A WORKBENCH ITEM", accepted: false };
}

/** The chip the overlay wears before the release. */
export function dropIntentLabel(intent: DropIntent): string {
  return intent.verb === "NOT A WORKBENCH ITEM"
    ? `NO DROP · ${intent.verb}`
    : `DROP TARGET · ${intent.verb}`;
}

/* ── item card ─────────────────────────────────────────────────────── */

/** HS-132-07 — the pause that ends a typing burst, matching the desk's
 * other inline editors (`useDebouncedSave`). */
export const BODY_SAVE_PAUSE_MS = 450;

function WorkbenchItemCard({
  item,
  expanded,
  recipeId,
  workbenchId,
  workbenchName,
  onToggle,
  onReload,
  onRemove,
  onCopy,
  write,
  restored = false,
}: {
  item: WorkbenchItem;
  /** PHILO-13-02 — the item Restore just brought back: in view, marked. */
  restored?: boolean;
  expanded: boolean;
  recipeId: string | null;
  workbenchId: string;
  workbenchName: string;
  onToggle: () => void;
  onReload: () => void;
  onRemove: (item: WorkbenchItem) => void;
  onCopy: (text: string) => void;
  /** HS-132-06 — the window's write-receipt channel (the card has no foot). */
  write: WriteAttempt;
}) {
  const chip = STATUS_CHIPS[item.status] || STATUS_CHIPS.pending;
  const cardRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (restored) cardRef.current?.scrollIntoView?.({ block: "nearest" });
  }, [restored]);
  const egressLamp = item.result_egress?.boundary
    ? boundaryEgressLamp(item.result_egress.boundary)
    : null;
  const hasResult = !!(item.result && (item.status === "done" || item.status === "failed"));
  const failureReason =
    item.status === "failed" ? item.error_reason || item.error : null;
  const hasGrounding =
    item.grounding &&
    typeof item.grounding === "object" &&
    Object.keys(item.grounding).length > 0;

  const updateItem = async (
    fields: Record<string, unknown>,
    verb = "SAVE ITEM",
  ) => {
    const result = await write(verb, () =>
      updateWorkbenchItem(workbenchId, item.id, fields),
    );
    if (result.ok) onReload();
    return result.ok;
  };

  const rerunItem = () => void updateItem({ status: "pending", result: null, result_egress: null, tokens_consumed: 0, completed_at: null }, "RE-RUN ITEM");
  const dismissItem = () => void updateItem({ status: "dismissed" }, "DISMISS ITEM");

  // HS-132-07 — the body is a LOCAL draft. The old well bound the server
  // value straight to the textarea and fired a PUT + full refetch on every
  // keystroke, so a refetch landing mid-word overwrote what was typed. The
  // draft owns the characters; the hub sees one PUT per pause (the same
  // 450ms the desk's other editors use), and a refused save still names
  // itself through the window's write-receipt channel.
  const serverBody = item.body || "";
  const [bodyDraft, setBodyDraft] = useState<string | null>(null);
  const bodyTimer = useRef<number | null>(null);
  useEffect(
    () => () => {
      if (bodyTimer.current) window.clearTimeout(bodyTimer.current);
    },
    [],
  );
  // Once the hub holds exactly what was typed, the draft dissolves and the
  // server value drives the well again.
  useEffect(() => {
    if (bodyDraft !== null && bodyDraft === serverBody && bodyTimer.current === null)
      setBodyDraft(null);
  }, [bodyDraft, serverBody]);
  const editBody = (next: string) => {
    setBodyDraft(next);
    if (bodyTimer.current) window.clearTimeout(bodyTimer.current);
    bodyTimer.current = window.setTimeout(() => {
      bodyTimer.current = null;
      void updateItem({ body: next });
    }, BODY_SAVE_PAUSE_MS);
  };

  const [keeping, setKeeping] = useState(false);
  const handleKeep = async () => {
    if (!recipeId || !item.result) return;
    setKeeping(true);
    // keepReply reports its own refusal as null (it never throws), so the
    // null is raised here to reach the one channel.
    const result = await write("KEEP", async () => {
      const artifactId = await keepReply(recipeId, item.title, item.result!);
      if (!artifactId) throw new Error("keep refused");
      return artifactId;
    });
    if (result.ok) void useDesk.getState().refresh();
    setKeeping(false);
  };

  // Issue 5: inline expansion for pending-review artifacts (no desk pullout)
  const [artifactExpanded, setArtifactExpanded] = useState(false);

  const [minting, setMinting] = useState(false);
  const handleRetryMint = async () => {
    setMinting(true);
    const result = await write("RETRY MINT", async () => {
      const artifactId = await retryMint(workbenchId, item.id);
      if (!artifactId) throw new Error("mint refused");
      return artifactId;
    });
    if (result.ok) onReload();
    setMinting(false);
  };

  const artifactId = item.result_artifact_id;
  const hasMintedArtifact = !!artifactId;
  // Issue 4 fix: use mint_attempted to distinguish "mint failed" from "legacy pre-mint item"
  const mintFailed = item.status === "done" && !!item.result && !hasMintedArtifact && !!item.mint_attempted;
  const legacyKeep = item.status === "done" && !!item.result && !hasMintedArtifact && !item.mint_attempted;

  return (
    <div
      ref={cardRef}
      className="wb-card"
      data-status={item.status}
      data-restored={restored || undefined}
    >
      {/* ── head line ──────────────────────────────────────────── */}
      <Button
        variant="chrome"
        className="wb-card-head"
        onClick={onToggle}
        aria-expanded={expanded}
      >
        <span
          className="desk-chip wb-item-priority"
          data-tone={item.priority === 1 ? "fail" : item.priority === 2 ? "warn" : undefined}
        >
          {PRIORITY_LABELS[item.priority] || "P3"}
        </span>
        <span className="wb-card-title">{item.title}</span>
        {item.status === "claimed" ? (
          <LedMeter label="WORKING" value={0} scanning />
        ) : null}
        <span className="desk-chip" data-tone={chip.tone}>
          {chip.label}
        </span>
      </Button>
      <WhyControl workType="workbench_item" workRef={item.id} />

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
              value={bodyDraft ?? serverBody}
              onChange={editBody}
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
                    ▣ {String(typeof val === "object" && val !== null && "title" in val ? (val as Record<string, unknown>).title : key)}
                  </span>
                ) : null,
              )}
            </div>
          ) : null}

          {/* result + egress */}
          {hasResult ? (
            <div className="wb-card-result">
              <div className="wb-card-result-head">
                <span className="wb-card-result-label">
                  {item.status === "failed" ? "FAILED" : "RESULT"}
                </span>
                <button
                  type="button"
                  className="desk-chip quiet"
                  onClick={() => onCopy(item.result!)}
                >
                  Copy
                </button>
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
                {hasMintedArtifact ? (
                  <span className="desk-chip" data-tone="info">pending-review</span>
                ) : null}
                {mintFailed ? (
                  <span className="desk-chip" data-tone="fail">Mint failed</span>
                ) : null}
              </div>
              {hasMintedArtifact ? (
                <div className="wb-card-artifact-link">
                  <span className="wb-card-artifact-title">
                    {workbenchName}: {item.title}
                  </span>
                </div>
              ) : null}
              {failureReason ? (
                <div className="wb-card-error-reason" role="alert">
                  <span>ERROR</span>
                  <span>{failureReason}</span>
                </div>
              ) : null}
              <div className="wb-card-result-body">
                <Material>{item.result!}</Material>
              </div>
              {/* Issue 5: inline artifact detail (not a desk pullout) */}
              {hasMintedArtifact && artifactExpanded ? (
                <div className="wb-card-artifact-detail">
                  <div className="wb-card-artifact-detail-head">
                    <span className="desk-chip" data-tone="info">pending-review</span>
                    <span className="wb-card-artifact-detail-id">{artifactId}</span>
                  </div>
                  <div className="wb-card-artifact-detail-body">
                    <Material>{item.result!}</Material>
                  </div>
                  {egressLamp ? (
                    <div className="wb-card-artifact-detail-egress">
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
                    </div>
                  ) : null}
                </div>
              ) : null}
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
            {/* Minted artifact: inline expand (Issue 5: no desk pullout for pending-review) */}
            {hasMintedArtifact ? (
              <button
                type="button"
                className="desk-chip"
                onClick={() => setArtifactExpanded(!artifactExpanded)}
                aria-expanded={artifactExpanded}
              >
                {artifactExpanded ? "Collapse" : "Open"}
              </button>
            ) : null}
            {/* Mint failed: show Retry mint verb */}
            {mintFailed ? (
              <button
                type="button"
                className="desk-chip"
                disabled={minting}
                onClick={() => void handleRetryMint()}
              >
                {minting ? "Minting…" : "Retry mint"}
              </button>
            ) : null}
            {/* Legacy Keep: only for pre-Phase-118 items (mint never attempted) */}
            {legacyKeep && recipeId ? (
              <button
                type="button"
                className="desk-chip quiet"
                disabled={keeping}
                onClick={() => void handleKeep()}
              >
                {keeping ? "Keeping…" : "Keep"}
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
              <Button dense variant="ghost" onClick={dismissItem}>
                Dismiss
              </Button>
            ) : null}
            {/* PHILO-13-02: Park, never delete (one press; Restore undoes
                it). A claimed item shows no Park (today's rule stays). */}
            {item.status !== "claimed" ? (
              <Button dense variant="ghost" onClick={() => onRemove(item)}>
                Park
              </Button>
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
  const recipes = useDesk((s) => s.items.recipe);

  /* ── data loading (usePrimitiveDetail) ──────────────────────────── */

  const detailHook = usePrimitiveDetail("workbench", workbenchId, fetchWorkbenchDetail);
  const runsHook = usePrimitiveDetail("workbench-runs", workbenchId, fetchWorkbenchRuns);
  const memoryHook = usePrimitiveDetail("workbench-memory", workbenchId, fetchWorkbenchMemory);
  const skillsHook = usePrimitiveDetail<Skill[]>("skills", workbenchId, fetchSkills);
  const automationsHook = usePrimitiveDetail<WorkbenchAutomation[]>("workbench-automations", workbenchId, fetchWorkbenchAutomations);
  const resourcefulHook = usePrimitiveDetail<ResourcefulPolicy>("workbench-resourceful", workbenchId, fetchResourcefulPolicy);

  const detail = detailHook.data;
  const runs = runsHook.data ?? [];
  const memoryEntries = memoryHook.data ?? [];
  const skills = skillsHook.data ?? [];
  const automations = automationsHook.data ?? [];
  const resourcefulPolicy = resourcefulHook.data;
  const error = detailHook.error ?? "";

  // Convenience aliases for the old load/loadX callbacks used by WS handlers and mutations.
  const load = detailHook.refresh;
  const loadRuns = runsHook.refresh;
  const loadMemory = memoryHook.refresh;
  const loadSkills = skillsHook.refresh;
  const loadAutomations = automationsHook.refresh;
  const loadResourceful = resourcefulHook.refresh;
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  // HS-132-06 — every write verb in this window reports here; the receipt
  // seats in the footer's receipt slot, never over the work.
  const {
    attempt: write,
    fail: failWrite,
    clear: clearWrite,
    failure: writeFailure,
    receipt: writeReceipt,
  } = useWriteReceipt();
  // PHILO-13-02 (A1-F): the park outcome, the parked items, the Parked filter.
  const [parkOutcome, setParkOutcome] = useState<ParkOutcome | null>(null);
  const [parked, setParked] = useState<ParkedRow[]>([]);
  const [parkedOn, setParkedOn] = useState(false);
  const [restoredId, setRestoredId] = useState<string | null>(null);
  const parkTimes = useRef(new Map<string, string>());
  const loadParked = useCallback(async () => {
    try {
      const rows = await fetchParkedWorkbenchItems(workbenchId);
      setParked(
        rows.map((item) => ({
          id: item.id,
          title: item.title,
          at:
            parkTimes.current.get(item.id) ??
            (item.last_modified ? parkClock(new Date(item.last_modified)) : ""),
        })),
      );
    } catch {
      // The strip keeps its last read.
    }
  }, [workbenchId]);
  useEffect(() => {
    void loadParked();
  }, [loadParked, detail]);
  useEffect(() => {
    if (!parked.length) setParkedOn(false);
  }, [parked.length]);
  // A copy receipt takes the slot from the park outcome.
  const copying = Boolean(copyReceipt);
  useEffect(() => {
    if (copying) setParkOutcome(null);
  }, [copying]);

  const [expanded, setExpanded] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [configOpen, setConfigOpen] = useState<boolean | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [newBody, setNewBody] = useState("");
  const [newPriority, setNewPriority] = useState(3);
  const [grounding, setGrounding] = useState<GroundingSelection>(emptyGrounding);
  const [groundingRefs, setGroundingRefs] = useState<ResolvedRef[]>([]);
  const [runLifecycle, dispatchRun] = useReducer(
    workbenchRunReducer,
    initialWorkbenchRunState,
  );
  const running = isWorkbenchRunActive(runLifecycle);
  const runProgress = runLifecycle.progress;
  const [activeWing, setActiveWing] = useState("items");
  const [openRunId, setOpenRunId] = useState<string | null>(null);
  const [voiceProposal, setVoiceProposal] = useState<VoiceProposal | null>(null);
  const [dropHover, setDropHover] = useState(false);
  // HS-132-07 — what the drag under the cursor will actually do here.
  const [dropIntent, setDropIntent] = useState<DropIntent | null>(null);
  const [resolving, setResolving] = useState(false);
  const [resolverError, setResolverError] = useState<string | null>(null);
  const generationRef = useRef(0);
  const configAutoExpanded = useRef(false);
  const runTimeoutRef = useRef<number | null>(null);

  const clearRunTimeout = useCallback(() => {
    if (runTimeoutRef.current === null) return;
    window.clearTimeout(runTimeoutRef.current);
    runTimeoutRef.current = null;
  }, []);

  useEffect(() => clearRunTimeout, [clearRunTimeout]);

  /* ── @-reference autocomplete state ─────────────────────────────── */
  const zones = useDesk((s) => s.items.directory || []);
  const [cursorPos, setCursorPos] = useState(0);
  const [acSelectedIndex, setAcSelectedIndex] = useState(0);
  const [acDismissed, setAcDismissed] = useState(false);
  const typedAtPosRef = useRef<number | null>(null);
  const inletInputRef = useRef<HTMLInputElement>(null);
  const prevAcQueryRef = useRef("");

  // Fix #2: only open autocomplete for typed @ characters.
  const rawAtPos = acDismissed ? -1 : findAtTrigger(newTitle, cursorPos, zones);
  const atPos =
    rawAtPos >= 0 && typedAtPosRef.current !== null && rawAtPos === typedAtPosRef.current
      ? rawAtPos
      : -1;
  const acOpen = atPos >= 0;
  const acQuery = acOpen ? newTitle.slice(atPos + 1, cursorPos) : "";
  const acMatches = acOpen ? filterZones(acQuery, zones) : [];

  // Fix #5: reset selected index when query changes.
  if (acQuery !== prevAcQueryRef.current) {
    prevAcQueryRef.current = acQuery;
    if (acSelectedIndex !== 0) {
      setAcSelectedIndex(0);
    }
  }

  // Clamp selected index when matches change.
  const clampedAcIndex = Math.min(acSelectedIndex, Math.max(0, acMatches.length - 1));
  if (clampedAcIndex !== acSelectedIndex) {
    setAcSelectedIndex(clampedAcIndex);
  }
  const acActiveId =
    acOpen && acMatches.length > 0
      ? `wb-inlet-option-${acMatches[clampedAcIndex].id}`
      : undefined;

  const addGroundingRef = useCallback((ref: ResolvedRef) => {
    setGroundingRefs((prev) => {
      if (prev.some((r) => r.ref === ref.ref)) return prev;
      return [...prev, ref];
    });
  }, []);

  const removeGroundingRef = useCallback((ref: string) => {
    setGroundingRefs((prev) => prev.filter((r) => r.ref !== ref));
  }, []);

  const selectAutocompleteZone = useCallback((zone: typeof zones[number]) => {
    const ref = zoneToRef(zone);
    addGroundingRef(ref);
    // Fix #6, #7: remove @query span with whitespace collapse.
    if (atPos >= 0) {
      const result = removeAtSpan(newTitle, atPos, cursorPos);
      setNewTitle(result.text);
      setCursorPos(result.cursor);
      // Focus and set cursor position on next tick.
      requestAnimationFrame(() => {
        if (inletInputRef.current) {
          inletInputRef.current.setSelectionRange(result.cursor, result.cursor);
          inletInputRef.current.focus();
        }
      });
    }
    setAcSelectedIndex(0);
    setAcDismissed(false);
    typedAtPosRef.current = null;
  }, [atPos, newTitle, cursorPos, addGroundingRef]);

  // Fix #3: close autocomplete when mic arms.
  const handleMicState = useCallback((state: MicState) => {
    if (state === "listening") {
      setAcDismissed(true);
      typedAtPosRef.current = null;
    }
  }, []);

  const recipe = recipes.find(
    (r) => r.id === (detail?.recipe_id || wb?.recipeId),
  );
  const resolveInletReferences = useCallback((text = newTitle) => {
    if (!detail || !text.trim()) return;
    const gen = ++generationRef.current;
    setResolving(true);
    setResolverError(null);
    void resolveVoiceReferences(workbenchId, text, `vr_${gen}_${Date.now()}`)
      .then((result) => {
        if (generationRef.current !== gen) return;
        if (result.error) {
          setResolverError(result.error);
        } else {
          result.refs.forEach((ref) => addGroundingRef(ref));
        }
      })
      .catch((err: unknown) => {
        if (generationRef.current !== gen) return;
        const status = (err as { status?: number }).status;
        setResolverError(
          status === 409
            ? "resolver_not_configured"
            : status === 503
              ? "resolver_unavailable"
              : "resolver_error",
        );
      })
      .finally(() => {
        if (generationRef.current === gen) setResolving(false);
      });
  }, [addGroundingRef, detail, newTitle, workbenchId]);

  useEffect(() => {
    if (detail && configOpen === null && !configAutoExpanded.current) {
      configAutoExpanded.current = true;
      setConfigOpen(!detail.recipe_id);
    }
  }, [detail, configOpen]);

  /* ── WebSocket subscription for live run feedback ─────────────── */
  /* HS-132-03: these five subscriptions had no emitter — the conductor's
     broadcast seam was wired to the hub and never called, so a running
     workbench never moved until a reload. WorkbenchRunner now emits at the
     real transitions (holdspeak/workbench_conductor.py emit_* helpers); the
     payload contract is {workbench_id, run_id, item_id, index, total} with
     item_count on run_start. */

  const bus = useRuntimeBus();

  /* ── the engine this workbench runs on ─────────────────────────── */
  /* Run is not offered when no engine is assigned (A.11). The fact is the
     hub's own: the detail's `assignment_summary` is resolved for THIS
     workbench with the runner's precedence (subject, capability, group,
     global; `WorkbenchService._wb_payload` -> `resolve_effective`). A detail
     without the summary is UNKNOWN: Run stays live and the hub's named
     refusal decides. A named refusal stands until the assignment changes. */
  const [hubRefusedNoEngine, setHubRefusedNoEngine] = useState(false);
  const summary = detail?.assignment_summary;
  const summaryKey = summary ? JSON.stringify(summary) : "";
  useEffect(() => { setHubRefusedNoEngine(false); }, [summaryKey]);
  const engine: "unknown" | "set" | "none" =
    hubRefusedNoEngine || (summary?.status && summary.status !== "assigned")
      ? "none"
      : summary?.status === "assigned" ? "set" : "unknown";
  const readEngine = useCallback(() => { setHubRefusedNoEngine(false); load(); }, [load]);
  // He comes back from Models, or the desk changed: read again.
  useEffect(() => onReturnToTask(readEngine), [readEngine]);
  useEffect(() => bus.subscribe("desk_changed", () => { load(); }), [bus, load]);
  const chooseEngine = () => {
    rememberTaskFocus();
    openSurfaceOr("configure-runs-on", "/settings", "models");
  };

  useEffect(() => {
    const handleRunFrame = (frame: RuntimeFrame) => {
      const plan = planWorkbenchRunFrame(workbenchId, frame);
      if (!plan) return;
      if (plan.clearRequestTimeout) clearRunTimeout();
      dispatchRun(plan.action);
      if (plan.refresh.detail) load();
      if (plan.refresh.runs) loadRuns();
      if (plan.refresh.memory) loadMemory();
    };
    const unsubs = WORKBENCH_RUN_FRAME_TYPES.map((type) =>
      bus.subscribe(type, handleRunFrame),
    );
    return () => unsubs.forEach((u) => u());
  }, [bus, workbenchId, load, loadRuns, loadMemory, clearRunTimeout]);

  useEffect(() => {
    if (runLifecycle.phase !== "reconciling") return;
    if (detailHook.loading || runsHook.loading || memoryHook.loading) return;
    dispatchRun({ type: "reconciled" });
  }, [
    runLifecycle.phase,
    detailHook.loading,
    runsHook.loading,
    memoryHook.loading,
  ]);

  // Reconnect-safe: detect in-progress run from item states
  useEffect(() => {
    if (!detail) return;
    dispatchRun({
      type: "detail_observed",
      hasClaimedItem: detail.items.some((i) => i.status === "claimed"),
    });
  }, [detail]);

  /* ── mutations ──────────────────────────────────────────────────── */

  const updateField = async (fields: Record<string, unknown>) => {
    const result = await write("SAVE WORKBENCH", () =>
      updateWorkbenchField(workbenchId, fields),
    );
    if (!result.ok) return;
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
    load();
    void useDesk.getState().refresh();
  };

  const updateName = (name: string) => void updateField({ name });
  const updateRecipe = (id: string) => void updateField({ recipe_id: id });
  const updateSchedule = (cron: string | null) =>
    void updateField({
      schedule: cron,
      schedule_enabled: cron !== null,
    });
  const toggleSchedule = (enabled: boolean) =>
    void updateField({ schedule_enabled: enabled });

  /* ── item actions ──────────────────────────────────────────────── */

  /* PHILO-13-02 (A1-F) — Park, never delete (C1-5f–j). One press parks at
     once (no confirm, no countdown): Restore undoes it. The outcome is a
     receipt in the footer's receipt slot; a refusal by the hub stays in the
     write channel with Retry; a run's claim is refused in place. */
  const parkItems = (targets: WorkbenchItem[], verb: string) => {
    const ids = targets.map((item) => item.id);
    if (!ids.length) return Promise.resolve();
    // A new Park of this item supersedes its old refusal (another item's
    // failure stays).
    if (writeFailure && ids.length === 1 && writeFailure.subject === ids[0]) clearWrite();
    return write(
      verb,
      async () => {
        try {
          if (ids.length === 1) await parkWorkbenchItem(workbenchId, ids[0]);
          else await parkWorkbenchItems(workbenchId, ids);
        } catch (cause) {
          if (cause instanceof ApiError && cause.status === 409) {
            setParkOutcome(notParkedOutcome("CLAIMED BY A RUN"));
            load();
            return;
          }
          throw cause;
        }
        const at = parkClock();
        for (const id of ids) parkTimes.current.set(id, at);
        setParkOutcome(parkedOutcome(ids, at));
        setParkedOn(false);
        load();
        void loadParked();
      },
      { subject: ids.length === 1 ? ids[0] : undefined },
    ).then(() => undefined);
  };
  const handleRemove = (item: WorkbenchItem) => void parkItems([item], "PARK ITEM");
  const restoreParked = async (ids: string[]) => {
    try {
      await restoreWorkbenchItems(workbenchId, ids);
      for (const id of ids) parkTimes.current.delete(id);
      setParkOutcome(restoredOutcome(ids));
      setParkedOn(false);
      setRestoredId(ids[0] ?? null);
      load();
      void loadParked();
    } catch {
      setParkOutcome(restoreFailedOutcome(ids));
    }
  };

  const addItem = async () => {
    generationRef.current++;
    setResolverError(null);
    setResolving(false);
    const title = newTitle.trim();
    if (!title) return;
    // Derive a short title (first 64 chars at word boundary) from the full instruction.
    const shortTitle = title.length <= 64
      ? title
      : title.slice(0, 64).replace(/\s+\S*$/, "") || title.slice(0, 64);
    const payload: Record<string, unknown> = {
      title: shortTitle,
      body: title,
      priority: newPriority,
    };
    // Build grounding from both legacy selection and @-ref tray.
    const legacyGround = !groundingIsEmpty(grounding) ? hubGrounding(grounding) : null;
    if (legacyGround || groundingRefs.length > 0) {
      const g: Record<string, unknown> = legacyGround ? { ...legacyGround } : {};
      if (groundingRefs.length > 0) {
        const existingRefs = (g.refs as string[]) || [];
        g.refs = [...existingRefs, ...groundingRefs.map((r) => r.ref)];
      }
      payload.grounding = g;
    }
    // The inlet keeps the typed instruction until the hub takes it, so a
    // refused add can be re-issued by RETRY (which replays this whole body).
    await write("ADD ITEM", async () => {
      await addWorkbenchItem(workbenchId, payload);
      setNewTitle("");
      setResolverError(null);
      setNewBody("");
      setNewPriority(3);
      setGrounding(emptyGrounding());
      setGroundingRefs([]);
      setCursorPos(0);
      typedAtPosRef.current = null;
      load();
    });
  };

  const triggerRun = async () => {
    clearRunTimeout();
    const pendingCount = detail?.items.filter((i) => i.status === "pending").length || 0;
    dispatchRun({ type: "start_requested", total: pendingCount });
    const timeout = window.setTimeout(() => {
      if (runTimeoutRef.current !== timeout) return;
      runTimeoutRef.current = null;
      dispatchRun({ type: "request_timed_out" });
    }, 60_000);
    runTimeoutRef.current = timeout;
    // The named refusal is handled INSIDE the write, so the receipt's Retry
    // (which replays only this callback) handles it on every attempt. The
    // hub named the state: the face shows NO ENGINE and its door, never
    // "RUN FAILED · HTTP 409".
    const result = await write("RUN", async () => {
      try {
        await triggerWorkbenchRun(workbenchId);
        return "started" as const;
      } catch (cause) {
        if (!isNoEngineRefusal(cause)) throw cause;
        clearRunTimeout();
        setHubRefusedNoEngine(true);
        dispatchRun({ type: "request_refused", reason: "NO ENGINE" });
        return "no_engine" as const;
      }
    });
    if (result.ok && result.value === "no_engine") return;
    if (result.ok) {
      clearRunTimeout();
      dispatchRun({ type: "request_succeeded" });
      load();
      loadRuns();
      return;
    }
    clearRunTimeout();
    dispatchRun(workbenchRunRequestFailure(result.reason));
  };

  /* ── voice command handler ─────────────────────────────────────── */

  const handleVoiceProposal = async (proposal: VoiceProposal) => {
    const p = proposal.params as Record<string, unknown>;
    switch (proposal.intentId) {
      case "add-item": {
        const title = String(p.title || "").trim();
        if (!title) return;
        await write("ADD ITEM", async () => {
          await addWorkbenchItem(workbenchId, { title, priority: p.priority || 3 });
          load();
        });
        break;
      }
      case "run":
        void triggerRun();
        break;
      case "clear-done": {
        const doneItems = (detail?.items || []).filter(
          (i) => i.status === "done" || i.status === "dismissed",
        );
        if (!doneItems.length) break;
        // PHILO-13-02: bulk park, one PARKED n receipt (C1-5j).
        await parkItems(doneItems, "CLEAR DONE");
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
      case "set-agent": {
        // HS-130-09 — the same assignment the config UI performs
        // (updateRecipe → updateField({ recipe_id })). Resolve the spoken
        // name against the loaded recipes; exact match wins, else a
        // case-insensitive substring.
        const q = String(p.agentName || "").trim().toLowerCase();
        if (!q) break;
        const match =
          recipes.find((r) => String(r.name || "").toLowerCase() === q) ||
          recipes.find((r) => String(r.name || "").toLowerCase().includes(q));
        if (match) void updateField({ recipe_id: match.id });
        break;
      }
      case "dismiss": {
        // HS-130-09 — dismiss the workbench item whose title matches the
        // spoken query (the same status the item card's Dismiss verb sets).
        const q = String(p.query || "").trim().toLowerCase();
        if (!q) break;
        const item =
          (detail?.items || []).find(
            (i) => String(i.title || "").toLowerCase() === q,
          ) ||
          (detail?.items || []).find((i) =>
            String(i.title || "").toLowerCase().includes(q),
          );
        if (item) {
          await write("DISMISS ITEM", async () => {
            await updateWorkbenchItem(workbenchId, item.id, {
              status: "dismissed",
            });
            load();
          });
        }
        break;
      }
    }
    setVoiceProposal(null);
  };

  /* ── drop-to-work handler ─────────────────────────────────────── */

  /** Name the outcome BEFORE the release, from the payload types alone. */
  const armDrop = (e: React.DragEvent) => {
    setDropHover(true);
    setDropIntent(workbenchDropVerb(dropTypes(e.dataTransfer)));
  };

  const handleDrop = async (e: React.DragEvent) => {
    const intent = workbenchDropVerb(dropTypes(e.dataTransfer));
    setDropHover(false);
    setDropIntent(null);
    // A file is the desk's payload, not the workbench's: it rides through
    // to the glass layer that imports it as a Meeting. Claiming it here
    // (preventDefault) would swallow the drop.
    if (intent.verb === "IMPORT AS MEETING") return;
    e.preventDefault();
    const text = e.dataTransfer.getData("application/x-desk-item");
    if (!text) {
      // The refusal the overlay already promised, spoken once more on release.
      failWrite("DROP TO WORK", intent.accepted ? "EMPTY PAYLOAD" : intent.verb);
      return;
    }
    let dropped: Array<{ kind: string; id: string; title: string; body?: string }>;
    try {
      dropped = JSON.parse(text);
    } catch {
      // Not a write failure — the payload never got that far. Named, not silent.
      failWrite("DROP TO WORK", "BAD PAYLOAD");
      return;
    }
    await write("DROP TO WORK", async () => {
      for (const item of dropped) {
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
        await addWorkbenchItem(workbenchId, payload);
      }
      load();
    });
  };

  /* ── render ─────────────────────────────────────────────────────── */

  if (!wb) return null;
  const name = String(wb.name || "Workbench");
  const items = detail?.items || [];
  const doneCount = items.filter((i) => i.status === "done" || i.status === "dismissed").length;
  const lastRun = detail?.last_run;
  const isConfigured = !!detail?.recipe_id;
  const showConfig = configOpen ?? !isConfigured;
  const boundSkillCount = detail?.recipe_id
    ? skills.filter((s) => s.recipe_ids.includes(detail.recipe_id!)).length
    : 0;
  const startSummary = resourcefulPolicy?.enabled
    ? `Resourceful · ${resourcefulPolicy.nightly_target}/night · ${resourcefulPolicy.cooldown_hours}h`
    : automations.length
      ? `${automations[0].name}${automations.length > 1 ? ` +${automations.length - 1}` : ""}`
      : null;

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

  // HS-132-07 / HS-135-15 — the ghosted grammar: RUN names what is
  // missing as a visible reason label, not just a tooltip.
  const runDisabledReason = running
    ? "Run in progress"
    : !detail
      ? "Workbench still loading"
      : !detail.recipe_id
        ? "Bind an agent first"
        : engine === "none"
          ? "No engine"
          : null;

  return (
    <DeskWindowFrame
      id={`workbench:${workbenchId}`}
      glyph="◉"
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
        <Button
          variant="chrome"
          className="desk-chip"
          data-tone={running ? "warn" : undefined}
          disabled={!!runDisabledReason}
          onClick={() => void triggerRun()}
          title={runDisabledReason ?? "Run this workbench now"}
          aria-label={
            runDisabledReason
              ? `Run: ${runDisabledReason}`
              : "Run this workbench now"
          }
        >
          {runButtonLabel}
          {runDisabledReason && !running ? (
            <small className="quiet"> · {runDisabledReason}</small>
          ) : null}
        </Button>
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
        onDragOver={(e) => { e.preventDefault(); armDrop(e); }}
        onDragEnter={(e) => { e.preventDefault(); armDrop(e); }}
        onDragLeave={() => { setDropHover(false); setDropIntent(null); }}
        onDrop={handleDrop}
      >
        {dropHover && dropIntent ? (
          <div className="wb-drop-zone">
            <span
              className="desk-chip"
              data-tone={dropIntent.accepted ? undefined : "warn"}
            >
              {dropIntentLabel(dropIntent)}
            </span>
          </div>
        ) : null}
        {error ? <SurfaceState error={error} onRetry={() => void load()} /> : null}

        {/* ── quiet run state ─────────────────────────────────────── */}
        {running ? <SurfaceState loading /> : null}

        {/* ── config strip / panel ────────────────────────────────── */}
        {detail && !showConfig ? (
          <ConfigStrip
            recipe={recipe}
            schedule={detail.schedule}
            scheduleEnabled={detail.schedule_enabled}
            startSummary={startSummary}
            skillCount={boundSkillCount}
            onClick={() => setConfigOpen(true)}
          />
        ) : null}

        {detail && showConfig ? (
          <ConfigPanel
            onEngineChanged={readEngine}
            detail={detail}
            recipes={recipes}
            skills={skills}
            onUpdateRecipe={updateRecipe}
            onUpdateSchedule={updateSchedule}
            onToggleSchedule={toggleSchedule}
            workbenchId={workbenchId}
            write={write}
            automations={automations}
            resourcefulPolicy={resourcefulPolicy}
            onAutomationsChanged={loadAutomations}
            onResourcefulChanged={loadResourceful}
            onCollapse={() => setConfigOpen(false)}
          />
        ) : null}

        {/* ── items wing ─────────────────────────────────────────── */}
        {activeWing === "items" ? (
          <>
            <div className="wb-items">
              {/* HS-130-09 — the template picker is a PRE-persistence chooser
                 (NewWorkbenchChooser); a persisted blank Workbench shows the
                 empty state, never another picker (which would create yet
                 another record). */}
              {items.length === 0 && !error ? (
                <SurfaceState
                  empty
                  emptyLabel="No items yet"
                  emptyGlyph="○"
                  actionLabel="Add an item"
                  onAction={() => inletInputRef.current?.focus()}
                />
              ) : null}

              <ParkedStrip
                rows={parked}
                on={parkedOn}
                onToggle={setParkedOn}
                onRestore={(ids) => void restoreParked(ids)}
                data-testid="wb-parked"
              />
              {(parkedOn ? [] : items).map((item) => (
                <WorkbenchItemCard
                  key={item.id}
                  restored={restoredId === item.id}
                  item={item}
                  expanded={expanded === item.id}
                  recipeId={detail?.recipe_id || null}
                  workbenchId={workbenchId}
                  workbenchName={name}
                  onToggle={() =>
                    setExpanded(expanded === item.id ? null : item.id)
                  }
                  onReload={load}
                  onRemove={handleRemove}
                  onCopy={(text) => void copy(text)}
                  write={write}
                />
              ))}
            </div>

            {/* PHILO-13-02: the voice intent "Clear done", also a visible
                verb while done items exist; it parks them all (C1-5j). */}
            {doneCount > 0 && !parkedOn ? (
              <div className="wb-clear-done">
                <Button
                  dense
                  variant="ghost"
                  onClick={() =>
                    void parkItems(
                      items.filter((i) => i.status === "done" || i.status === "dismissed"),
                      "CLEAR DONE",
                    )
                  }
                >
                  Clear done
                </Button>
              </div>
            ) : null}
            {/* ── voice proposal strip ───────────────────────────────── */}
            {voiceProposal ? (
              <div className="wb-proposal-strip">
                <span className="wb-proposal-text">
                  {voiceProposal.intentId === "add-item"
                    ? `Add: "${(voiceProposal.params as Record<string, unknown>).title}" P${(voiceProposal.params as Record<string, unknown>).priority || 3}`
                    : voiceProposal.intentId === "run"
                      ? "Run this workbench"
                      : voiceProposal.intentId === "clear-done"
                        ? "Clear done items"
                        : voiceProposal.intentId === "set-agent"
                          ? `Set agent: ${(voiceProposal.params as Record<string, unknown>).agentName}`
                          : voiceProposal.intentId === "dismiss"
                            ? `Dismiss: ${(voiceProposal.params as Record<string, unknown>).query}`
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

            {/* ── inlet (HS-118-03/04) ─────────────────────────────── */}
            <div className="wb-inlet">
              {/* grounding tray */}
              {groundingRefs.length > 0 ? (
                <div className="wb-inlet-tray">
                  {groundingRefs.map((r) => (
                    <span key={r.ref} className="desk-chip quiet">
                      {r.name}
                      <button
                        type="button"
                        className="wb-inlet-chip-remove"
                        onClick={() => removeGroundingRef(r.ref)}
                        aria-label={`Remove ${r.name}`}
                      >
                        &times;
                      </button>
                    </span>
                  ))}
                </div>
              ) : null}
              {/* resolver state (HS-118-05) */}
              {resolving ? <SurfaceState loading /> : null}
              {resolverError ? (
                <SurfaceState
                  error={
                    resolverError === "resolver_timeout"
                      ? "RESOLVER TIMEOUT"
                      : resolverError === "resolver_unavailable"
                        ? "RESOLVER UNAVAILABLE"
                        : resolverError === "resolver_not_configured"
                          ? "RESOLVER NOT CONFIGURED"
                          : "RESOLVER ERROR"
                  }
                  onRetry={() => void resolveInletReferences()}
                />
              ) : null}
              {/* autocomplete popover */}
              {acOpen ? (
                <InletAutocomplete
                  zones={zones}
                  matches={acMatches}
                  selectedIndex={clampedAcIndex}
                  onSelect={selectAutocompleteZone}
                  onSelectedIndexChange={setAcSelectedIndex}
                />
              ) : null}
              <div className="wb-inlet-row">
                <MicButton
                  draftScope={`workbench:${workbenchId}`}
                  grammar={workbenchVoiceGrammar}
                  onText={(t) => {
                    // Insert transcript IMMEDIATELY — before any async work
                    setNewTitle((v) => (v ? v + " " + t : t));

                    // Fast path: immediate client-side resolution
                    const fastZones = useDesk.getState().items.directory || [];
                    const { refs: fastRefs } = resolveDrawerNames(t, fastZones);
                    fastRefs.forEach((r) => addGroundingRef(r));

                    // Smart path: fire-and-forget (if configured).
                    if (detail) void resolveInletReferences(t);
                  }}
                  onProposalConfirm={(p) => setVoiceProposal(p)}
                  onState={handleMicState}
                />
                {/* UX-CANON: needs redesign (HS-170-04) — combobox inlet with autocomplete can't use StringGadget */}
                <input
                  ref={inletInputRef}
                  type="text"
                  className="wb-inlet-input"
                  placeholder="What needs doing?"
                  role="combobox"
                  aria-expanded={acOpen}
                  aria-controls="wb-inlet-listbox"
                  aria-activedescendant={acActiveId}
                  value={newTitle}
                  onChange={(e) => {
                    setNewTitle(e.target.value);
                    setCursorPos(e.target.selectionStart ?? e.target.value.length);
                    setAcDismissed(false);
                  }}
                  onPaste={() => {
                    typedAtPosRef.current = null;
                  }}
                  onSelect={(e) => {
                    setCursorPos((e.target as HTMLInputElement).selectionStart ?? cursorPos);
                  }}
                  onKeyDown={(e) => {
                    // Fix #2: detect typed @ (fires before insertion).
                    if (e.key === "@" && !e.ctrlKey && !e.metaKey && !e.altKey) {
                      typedAtPosRef.current = (e.target as HTMLInputElement).selectionStart ?? 0;
                    }
                    if (acOpen) {
                      if (e.key === "ArrowDown") {
                        e.preventDefault();
                        setAcSelectedIndex(Math.min(clampedAcIndex + 1, acMatches.length - 1));
                        return;
                      }
                      if (e.key === "ArrowUp") {
                        e.preventDefault();
                        setAcSelectedIndex(Math.max(clampedAcIndex - 1, 0));
                        return;
                      }
                      if (e.key === "Enter") {
                        if (acMatches.length > 0) {
                          e.preventDefault();
                          selectAutocompleteZone(acMatches[clampedAcIndex]);
                          return;
                        }
                      }
                      // Fix #4: Shift+Tab should not select.
                      if (e.key === "Tab" && !e.shiftKey) {
                        if (acMatches.length > 0) {
                          e.preventDefault();
                          selectAutocompleteZone(acMatches[clampedAcIndex]);
                          return;
                        }
                      }
                      if (e.key === "Escape") {
                        e.preventDefault();
                        setAcDismissed(true);
                        typedAtPosRef.current = null;
                        return;
                      }
                      if (e.key === " " && acMatches.length === 0) {
                        // Space with no matches closes popover.
                        setAcDismissed(true);
                        typedAtPosRef.current = null;
                        return;
                      }
                      if (e.key === "Backspace") {
                        // Check if backspacing past @ would close.
                        const sel = (e.target as HTMLInputElement).selectionStart ?? 0;
                        if (sel <= atPos + 1) {
                          setAcDismissed(true);
                          typedAtPosRef.current = null;
                        }
                      }
                    }
                    if (!acOpen && e.key === "Enter") void addItem();
                  }}
                  aria-label="New item instruction"
                />
                <Button
                  variant="chrome"
                  className="desk-chip wb-priority-cycle"
                  data-priority={newPriority}
                  onClick={() => setNewPriority((p) => (p >= 3 ? 1 : p + 1))}
                  title={`Priority ${newPriority}. Click to cycle`}
                >
                  P{newPriority}
                </Button>
                <Button
                  variant="chrome"
                  className="desk-chip is-primary"
                  disabled={!newTitle.trim()}
                  title={
                    newTitle.trim() ? "Add this item" : "No instruction typed"
                  }
                  onClick={() => void addItem()}
                >
                  Add
                </Button>
              </div>
            </div>
          </>
        ) : null}

        {/* ── runs wing ────────────────────────────────────────────── */}
        {activeWing === "runs" ? (
          <WorkbenchRunsWing
            runs={runs}
            configured={isConfigured}
            running={running}
            openRunId={openRunId}
            onToggleRun={(runId) =>
              setOpenRunId(openRunId === runId ? null : runId)
            }
            onRun={() => void triggerRun()}
            onBindAgent={() => setConfigOpen(true)}
          />
        ) : null}

        {/* ── memory wing ──────────────────────────────────────────── */}
        {activeWing === "memory" ? (
          <div className="wb-memory-wing">
            <SurfaceLedger
              count={countLabel("MEMORIES", memoryEntries.length)}
              controls={
                memoryEntries.length > 0 ? (
                  <ConfirmVerb
                    label="Clear"
                    confirmLabel="Clear all?"
                    onConfirm={async () => {
                      await write("CLEAR MEMORY", async () => {
                        await clearWorkbenchMemory(workbenchId);
                        loadMemory();
                      });
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
                        <span className="desk-chip wb-badge-compact">
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
                      {(() => { const itemTitle = entry.item_title; return itemTitle ? (
                        <span className="wb-memory-source">from: {itemTitle}</span>
                      ) : null; })()}
                      <div className="wb-memory-verbs">
                        <button
                          type="button"
                          className="desk-chip"
                          onClick={async () => {
                            await write("PROMOTE TO SKILL", async () => {
                              await promoteMemoryToSkill(workbenchId, i);
                              loadSkills();
                            });
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

      <SurfaceFooter
        // The repair door sits in the footer's verb slot, so no receipt
        // (a failed write, a Park outcome, a copy) can cover it.
        verbs={engine === "none" ? (
          <span data-testid="wb-no-engine">
            <Button dense variant="ghost" onClick={chooseEngine}>
              Choose an engine
            </Button>
          </span>
        ) : undefined}
        receipt={
          // HS-132-06: a refused write outranks the quieter receipts; then
          // PHILO-13-02's park outcome (PARKED + Restore, RESTORED, refusals).
          writeReceipt ||
          (parkOutcome ? (
            <ParkReceipt
              outcome={parkOutcome}
              onRestore={(ids) => void restoreParked(ids)}
              data-testid="wb-park-receipt"
            />
          ) : null) ||
          copyReceipt || (engine === "none" ? (
            <span className="wb-footer-status">
              <LampGadget label="No engine" on tone="warn" />
            </span>
          ) : null) || (
            <span className="wb-footer-status">
              {countToken(items.length, "ITEM") ?? "No items"}
              {lastRun
                ? ` · last run ${humanTime(lastRun.completed_at || lastRun.started_at)}`
                : ""}
              {lastRun?.total_tokens
                ? ` · ${lastRun.total_tokens.toLocaleString()} tok`
                : ""}
              {saved ? <LampGadget label="Saved" on tone="ok" /> : null}
            </span>
          )
        }
      />
    </DeskWindowFrame>
  );
}
