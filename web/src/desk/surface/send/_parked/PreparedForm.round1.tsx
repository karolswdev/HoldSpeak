// Parked: shared SendFace replaces the frozen-only form and discard band.
        <InspectorForm
          completion={{
            cancel: () => onBack?.(),
            cancelDisabled: busy,
            cancelTestId: "send-back",
            primary: {
              label: o.kind === "lost" ? SEND_WORDS.retry : SEND_WORDS.send,
              testId: o.kind === "lost" ? "prepared-retry" : "prepared-send",
              busy,
              disabled: dead,
              run: () => void press(docRef, s.id, () => ({ send_id: s.id }), reload, onSettled),
            },
          }}
          notice={
            <>
              <OutcomeLine o={o} />
              {s.state === "dispatching" ? <LatestReceipt s={s} /> : null}
              <PaneActions>
                <Button dense variant="ghost" disabled={busy} data-testid="prepared-discard" onClick={() => setQuestion(revision)}>
                  Discard
                </Button>
                <SendEgress channel={s.channel} synced={dest?.synced} eg={eg} />
              </PaneActions>
            </>
          }
        >
          <GadgetRow label="Destination">
            <span>{name}</span>
          </GadgetRow>
          <GadgetRow label="Prepared">
            <span data-testid="prepared-by">{byWord(s)}</span>
            <span data-testid="prepared-label">{stateWords(safeSendText(label))}</span>
          </GadgetRow>
          {acc ? (
            <GadgetRow label="Account">
              <StateChip state={acc.state} label={safeSendText(acc.label)} />
            </GadgetRow>
          ) : null}
          <GadgetRow label="Preview" wide>
            <div data-send="inspection" data-testid="prepared-open">
              <PreviewWell preview={previewOf(s.channel, s.target, s.account, s.preview, s.file_path)} testid="prepared-preview" />
            </div>
          </GadgetRow>
        </InspectorForm>