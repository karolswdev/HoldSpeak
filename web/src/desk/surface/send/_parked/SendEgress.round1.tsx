// Parked: the kit completion leading slot owns disclosure and secondary verbs.
/** InspectorForm owns the completion row. Egress is the Send-specific
 * disclosure in that same row, never a second footer or a destination chip. */
function SendEgress({ channel, synced, eg }: { channel: string; synced?: boolean; eg: ReturnType<typeof egressOf> }) {
  const marker = useRef<HTMLSpanElement>(null);
  const [seat, setSeat] = useState<Element | null>(null);
  useLayoutEffect(() => {
    setSeat(marker.current?.closest(".surface-inspector-form")?.querySelector(":scope > .surface-inspector-actions") ?? null);
  }, []);
  return (
    <>
      <span ref={marker} hidden />
      {seat && (channel !== "file" || synced)
        ? createPortal(<EgressChip label={safeSendText(eg.label)} scope={eg.scope} title={safeSendText(eg.title ?? "")} />, seat)
        : null}
    </>
  );
}
