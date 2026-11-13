import { useRef, useState, type ReactNode } from "react";
import {
  InspectorQuestion,
  InspectorFacts,
  SurfaceState,
  wireDayClock,
  type ListVerb,
} from "../../desk/surface";
import { openSurfaceOr } from "../../desk/shell";
import { formatTimeShort, sentenceToken } from "./core/format";
import { registerProjectRepository } from "../../desk/projectRepository";
import type { ProjectRoomController } from "./useProjectRoomController";
import type { RoomSnapshot } from "./model";
import { RoomList, roomFacts, roomSourceName, type RoomEntry } from "./RoomList";
import * as api from "./api";
import { ApiError, readableError } from "../../lib/api";

export function RoomSources({
  room,
  ctrl,
  verbs,
  field,
  onReload,
}: {
  room: RoomSnapshot;
  ctrl: ProjectRoomController;
  verbs: ListVerb[];
  field: ReactNode;
  onReload(): Promise<void>;
}) {
  const [picked, setPicked] = useState<string | null>(null),
    [armed, setArmed] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [registerRetry, setRegisterRetry] = useState<string | null>(null);
  const register = async (scope: string) => {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    try {
      await registerProjectRepository(room.projectId, scope);
      setError("");
      setRegisterRetry(null);
      await onReload();
    } catch {
      setRegisterRetry(scope);
      setError(
        "Could not register the repository · Nothing changed · Try again",
      );
    } finally {
      pending.current = false;
      setBusy(false);
    }
  };
  const [failed, setFailed] = useState<{
    action: "Pause" | "Resume" | "Remove";
    ids: string[];
  } | null>(null);
  const [busy, setBusy] = useState(false),
    pending = useRef(false);
  const sources = room.sources.state === "ok" ? room.sources.items : [];
  const source = sources.find((row) => row.watchId === picked);
  const suggestion = ctrl.suggestedSources.find((row) => row.id === picked);
  const target = source
    ? `${source.watchIds.join(":")}:${JSON.stringify(source.watchBindings)}:${source.state}:${source.checkedAt}`
    : suggestion
      ? `${suggestion.id}:${suggestion.status}`
      : "";
  const change = async (
    action: "Pause" | "Resume" | "Remove",
    ids: string[],
  ) => {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      const operation =
        action === "Pause"
          ? api.pauseWatch
          : action === "Resume"
            ? api.resumeWatch
            : api.retireWatch;
      const answers = await Promise.allSettled(ids.map((id) => action === "Remove" ? api.retireWatch(id, sources.find((row) => row.watchIds.includes(id))?.watchBindings?.[id]) : operation(id)));
      const rejected = ids.filter(
        (_, index) => answers[index].status === "rejected",
      );
      setFailed(rejected.length ? { action, ids: rejected } : null);
      if (rejected.length) {
        const cause = (answers.find((answer) => answer.status === "rejected") as PromiseRejectedResult).reason;
        const stale = cause instanceof ApiError && (cause.payload as { code?: string } | null)?.code === "answer_stale";
        setError(stale && rejected.length === ids.length ? readableError(cause) : `Could not ${action.toLowerCase()} all watches · Other changes stay · Retry`);
      } else setArmed(null);
      await onReload();
    } finally {
      pending.current = false;
      setBusy(false);
    }
  };
  const rows: RoomEntry[] = [
    ...ctrl.suggestedSources.map((row) => ({
      id: row.id,
      name: row.reference,
      kind: row.provider,
      kindWord: row.provider,
      cells: { when: "Suggested" },
      facts: [
        { label: "From", value: "Meeting" },
        { label: "What it says", value: row.reference },
      ],
      open: () => setPicked(row.id),
    })),
    ...sources.map((row) => ({
      id: row.watchId,
      name:
        roomSourceName(row.provider, row.scope) ||
        (row.provider === "github"
          ? "GitHub"
          : row.provider === "jira"
            ? "Jira"
            : row.provider === "confluence"
              ? "Confluence"
              : "Meeting"),
      kind: row.provider,
      kindWord:
        row.provider === "github"
          ? "Repository"
          : row.provider === "jira"
            ? "Project"
            : row.provider === "meeting"
              ? "Meeting"
              : "Space",
      when:
        row.state === "cant_check" &&
        /sign|auth|credential|token|401|403/i.test(row.plainReason || "")
          ? "Sign in again"
          : row.state === "cant_check"
            ? "Could not read"
            : row.checkedAt
              ? wireDayClock(row.checkedAt)
              : "Never read",
      facts: [
        { label: "From", value: row.provider },
        ...(row.provider === "jira" && row.scope.includes("|") ? [{ label: "Project name", value: "Not available" }] : []),
        { label: "Last read", value: wireDayClock(row.checkedAt) },
        {
          label: "State",
          value:
            row.state === "paused"
              ? "Paused"
              : row.state === "cant_check"
                ? row.plainReason
                : row.freshness === "stale"
                  ? "Stale"
                  : row.freshness === "quiet" && row.quietUntil
                    ? `Quiet until ${formatTimeShort(row.quietUntil)}`
                    : "",
        },
        {
          label: "What it says",
          value: row.tokens.map(sentenceToken).join(" · "),
        },
      ],
      open: () => {
        if (row.provider === "github")
          window.open(`https://github.com/${row.scope}`, "_blank", "noopener");
        else openSurfaceOr("configure-connections", "/settings", "connections");
      },
    })),
  ];
  const actions: ListVerb[] = [
    ...verbs,
    {
      id: "pause",
      label: source?.state === "paused" ? "Resume" : "Pause",
      enabled: () => Boolean(source) && !busy && !failed,
      run: () => {
        if (source)
          void change(
            source.state === "paused" ? "Resume" : "Pause",
            source.watchIds,
          );
      },
    },
    {
      id: "remove",
      label: "Remove",
      enabled: () => Boolean(source) && !busy && !failed,
      run: () => setArmed(target),
    },
    {
      id: "fix",
      label: "Sign in again",
      enabled: () => source?.state === "cant_check",
      run: () =>
        openSurfaceOr("configure-connections", "/settings", "connections"),
    },
    {
      id: "add",
      label: "Add",
      enabled: () => Boolean(suggestion) && !ctrl.suggestionBusy,
      run: () => {
        if (suggestion) void ctrl.handleAddSuggestion(suggestion.reference);
      },
    },
    {
      id: "dismiss",
      label: "Dismiss",
      enabled: () => Boolean(suggestion),
      run: () => setArmed(target),
    },
    {
      id: "register",
      label: "Register repository",
      enabled: () => source?.provider === "github" && !busy,
      run: () => {
        if (source) void register(source.scope);
      },
    },
  ];
  const readAgain = () => { setError(""); setFailed(null); setArmed(null); void onReload(); };
  const retry = failed && failed.action !== "Remove" ? () => { void change(failed.action, failed.ids); }
    : registerRetry ? () => { void register(registerRetry); } : readAgain;
  const refusal = error ? <SurfaceState error={error} onRetry={retry} retryLabel={failed?.action === "Remove" ? "Read again" : undefined} /> : undefined;
  return (
    <RoomList
      label="Sources"
      rows={rows}
      selectedId={picked}
      onSelect={(id) => {
        setPicked(id);
        setArmed(null);
      }}
      columns={[
        { key: "name", word: "Source", priority: 10 },
        { key: "kind", word: "Kind", priority: 1 },
        { key: "when", word: "Last read", priority: 9 },
      ]}
      verbs={actions}
      field={field}
      error={
        room.sources.state === "degraded"
          ? "Could not read the sources · Nothing changed"
          : null
      }
      retryLabel={failed?.action === "Remove" ? "Read again" : undefined}
      retry={
        failed && failed.action !== "Remove"
          ? () => {
              void change(failed.action, failed.ids);
            }
          : registerRetry
            ? () => {
                void register(registerRetry);
              }
            : () => {
                setError("");
                setFailed(null);
                setArmed(null);
                void onReload();
              }
      }
      empty="No sources"
    >
      {armed && armed === target ? (
        <InspectorQuestion
          actionId="remove"
          targetId={target}
          question={
            source
              ? `Remove ${roomSourceName(source.provider, source.scope)}?`
              : `Dismiss ${suggestion?.reference}?`
          }
          keeps={["Saved project records"]}
          cancel={() => setArmed(null)}
          onDisarm={() => setArmed(null)}
          verb={{
            label: source ? "Remove" : "Dismiss",
            busy,
            run: () => {
              if (source) void change("Remove", source.watchIds);
              else if (suggestion)
                void ctrl
                  .handleDismissSuggestion(suggestion.reference)
                  .then(() => setArmed(null));
            },
          }}
          notice={refusal}
        />
      ) : error ? (
        <InspectorFacts
          name={source ? roomSourceName(source.provider, source.scope) : suggestion?.reference || "Source"}
          rows={roomFacts(rows.find((row) => row.id === picked)?.facts ?? [])}
          notice={refusal}
          data-feedback-redact="true"
        />
      ) : undefined}
    </RoomList>
  );
}
