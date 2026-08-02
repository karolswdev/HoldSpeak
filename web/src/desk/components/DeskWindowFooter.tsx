import type { ReactNode } from "react";

interface DeskWindowFooterProps {
  status?: ReactNode;
  children?: ReactNode;
}

/** The shared footer rail for content-sized Desk windows. */
export function DeskWindowFooter({ status, children }: DeskWindowFooterProps) {
  return (
    <footer className="desk-pullout-foot">
      {status ? <span className="desk-window-footer-status">{status}</span> : null}
      {children ? (
        <span
          className="desk-window-footer-actions"
          style={{
            display: "inline-flex",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "8px",
            ...(status ? { marginLeft: "auto" } : {}),
          }}
        >
          {children}
        </span>
      ) : null}
    </footer>
  );
}
