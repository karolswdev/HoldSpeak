// HS-172-07 — PEOPLE section in the Room.
//
// Board: RoomPeople (640), RoomPeoplePhone (393).
// Lead slot = two-letter monogram in muted emblem style.
// Primary = display name as stored.
// Caption tokens: N PRS WAITING · N ASSIGNMENT(S) OVERDUE (warning color).
// Tokens absent at zero. Section absent when no resolved people.
// Trailing: Open (ghost) opens the People window on that relationship.
import { useEffect, useState } from "react";
import {
  SurfaceSection,
  SurfaceLedger,
  SurfaceLedgerRow,
} from "../../desk/surface";
import { Button } from "../../components/signal/Signal";
import { openSurfaceOr } from "../../desk/shell";
import { countToken, countLabel } from "../../desk/surface/count";
import { fetchRoomPeople, type RoomPersonItem } from "./api";

/* ── Monogram ── */

/**
 * Two-letter monogram from a display name.
 * Takes the first letter of the first two words.
 * Never derives a first name or pronoun from the display name.
 */
export function monogram(displayName: string): string {
  const words = displayName.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return "";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

/* ── Token builder ── */

export type PersonTokens = {
  prsWaiting: string | null;
  assignmentsOverdue: string | null;
};

/**
 * Build the caption tokens for a person row.
 * Absent at zero. Overdue in warning color.
 */
export function buildPersonTokens(person: RoomPersonItem): PersonTokens {
  return {
    prsWaiting: countToken(person.prs_waiting, "PR WAITING", "PRS WAITING"),
    assignmentsOverdue: countToken(
      person.assignments_overdue,
      "ASSIGNMENT OVERDUE",
      "ASSIGNMENTS OVERDUE",
    ),
  };
}

/* ── Component ── */

export function RoomPeopleSection({
  projectId,
}: {
  projectId: string;
}) {
  const [people, setPeople] = useState<RoomPersonItem[]>([]);

  useEffect(() => {
    let cancelled = false;
    void fetchRoomPeople(projectId).then((items) => {
      if (!cancelled) setPeople(items);
    }).catch(() => {
      if (!cancelled) setPeople([]);
    });
    return () => { cancelled = true; };
  }, [projectId]);

  // Section absent at zero (UX-CANON A.8)
  if (people.length === 0) return null;

  return (
    <SurfaceSection
      label={countLabel("PEOPLE", people.length)}
    >
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows">
          {people.map((person) => {
            const tokens = buildPersonTokens(person);
            const mono = monogram(person.display_name);
            return (
              <SurfaceLedgerRow
                key={person.relationship_id}
                lead={mono}
                primary={
                  <span className="room-people-primary">
                    <span className="surface-primary">{person.display_name}</span>
                    {tokens.prsWaiting ? (
                      <span className="surface-token room-people-tok">
                        {tokens.prsWaiting}
                      </span>
                    ) : null}
                    {tokens.prsWaiting && tokens.assignmentsOverdue ? (
                      <span className="surface-token room-people-sep"> · </span>
                    ) : null}
                    {tokens.assignmentsOverdue ? (
                      <span className="surface-token room-people-tok room-people-overdue" data-tone="warn">
                        {tokens.assignmentsOverdue}
                      </span>
                    ) : null}
                  </span>
                }
                wrap
                open
                expands={false}
                trailing={
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => {
                      openSurfaceOr(
                        "open-people",
                        "/",
                        `people:${person.relationship_id}`,
                      );
                    }}
                    data-testid="room-people-open"
                  >
                    Open
                  </Button>
                }
                data-testid="room-people-row"
              />
            );
          })}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}
