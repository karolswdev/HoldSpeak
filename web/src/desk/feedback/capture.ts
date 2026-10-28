import { apiFetch } from "../../lib/api";
import { useDesk } from "../store";
import { toWav16kMono } from "../../lib/speakToFill";
import {
  abortHold,
  beginHold,
  endHold,
  holdOwnsFloor,
  micPhase,
  openMicRunning,
  type HoldToken,
} from "../../lib/micSession";
import {
  FLOOR_RENEW_MS,
  claimAudioFloor,
  releaseAudioFloor,
  renewAudioFloor,
} from "../../lib/audioFloor";

export const FEEDBACK_MAX_MS = 120_000;
const MAX_TEXT = 800;
const MAX_FIELDS = 120;
const MAX_SCROLLS = 80;
const MAX_CONTEXT_BYTES = 256_000;
const MAX_VALUE = 32_000;
let frozenCaptureSequence = 0;

const SENSITIVE_WORD =
  /(?:pass(?:word|code)?|token|secret|credential|api[ _-]?key|authorization|client[ _-]?secret)/i;

export interface FeedbackElementSnapshot {
  tag: string;
  id: string;
  role: string | null;
  testid: string | null;
  name: string | null;
  label: string | null;
  text: string;
  rect: { x: number; y: number; width: number; height: number };
  attributes: Record<string, string>;
  sensitive: boolean;
}

export interface FeedbackFieldSnapshot {
  tag: string;
  id: string;
  name: string | null;
  type: string | null;
  label: string | null;
  value?: string;
  checked?: boolean;
  selected?: Array<{ value: string; label: string }>;
  rect: { x: number; y: number; width: number; height: number };
}

export interface FeedbackContext {
  owner: {
    window_id: string | null;
    name: string;
    rect: { x: number; y: number; width: number; height: number };
    window_text: string;
    hub_row: unknown | null;
  };
  selected_element: FeedbackElementSnapshot;
  fields: FeedbackFieldSnapshot[];
  selected_tabs: Array<{ id: string; label: string; selected: string }>;
  scroll: Array<{ id: string; top: number; left: number }>;
  viewport: { width: number; height: number; dpr: number };
  page: { origin: string; path: string };
  desk: {
    windows: Record<string, unknown>;
    panel_rects: Record<string, unknown>;
    panel_order: string[];
    panel_depth: Record<string, number>;
    panel_min: string[];
    panel_max: string[];
    panel_zoom: Record<string, unknown>;
    drafts: Record<string, string>;
  };
}

export interface CapturedAudio {
  wav: ArrayBuffer;
  durationMs: number;
}

export interface FeedbackAudioSession {
  stop(): CapturedAudio | null;
  cancel(): void;
  lost(): boolean;
  onFloorLost(listener: () => void): void;
}

function text(value: string | null | undefined, max = MAX_TEXT): string {
  return (value ?? "").replace(/\s+/g, " ").trim().slice(0, max);
}

function safeWindowText(value: string | null | undefined): string {
  const result = text(value, 180);
  return SENSITIVE_WORD.test(result) ? "[REDACTED]" : result;
}

function rectOf(element: Element): { x: number; y: number; width: number; height: number } {
  const rect = element.getBoundingClientRect();
  return {
    x: Math.round(rect.x),
    y: Math.round(rect.y),
    width: Math.round(rect.width),
    height: Math.round(rect.height),
  };
}

export function isSensitiveElement(element: Element): boolean {
  if (!(element instanceof Element)) return false;
  if (element.closest("[data-feedback-redact='true']")) return true;
  if (element.matches("input[type='password'], input[type='file']")) return true;
  const attrs = ["id", "name", "aria-label", "autocomplete", "data-testid", "title"]
    .map((name) => element.getAttribute(name) ?? "")
    .join(" ");
  if (SENSITIVE_WORD.test(attrs)) return true;
  if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement) {
    return Array.from(element.labels ?? []).some((label) => visible(label) && SENSITIVE_WORD.test(text(label.innerText || label.textContent, 160)));
  }
  return false;
}

function visible(element: Element): boolean {
  for (let current: Element | null = element; current; current = current.parentElement) {
    if (current.hasAttribute("hidden")) return false;
    const style = getComputedStyle(current);
    if (style.display === "none" || style.visibility === "hidden") return false;
  }
  return true;
}

