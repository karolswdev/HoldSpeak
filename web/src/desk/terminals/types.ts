/** Browser-side contract for one native terminal window.
 *
 * A descriptor is a server-issued description.  It is deliberately not a
 * selection from the global steering store: once a controller is created its
 * target is immutable for the lifetime of that controller.
 */

export interface TerminalTarget {
  node_id: string;
  target_id: string;
  target_generation: string;
}

export interface TerminalProjectRef {
  id: string;
  name: string;
}

export interface TerminalSourceRef {
  id: string;
  name: string;
}

export interface TerminalWorktreeRef {
  id: string;
  branch: string;
}

export interface TerminalLaunchRef {
  id: string;
  profile_id: string;
  state: string;
  role: string;
  origin_ref: string | { kind?: string; id?: string; [key: string]: unknown } | null;
  attempt_id: string;
}

export interface TerminalProgramRef {
  id: string;
  title: string;
  step_id: string;
  step_ordinal: number | null;
}

export interface TerminalMcpRef {
  status: "configured" | "unknown";
  server: string;
  palette: string;
  pre_approved: boolean;
  read_only: boolean;
}

export type TerminalContextStatus = "bound" | "worktree" | "unbound" | "unavailable";

export interface TerminalContext {
  status: TerminalContextStatus;
  project: TerminalProjectRef | null;
  source: TerminalSourceRef | null;
  worktree: TerminalWorktreeRef | null;
  launch: TerminalLaunchRef | null;
  program: TerminalProgramRef | null;
  mcp: TerminalMcpRef | null;
}

export interface TerminalDescriptor {
  id: string;
  label: string;
  session: string;
  key: string;
  agent: string;
  command: string;
  current_path: string;
  state: string;
  target: TerminalTarget;
  pane_id: string;
  /** Optional additive context. Old hubs still produce useful live terminals. */
  context: TerminalContext;
}

export interface TerminalPaneGeometry {
  width: number;
  height: number;
  cursorX: number;
  cursorY: number;
}

export type TerminalStatus =
  | "idle"
  | "loading"
  | "live"
  | "resyncing"
  | "not_modified"
  | "tmux_absent"
  | "stream_unavailable"
  | "target_gone"
  | "generation_mismatch"
  | "unauthorized"
  | "unreachable"
  | "error";

export interface TerminalReceipt {
  id?: string;
  receipt_id?: string;
  command_id?: string;
  state?: string;
  outcome?: string;
  detail?: string;
  [key: string]: unknown;
}

export interface TerminalDimensions {
  cols: number;
  rows: number;
}

export interface TerminalResizeState {
  desired: TerminalDimensions | null;
  acknowledged: TerminalDimensions | null;
  busy: boolean;
  error: string | null;
}

export interface TerminalOutputFrame {
  kind: "snapshot" | "output" | "resync";
  data: Uint8Array;
  sequence: number;
  pane?: TerminalPaneGeometry | null;
  streamId?: string | null;
}

/** A direct frame seam for a mounted xterm. It deliberately lives on the
 * descriptor session, not in a global stream store: each target owns its
 * stream identity and its bounded replay cursor. */
export interface TerminalOutputSource {
  subscribe(listener: (frame: TerminalOutputFrame) => void): () => void;
  subscribeResync?(listener: () => void): () => void;
  current(): TerminalOutputFrame | null;
  replay?(afterSequence: number): TerminalOutputFrame[] | null;
  snapshot?(): TerminalOutputFrame | null;
  requestResync?(): void;
}

export interface TerminalSnapshot {
  status: TerminalStatus;
  raw: string | null;
  lines: string[];
  pane: TerminalPaneGeometry | null;
  canType: boolean;
  busy: boolean;
  error: string | null;
  receipt: TerminalReceipt | null;
  sequence: number;
  hash: string | null;
  changedAt: number | null;
  focused: boolean;
  visible: boolean;
}

export interface TerminalActivity {
  focused: boolean;
  visible: boolean;
}

export interface TerminalSessionState extends TerminalSnapshot {
  descriptor: TerminalDescriptor;
  output: TerminalOutputSource | null;
  live: boolean;
  resize: TerminalResizeState;
  start(): void;
  stop(): void;
  setActivity(activity: TerminalActivity): void;
  setHostGeometry(dimensions: TerminalDimensions): void;
  retryResize(): Promise<boolean>;
  enableTyping(): Promise<boolean>;
  disableTyping(): Promise<void>;
  sendData(data: string): boolean;
  sendText(text: string, submit?: boolean): Promise<boolean>;
  sendKeys(keys: TerminalKey[], label?: string): Promise<boolean>;
}

/** The wire shape accepted by the existing coder-keys authority. */
export type TerminalKey = string | { literal: string };
