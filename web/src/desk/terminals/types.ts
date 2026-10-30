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
  start(): void;
  stop(): void;
  setActivity(activity: TerminalActivity): void;
  enableTyping(): Promise<boolean>;
  disableTyping(): Promise<void>;
  sendData(data: string): boolean;
  sendText(text: string, submit?: boolean): Promise<boolean>;
  sendKeys(keys: TerminalKey[], label?: string): Promise<boolean>;
}

/** The wire shape accepted by the existing coder-keys authority. */
export type TerminalKey = string | { literal: string };