function fieldLabel(element: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement): string | null {
  const explicit = element.getAttribute("aria-label") || element.getAttribute("title");
  if (explicit) return text(explicit, 160);
  const labels = Array.from(element.labels ?? []).map((label) => text(label.innerText || label.textContent, 160));
  return labels.find(Boolean) ?? null;
}

function safeRenderedText(element: Element): string {
  const clone = element.cloneNode(true) as Element;
  clone.querySelectorAll("*").forEach((child) => {
    if (isSensitiveElement(child)) child.remove();
  });
  return ((clone as HTMLElement).innerText || clone.textContent || "").replace(/\s+/g, " ").trim();
}

function safeText(element: Element): string {
  return safeRenderedText(element).slice(0, MAX_TEXT);
}

function attributesOf(element: Element): Record<string, string> {
  const result: Record<string, string> = {};
  for (const attr of Array.from(element.attributes)) {
    if (/^(?:value|src|href|action)$/i.test(attr.name)) continue;
    if (SENSITIVE_WORD.test(`${attr.name} ${attr.value}`)) continue;
    result[attr.name] = attr.value.slice(0, 180);
  }
  return result;
}

export function snapshotElement(element: Element): FeedbackElementSnapshot {
  const sensitive = isSensitiveElement(element);
  const html = element as HTMLElement;
  const label =
    element.getAttribute("aria-label") ||
    element.getAttribute("title") ||
    (html instanceof HTMLInputElement || html instanceof HTMLTextAreaElement || html instanceof HTMLSelectElement
      ? fieldLabel(html)
      : null);
  return {
    tag: element.tagName.toLowerCase(),
    id: element.id,
    role: element.getAttribute("role"),
    testid: element.getAttribute("data-testid"),
    name: element.getAttribute("name"),
    label: label ? text(label, 160) : null,
    text: sensitive ? "[REDACTED]" : safeText(element),
    rect: rectOf(element),
    attributes: sensitive ? {} : attributesOf(element),
    sensitive,
  };
}

function snapshotField(element: Element): FeedbackFieldSnapshot | null {
  const editable = element instanceof HTMLElement && element.isContentEditable;
  if (!(element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement || editable)) return null;
  if (!visible(element) || isSensitiveElement(element)) return null;
  if (element instanceof HTMLInputElement && element.type === "file") return null;
  const base = {
    tag: element.tagName.toLowerCase(),
    id: element.id,
    name: element.getAttribute("name"),
    type: element instanceof HTMLInputElement ? element.type : null,
    label: element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement ? fieldLabel(element) : element.getAttribute("aria-label"),
    rect: rectOf(element),
  };
  if (element instanceof HTMLInputElement) {
    if (element.type === "checkbox" || element.type === "radio") return { ...base, checked: element.checked };
    return { ...base, value: element.value };
  }
  if (element instanceof HTMLSelectElement) {
    return {
      ...base,
      value: element.value,
      selected: Array.from(element.selectedOptions).slice(0, 20).map((option) => ({ value: option.value.slice(0, 160), label: text(option.label, 160) })),
    };
  }
  if (element instanceof HTMLTextAreaElement) return { ...base, value: element.value };
  return { ...base, value: (element as HTMLElement).innerText || element.textContent || "" };
}

function selectedTabs(root: Element): FeedbackContext["selected_tabs"] {
  return Array.from(root.querySelectorAll("[role='tab'][aria-selected='true'], [aria-current='page'], [aria-pressed='true']"))
    .filter((element) => !isSensitiveElement(element))
    .slice(0, 40)
    .map((element) => ({
      id: element.id,
      label: text(element.getAttribute("aria-label") || element.textContent, 160),
      selected: element.getAttribute("aria-selected") || element.getAttribute("aria-current") || element.getAttribute("aria-pressed") || "true",
    }));
}

function scrolls(root: Element): FeedbackContext["scroll"] {
  const result: FeedbackContext["scroll"] = [];
  for (const element of [root, ...Array.from(root.querySelectorAll("*")).slice(0, 400)]) {
    const candidate = element as HTMLElement;
    if (candidate.scrollTop || candidate.scrollLeft) {
      result.push({ id: candidate.id, top: Math.round(candidate.scrollTop), left: Math.round(candidate.scrollLeft) });
      if (result.length >= MAX_SCROLLS) break;
    }
  }
  return result;
}

