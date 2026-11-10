// Parked 2026-11-09: requests.ts owns Walk and agent speech.
// Original Walk effects, retained for reference.
/*
  // The guide speaks. A step that will ask says its words with the question
  // when the bar opens (one utterance: the question never cuts the words).
  const sheetOpen = !done && !!step?.ask && stage.ready && !stage.line;
  const bubbleNow = !done && stage.ready && stage.line ? stage.line : done ? "" : spoken;
  useEffect(() => {
    if (!voiceRef.current || !begun || !step || !bubbleNow) return;
    if (step.ask && !step.press && !stage.line) return;
    if (saidRef.current === bubbleNow) return;
    saidRef.current = bubbleNow;
    speak(bubbleNow);
  }, [bubbleNow, begun, step, stage.line]);
  useEffect(() => {
    if (!voiceRef.current || !sheetOpen || !step?.ask) return;
    const before = spoken && saidRef.current !== spoken ? `${spoken} ` : "";
    saidRef.current = spoken;
    speak(`${before}${step.ask.question}`);
  }, [sheetOpen, step, spoken]);
*/
export {};
