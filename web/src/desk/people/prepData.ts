import { apiFetch } from "../../lib/api";

export type PrepCalendarEvent = {
  id: string;
  uid: string;
  title: string;
  starts_at: string;
  ends_at: string;
  source_id: string;
  source_label: string;
};

export type PrepAgendaItem = {
  id: string;
  session_id?: string | null;
  relationship_id?: string | null;
  body: string;
  visibility?: string;
  state?: string;
  rolled_from_id?: string | null;
};

export type PrepMeetingAction = {
  id: string;
  meeting_id: string;
  task: string;
  owner: string | null;
  due: string | null;
  delegated_at: string | null;
  meeting_title?: string | null;
  meeting_started_at?: string;
  calendar_event_id?: string | null;
};

export type PrepProject = {
  id: string;
  name: string;
};

export type PeopleBriefWire = {
  calendar_link_suggestions?: PrepCalendarEvent[] | null;
  next_one_on_one?: PrepCalendarEvent | null;
  agenda_items?: PrepAgendaItem[] | null;
  open_meeting_actions?: PrepMeetingAction[] | null;
  projects?: PrepProject[] | null;
};

export type PeoplePrepData = {
  calendarLinkSuggestions: PrepCalendarEvent[];
  nextOneOnOne: PrepCalendarEvent | null;
  agenda: PrepAgendaItem[];
  openMeetingActions: PrepMeetingAction[];
  projects: PrepProject[];
};

/** Compose the People brief into the data contract the Prep face consumes. */
export function composePeoplePrep(brief: PeopleBriefWire): PeoplePrepData {
  return {
    calendarLinkSuggestions: [...(brief.calendar_link_suggestions ?? [])],
    nextOneOnOne: brief.next_one_on_one ?? null,
    agenda: [...(brief.agenda_items ?? [])],
    openMeetingActions: [...(brief.open_meeting_actions ?? [])],
    projects: [...(brief.projects ?? [])],
  };
}

/** Read the existing transient People brief; this function does not write. */
export async function readPeoplePrep(
  relationshipId: string,
  fetcher: typeof apiFetch = apiFetch,
): Promise<PeoplePrepData> {
  const response = await fetcher<{ brief: PeopleBriefWire }>(
    `/api/people/relationships/${encodeURIComponent(relationshipId)}/brief`,
  );
  return composePeoplePrep(response.brief ?? {});
}
