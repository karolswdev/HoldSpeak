// Parked: Prepared exists as a tab only while a selected waiting row exists.
              ) : (
                <InspectorForm
                  completion={{
                    ...ordinaryCompletion,
                    primary: { ...ordinaryCompletion.primary, disabled: true },
                  }}
                  rows={[
                    {
                      label: "Prepared",
                      control: <span>No prepared sends</span>,
                    },
                  ]}
                />
              )}
