import { createPortal } from "react-dom";
import {
  Children,
  Fragment,
  isValidElement,
  useContext,
  useRef,
  useState,
  type ReactElement,
  type ReactNode,
} from "react";
import { FootSlotContext } from "./foot";
import { Button } from "../../components/signal/Signal";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import { useCompactViewport } from "../useCompactViewport";
import "./surface-footer.css";

type FooterVerb = {
  node: ReactElement;
  label: string;
  primary: boolean;
  disabled: boolean;
  onClick: (...args: never[]) => void;
};

function verbLabel(node: ReactElement): string {
  const props = node.props as { "aria-label"?: string; children?: ReactNode };
  if (props["aria-label"]) return props["aria-label"];
  const text = Children.toArray(props.children)
    .filter((child): child is string | number => typeof child === "string" || typeof child === "number")
    .join(" ")
    .trim();
  return text || "Action";
}

function collectVerbs(node: ReactNode, out: FooterVerb[], opaque: ReactNode[]): void {
  for (const child of Children.toArray(node)) {
    if (!isValidElement(child)) {
      if (child != null) opaque.push(child);
      continue;
    }
    const props = child.props as { children?: ReactNode; onClick?: unknown; variant?: string; disabled?: boolean; loading?: boolean };
    if (child.type === Fragment) {
      collectVerbs(props.children, out, opaque);
      continue;
    }
    // Only the library Button can be safely moved into the compact More
    // menu. A custom component may hide its action below this element, and
    // a submit-only control may rely on its surrounding form, so both stay
    // opaque and in their original position.
    if (child.type === Button && typeof props.onClick === "function") {
      out.push({
        node: child,
        label: verbLabel(child),
        primary: props.variant === "primary",
        disabled: Boolean(props.disabled || props.loading),
        onClick: props.onClick as (...args: never[]) => void,
      });
      continue;
    }
    // Span/div wrappers are layout only. Walk through them so a face can
    // group its library Buttons without making the whole group opaque.
    // Keep other native elements intact: their submit/keyboard semantics
    // belong to the element and its owner.
    if (child.type === "span" || child.type === "div") {
      collectVerbs(props.children, out, opaque);
      continue;
    }
    // A submit-only Button or a custom action component may keep its handler
    // below this element. React cannot safely inspect that rendered tree, so
    // retain the original node where the owner can still use its action.
    opaque.push(child);
  }
}

export function SurfaceFooter({
  egress,
  receipt,
  verbs,
  className,
}: {
  egress?: ReactNode;
  receipt?: ReactNode;
  verbs?: ReactNode;
  /** HS-169-02 — a face-scoped hook: the layout is portaled into the
   *  frame's foot slot, so a face cannot reach it by descendant selector. */
  className?: string;
}) {
  const compact = useCompactViewport();
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLButtonElement | null>(null);
  const footerVerbs: FooterVerb[] = [];
  const opaqueVerbs: ReactNode[] = [];
  collectVerbs(verbs, footerVerbs, opaqueVerbs);
  const primary = footerVerbs.find((verb) => verb.primary) ?? footerVerbs[0];
  const extras = primary ? footerVerbs.filter((verb) => verb !== primary) : footerVerbs;
  const compactVerbs = compact ? (
    <>
      {primary ? primary.node : null}
      {extras.length ? (
        <Button
          ref={moreRef}
          dense
          variant="ghost"
          aria-label="More actions"
          aria-expanded={moreOpen}
          onClick={() => setMoreOpen((open) => !open)}
        >
          More
        </Button>
      ) : null}
      {moreOpen && moreRef.current ? (
        <WorkMenu
          label="More actions"
          anchor="above"
          x={moreRef.current.getBoundingClientRect().left}
          y={moreRef.current.getBoundingClientRect().top}
          entries={extras.map((verb, index): WorkMenuEntry => ({
            type: "item",
            id: `surface-footer-action-${index}`,
            label: verb.label,
            ghost: verb.disabled ? "Busy" : undefined,
            onSelect: () => verb.onClick(),
          }))}
          onClose={() => setMoreOpen(false)}
        />
      ) : null}
      {opaqueVerbs.length ? (
        <span className="surface-footer-opaque-actions">{opaqueVerbs}</span>
      ) : null}
    </>
  ) : verbs;
  // HS-129-05 — the layout sits inside the frame-owned foot so its narrow
  // container query can reflow the slots without making another footer root.
  const contents = (
    <div className={className ? `surface-footer-layout ${className}` : "surface-footer-layout"}>
      <div className="surface-footer-egress">{egress}</div>
      <div className="surface-footer-receipt">{receipt}</div>
      <div className="surface-footer-verbs">{compactVerbs}</div>
    </div>
  );
  const target = useContext(FootSlotContext);
  return target
    ? createPortal(contents, target)
    : <footer className="surface-footer">{contents}</footer>;
}
