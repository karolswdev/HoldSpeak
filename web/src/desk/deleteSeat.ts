/** PHILO-8-02 round two — how many faces show the delete receipt right now.
 * A delete is offered only where its receipt can be read (UX-CANON A.11):
 * the spatial Floor and the list seat it; the Chair does not. Kept apart
 * from deleteReceipt.tsx so the verb registry can read it without an
 * import cycle. */
let seats = 0;

export function deleteSeatShown(): boolean {
  return seats > 0;
}

/** A face's receipt seat mounted; returns the count after. */
export function seatMounted(): number {
  seats += 1;
  return seats;
}

/** A face's receipt seat unmounted; returns the count after. */
export function seatUnmounted(): number {
  seats = Math.max(0, seats - 1);
  return seats;
}
