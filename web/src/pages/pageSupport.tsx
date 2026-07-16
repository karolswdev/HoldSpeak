import {
  type ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { Link, useLocation } from "react-router-dom";
import { apiFetch, readableError } from "../lib/api";
import {
  Button,
  Dialog,
  EmptyState,
  InlineMessage,
  Skeleton,
} from "../components/signal/Signal";
import {
  controlModeDescription,
  controlModeLabel,
} from "../lib/productLanguage";
import {
  decodeWorkroomContext,
  workroomActionLabel,
  workroomReturnHref,
  type WorkroomContext,
} from "../workrooms/context";

const SUBJECT_LABELS: Record<string, string> = {
  artifact: "Artifact",
  integration: "Integration",
  knowledge: "Knowledge",
  meeting: "Meeting",
  note: "Note",
  persona: "Persona",
  project: "Project",
  workflow: "Workflow",
  zone: "Zone",
};

function subjectDescription(context: WorkroomContext): string | null {
  const ref = context.subject_ref;
  if (!ref) return null;
  const split = ref.indexOf(":");
  if (split < 1) return null;
  const kind = ref.slice(0, split);
  const id = ref.slice(split + 1);
  return `${SUBJECT_LABELS[kind] ?? kind.replace(/_/g, " ")} · ${id}`;
}

export function WorkroomBar({
  context,
  subjectLabel,
}: {
  context: WorkroomContext | null;
  subjectLabel?: string | null;
}) {
  const subject =
    subjectLabel || (context ? subjectDescription(context) : null);
  const returnsToSubject = Boolean(context?.return_ref ?? context?.subject_ref);
  return (
    <nav className="workroom-bar" aria-label="Workroom context">
      <span className="signal-eyebrow">
        {context ? "From Desk" : "Opened directly"}
      </span>
      {subject ? <strong>{subject}</strong> : null}
      {context ? <span>{workroomActionLabel(context.action)}</span> : null}
      <Link to={workroomReturnHref(context)}>
        {returnsToSubject ? "Back to subject on Desk" : "Back to Desk"}
      </Link>
    </nav>
  );
}

export function PageHero({
  eyebrow,
  title,
  children,
  actions,
  workroomSubject,
}: {
  eyebrow?: string;
  title: string;
  children?: ReactNode;
  actions?: ReactNode;
  workroomSubject?: string | null;
}) {
  const location = useLocation();
  const context = decodeWorkroomContext(location.search);
  return (
    <>
      <header className="page-hero">
        <div>
          {eyebrow ? <span className="signal-eyebrow">{eyebrow}</span> : null}
          <h1>{title}</h1>
          {children ? <p>{children}</p> : null}
        </div>
        {actions}
      </header>
      <WorkroomBar context={context} subjectLabel={workroomSubject} />
    </>
  );
}

/**
 * The one chrome for a control posture: the canonical label, optionally
 * followed by the canonical description. Renders inline so it can sit inside
 * facts lines and supporting text alike.
 */
export function PostureNote({
  mode,
  describe = false,
}: {
  mode: string;
  describe?: boolean;
}) {
  return (
    <span className="posture-note">
      <strong>{controlModeLabel(mode)}</strong>
      {describe ? <> · {controlModeDescription(mode)}</> : null}
    </span>
  );
}

export function useResource<T>(url: string, initial: T) {
  const [data, setData] = useState<T>(initial);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const mounted = useRef(true);

  useEffect(
    () => () => {
      mounted.current = false;
    },
    [],
  );
  const reload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await apiFetch<T>(url);
      if (mounted.current) setData(result);
      return result;
    } catch (reason) {
      if (mounted.current) setError(readableError(reason));
      return null;
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, [url]);
  useEffect(() => {
    void reload();
  }, [reload]);
  return { data, setData, loading, error, setError, reload };
}

export function ResourceState({
  loading,
  error,
  empty,
  onRetry,
  children,
}: {
  loading: boolean;
  error: string;
  empty?: boolean;
  onRetry(): void;
  children: ReactNode;
}) {
  if (loading) return <Skeleton rows={4} />;
  if (error)
    return (
      <InlineMessage tone="error">
        {error}{" "}
        <Button dense variant="ghost" onClick={onRetry}>
          Try again
        </Button>
      </InlineMessage>
    );
  if (empty)
    return (
      <EmptyState title="Nothing here yet">
        This surface will fill as HoldSpeak records real work.
      </EmptyState>
    );
  return children;
}

export function ConfirmAction({
  open,
  title,
  detail,
  busy,
  onConfirm,
  onClose,
}: {
  open: boolean;
  title: string;
  detail: string;
  busy?: boolean;
  onConfirm(): void;
  onClose(): void;
}) {
  return (
    <Dialog open={open} title={title} onClose={onClose}>
      <p>{detail}</p>
      <div className="button-row">
        <Button variant="danger" loading={busy} onClick={onConfirm}>
          Confirm
        </Button>
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </Dialog>
  );
}

export function valueAt(record: unknown, path: string, fallback = ""): string {
  let value: unknown = record;
  for (const key of path.split(".")) {
    if (!value || typeof value !== "object") return fallback;
    value = (value as Record<string, unknown>)[key];
  }
  return value === null || value === undefined ? fallback : String(value);
}

export function asRows(
  value: unknown,
  keys: string[],
): Array<Record<string, unknown>> {
  if (Array.isArray(value))
    return value.filter(
      (row): row is Record<string, unknown> =>
        Boolean(row) && typeof row === "object",
    );
  if (value && typeof value === "object") {
    for (const key of keys) {
      const rows = (value as Record<string, unknown>)[key];
      if (Array.isArray(rows)) return asRows(rows, []);
    }
  }
  return [];
}

export function rowId(row: Record<string, unknown>, index: number): string {
  return String(row.id ?? row.key ?? row.name ?? row.session_id ?? index);
}
