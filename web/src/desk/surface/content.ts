import { Children, Fragment, isValidElement, type ReactNode } from "react";

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

/** Text already present in a declaration, for measurement and short labels. */
export function contentText(value: ReactNode, between = ""): string {
  return Children.toArray(value).map(child => isValidElement<{children?: ReactNode}>(child)
    ? contentText(child.props.children, between)
    : typeof child === "string" || typeof child === "number" ? String(child) : "").join(between);
}

/** Only one to three words belong to the tracked-capitals label species. */
export function labelCaption(value: ReactNode): "short" | "content" {
  const words = contentText(value, " ").trim().split(/\s+/).filter(Boolean);
  return words.length > 0 && words.length <= 3 ? "short" : "content";
}
