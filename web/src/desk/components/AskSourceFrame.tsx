import { Button } from "../../components/signal/Signal";
import { FoldGadget, PaneActions, ReadingDocument } from "../surface";

/** The source frame shared by Ask and its Components specimen. Its owner
 * supplies the quote and verbs; this view holds no source or thread state. */
export function AskSourceFrame({ quote, open, onToggle, onClear, onBack }: {
  quote: string;
  open: boolean;
  onToggle: (open: boolean) => void;
  onClear: () => void;
  onBack?: () => void;
}) {
  const hasQuote = Boolean(quote.trim());
  return <div data-testid="ask-selected-passage" data-feedback-redact="true">
    <FoldGadget title={hasQuote ? "Selected text" : "Source"} open={open} onToggle={onToggle}>
      {hasQuote ? <ReadingDocument>{quote}</ReadingDocument> : null}
      {hasQuote ? <PaneActions>
        <Button dense variant="ghost" onClick={onClear}>Clear quote</Button>
      </PaneActions> : null}
    </FoldGadget>
    {onBack ? <PaneActions>
      <Button dense variant="ghost" onClick={onBack}>Back to note</Button>
    </PaneActions> : null}
  </div>;
}