function cloneRecord<T>(value: T): T {
  try {
    return structuredClone(value);
  } catch {
    return JSON.parse(JSON.stringify(value)) as T;
  }
}

function selectedRecord<T>(record: Record<string, T>, id: string | null): Record<string, T> {
  if (!id || !(id in record)) return {};
  return { [id]: cloneRecord(record[id]) };
}

function selectedTextMap(record: Record<string, string>, id: string | null): Record<string, string> {
  if (!id) return {};
  return Object.fromEntries(
    Object.entries(record)
      .filter(([key]) => key.includes(id) && !SENSITIVE_WORD.test(key))
      .map(([key, value]) => [key, value.slice(0, MAX_VALUE)]),
  );
}

function deskSnapshot(windowId: string | null): FeedbackContext["desk"] {
  const state = useDesk.getState();
  return {
    windows: selectedRecord(state.windowsById, windowId),
    panel_rects: selectedRecord(state.panelRects, windowId),
    panel_order: windowId && state.panelOrder.includes(windowId) ? [windowId] : [],
    panel_depth: selectedRecord(state.panelDepth, windowId),
    panel_min: windowId && state.panelMin.includes(windowId) ? [windowId] : [],
    panel_max: windowId && state.panelMax.includes(windowId) ? [windowId] : [],
    panel_zoom: selectedRecord(state.panelZoom, windowId),
    drafts: selectedTextMap(state.drafts, windowId),
  };
}

export function snapshotContext(target: Element, root: Element, hubRow: unknown | null): FeedbackContext {
  const fields = Array.from(root.querySelectorAll("input, textarea, select, [contenteditable='true']"))
    .map(snapshotField)
    .filter((field): field is FeedbackFieldSnapshot => field !== null)
    .slice(0, MAX_FIELDS);
  const ownerId = root.getAttribute("data-layer") === "window" ? root.id || null : null;
  const result: FeedbackContext = {
    owner: {
      window_id: ownerId,
      rect: rectOf(root),
      name: safeWindowText(root.getAttribute("aria-label") || root.querySelector(".desk-window-title")?.textContent || "Desk"),
      window_text: safeRenderedText(root),
      hub_row: hubRow,
    },
    selected_element: snapshotElement(target),
    fields,
    selected_tabs: selectedTabs(root),
    scroll: scrolls(root),
    viewport: { width: window.innerWidth, height: window.innerHeight, dpr: window.devicePixelRatio || 1 },
    page: { origin: window.location.origin, path: window.location.pathname },
    desk: deskSnapshot(ownerId),
  };
  if (new TextEncoder().encode(JSON.stringify(result)).byteLength > MAX_CONTEXT_BYTES)
    throw new Error("Feedback context is too large to save.");
  return result;
}

function throwIfCaptureAborted(signal?: AbortSignal): void {
  if (!signal?.aborted) return;
  const error = new Error("Feedback capture was cancelled.");
  error.name = "AbortError";
  throw error;
}

function captureStep<T>(work: Promise<T>, signal?: AbortSignal): Promise<T> {
  if (!signal) return work;
  return new Promise<T>((resolve, reject) => {
    const aborted = () => {
      try { throwIfCaptureAborted(signal); } catch (error) { reject(error); }
    };
    if (signal.aborted) aborted();
    else signal.addEventListener("abort", aborted, { once: true });
    work.then(
      (value) => { signal.removeEventListener("abort", aborted); resolve(value); },
      (error) => { signal.removeEventListener("abort", aborted); reject(error); },
    );
  });
}

function computedStyleText(style: CSSStyleDeclaration, properties: string[]): string {
  let result = "";
  for (const property of properties) {
    const value = style.getPropertyValue(property);
    if (value) result += `${property}: ${value};`;
  }
  return result;
}

function clearPositionOffsets(style: CSSStyleDeclaration): void {
  for (const property of [
    "inset",
    "inset-block",
    "inset-block-start",
    "inset-block-end",
    "inset-inline",
    "inset-inline-start",
    "inset-inline-end",
    "top",
    "right",
    "bottom",
    "left",
  ]) style.removeProperty(property);
}

