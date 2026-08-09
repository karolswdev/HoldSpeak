import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { openIntelligence } from "../intelligenceNavigation";

type ReceiptLink = { id: string; lifecycle?: string };

/** Compact, honest reason link: it renders only governing decision receipts. */
export function WhyControl({ workType, workRef }: { workType: string; workRef: string }) {
  const [receiptIds, setReceiptIds] = useState<string[] | null>(null);

  useEffect(() => {
    let live = true;
    void apiFetch<ReceiptLink[]>(
      `/api/decision-records/work/${encodeURIComponent(workType)}/${encodeURIComponent(workRef)}`,
    ).then((receipts) => {
      if (!live) return;
      setReceiptIds(
        (Array.isArray(receipts) ? receipts : [])
          .filter((receipt) => receipt.lifecycle === "active")
          .map((receipt) => receipt.id),
      );
    }).catch(() => {
      if (live) setReceiptIds([]);
    });
    return () => { live = false; };
  }, [workRef, workType]);

  if (!receiptIds?.length) return null;
  return (
    <button
      type="button"
      className="desk-chip quiet why-control"
      aria-label={`Why: ${receiptIds.length} governing decision receipt${receiptIds.length === 1 ? "" : "s"}`}
      onClick={(event) => {
        event.stopPropagation();
        openIntelligence({ view: "receipts", receiptWorkRef: `${workType}:${workRef}`, whyOnly: true });
      }}
    >
      WHY {receiptIds.length}
    </button>
  );
}
