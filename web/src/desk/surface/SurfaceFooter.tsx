import { createPortal } from "react-dom";
import { useContext, type ReactNode } from "react";
import { FootSlotContext } from "./foot";
import "./surface-footer.css";

export function SurfaceFooter({
  egress,
  receipt,
  verbs,
}: {
  egress?: ReactNode;
  receipt?: ReactNode;
  verbs?: ReactNode;
}) {
  // HS-129-05 — the layout sits inside the frame-owned foot so its narrow
  // container query can reflow the slots without making another footer root.
  const contents = (
    <div className="surface-footer-layout">
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
