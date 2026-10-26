import { wireDate } from "../surface/format";
import "./chrome-menus.css";
import { useEffect, useMemo, useState } from "react";
import { apiFetch, readableError } from "../../lib/api";
import {
  authorityBasisLabel,
  controlModeDescription,
  controlModeLabel,
  effectClassLabel,
  humanizeWireValue,
} from "../../lib/productLanguage";
import { openNewThread } from "../newThread";
import { contextualIntegrationActions } from "../contextual";
import { useProjections } from "../projections";
import { useDesk } from "../store";
import { openSurfaceOr } from "../shell";
import { allObjects } from "../world";
import { qualifiedRef } from "../api";
import {
  FoldGadget, GadgetGroup, GadgetRow, Material,
  StateChip, SurfaceFooter, SurfaceSection, SurfaceState, SurfaceWell,
  type ChipState,
} from "../surface";
import { bareHost, egressFor } from "../surface/egress";
import { Button } from "../../components/signal/Signal";
import { DeskWindowFrame } from "./DeskWindow";
import { WhyControl } from "./WhyControl";

interface Proposal {
  id: string;
  status: "proposed" | "approved" | "executed" | "failed" | "rejected";
  target: string;
  preview: string;
  error?: string | null;
  result?: Record<string, unknown> | null;
  commitment?: { approve?: string; reject?: string };
  operation?: {
    effect_class?: string;
    destination?: string;
    consequence?: string;
  };
  policy_snapshot?: {
    mode?: string;
    source?: string;
    policy_version?: string;
    outcome?: string;
    reason_code?: string;
    authority_basis?: string;
    next_state?: string;
    eligible?: boolean;
  };
  payload?: {
    _source?: { ref?: string; label?: string };
  };
}

interface AuthorityPolicy {
  control_mode?: string;
  control_mode_label?: string;
  control_mode_description?: string;
  policy_version?: string;
  source?: string;
  applies_to?: string;
}

const INTEGRATION_TARGET: Record<string, "slack" | "webhook" | "github"> = {
  slack: "slack",
  companion_webhook: "webhook",
  github: "github",
};

function Fact({ label, value }: { label: string; value: unknown }) {
  if (value === undefined || value === null || value === "") return null;
  return (
    <GadgetRow label={label} controlWidth="full">
      <span className="desk-tool-value">{String(value)}</span>
    </GadgetRow>
  );
}

function when(value: string): string {
  const date = wireDate(value);
  return !date ? value : date.toLocaleString();
}

