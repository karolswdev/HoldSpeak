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
  const contents = (
    <>
      <div className="surface-footer-egress">{egress}</div>
      <div className="surface-footer-receipt">{receipt}</div>
      <div className="surface-footer-verbs">{verbs}</div>
    </>
  );
  const target = useContext(FootSlotContext);
  return target
    ? createPortal(contents, target)
    : <footer className="surface-footer">{contents}</footer>;
}
