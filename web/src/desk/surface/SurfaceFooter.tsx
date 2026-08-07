import type { ReactNode } from "react";
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
  return (
    <footer className="surface-footer">
      <div className="surface-footer-egress">{egress}</div>
      <div className="surface-footer-receipt">{receipt}</div>
      <div className="surface-footer-verbs">{verbs}</div>
    </footer>
  );
}
