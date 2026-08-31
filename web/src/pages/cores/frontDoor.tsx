/**
 * HS-156-04 — The door surface: pack cards, the health strip, the advanced fold.
 *
 * Settings → Models opens on the DOOR when anything is unconfigured:
 * three pack cards + "set up my own" (jumps to the advanced layer).
 * After setup, the door collapses to a one-line health strip above
 * the advanced view.
 *
 * Council law: the cards ARE ChoiceCardGroup, the plan IS ProgressPlan,
 * the strip IS ActionNotice, the fold IS Disclosure. Zero new one-off
 * furniture — the ratchet fence enforces it.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import {
  ActionNotice,
  ChoiceCardGroup,
  ChoiceCard,
  Disclosure,
  ProgressPlan,
  type PlanStep,
  SurfaceState,
} from "../../desk/surface";
import {
  getAssignmentSummary,
  type AssignmentSummary,
  type AssignmentSummaryRow,
} from "./assignmentExperience";
import { ModelLibraryCore } from "./ModelLibraryCore";
import { CapabilityAssignmentsCore } from "./CapabilityAssignmentsCore";
import "./frontDoor.css";

// ── Types ────────────────────────────────────────────────────────────────

type PackDisplayLine = {
  group_id?: string;
  group_label?: string;
  source_label?: string;
  provenance?: string | null;
  job?: string;
  label?: string;
  source?: string;
};

type FrontDoorPack = {
  id: string;
  label: string;
  summary: string;
  recommended: boolean;
  display_lines: PackDisplayLine[];
  plan: unknown[];
  total_download_bytes: number;
};

type Recommendation = {
  packs: FrontDoorPack[];
  facts: Record<string, unknown>;
};

type PlanItem = {
  ordinal: number;
  entry: {
    kind: string;
    group_id?: string;
    preset_id?: string;
    [key: string]: unknown;
  };
  status: "queued" | "running" | "done" | "failed";
  receipt: unknown;
  error: string | null;
};

type ApplyPlan = {
  id: string;
  pack_id: string;
  status: "running" | "done" | "failed";
  items: PlanItem[];
  created_at: string;
  updated_at: string;
};

// ── Helpers ──────────────────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(0)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function lineLabel(line: PackDisplayLine): string {
  return line.group_label ?? line.label ?? line.job ?? "Unknown";
}

function lineValue(line: PackDisplayLine): string {
  return line.source_label ?? line.source ?? "";
}

/** HS-156-05: produce a sentence from an attention row, never echoing the action verb. */
function repairCopy(row: AssignmentSummaryRow): string {
  const { label, repair } = row;
  if (!repair) return `${label} needs attention`;
  // Short action verbs ("Fix", "Add") are not descriptive — convert to sentence
  const trimmed = repair.trim();
  if (/^[A-Z]\w{0,5}$/.test(trimmed)) {
    return `${label} needs attention`;
  }
  // Descriptive phrase (e.g. "has no model") — compose as sentence
  return `${label} ${repair}`;
}

function hasUnconfiguredGroups(summary: AssignmentSummary | null): boolean {
  if (!summary) return true;
  // global row is special — check group rows only
  const groupRows = summary.rows.filter((r) => r.id !== "global");
  return groupRows.some((row) => !row.assignment);
}

function firstAttentionRow(summary: AssignmentSummary | null): AssignmentSummaryRow | null {
  if (!summary) return null;
  return summary.rows.find((row) => row.repair != null) ?? null;
}

function planItemToStep(item: PlanItem, pack: FrontDoorPack | null): PlanStep {
  const entry = item.entry;
  let label = "";

  // Match to display_lines by group_id if possible
  if (pack && entry.group_id) {
    const line = pack.display_lines.find(
      (dl) => dl.group_id === entry.group_id,
    );
    if (line) {
      label = `${lineLabel(line)} → ${lineValue(line)}`;
    }
  }
  if (!label && entry.kind === "assignments") {
    label = "Assign models to groups";
  }
  if (!label) {
    label = `${entry.kind} ${entry.group_id ?? ""}`.trim();
  }

  return {
    id: `item-${item.ordinal}`,
    label,
    status: item.status,
    detail: item.error ?? undefined,
  };
}

