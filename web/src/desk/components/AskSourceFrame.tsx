import { Button } from "../../components/signal/Signal";
import { FoldGadget } from "../surface/gadgets";
import "./AskSourceFrame.css";

/** The source frame shared by Ask and its Components specimen. Its owner
 * supplies the quote and verbs; this view holds no source or thread state. */
export function AskSourceFrame({ quote, open, onToggle, onClear, onBack }: {
  quote: string;
  open: boolean;
  onToggle: (open: boolean) => void;
  onClear: () => void;
  onBack: () => void;
}) {
  const hasQuote = Boolean(quote.trim());
  return <div className="desk-ask-passage" data-testid="ask-selected-passage">
    <FoldGadget title={hasQuote ? "Selected text" : "Source"} open={open} onToggle={onToggle}>
      {hasQuote ? <blockquote>{quote}</blockquote> : null}
      {hasQuote ? <div className="desk-ask-selection-verbs">
        <Button dense variant="ghost" onClick={onClear}>Clear quote</Button>
      </div> : null}
    </FoldGadget>
    <div className="desk-ask-selection-verbs">
      <Button dense variant="ghost" onClick={onBack}>Back to Thought</Button>
    </div>
  </div>;
}
