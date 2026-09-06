import { useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { countToken } from "../surface";
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

  const whyLabel = countToken(receiptIds?.length ?? 0, "WHY", "WHY");
  if (!whyLabel) return null;
  return (
    <Button
      dense
      variant="ghost"
      className="why-control"
      aria-label={`${whyLabel} governing decision receipt${(receiptIds?.length ?? 0) === 1 ? "" : "s"}`}
      onClick={(event) => {
        event.stopPropagation();
        openIntelligence({ view: "receipts", receiptWorkRef: `${workType}:${workRef}`, whyOnly: true });
      }}
    >
      {whyLabel}
    </Button>
  );
}