function findPackById(packs: FrontDoorPack[], id: string): FrontDoorPack | null {
  return packs.find((p) => p.id === id) ?? null;
}

// ── Door view states ─────────────────────────────────────────────────────

type DoorPhase =
  | "loading"
  | "error"
  | "cards"     // unconfigured — show pack cards
  | "applying"  // plan in progress
  | "strip";    // configured — health strip + advanced fold

// ── Component ────────────────────────────────────────────────────────────

export function FrontDoorView({
  onOpenAssignments,
}: {
  onOpenAssignments?: () => void;
}) {
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [plan, setPlan] = useState<ApplyPlan | null>(null);
  const [assignmentSummary, setAssignmentSummary] = useState<AssignmentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [selectedPack, setSelectedPack] = useState<string | null>(null);
  const [applyError, setApplyError] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval>>(undefined);
  const mountedRef = useRef(true);

  useEffect(
    () => () => {
      mountedRef.current = false;
      if (pollRef.current) clearInterval(pollRef.current);
    },
    [],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const [rec, planRes, summary] = await Promise.all([
        apiFetch<Recommendation>("/api/front-door/recommendation"),
        apiFetch<{ plan: ApplyPlan | null }>("/api/front-door/apply"),
        getAssignmentSummary(),
      ]);
      if (!mountedRef.current) return;
      setRecommendation(rec);
      setPlan(planRes.plan);
      setAssignmentSummary(summary);
    } catch (e) {
      if (mountedRef.current) setLoadError(readableError(e));
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // ── Determine the current phase ──
  const phase: DoorPhase = (() => {
    if (loading) return "loading";
    if (loadError) return "error";
    // Active plan takes precedence
    if (plan && (plan.status === "running" || plan.status === "failed")) return "applying";
    // Unconfigured groups → show cards
    if (hasUnconfiguredGroups(assignmentSummary)) return "cards";
    // Everything configured → strip
    return "strip";
  })();

  // ── Polling for plan progress ──
  const startPolling = useCallback(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const result = await apiFetch<{ plan: ApplyPlan | null }>(
          "/api/front-door/apply",
        );
        if (!mountedRef.current) return;
        if (result.plan) {
          setPlan(result.plan);
          if (result.plan.status !== "running") {
            clearInterval(pollRef.current);
            pollRef.current = undefined;
            // Reload assignment summary to detect configured state
            try {
              const summary = await getAssignmentSummary();
              if (mountedRef.current) setAssignmentSummary(summary);
            } catch {
              // best-effort
            }
          }
        }
      } catch {
        // silently retry on next tick
      }
    }, 1500);
  }, []);

  const confirmPack = useCallback(async () => {
    if (!selectedPack) return;
    setApplyError("");
    // Fire the POST — it may block for a while on downloads
    apiFetch<{ plan_id: string; status: string; items: PlanItem[] }>(
      "/api/front-door/apply",
      { method: "POST", json: { pack_id: selectedPack } },
    )
      .then((result) => {
        if (!mountedRef.current) return;
        setPlan({
          id: result.plan_id,
          pack_id: selectedPack,
          status: result.status as ApplyPlan["status"],
          items: result.items,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
        if (result.status !== "running") {
          // Plan already finished (fast items). Reload summary.
          void getAssignmentSummary()
            .then((s) => {
              if (mountedRef.current) setAssignmentSummary(s);
            })
            .catch(() => {});
        }
      })
      .catch((e) => {
        if (mountedRef.current) setApplyError(readableError(e));
      });

    // Optimistic: show plan immediately with queued steps
    const pack = findPackById(recommendation?.packs ?? [], selectedPack);
    if (pack) {
      const optimisticItems: PlanItem[] = pack.plan.map((entry, i) => ({
        ordinal: i,
        entry: entry as PlanItem["entry"],
        status: "queued" as const,
        receipt: null,
        error: null,
      }));
      setPlan({
        id: "pending",
        pack_id: selectedPack,
        status: "running",
        items: optimisticItems,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    }

    startPolling();
  }, [selectedPack, recommendation, startPolling]);

  const resumePlan = useCallback(() => {
    if (!plan) return;
    setApplyError("");
    // Re-apply the same pack to resume from failed items
    apiFetch<{ plan_id: string; status: string; items: PlanItem[] }>(
      "/api/front-door/apply",
      { method: "POST", json: { pack_id: plan.pack_id } },
    )
      .then((result) => {
        if (!mountedRef.current) return;
        setPlan({
          id: result.plan_id,
          pack_id: plan.pack_id,
          status: result.status as ApplyPlan["status"],
          items: result.items,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
      })
      .catch((e) => {
        if (mountedRef.current) setApplyError(readableError(e));
      });
    startPolling();
  }, [plan, startPolling]);

  // ── Resolved pack for display ──
  const activePack = recommendation
    ? findPackById(recommendation.packs, plan?.pack_id ?? selectedPack ?? "")
    : null;

  // ── Attention state ──
  const attentionRow = firstAttentionRow(assignmentSummary);

  // ── Render ─────────────────────────────────────────────────────────────

  if (phase === "loading") return <SurfaceState loading />;
  if (phase === "error")
    return <SurfaceState error={loadError} onRetry={() => void load()} />;

  // ── CARDS: unconfigured ──
  if (phase === "cards") {
    const packs = recommendation?.packs ?? [];
    return (
      <div className="front-door" data-testid="front-door-cards">
        <ChoiceCardGroup
          name="front-door-pack"
          value={selectedPack}
          onChange={setSelectedPack}
          confirmLabel="Set up"
          onConfirm={() => void confirmPack()}
          ariaLabel="Choose a setup pack"
        >
          {packs.map((pack) => (
            <ChoiceCard
              key={pack.id}
              value={pack.id}
              label={pack.label}
              description={pack.summary}
              recommended={pack.recommended}
              name="front-door-pack"
              selectedValue={selectedPack}
              onChange={setSelectedPack}
              facts={pack.display_lines.map((line) => ({
                label: lineLabel(line),
                value: lineValue(line),
              }))}
              cost={
                pack.total_download_bytes > 0
                  ? `${formatBytes(pack.total_download_bytes)} download`
                  : "No downloads needed"
              }
            />
          ))}
        </ChoiceCardGroup>
        <button
          type="button"
          className="front-door-own-setup"
          onClick={() => setShowAdvanced(true)}
        >
          Set up my own
        </button>
        {applyError ? (
          <ActionNotice tone="danger" role="alert">
            {applyError}
          </ActionNotice>
        ) : null}
        {showAdvanced ? (
          <div className="front-door-advanced-inline" data-testid="front-door-advanced">
            <ModelLibraryCore />
            <CapabilityAssignmentsCore />
          </div>
        ) : null}
      </div>
    );
  }

  // ── APPLYING: plan in progress or failed ──
  if (phase === "applying") {
    const steps: PlanStep[] = (plan?.items ?? []).map((item) =>
      planItemToStep(item, activePack),
    );
    const hasFailed = plan?.status === "failed";
    return (
      <div className="front-door" data-testid="front-door-plan">
        <ProgressPlan
          steps={steps}
          ariaLabel="Setup progress"
          action={
            hasFailed
              ? { label: "Resume", onClick: resumePlan }
              : undefined
          }
        />
        {applyError ? (
          <ActionNotice tone="danger" role="alert">
            {applyError}
          </ActionNotice>
        ) : null}
      </div>
    );
  }

  // ── STRIP: configured ──
  const packLabel = activePack?.label ?? plan?.pack_id ?? "";
  return (
    <div className="front-door" data-testid="front-door-strip">
      {attentionRow ? (
        <ActionNotice
          tone="warn"
          action={{
            label: "Fix it",
            onClick: () => {
              setShowAdvanced(true);
              onOpenAssignments?.();
            },
          }}
        >
          {repairCopy(attentionRow)}
        </ActionNotice>
      ) : (
        <ActionNotice
          tone="ok"
          action={{
            label: "Change",
            onClick: () => void load(),
          }}
        >
          Everything wired{packLabel ? ` · ${packLabel}` : ""} · change
        </ActionNotice>
      )}
      <Disclosure
        label="Advanced"
        defaultOpen={false}
        open={showAdvanced}
        onOpenChange={setShowAdvanced}
        variant="default"
      >
        <div className="front-door-advanced" data-testid="front-door-advanced">
          <ModelLibraryCore />
          <CapabilityAssignmentsCore />
        </div>
      </Disclosure>
    </div>
  );
}
