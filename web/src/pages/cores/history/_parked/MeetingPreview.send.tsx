// Parked: a long-form PreferenceWell released the bounded Send tab and scrolled completion out of view.
  if (tab === "send") return <PreferencePane label="Send meeting" testId="meeting-list-preview"><PreferenceWell>
    <MeetingSendWellLazy meetingId={id} title={String(meeting.title || "Meeting")} startedAt={String(meeting.started_at ?? meeting.created_at ?? "")} onBack={() => setTab("summary")} />
  </PreferenceWell></PreferencePane>;
