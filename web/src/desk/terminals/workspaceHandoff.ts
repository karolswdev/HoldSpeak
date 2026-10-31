/**
 * The browser-side seam between the Terminal workspace and StartAgent.
 *
 * A workspace file is not a Desk object.  It has no canonical `file:<id>`
 * reference and must not be made one here.  The hand is still made as the
 * existing Note contract; this module only records the repository source,
 * worktree, path and (when the owner has read it) its captured bytes in the
 * user-reviewed Note words.
 */

export interface WorkspaceHandoffProject {
  id: string;
  name?: string | null;
}
export interface WorkspaceHandoffSource {
  /** The registered repository/source identity, not a fabricated file ref. */
  id: string;
  /** The human name shown beside the prepared words. Producers call this `title` or `name`. */
  title?: string | null;
  name?: string | null;
}
export interface WorkspaceHandoffWorktree {
  id: string;
  branch?: string | null;
}

export interface WorkspaceHandoffFile {
  /** The path inside `source`, exactly as read by the workspace. */
  path: string;
  /** Bytes returned by the read operation, when the owner chose to include them. */
  content?: string | null;
  /** The read revision, when the producer returned one. */
  revision?: string | null;
}

/**
 * A prepared handoff captured from one workspace scope.  Every field is
 * explicit so a shell cwd cannot silently supply a Project, launch, source,
 * or worktree.
 */
export interface WorkspaceHandoffContext {
  project: WorkspaceHandoffProject | null;
  source: WorkspaceHandoffSource | null;
  worktree: WorkspaceHandoffWorktree | null;
  file: WorkspaceHandoffFile | null;
}

export interface WorkspaceHandoffPreparation {
  /** The editable task words. Context is shown separately and appended only at Start. */
  words: string;
  context: WorkspaceHandoffContext;
}

/** One StartAgent draft, kept as JSON in the existing Desk draft map. */
export interface WorkspaceHandoffDraft {
  words: string;
  preparedWords?: string;
  projectId?: string;
  scope?: string;
  noteId?: string;
  filed?: boolean;
}

export function readWorkspaceHandoffDraft(raw: string | null | undefined): WorkspaceHandoffDraft | null {
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<WorkspaceHandoffDraft>;
    if (typeof parsed.words === "string") return {
      words: parsed.words,
      ...(typeof parsed.preparedWords === "string" ? { preparedWords: parsed.preparedWords } : {}),
      ...(typeof parsed.projectId === "string" ? { projectId: parsed.projectId } : {}),
      ...(typeof parsed.scope === "string" ? { scope: parsed.scope } : {}),
      ...(typeof parsed.noteId === "string" ? { noteId: parsed.noteId } : {}),
      ...(parsed.filed === true ? { filed: true } : {}),
    };
  } catch {
    // A pre-prepared release stored plain words. Keep those recoverable.
  }
  return { words: raw };
}

export function writeWorkspaceHandoffDraft(draft: WorkspaceHandoffDraft): string {
  return JSON.stringify(draft);
}

export const EMPTY_WORKSPACE_HANDOFF: WorkspaceHandoffContext = {
  project: null,
  source: null,
  worktree: null,
  file: null,
};

/** Keep a local read useful without allowing a large file to balloon a Note. */
export const MAX_CAPTURED_FILE_CONTENT = 12_000;

export function capturedWorkspaceFileContent(content: string): { text: string; shortened: boolean } {
  if (content.length <= MAX_CAPTURED_FILE_CONTENT) return { text: content, shortened: false };
  return {
    text: `${content.slice(0, MAX_CAPTURED_FILE_CONTENT)}\n[… captured content shortened …]`,
    shortened: true,
  };
}
/**
 * Stable, non-content scope for the existing Desk draft map. The path is
 * included because two files in one worktree must retain separate words.
 */
export function workspaceHandoffScope(context: WorkspaceHandoffContext | null | undefined, projectId?: string | null): string {
  // An explicit picker value is authoritative when the owner changes the
  // filing target; otherwise the captured Project remains the scope.
  const project = projectId || context?.project?.id || "none";
  const source = context?.source?.id || "none";
  const worktree = context?.worktree?.id || "none";
  const path = context?.file?.path || "none";
  return ["agent-start", project, source, worktree, path].map(encodeURIComponent).join(":");
}

/** A concise source line for the preparation plate and its tests. */
export function workspaceHandoffSourceWords(context: WorkspaceHandoffContext): string | null {
  if (!context.source) return null;
  const source = context.source.title || context.source.name || context.source.id;
  const path = context.file?.path ? ` · ${context.file.path}` : "";
  return `${source}${path}`;
}

/**
 * Turn the captured workspace facts into Note words.  The caller's words are
 * kept first and remain editable; source facts are plainly labelled so the
 * agent can distinguish a read file from a canonical Desk object.
 */
export function workspaceHandoffWords(words: string, context: WorkspaceHandoffContext | null | undefined): string {
  const task = words.trim();
  if (!context?.source) return task;

  const lines = [
    task,
    "",
    "Reference file (read copy; new work uses the Project's normal repository):",
    `Repository source: ${context.source.title || context.source.name || context.source.id}`,
    `Source id: ${context.source.id}`,
  ];
  if (context.project?.name) lines.push(`Project: ${context.project.name}`);
  if (context.worktree) {
    lines.push(`Captured worktree: ${context.worktree.id}${context.worktree.branch ? ` · ${context.worktree.branch}` : ""}`);
  }
  if (context.file?.path) lines.push(`File path: ${context.file.path}`);
  if (context.file?.revision) lines.push(`Read revision: ${context.file.revision}`);
  if (context.file && context.file.content != null) {
    const captured = capturedWorkspaceFileContent(context.file.content);
    lines.push(
      "",
      captured.shortened
        ? "Captured file content excerpt (read before handoff; shortened):"
        : "Captured file content (read before handoff):",
      // Indentation keeps file bytes as a literal block even if the file
      // itself contains Markdown fences or headings.
      ...captured.text.split("\n").map((line) => `    ${line}`),
    );
  }
  return lines.join("\n");
}

/** Clone only the captured request data before any asynchronous read/hand. */
export function captureWorkspaceHandoff(context: WorkspaceHandoffContext | null | undefined): WorkspaceHandoffContext | null {
  if (!context) return null;
  return {
    project: context.project ? { ...context.project } : null,
    source: context.source ? { ...context.source } : null,
    worktree: context.worktree ? { ...context.worktree } : null,
    file: context.file ? { ...context.file } : null,
  };
}