export function DeskToolInspector() {
  const inspector = useDesk((state) => state.toolInspector);
  const projects = useDesk((state) => state.projects);
  const targets = useDesk((state) => state.inferenceTargets);
  const setup = useDesk((state) => state.setup);
  const items = useDesk((state) => state.items);
  const models = useDesk((state) => state.models);
  const selectedIds = useDesk((state) => state.selectedIds);
  const { closeToolInspector, openPullout, refresh } = useDesk.getState();
  const [projectResources, setProjectResources] = useState<
    Array<{ resource_ref: string; relationship: string }>
  >([]);
  const [loadingProject, setLoadingProject] = useState(false);
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [authority, setAuthority] = useState<AuthorityPolicy | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const project =
    inspector?.kind === "project"
      ? (projects.find((candidate) => candidate.id === inspector.id) ?? null)
      : null;
  const integration =
    inspector?.kind === "integration"
      ? (setup?.trust?.destinations?.find(
          (candidate) => candidate.id === inspector.id,
        ) ?? null)
      : null;
  const target =
    inspector?.kind === "target"
      ? (targets.find((candidate) => candidate.id === inspector.id) ?? null)
      : null;
  const integrationAction = integration
    ? (contextualIntegrationActions([integration], items, selectedIds)[0] ??
      null)
    : null;
  const proposalSource = proposal?.payload?._source;
  const boundSource = proposalSource?.ref
    ? {
        ref: proposalSource.ref,
        label:
          proposalSource.label ||
          proposalSource.ref.slice(proposalSource.ref.indexOf(":") + 1),
      }
    : integrationAction
      ? {
          ref: integrationAction.source.ref,
          label: integrationAction.source.title,
        }
      : null;

  const resourceObjects = useMemo(() => {
    const objects = allObjects(items);
    return projectResources.map((resource) => ({
      ...resource,
      object:
        objects.find(
          (candidate) =>
            qualifiedRef(candidate.kind, candidate.id) ===
            resource.resource_ref,
        ) ?? null,
    }));
  }, [items, projectResources]);

  useEffect(() => {
    setProposal(null);
    setAuthority(null);
    setError("");
  }, [inspector?.kind, inspector?.id]);

  useEffect(() => {
    if (!integration) return;
    void apiFetch<AuthorityPolicy>("/api/authority/policy")
      .then(setAuthority)
      .catch((reason) => setError(readableError(reason)));
  }, [integration?.id]);

  useEffect(() => {
    if (!project) {
      setProjectResources([]);
      return;
    }
    setLoadingProject(true);
    void apiFetch<{
      resources: Array<{ resource_ref: string; relationship: string }>;
    }>(`/api/projects/${encodeURIComponent(project.id)}/resources`)
      .then((response) => setProjectResources(response.resources ?? []))
      .catch((reason) => setError(readableError(reason)))
      .finally(() => setLoadingProject(false));
  }, [project?.id]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && inspector) closeToolInspector();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [inspector]);

  if (!inspector) return null;

  const propose = async () => {
    if (!integrationAction) return;
    const wireTarget = INTEGRATION_TARGET[integrationAction.id];
    setBusy(true);
    setError("");
    try {
      const response = await apiFetch<{ proposal: Proposal }>(
        `/api/desk/actuators/${wireTarget}/propose`,
        {
          method: "POST",
          json: {
            text: integrationAction.source.text,
            title: integrationAction.source.title,
            source_ref: integrationAction.source.ref,
            source_label: integrationAction.source.title,
          },
        },
      );
      setProposal(response.proposal);
      if (
        response.proposal.status !== "proposed" ||
        response.proposal.policy_snapshot?.outcome === "refused"
      ) {
        await Promise.all([
          useProjections.getState().refresh(true),
          useProjections.getState().refreshAmbient(),
        ]);
      }
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setBusy(false);
    }
  };

  const decide = async (decision: "approved" | "rejected") => {
    if (!proposal) return;
    setBusy(true);
    setError("");
    try {
      const response = await apiFetch<{ proposal: Proposal }>(
        `/api/desk/actuators/${proposal.target}/${encodeURIComponent(proposal.id)}/decision`,
        { method: "POST", json: { decision, decided_by: "web-desk" } },
      );
      setProposal(response.proposal);
      await Promise.all([
        useProjections.getState().refresh(true),
        useProjections.getState().refreshAmbient(),
      ]);
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setBusy(false);
    }
  };

  const title =
    project?.name ?? integration?.name ?? target?.name ?? "Desk tool";
  const refused = proposal?.policy_snapshot?.outcome === "refused";
  const terminal = proposal && (refused || ["executed", "rejected", "failed"].includes(proposal.status));
  const outcome: { state: ChipState; label: string } | null = busy
    ? { state: "working", label: "Working…" }
    : proposal
      ? refused ? { state: "warning", label: "Refused" }
        : proposal.status === "executed" ? { state: "success", label: "Executed" }
          : proposal.status === "failed" ? { state: "failure", label: "Failed" }
            : proposal.status === "rejected" ? { state: "idle", label: "Rejected" }
              : { state: "warning", label: "Awaiting approval" }
      : null;
  const destination = integration?.destination || "";
  // The trust projection may name an endpoint without exposing its host.
  // Only a real route gets host classification; an opaque label stays remote.
  const route = integration?.id === "github" ? egressFor("github.com")
    : /^[a-z][a-z0-9+.-]*:\/\//i.test(destination) ? egressFor(bareHost(destination))
      : { label: destination, scope: "remote" as const };
  // Owner ruling 2026-10-25 (UX-CANON A.9): the route is named at the verb, in its hover title.
  const routeTitle = integration?.enabled && route.label ? `Goes to ${route.label}` : undefined;
  const sourceText = boundSource
    ? allObjects(items).find((object) => qualifiedRef(object.kind, object.id) === boundSource.ref)?.ref
    : null;
  const sourceBody = sourceText && "bodyMarkdown" in sourceText ? String(sourceText.bodyMarkdown || "")
    : integrationAction?.source.ref === boundSource?.ref ? integrationAction?.source.text || "" : "";
  const configureIntegration = () => {
    if (integration) openSurfaceOr("configure-integration", "/settings", `integration:${integration.id}`);
  };
  return (
    <DeskWindowFrame
      id="inspector"
      glyph="⌕"
      label={title}
      className="desk-tool-inspector"
      title={title}
      defaultW={620}
      minW={320}
      fitContent
      entrance={false}
      open={Boolean(inspector)}
      onClose={closeToolInspector}
    >
      {/* The frame owns geometry; the body owns the reading scroll. */}
      <div className="desk-pullout-body desk-surface-body desk-tool-inspector-body">
      {project ? (
        <>
          {project.description ? <Material>{project.description}</Material> : null}
          <GadgetGroup label="Project" material="inset">
            <Fact label="Meetings" value={project.meeting_count} />
            <Fact label="Updated" value={when(project.updated_at)} />
          </GadgetGroup>
          <WhyControl workType="project" workRef={project.id} />
          <SurfaceSection label="Related material">
            {loadingProject ? <SurfaceState loading /> : null}
            {!loadingProject && !resourceObjects.length ? (
              <SurfaceState empty emptyLabel="No material" />
            ) : null}
            <ul className="desk-tool-resource-list">
              {resourceObjects.map((resource) => (
                <li key={resource.resource_ref}>
                  {resource.object ? (
                    <Button
                      dense variant="ghost"
                      onClick={() => openPullout(resource.resource_ref)}
                    >
                      {resource.object.title}
                    </Button>
                  ) : (
                    <span>
                      <strong>{(() => { const ref = resource.resource_ref; return humanizeWireValue(String(ref)); })()}</strong>
                      <small>
                        {humanizeWireValue(String(resource.relationship))} · unavailable on this Desk
                      </small>
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </SurfaceSection>
        </>
      ) : null}

      {target ? (
        <>
          <StateChip state={target.readiness.available ? "success" : "unreachable"} label={target.readiness.available ? "Ready" : "Unavailable"} />
          {!target.readiness.available && target.readiness.reason ? <SurfaceState error={target.readiness.reason} /> : null}
          <GadgetGroup label="Engine" material="inset">
            <Fact label="Boundary" value={target.boundary} />
            <Fact label="Engine" value={target.engine} />
            <Fact label="Model" value={target.model || "Hub default"} />
            <Fact label="Sends" value={target.data_scope.sent.join(", ")} />
            <Fact
              label="Returns"
              value={target.data_scope.returned.join(", ")}
            />
          </GadgetGroup>
        </>
      ) : null}

      {integration ? (
        <>
          <div className="desk-tool-status">
            <StateChip state={integration.enabled ? "success" : "idle"} label={integration.enabled ? "Configured" : "Not configured"} />
            {integration.enabled && destination ? <strong className="surface-primary">{destination}</strong> : null}
          </div>
          {boundSource ? (
            <GadgetGroup label="Source" material="inset">
              <GadgetRow label="Selected material" controlWidth="full"><strong className="surface-primary">{boundSource.label}</strong></GadgetRow>
              {sourceBody ? <FoldGadget title="Source text"><Material>{sourceBody}</Material></FoldGadget> : null}
            </GadgetGroup>
          ) : integration.enabled ? <SurfaceState empty emptyLabel="No selected text" /> : null}
          {proposal ? (
            <SurfaceWell head="Preview"><Material>{proposal.preview}</Material></SurfaceWell>
          ) : null}
          <FoldGadget title="Details">
            <GadgetGroup material="inset">
              <Fact label="Operation" value={integration.operation} />
              <Fact label="Boundary" value={integration.boundary} />
              <Fact label="Data" value={integration.data_class} />
              <Fact label="Control posture" value={authority?.control_mode_label || (authority?.control_mode ? controlModeLabel(authority.control_mode) : undefined)} />
              <Fact label="Authority" value={authority?.control_mode ? controlModeDescription(authority.control_mode) : integration.authority_basis} />
              <Fact label="Background" value={integration.background_ability} />
              {proposal ? <>
                <Fact
                  label="Effect"
                  value={
                    proposal.operation?.effect_class
                      ? effectClassLabel(proposal.operation.effect_class)
                      : undefined
                  }
                />
                <Fact
                  label="Destination"
                  value={proposal.operation?.destination}
                />
                <Fact
                  label="Control posture"
                  value={
                    proposal.policy_snapshot?.mode
                      ? controlModeLabel(proposal.policy_snapshot.mode)
                      : undefined
                  }
                />
                <Fact
                  label="Authority basis"
                  value={
                    proposal.policy_snapshot?.authority_basis
                      ? authorityBasisLabel(
                          proposal.policy_snapshot.authority_basis,
                        )
                      : undefined
                  }
                />
                <Fact
                  label="Next state"
                  value={
                    proposal.policy_snapshot?.next_state
                      ? humanizeWireValue(proposal.policy_snapshot.next_state)
                      : undefined
                  }
                />
              </> : null}
            </GadgetGroup>
          </FoldGadget>
          {proposal?.error ? <SurfaceState error={proposal.error} /> : null}
        </>
      ) : null}

      {error ? <SurfaceState error={error} /> : null}
      </div>
      <div className="desk-surface-foot">
        <SurfaceFooter
          receipt={outcome ? <StateChip state={outcome.state} label={outcome.label} /> : undefined}
          verbs={<>
            {project ? <Button dense variant="primary" onClick={() => openSurfaceOr("dictate", "/dictation", `project:${project.id}`)}>Open Project context</Button> : null}
            {target ? <>
              {target.model && models.some((model) => model.name === target.model) ? <Button dense variant="primary" disabled={!target.readiness.available} onClick={() => void openNewThread({ title: target.model, profile_override: target.model })}>Continue in thread</Button> : null}
              <Button dense variant="ghost" onClick={() => openSurfaceOr("configure-runs-on", "/profiles")}>Engines</Button>
            </> : null}
            {integration ? <>
              {!proposal && integrationAction ? <Button dense variant="primary" loading={busy} title={routeTitle} onClick={() => void propose()}>{integrationAction.label}</Button> : null}
              {proposal?.status === "proposed" && !refused ? <>
                <Button dense variant="primary" loading={busy} title={routeTitle} onClick={() => void decide("approved")}>{proposal.commitment?.approve || `Approve ${integration.operation}`}</Button>
                <Button dense variant="ghost" disabled={busy} onClick={() => void decide("rejected")}>Reject proposed action</Button>
              </> : null}
              {proposal?.status === "failed" ? <Button dense variant="primary" loading={busy} onClick={() => void decide("approved")}>Retry {proposal.commitment?.approve || integration.operation}</Button> : null}
              {terminal && boundSource ? <Button dense variant="ghost" onClick={() => openPullout(boundSource.ref)}>Return to {boundSource.label}</Button> : null}
              <Button dense variant={!integration.enabled ? "primary" : "ghost"} onClick={configureIntegration}>Configure {integration.name}</Button>
            </> : null}
          </>}
        />
      </div>
    </DeskWindowFrame>
  );
}