function frozenClone(root: Element, signal?: AbortSignal): {
  wrapper: HTMLDivElement;
  clone: HTMLElement;
} {
  throwIfCaptureAborted(signal);
  const source = [root, ...Array.from(root.querySelectorAll("*"))];
  const clone = root.cloneNode(true) as HTMLElement;
  const copies = [clone, ...Array.from(clone.querySelectorAll("*"))];
  const rootStyle = getComputedStyle(root);
  const standardStyleProperties = Array.from(rootStyle).filter((property) => !property.startsWith("--"));
  const pseudoStyleProperties = standardStyleProperties.includes("content")
    ? standardStyleProperties
    : [...standardStyleProperties, "content"];
  const captureClassPrefix = `hs-feedback-pseudo-${++frozenCaptureSequence}`;
  const pseudoRules: string[] = [];
  const copyComputedStyle = (
    from: Element,
    to: HTMLElement | SVGElement,
    includeCustomProperties = false,
    computed?: CSSStyleDeclaration,
  ) => {
    const style = computed ?? (from === root ? rootStyle : getComputedStyle(from));
    const properties = includeCustomProperties
      ? Array.from(style)
      : standardStyleProperties;
    to.style.cssText = computedStyleText(style, properties);
  };
  const freezePseudoStyles = (from: Element, to: Element, nodeIndex: number) => {
    for (const pseudo of ["::before", "::after"] as const) {
      throwIfCaptureAborted(signal);
      const style = getComputedStyle(from, pseudo);
      const content = style.getPropertyValue("content");
      if (!content || content === "none") continue;
      const className = `${captureClassPrefix}-${nodeIndex}-${pseudo.slice(2)}`;
      to.classList.add(className);
      pseudoRules.push(`.${className}${pseudo}{${computedStyleText(style, pseudoStyleProperties)}}`);
    }
  };
  const preserveScroll = (from: HTMLElement, to: HTMLElement) => {
    throwIfCaptureAborted(signal);
    if (!from.scrollTop && !from.scrollLeft) return;
    to.scrollTop = from.scrollTop;
    to.scrollLeft = from.scrollLeft;
    to.style.overflow = "hidden";
    for (const child of Array.from(to.children)) {
      throwIfCaptureAborted(signal);
      if (!(child instanceof HTMLElement)) continue;
      const transform = child.style.transform;
      child.style.transform = `translate(${-from.scrollLeft}px, ${-from.scrollTop}px)${transform && transform !== "none" ? ` ${transform}` : ""}`;
    }
  };
  // A subtree that draws nothing (display: none) leaves the image. A loaded
  // Settings window at 1440 holds about 1,400 elements and most of them are
  // closed panes; freezing ~370 properties on each of them blocked the page
  // for about a second before the strip showed "Capturing".
  const dropped = new Set<Element>();
  source.forEach((element, index) => {
    throwIfCaptureAborted(signal);
    const copy = copies[index];
    if (!copy) return;
    if (element.parentElement && dropped.has(element.parentElement)) {
      dropped.add(element);
      return;
    }
    if (element.matches("[data-ui-feedback], [data-ui-feedback] *") || isSensitiveElement(element)) {
      copy.remove();
      dropped.add(element);
      return;
    }
    const style = element === root ? rootStyle : getComputedStyle(element);
    if (
      index > 0
      && element instanceof HTMLElement
      && !(element instanceof HTMLStyleElement)
      && style.getPropertyValue("display") === "none"
    ) {
      copy.remove();
      dropped.add(element);
      return;
    }
    if (copy instanceof HTMLElement || copy instanceof SVGElement) copyComputedStyle(element, copy, index === 0, style);
    freezePseudoStyles(element, copy, index);
    if (element instanceof HTMLInputElement && copy instanceof HTMLInputElement) {
      copy.value = element.value;
      copy.checked = element.checked;
    } else if (element instanceof HTMLCanvasElement && copy instanceof HTMLCanvasElement) {
      copy.width = element.width;
      copy.height = element.height;
      copy.getContext("2d")?.drawImage(element, 0, 0);
    } else if (element instanceof HTMLTextAreaElement && copy instanceof HTMLTextAreaElement) {
      copy.value = element.value;
      copy.textContent = element.value;
    } else if (element instanceof HTMLSelectElement && copy instanceof HTMLSelectElement) {
      copy.selectedIndex = element.selectedIndex;
      Array.from(copy.options).forEach((option, optionIndex) => {
        option.selected = element.options[optionIndex]?.selected ?? false;
      });
    } else if (element instanceof HTMLElement && copy instanceof HTMLElement && element.isContentEditable) {
      copy.innerText = element.innerText;
    }
  });
  source.forEach((element, index) => {
    throwIfCaptureAborted(signal);
    const copy = copies[index];
    if (dropped.has(element)) return;
    if (element instanceof HTMLElement && copy instanceof HTMLElement) preserveScroll(element, copy);
  });
  if (pseudoRules.length > 0) {
    const pseudoStyle = document.createElement("style");
    pseudoStyle.textContent = pseudoRules.join("");
    clone.appendChild(pseudoStyle);
  }
  const wrapper = document.createElement("div");
  const rect = root.getBoundingClientRect();
  const shell = root.closest(".desk-next");
  if (shell instanceof HTMLElement) {
    wrapper.className = shell.className;
    for (const attribute of Array.from(shell.attributes)) {
      if (attribute.name.startsWith("data-")) wrapper.setAttribute(attribute.name, attribute.value);
    }
    copyComputedStyle(shell, wrapper, true);
  }
  clearPositionOffsets(wrapper.style);
  wrapper.style.position = "fixed";
  wrapper.style.left = "-100000px";
  wrapper.style.top = "0";
  wrapper.style.right = "auto";
  wrapper.style.bottom = "auto";
  wrapper.style.width = `${Math.max(1, Math.round(rect.width))}px`;
  wrapper.style.height = `${Math.max(1, Math.round(rect.height))}px`;
  wrapper.style.pointerEvents = "none";
  wrapper.style.overflow = "hidden";
  wrapper.style.background = getComputedStyle(document.body).backgroundColor;
  clone.style.width = `${Math.max(1, Math.round(rect.width))}px`;
  clone.style.height = `${Math.max(1, Math.round(rect.height))}px`;
  clearPositionOffsets(clone.style);
  clone.style.position = "relative";
  clone.style.left = "0";
  clone.style.top = "0";
  clone.style.right = "auto";
  clone.style.bottom = "auto";
  clone.style.transform = "none";
  clone.style.margin = "0";
  clone.style.boxSizing = rootStyle.boxSizing;
  wrapper.appendChild(clone);
  return { wrapper, clone };
}

