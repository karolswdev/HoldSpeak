import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, readableError } from "../../lib/api";
import {
  authorityBasisLabel,
  controlModeDescription,
  controlModeLabel,
  effectClassLabel,
  humanizeWireValue,
} from "../../lib/productLanguage";
import { workroomHref } from "../../workrooms/context";
import { modelChatId } from "../chat";
import { contextualIntegrationActions } from "../contextual";
import { useProjections } from "../projections";
import { useDesk } from "../store";
import { allObjects } from "../world";
import { qualifiedRef } from "../api";
import { DeskWindowFrame } from "./DeskWindow";

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
    <div>
      <dt>{label}</dt>
      <dd>{String(value)}</dd>
    </div>
  );
}

function when(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? value : date.toLocaleString();
}

export function DeskToolInspector() {
  const inspector = useDesk((state) => state.toolInspector);
  const projects = useDesk((state) => state.projects);
  const targets = useDesk((state) => state.inferenceTargets);
  const setup = useDesk((state) => state.setup);
  const items = useDesk((state) => state.items);
  const models = useDesk((state) => state.models);
  const selectedIds = useDesk((state) => state.selectedIds);
  const { closeToolInspector, openPullout, openChat } = useDesk.getState();
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
  return (
    <DeskWindowFrame
      id="inspector"
      label={title}
      className="desk-tool-inspector"
      eyebrow={project ? "Project" : integration ? "Integration" : "Runs on"}
      title={<h2 className="desk-panel-title">{title}</h2>}
      entrance={false}
      open={Boolean(inspector)}
      onClose={closeToolInspector}
    >

      {project ? (
        <>
          <p>
            {project.description ||
              "Work and material assigned to this Project."}
          </p>
          <dl className="desk-tool-facts">
            <Fact label="Meetings" value={project.meeting_count} />
            <Fact label="Updated" value={when(project.updated_at)} />
          </dl>
          <section>
            <h3>Related Desk material</h3>
            {loadingProject ? <p>Loading Project material…</p> : null}
            {!loadingProject && !resourceObjects.length ? (
              <p>No Desk material is assigned.</p>
            ) : null}
            <ul className="desk-tool-resource-list">
              {resourceObjects.map((resource) => (
                <li key={resource.resource_ref}>
                  {resource.object ? (
                    <button
                      type="button"
                      onClick={() => openPullout(resource.resource_ref)}
                    >
                      <strong>{resource.object.title}</strong>
                      <small>{resource.relationship}</small>
                    </button>
                  ) : (
                    <span>
                      <strong>{resource.resource_ref}</strong>
                      <small>
                        {resource.relationship} · unavailable on this Desk
                      </small>
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </section>
          <Link
            className="desk-chip"
            to={workroomHref("/dictation", {
              action: "use-project-context",
              subjectRef: `project:${project.id}`,
            })}
          >
            Open Project context
          </Link>
        </>
      ) : null}

      {target ? (
        <>
          <p>
            {target.readiness.available
              ? "Ready for model-backed work."
              : target.readiness.reason}
          </p>
          <dl className="desk-tool-facts">
            <Fact
              label="State"
              value={target.readiness.available ? "Ready" : "Unavailable"}
            />
            <Fact label="Boundary" value={target.boundary} />
            <Fact label="Engine" value={target.engine} />
            <Fact label="Model" value={target.model || "Hub default"} />
            <Fact label="Sends" value={target.data_scope.sent.join(", ")} />
            <Fact
              label="Returns"
              value={target.data_scope.returned.join(", ")}
            />
          </dl>
          <div className="desk-tool-actions">
            {target.model &&
            models.some((model) => model.name === target.model) ? (
              <button
                type="button"
                className="desk-chip"
                disabled={!target.readiness.available}
                onClick={() => openChat(modelChatId(target.model))}
              >
                Chat with {target.model}
              </button>
            ) : null}
            <Link
              className="desk-chip quiet"
              to={workroomHref("/profiles", {
                action: "configure-runs-on",
              })}
            >
              Configure Runs on
            </Link>
          </div>
        </>
      ) : null}

      {integration ? (
        <>
          <p>{integration.operation}</p>
          <dl className="desk-tool-facts">
            <Fact
              label="State"
              value={integration.enabled ? "Configured" : "Not configured"}
            />
            <Fact label="Destination" value={integration.destination} />
            <Fact label="Boundary" value={integration.boundary} />
            <Fact label="Data" value={integration.data_class} />
            <Fact
              label="Control posture"
              value={
                authority?.control_mode_label ||
                (authority?.control_mode
                  ? controlModeLabel(authority.control_mode)
                  : undefined)
              }
            />
            <Fact
              label="Authority"
              value={
                authority?.control_mode
                  ? controlModeDescription(authority.control_mode)
                  : integration.authority_basis
              }
            />
            <Fact label="Background" value={integration.background_ability} />
          </dl>
          {integrationAction ? (
            <section className="desk-integration-effect">
              <h3>Selected source</h3>
              <strong>{integrationAction.source.title}</strong>
              <pre>{integrationAction.source.text}</pre>
              {!proposal ? (
                <button
                  type="button"
                  className="desk-chip"
                  disabled={busy}
                  onClick={() => void propose()}
                >
                  {busy
                    ? "Preparing proposed action…"
                    : integrationAction.label}
                </button>
              ) : null}
            </section>
          ) : (
            <p className="desk-tool-empty">
              {integration.enabled
                ? "Select one Note or Artifact with text to use this Integration."
                : "Configure this Integration before using it from selected material."}
            </p>
          )}
          {proposal ? (
            <section className="desk-integration-proposal" aria-live="polite">
              <h3>
                {proposal.policy_snapshot?.outcome === "refused"
                  ? "Operation refused"
                  : proposal.status === "proposed"
                    ? "Proposed action"
                    : "Operation Receipt"}
              </h3>
              <p>{proposal.preview}</p>
              <dl className="desk-tool-facts">
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
              </dl>
              {proposal.status === "proposed" &&
              proposal.policy_snapshot?.outcome !== "refused" ? (
                <div className="desk-tool-actions">
                  <button
                    type="button"
                    className="desk-chip"
                    disabled={busy}
                    onClick={() => void decide("approved")}
                  >
                    {proposal.commitment?.approve ||
                      `Approve ${integration.operation}`}
                  </button>
                  <button
                    type="button"
                    className="desk-chip quiet"
                    disabled={busy}
                    onClick={() => void decide("rejected")}
                  >
                    Reject proposed action
                  </button>
                </div>
              ) : null}
              {proposal.status === "failed" ? (
                <button
                  type="button"
                  className="desk-chip"
                  disabled={busy}
                  onClick={() => void decide("approved")}
                >
                  Retry {proposal.commitment?.approve || integration.operation}
                </button>
              ) : null}
              {["executed", "rejected", "failed"].includes(proposal.status) ||
              proposal.policy_snapshot?.outcome === "refused" ? (
                <div className="desk-integration-receipt">
                  <strong>
                    Receipt ·{" "}
                    {proposal.policy_snapshot?.outcome === "refused"
                      ? "refused"
                      : proposal.status}
                  </strong>
                  <p>
                    Source retained ·{" "}
                    {boundSource?.label || "selected material"}
                  </p>
                  {proposal.error ? <p>{proposal.error}</p> : null}
                  {boundSource ? (
                    <button
                      type="button"
                      className="desk-chip quiet"
                      onClick={() => openPullout(boundSource.ref)}
                    >
                      Return to {boundSource.label}
                    </button>
                  ) : null}
                </div>
              ) : null}
            </section>
          ) : null}
          <Link
            className="desk-chip quiet"
            to={workroomHref("/settings", {
              action: "configure-integration",
              subjectRef: `integration:${integration.id}`,
            })}
          >
            Configure {integration.name}
          </Link>
        </>
      ) : null}

      {error ? (
        <p className="desk-run-warning" role="alert">
          {error} Selected material is retained; retry the action.
        </p>
      ) : null}
    </DeskWindowFrame>
  );
}
