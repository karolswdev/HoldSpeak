// HS-104-05 — one receipt line in the egress-badge tradition:
// maximal honesty, minimal ink. Renders nothing until the hub
// answers; renders only the tiers the hub could vouch for.
import { useEffect, useState } from "react";
import { fetchReceipt, receiptSegments, type SessionReceipt } from "../receipts";

export function ReceiptLine({ sessionKey }: { sessionKey: string }) {
  const [receipt, setReceipt] = useState<SessionReceipt | null>(null);

  useEffect(() => {
    let live = true;
    void fetchReceipt(sessionKey).then((r) => {
      if (live) setReceipt(r);
    });
    return () => {
      live = false;
    };
  }, [sessionKey]);

  if (!receipt) return null;
  const segments = receiptSegments(receipt);
  if (segments.length === 0) return null;
  return (
    <p className="desk-receipt-line" title="Session receipt, hub records">
      {segments.join(" · ")}
    </p>
  );
}
