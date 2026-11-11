// Parked: Send owns the reader body while it is open; it is no longer below Read.
const _parkedSend = <>
              {sendRequested ? (
            <div id={`meeting-${id}-send`} className="meetings-detail-anchor">
              {summaryIntel?.summary?.trim() ? (
                <MeetingSendWell meetingId={id} title={meetingTitle} onBack={onSendBack}
                  startedAt={String((detail ?? meeting)?.started_at ?? "") || null} />
              ) : (
                <div role="status">Summary unavailable <Button dense variant="ghost" onClick={onDeleted}>Retry</Button></div>
              )}
            </div>
          ) : null}

</>;
