// Parked: shared SendFace replaces ordinary-only rows and preview verbs.
            <InspectorForm
              completion={ordinaryCompletion}
              notice={
                <>
                  {receipt}
                  {(orderedDestinations ?? [])
                    .filter((other) => other.id !== d?.id)
                    .map((other) => {
                      const outcome = store.outcomes.get(`${ref}|${other.id}`);
                      const latest = latestFor(sends, other.id);
                      if (!outcome && latest?.state !== "failed" && latest?.state !== "unknown") return null;
                      if (
                        outcome?.kind !== "lost" &&
                        outcome?.kind !== "refused" &&
                        latest?.state !== "failed" &&
                        latest?.state !== "unknown"
                      )
                        return null;
                      return (
                        <PaneActions key={other.id}>
                          <span>{safeSendText(other.name)}</span>
                          {outcome?.kind === "lost" || outcome?.kind === "refused" ? (
                            <OutcomeLine o={outcome} />
                          ) : (
                            <LatestReceipt s={latest} />
                          )}
                        </PaneActions>
                      );
                    })}
                  {d && eg && activePreview ? <SendEgress channel={d.channel} synced={d.synced} eg={eg} /> : null}
                </>
              }
            >
              <GadgetRow label="Destination">
                <CycleGadget
                  label="Destination"
                  value={d?.id ?? ""}
                  disabled={locked}
                  options={[
                    { value: "", label: "Choose a destination" },
                    ...(orderedDestinations ?? [])
                      .filter((d) => d.channel === activeTab)
                      .map((d) => ({
                        value: d.id,
                        label: safeSendText(d.name),
                      })),
                  ]}
                  onChange={select}
                />
              </GadgetRow>
              <GadgetRow label="">
                <Button dense variant="ghost" data-testid="send-add-destination" onClick={() => setAddingDestination(true)}>
                  {SEND_WORDS.addDestination}
                </Button>
              </GadgetRow>
              {acc ? (
                <GadgetRow label="Account">
                  <StateChip state={acc.state} label={safeSendText(acc.label)} />
                </GadgetRow>
              ) : null}
              {orderedDestinations?.length === 0 ? (
                <GadgetRow label="">
                  <span data-testid="send-none">{SEND_WORDS.noDestination}</span>
                </GadgetRow>
              ) : null}
              {d ? (
                <GadgetRow label="Preview" wide>
                  <div data-send="inspection" data-testid="send-open" data-destination={safeSendText(d.name)} data-feedback-redact="true">
                    {!activePreview && !pv ? (
                      <div data-testid="send-preview-loading">
                        <SurfaceState loading />
                      </div>
                    ) : null}
                    {activePreview ? (
                      <PreviewWell
                        preview={activePreview}
                        testid="send-preview"
                        onEdit={() => void edit(d, activePreview)}
                        editBusy={editingPreview === d.id}
                      />
                    ) : null}
                    {!activePreview && pv && "failed" in pv ? (
                      <PreviewFailed pv={pv} onRetry={() => setPreviewTry((n) => n + 1)} />
                    ) : null}
                    {editFailure ? (
                      <span data-testid="send-edit-failed">
                        <DotWord tone="fail">Could not make a note to edit · The preview stays here · Press Edit again</DotWord>
                      </span>
                    ) : null}
                  </div>
                </GadgetRow>
              ) : null}
            </InspectorForm>