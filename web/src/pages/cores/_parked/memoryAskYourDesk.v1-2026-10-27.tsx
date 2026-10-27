// PARKED (Window Program W2-ASKWELLS, 2026-10-27): Memory's own "Ask your
// desk" well. Memory's toolbar is now the Ask composer row
// (web/src/desk/components/askFace.tsx AskComposer). Code as it stood in
// MemoryCore.tsx; nothing imports it.
/* eslint-disable */
// @ts-nocheck
function AskYourDesk() {
  const [question, setQuestion] = useState("");
  const ask = useCallback(() => {
    const text = question.trim();
    if (!text) return;
    // No About chip means the Ask window uses the owner's whole desk.
    useDesk.getState().askQuestion(text);
  }, [question]);
  return (
    <span className="memory-ask" data-testid="memory-ask">
      <StringGadget
        label="Ask your desk"
        micLabel="Dictate into your question"
        type="search"
        value={question}
        placeholder="Ask your desk"
        onChange={setQuestion}
        onKeyDown={(event) => { if (event.key === "Enter") ask(); }}
      />
      <Button dense variant="secondary" disabled={!question.trim()} onClick={ask}>
        <ToolGlyph kind="ask" />
        Ask
      </Button>
    </span>
  );
}
