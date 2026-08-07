import type { ReactNode } from "react";
import { SurfaceFooter } from "../surface/SurfaceFooter";

interface DeskWindowFooterProps {
  status?: ReactNode;
  children?: ReactNode;
}

/** The shared footer rail for content-sized Desk windows. */
export function DeskWindowFooter({ status, children }: DeskWindowFooterProps) {
  return (
    <SurfaceFooter
      receipt={status ? <span className="desk-window-footer-status">{status}</span> : null}
      verbs={children ? <span className="desk-window-footer-actions">{children}</span> : null}
    />
  );
}
