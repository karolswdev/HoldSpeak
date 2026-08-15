import "./workbench-config.css";
import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { spriteUrl } from "../sprites";
import { useDesk } from "../store";
import type {
  WorkbenchDetail,
  WorkbenchItem,
  Skill,
} from "../detail-types";
import {
  fetchWorkbenchDetail,
  fetchWorkbenchRuns,
  fetchWorkbenchMemory,
  fetchSkills,
  updateWorkbenchField,
  addWorkbenchItem,
  updateWorkbenchItem,
  deleteWorkbenchItem,
  triggerWorkbenchRun,
  updateSkill,
  clearWorkbenchMemory,
  promoteMemoryToSkill,
  retryMint,
} from "../api";
import { usePrimitiveDetail } from "../hooks/usePrimitiveDetail";
import { useUndoReceipt } from "../hooks/useUndoReceipt";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { useWriteReceipt, type WriteAttempt } from "../hooks/useWriteReceipt";
import { boundaryEgressLamp } from "../inferenceEgress";
import { keepReply } from "../chat";
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
import { RunsOnPicker } from "./RunsOnPicker";
import { displayTargetToken, isInheritedTarget } from "./workbenchTarget";
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
      <span className="wb-config-strip-chevron" aria-hidden="true">▾</span>
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
  onUpdateResolverProfile,
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
  onUpdateResolverProfile: (id: string | null) => void;
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
      {/* HS-130-09 — the display token equals the stored token. An unset
         target reads as an explicit inherited default (never a fabricated
         "this_machine"); the effective target is resolved server-side
         (HS-130-01). */}
      <SurfaceSection label="RUNS ON">
        <div className="wb-config-runs-on">
          {isInheritedTarget(detail.profile_id) ? (
            <span className="desk-chip" data-tone="quiet">
              DEFAULT · INHERITED
            </span>
          ) : null}
          <RunsOnPicker
            targets={inferenceTargets}
            selectedId={displayTargetToken(detail.profile_id)}
            onChange={onUpdateTarget}
          />
          {!isInheritedTarget(detail.profile_id) ? (
            <LampGadget
              label={lamp.label}
              on={lamp.tone !== "fail"}
              tone={lamp.tone as "ok" | "warn" | "fail"}
            />
          ) : null}
        </div>
      </SurfaceSection>

      {/* ── resolves with (HS-118-05) ──────────────────────────────── */}
      <SurfaceSection label="RESOLVES WITH">
        <div className="wb-config-runs-on">
          <RunsOnPicker
            targets={inferenceTargets}
            selectedId={detail.resolver_profile_id || ""}
            onChange={(id) => onUpdateResolverProfile(id || null)}
          />
          {detail.resolver_profile_id ? (() => {
            const rt = inferenceTargets.find(
              (t: any) => t.profile_id === detail.resolver_profile_id || t.id === detail.resolver_profile_id
            );
            const rl = rt ? boundaryEgressLamp(rt.boundary) : null;
            return rl ? (
              <LampGadget
                label={rl.label}
                on={rl.tone !== "fail"}
                tone={rl.tone as "ok" | "warn" | "fail"}
              />
            ) : null;
          })() : null}
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
  onRemove,
  onCopy,
  write,
}: {
  item: WorkbenchItem;
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

  const hasMintedArtifact = !!item.result_artifact_id;
  // Issue 4 fix: use mint_attempted to distinguish "mint failed" from "legacy pre-mint item"
  const mintFailed = item.status === "done" && !!item.result && !hasMintedArtifact && !!item.mint_attempted;
  const legacyKeep = item.status === "done" && !!item.result && !hasMintedArtifact && !item.mint_attempted;

  return (
    <div className="wb-card" data-status={item.status}>
      {/* ── head line ──────────────────────────────────────────── */}
      <button
        type="button"
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
      </button>
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
                    <span className="wb-card-artifact-detail-id">{item.result_artifact_id}</span>
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
                onClick={() => onRemove(item)}
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

  /* ── data loading (usePrimitiveDetail) ──────────────────────────── */

  const detailHook = usePrimitiveDetail("workbench", workbenchId, fetchWorkbenchDetail);
  const runsHook = usePrimitiveDetail("workbench-runs", workbenchId, fetchWorkbenchRuns);
  const memoryHook = usePrimitiveDetail("workbench-memory", workbenchId, fetchWorkbenchMemory);
  const skillsHook = usePrimitiveDetail<Skill[]>("skills", workbenchId, fetchSkills);

  const detail = detailHook.data;
  const runs = runsHook.data ?? [];
  const memoryEntries = memoryHook.data ?? [];
  const skills = skillsHook.data ?? [];
  const error = detailHook.error ?? "";

  // Convenience aliases for the old load/loadX callbacks used by WS handlers and mutations.
  const load = detailHook.refresh;
  const loadRuns = runsHook.refresh;
  const loadMemory = memoryHook.refresh;
  const loadSkills = skillsHook.refresh;
  const { remove, receipt: undoReceipt } = useUndoReceipt();
  const { copy, receipt: copyReceipt } = useCopyReceipt();
  // HS-132-06 — every write verb in this window reports here; the receipt
  // seats in the footer's receipt slot, never over the work.
  const {
    attempt: write,
    fail: failWrite,
    receipt: writeReceipt,
  } = useWriteReceipt();

  const [expanded, setExpanded] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [configOpen, setConfigOpen] = useState<boolean | null>(null);
  const [newTitle, setNewTitle] = useState("");
  const [newBody, setNewBody] = useState("");
  const [newPriority, setNewPriority] = useState(3);
  const [grounding, setGrounding] = useState<GroundingSelection>(emptyGrounding);
  const [groundingRefs, setGroundingRefs] = useState<ResolvedRef[]>([]);
  const [running, setRunning] = useState(false);
  const [runProgress, setRunProgress] = useState<{ index: number; total: number } | null>(null);
  const [activeWing, setActiveWing] = useState("items");
  const [openRunId, setOpenRunId] = useState<string | null>(null);
  const [voiceProposal, setVoiceProposal] = useState<VoiceProposal | null>(null);
  const [dropHover, setDropHover] = useState(false);
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
  const target = inferenceTargets.find(
    (t) => t.id === (detail?.profile_id || wb?.profileId),
  );
  const lamp = boundaryEgressLamp(target?.boundary);

  const resolverProfileId = detail?.resolver_profile_id || null;
  const resolverTarget = resolverProfileId
    ? inferenceTargets.find((t: any) => t.profile_id === resolverProfileId || t.id === resolverProfileId)
    : null;
  const resolverLamp = resolverTarget ? boundaryEgressLamp(resolverTarget.boundary) : null;

  const resolveInletReferences = useCallback((text = newTitle) => {
    if (!resolverProfileId || !detail || !text.trim()) return;
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
  }, [addGroundingRef, detail, newTitle, resolverProfileId, workbenchId]);

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
        clearRunTimeout();
        setRunning(false);
        setRunProgress(null);
        void load();
        void loadRuns();
        void loadMemory();
      }),
    ];
    return () => unsubs.forEach((u) => u());
  }, [bus, workbenchId, load, loadRuns, loadMemory, clearRunTimeout]);

  // Reconnect-safe: detect in-progress run from item states
  useEffect(() => {
    if (!detail) return;
    const hasClaimed = detail.items.some((i) => i.status === "claimed");
    if (hasClaimed && !running) setRunning(true);
    if (!hasClaimed && running && !runProgress) setRunning(false);
  }, [detail, running, runProgress]);

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
  const updateTarget = (id: string) => void updateField({ profile_id: id });
  const updateResolverProfile = (id: string | null) => {
    generationRef.current++;
    setResolving(false);
    setResolverError(null);
    void updateField({ resolver_profile_id: id });
  };
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
    const result = await write("BIND SKILL", () =>
      updateSkill(skillId, { recipe_ids: recipeIds, ...extraFields }),
    );
    if (result.ok) loadSkills();
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
    const result = await write("APPROVE SKILL", () =>
      updateSkill(skillId, { status: "active" }),
    );
    if (result.ok) loadSkills();
  };

  const dismissSkill = async (skillId: string) => {
    const result = await write("DISMISS SKILL", () =>
      updateSkill(skillId, { status: "dismissed" }),
    );
    if (result.ok) loadSkills();
  };

  /* ── item actions ──────────────────────────────────────────────── */

  const handleRemove = (item: WorkbenchItem) => {
    remove(
      item.title,
      () =>
        void write("REMOVE ITEM", async () => {
          await deleteWorkbenchItem(workbenchId, item.id);
          load();
        }),
      () => load(),
    );
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
    setRunning(true);
    const pendingCount = detail?.items.filter((i) => i.status === "pending").length || 0;
    setRunProgress({ index: 0, total: pendingCount });
    const timeout = window.setTimeout(() => {
      if (runTimeoutRef.current !== timeout) return;
      runTimeoutRef.current = null;
      setRunning(false);
      setRunProgress(null);
    }, 60_000);
    runTimeoutRef.current = timeout;
    const result = await write("RUN", () => triggerWorkbenchRun(workbenchId));
    if (result.ok) {
      load();
      loadRuns();
      return;
    }
    clearRunTimeout();
    setRunning(false);
    setRunProgress(null);
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
        remove(
          `${doneItems.length} done items`,
          () =>
            void write("CLEAR DONE", async () => {
              for (const item of doneItems) {
                await deleteWorkbenchItem(workbenchId, item.id);
              }
              load();
            }),
          () => load(),
        );
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

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDropHover(false);
    const text = e.dataTransfer.getData("application/x-desk-item");
    if (!text) return;
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
          <div className="wb-drop-zone">
            <span className="desk-chip">DROP TARGET · ADD ITEM</span>
          </div>
        ) : null}
        {error ? <SurfaceState error={error} onRetry={() => void load()} /> : null}

        {/* ── quiet run state ─────────────────────────────────────── */}
        {running ? <SurfaceState loading /> : null}

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
            onUpdateResolverProfile={updateResolverProfile}
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
                  onRemove={handleRemove}
                  onCopy={(text) => void copy(text)}
                  write={write}
                />
              ))}
            </div>

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
              {/* pre-call egress disclosure (HS-118-05) */}
              {resolverLamp ? (
                <div className="wb-inlet-egress">
                  <EgressChip
                    label={`RESOLVER ${resolverLamp.label}`}
                    scope={resolverLamp.tone === "ok" ? "local" : resolverLamp.tone === "fail" ? "cloud" : "mixed"}
                  />
                </div>
              ) : null}
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
                    if (resolverProfileId && detail) void resolveInletReferences(t);
                  }}
                  onProposalConfirm={(p) => setVoiceProposal(p)}
                  onState={handleMicState}
                />
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
                <button
                  type="button"
                  className="desk-chip wb-priority-cycle"
                  data-priority={newPriority}
                  onClick={() => setNewPriority((p) => (p >= 3 ? 1 : p + 1))}
                  title={`Priority ${newPriority}. Click to cycle`}
                >
                  P{newPriority}
                </button>
                <TransportKey
                  compact
                  label="GO"
                  glyph=">"
                  disabled={!newTitle.trim()}
                  onClick={() => void addItem()}
                />
              </div>
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
                <SurfaceState
                  empty
                  emptyLabel="No runs yet"
                  emptyGlyph="○"
                  actionLabel="Run now"
                  onAction={detail?.recipe_id && !running ? () => void triggerRun() : undefined}
                />
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
                      {entry.item_title ? (
                        <span className="wb-memory-source">from: {entry.item_title}</span>
                      ) : null}
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
        receipt={
          // HS-132-06 — a refused write outranks the quieter receipts.
          writeReceipt ||
          undoReceipt ||
          copyReceipt || (
            <span className="wb-footer-status">
              {items.length} {items.length === 1 ? "item" : "items"}
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