export async function captureWindowPng(root: Element, signal?: AbortSignal): Promise<string> {
  let frozen: ReturnType<typeof frozenClone> | null = null;
  try {
    throwIfCaptureAborted(signal);
    frozen = frozenClone(root, signal);
    throwIfCaptureAborted(signal);
    const { toPng } = await captureStep(import("html-to-image"), signal);
    throwIfCaptureAborted(signal);
    document.body.appendChild(frozen.wrapper);
    if (document.fonts?.ready) await captureStep(document.fonts.ready, signal);
    throwIfCaptureAborted(signal);
    const dataUrl = await captureStep(toPng(frozen.clone, {
      cacheBust: true,
      fetchRequestInit: signal ? { signal } : undefined,
      includeStyleProperties: [],
      pixelRatio: Math.min(window.devicePixelRatio || 1, 2),
      filter: (node) => {
        throwIfCaptureAborted(signal);
        return !(node instanceof Element && (isSensitiveElement(node) || node.closest("[data-ui-feedback]")));
      },
    }), signal);
    throwIfCaptureAborted(signal);
    const prefix = "data:image/png;base64,";
    if (!dataUrl.startsWith(prefix)) throw new Error("PNG capture did not return an image.");
    return dataUrl.slice(prefix.length);
  } catch (error) {
    throwIfCaptureAborted(signal);
    if (error instanceof Error) throw error;
    throw new Error("Window image failed. Try again.");
  } finally {
    frozen?.wrapper.remove();
  }
}

export async function canonicalWindowRow(id: string | null): Promise<unknown | null> {
  if (!id) return null;
  try {
    const result = await apiFetch<{ windows?: unknown[] }>("/api/desk/windows");
    return result.windows?.find((row) => row && typeof row === "object" && (row as { id?: unknown }).id === id) ?? null;
  } catch {
    return null;
  }
}

