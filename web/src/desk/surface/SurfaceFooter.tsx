import { createPortal } from "react-dom";
import { useContext, type ReactNode } from "react";
import { FootSlotContext } from "./foot";
import "./surface-footer.css";

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
  // HS-129-05 — the layout sits inside the frame-owned foot so its narrow
  // container query can reflow the slots without making another footer root.
  const contents = (
    <div className={className ? `surface-footer-layout ${className}` : "surface-footer-layout"}>
      <div className="surface-footer-egress">{egress}</div>
      <div className="surface-footer-receipt">{receipt}</div>
      <div className="surface-footer-verbs">{verbs}</div>
    </div>
  );
  const target = useContext(FootSlotContext);
  return target
    ? createPortal(contents, target)
    : <footer className="surface-footer">{contents}</footer>;
}
