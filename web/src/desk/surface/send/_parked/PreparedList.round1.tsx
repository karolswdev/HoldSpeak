// Parked: prepared selection uses the same Destination pop-up, with saved send ids.
              {waiting.length > 1 ? (
                <ListView
                  label="Prepared sends"
                  headerless
                  rows={waiting.map((s) => ({
                    id: s.id,
                    kind: "note",
                    name: safeSendText(s.destination_name ?? "Destination"),
                  }))}
                  selectedId={preparedPick?.id}
                  onSelect={(id) => {
                    if (!locked) {
                      store.preparedOpen.set(ref, id);
                      bump();
                    }
                  }}
                />
              ) : null}
