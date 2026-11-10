import { Fragment, isValidElement, type ReactNode } from "react";

/** Empty placeholders do not occupy a fact or a control seat. */
export function hasWords(value: ReactNode): boolean {
  if (value == null || typeof value === "boolean") return false;
  if (typeof value === "string") return Boolean(value.trim());
  if (Array.isArray(value)) return value.some(hasWords);
  if (isValidElement<{ children?: ReactNode }>(value) && (typeof value.type === "string" || value.type === Fragment)) {
    return ["video", "audio", "img", "canvas", "input", "select", "textarea", "button"].includes(String(value.type)) || hasWords(value.props.children);
  }
  return true;
}