function base64(bytes: ArrayBuffer): string {
  const values = new Uint8Array(bytes);
  let output = "";
  for (let offset = 0; offset < values.length; offset += 0x8000) {
    output += String.fromCharCode(...values.subarray(offset, offset + 0x8000));
  }
  return btoa(output);
}

export function audioBase64(wav: ArrayBuffer): string {
  return base64(wav);
}

function newHexId(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export function newFeedbackId(): string {
  try {
    return newHexId();
  } catch {
    return `${Date.now().toString(16)}${Math.random().toString(16).slice(2)}`.padEnd(32, "0").slice(0, 32);
  }
}

export async function startFeedbackAudio(signal?: AbortSignal): Promise<FeedbackAudioSession> {
  if (signal?.aborted) throw new Error("Feedback capture was cancelled.");
  if (openMicRunning() || holdOwnsFloor() || micPhase() === "segmenting" || micPhase() === "held") {
    throw new Error("The microphone is already in use.");
  }
  await claimAudioFloor();
  if (signal?.aborted) {
    if (!openMicRunning() && !holdOwnsFloor()) await releaseAudioFloor();
    throw new Error("Feedback capture was cancelled.");
  }
  // The floor request yields. A same-tab hold or open mic can start during
  // that wait; never preempt the capture that won the race.
  if (openMicRunning() || holdOwnsFloor() || micPhase() === "segmenting" || micPhase() === "held") {
    throw new Error("The microphone is already in use.");
  }
  let token: HoldToken | undefined;
  let stopped = false;
  let floorLost = false;
  let canceled = false;
  let pendingRelease = false;
  let heartbeat: ReturnType<typeof setInterval> | null = null;
  let floorListener: (() => void) | null = null;
  let completed: CapturedAudio | null = null;
  let pending: Promise<HoldToken>;
  const stopHeartbeat = () => {
    if (heartbeat !== null) clearInterval(heartbeat);
    heartbeat = null;
  };
  const release = () => {
    if (pendingRelease) return;
    pendingRelease = true;
    stopHeartbeat();
    void releaseAudioFloor();
  };
  const releaseWhenFree = () => {
    // A late completion must never release a successor's same-tab hold.
    if (openMicRunning() || holdOwnsFloor()) {
      pendingRelease = true;
      stopHeartbeat();
      return;
    }
    release();
  };
  const onAbort = () => {
    canceled = true;
    if (token !== undefined) {
      abortHold(token);
      releaseWhenFree();
    } else {
      releaseWhenFree();
    }
  };
  const stopOwnHold = () => {
    if (token !== undefined) {
      if (!stopped) {
        stopped = true;
        const held = endHold(token);
        if (held) {
          completed = {
            wav: toWav16kMono(held.chunks, held.rate),
            durationMs: Math.round((held.chunks.reduce((n, chunk) => n + chunk.length, 0) / held.rate) * 1000),
          };
        }
      }
      releaseWhenFree();
    }
    return completed;
  };

  try {
    pending = beginHold(signal);
    signal?.addEventListener("abort", onAbort, { once: true });
    heartbeat = setInterval(() => {
      void renewAudioFloor().then((kept) => {
        if (kept || stopped || canceled) return;
        floorLost = true;
        const captured = stopOwnHold();
        if (captured) floorListener?.();
      });
    }, FLOOR_RENEW_MS);
    token = await pending;
    if (canceled) {
      abortHold(token);
      releaseWhenFree();
      throw new Error("Feedback capture was cancelled.");
    }
  } catch (error) {
    if (token !== undefined) abortHold(token);
    if (token === undefined || !holdOwnsFloor()) releaseWhenFree();
    throw error;
  }

  return {
    stop: () => {
      signal?.removeEventListener("abort", onAbort);
      const result = stopOwnHold();
      if (!holdOwnsFloor()) release();
      return result;
    },
    cancel: () => {
      signal?.removeEventListener("abort", onAbort);
      canceled = true;
      if (token !== undefined) {
        abortHold(token);
        releaseWhenFree();
      } else {
        pendingRelease = true;
        stopHeartbeat();
        void releaseAudioFloor();
        void pending.then((lateToken) => {
          abortHold(lateToken);
          releaseWhenFree();
        });
      }
    },
    lost: () => floorLost,
    onFloorLost: (listener) => { floorListener = listener; },
  };
}
