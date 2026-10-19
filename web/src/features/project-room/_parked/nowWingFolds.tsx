/* PARKED by Betterment P3 (2026-10-18), "The Now wing: where it stands in
 * ten seconds" (docs/internal/betterment/projects/RECIPE.md P3): these
 * sections left the project window's Now wing. Nothing was deleted: the
 * code is here as it stood in ProjectRoomCore.tsx at origin/main b024b1118,
 * and their data stays on the hub's /room read.
 *
 *  - HealthSection (SIGNALS plate): the head's state and reason say it now.
 *  - RoomFilesSection (Files fold): the project's drawer holds its files.
 *  - SinceYouLookedSection, DecisionsCommitmentsSection (+ RoomDecisionRow):
 *    This week (Decided, Risks, Changed) and Waiting on say them now.
 *  - RoomBriefsSection (Briefs fold): cluster D owns meeting preparation.
 *
 * Not compiled (web/tsconfig.json excludes _parked) and not imported. To
 * bring one back, move it into ProjectRoomCore.tsx, where its helpers
 * (formatTimeShort, formatDueShort, plainWord, the surface kit) live.
 */
// @ts-nocheck
/* eslint-disable */

/* ── HS-173: HEALTH section ── */

function healthToneToState(tone: "green" | "amber" | "red"): "success" | "warning" | "failure" {
  if (tone === "red") return "failure";
  if (tone === "amber") return "warning";
  return "success";
}

function HealthSection({ room, onRetry }: { room: RoomSnapshot; onRetry: () => void }) {
  // A failed health read is named, with Retry. It is never drawn as "no
  // health rows" (the same species as ITEMS UNAVAILABLE).
  if (room.health.state === "degraded") {
    return (
      <SurfaceSection
        label="HEALTH"
        actions={
          <Button dense variant="ghost" onClick={onRetry} data-testid="health-retry">
            Retry
          </Button>
        }
      >
        <span data-testid="health-not-read">
          <StateChip state="unreachable" label="HEALTH NOT READ" />
        </span>
      </SurfaceSection>
    );
  }
  const health = room.health.state === "ok"
    ? (room.health as RoomHealthData & { state: "ok" }) : null;
  if (!health?.signals) return null;

  const rows = resolveHealthRows(health.signals, health.mergeQueueDepth);
  if (rows.length === 0) return null;

  // CHECKED N MIN AGO on the plate's caption (addendum P2-8: one token, not per row)
  const checkedToken = health.checkedAt ? `CHECKED ${humanTime(health.checkedAt)}` : null;
  const tone = (t: "green" | "amber" | "red") => (t === "red" ? "danger" : t === "amber" ? "warn" : "ok");

  // PHILO-17 refit: the signals on a raised steel plate beside the plan:
  // a lamp, the plain name, the facts in mono.
  return (
    <section className="room-plate" data-testid="room-health">
      <header className="room-plate-cap">
        <span>SIGNALS</span>
        {checkedToken ? <span className="room-plate-when" data-testid="health-checked">{checkedToken}</span> : null}
      </header>
      <ul className="room-signals">
        {rows.map((row) => (
          <li key={row.key} className="room-signal" data-tone={tone(row.tone)} data-testid={`health-row-${row.key}`}>
            <span className="room-signal-lamp" data-state={healthToneToState(row.tone)} aria-hidden="true" />
            <span className="room-signal-name">{plainWord(row.label)}</span>
            <span className="room-signal-facts">
              {row.tokens.map((tok, ti) => (
                <span key={ti} data-testid={`health-token-${row.key}-${ti}`}>
                  {tok}{ti < row.tokens.length - 1 ? " ·" : ""}
                </span>
              ))}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}


function RoomFilesSection({ ctrl }: { ctrl: ReturnType<typeof useProjectRoomController> }) {
  const projectId = ctrl.projectId ?? "";
  const { members, failed, retry, settled } = useDrawerMembers(projectId, ctrl);
  useRoomRead("files", settled);
  const [sort, setSort] = useState<ObjectSort>({ key: "name", dir: "asc" });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selected = members.find((m) => m.id === selectedId) ?? null;
  // The Room names its own failed read; FILES names the reads only it makes
  // (A.10: a failed read is never an empty or a complete list).
  const unread = failed.filter((read) => read === "PEOPLE" || read === "RESOURCES");
  // Astra r2 on #1068: Park from Get Info leaves its receipt and Restore HERE
  // (the drawer that drew it is parked), also when FILES is left empty.
  const receipt = useDrawers((s) => s.receipts[projectId]);
  const restore = async (ids: string[]) => {
    const store = useDrawers.getState();
    try {
      for (const id of ids) await restoreMeeting(id);
      store.setReceipt(projectId, restoredOutcome(ids));
      store.changed();
      void useDesk.getState().refresh();
    } catch {
      store.setReceipt(projectId, restoreFailedOutcome(ids));
    }
  };
  // A filed object drags onto an agent (the hand), as the drawer's icons did;
  // no drag at 393 (the hand there is a press on a Room row).
  const compact = useCompactViewport();
  const host = drawerHost(projectId);
  const rowProps = (row: { id: string }) => {
    const member = members.find((m) => m.id === row.id);
    const origin = member && !compact ? handOriginOfRef(member.ref, member.name, projectId) : null;
    return origin && member
      ? handSourceProps({ origin, source: { kind: member.kind, id: member.id, sprite: member.sprite }, host })
      : {};
  };
  // A zero is never said (UX-CANON A.8): no files, nothing failed, no receipt: no section.
  if (!members.length && !unread.length && !receipt) return null;
  const open = (id: string | null) => {
    const member = members.find((m) => m.id === id);
    if (member && memberOpens(member)) openMember(member);
  };
  const onSort = (key: ObjectSortKey) =>
    setSort((now) => (now.key === key ? { key, dir: now.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" }));
  return (
    <SurfaceSection
      label={countLabel("FILES", members.length)}
      data-testid="room-files"
      actions={
        <>
          {unread.length ? (
            <Button dense variant="ghost" onClick={retry} data-testid="room-files-retry">
              Retry
            </Button>
          ) : null}
          <Button dense variant="ghost" disabled={!selected} onClick={() => selected && useDrawers.getState().openInfo(selected, projectId)} data-testid="room-files-info">
            Get Info
          </Button>
          <Button dense variant="ghost" disabled={!selected || !memberOpens(selected)} onClick={() => open(selectedId)} data-testid="room-files-open">
            Open
          </Button>
        </>
      }
    >
      {receipt ? (
        <ParkReceipt outcome={receipt} onRestore={(ids) => void restore(ids)} data-testid="room-files-park-receipt" />
      ) : null}
      <HandConfirmSlot host={host} />
      {unread.length ? (
        <div className="room-files-unread" data-testid="room-files-not-read">
          {unread.map((read) => <StateChip key={read} state="failure" label={`${read} · NOT READ`} />)}
          {members.length ? <StateChip state="warning" label="PARTIAL" /> : null}
        </div>
      ) : null}
      {members.length ? (
        <ObjectList
          label="Files"
          rows={members}
          sort={sort}
          onSort={onSort}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onOpen={open}
          rowProps={rowProps}
        />
      ) : null}
    </SurfaceSection>
  );
}

/* ── RECEIPTS section (HS-174-04: pipeline event receipts with origin badge) ── */


function SinceYouLookedSection({ room }: { room: RoomSnapshot }) {
  if (room.sinceRead.state !== "ok") return null;
  const { readAt, groups } = room.sinceRead;
  const caption = readAt ? "SINCE YOU LOOKED" : "SINCE CREATED";
  const readLabel = readAt ? formatReadAt(readAt) : null;

  if (groups.length === 0) {
    return (
      <SurfaceSection
        label={caption}
        actions={readLabel ? <span className="surface-token room-chip-faint">{readLabel}</span> : undefined}
      >
        <p className="room-empty-line" data-testid="since-read-empty">
          {readAt ? `Nothing since ${formatTimeShort(readAt)}` : "Created just now"}
        </p>
      </SurfaceSection>
    );
  }

  return (
    <SurfaceSection
      label={caption}
      actions={readLabel ? <span className="surface-token room-chip-faint">{readLabel}</span> : undefined}
    >
      {groups.map((group, gi) => (
        <div key={gi} className="room-since-group" data-testid="since-read-group">
          {/* S-2: the design's line is "GitHub · 2 opened · 1 merged" */}
          <p className="room-since-group-head surface-primary">
            {group.source}{group.summary ? ` · ${group.summary}` : ""}
          </p>
          <ul className="room-since-entries">
            {group.entries.map((entry, ei) => (
              <li key={ei} className="room-since-entry">
                <span className="room-since-phrase">{entry.phrase}</span>
                {entry.at ? (
                  <span className="room-since-time">{" · "}{humanTime(entry.at)}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </SurfaceSection>
  );
}

/* ── DECISIONS & COMMITMENTS section ── */

/** PHILO-11-05a (canvas B4, B4b): a decision row is a decision RECORD
 *  (design 6a), also when it is marked `source="meeting"`. The row unfolds
 *  in place and holds the record's SEND well (the seat); it carries
 *  PREPARED ×K when a send waits. Its `Open` opened nothing for a record
 *  (G1, ledgered), so it is withheld; a row with a real URL keeps its Open. */
function RoomDecisionRow({ dec, cells, ...rest }: React.ComponentProps<typeof SurfaceLedgerRow> & {
  dec: { id: string; text: string; kind?: string };
}) {
  const [open, setOpen] = useState(false);
  // PHILO-15 08 (Astra #983 r2): a confirmed ACTION's record is the anchor
  // of its commitment, not a decision: it reads "Action:", says ACTION, and
  // carries no decision Send well.
  if (dec.kind === "action") {
    return (
      <SurfaceLedgerRow {...rest} lineLabel={`Action: ${dec.text}`}
        cells={<><span className="surface-token" data-testid="room-row-kind">ACTION</span>{cells}</>} />
    );
  }
  return (
    <SurfaceLedgerRow {...rest} open={open} onToggle={() => setOpen((o) => !o)}
      lineLabel={`Decision: ${dec.text}`}
      cells={<>{cells}<DecisionRecordPreparedChip id={dec.id} /></>}>
      {open ? <DecisionRecordSendWells id={dec.id} text={dec.text} /> : null}
    </SurfaceLedgerRow>
  );
}

function DecisionsCommitmentsSection({ room }: { room: RoomSnapshot }) {
  const decisionItems = room.decisions.state === "ok" ? room.decisions.items : [];
  const commitmentItems = room.commitments.state === "ok" ? room.commitments.items : [];

  // HS-172-03: fold commitments into their decision row when the decision
  // carries a commitmentId that matches a commitment's id. The merged row
  // shows OWNER + BY DUE + CONFIRMED; the commitment is not listed separately.
  const foldedCommitmentIds = new Set<string>();
  const commitmentById = new Map(commitmentItems.map((c) => [c.id, c]));
  for (const dec of decisionItems) {
    if (dec.commitmentId && commitmentById.has(dec.commitmentId)) {
      foldedCommitmentIds.add(dec.commitmentId);
    }
  }
  const unfoldedCommitments = commitmentItems.filter((c) => !foldedCommitmentIds.has(c.id));

  const total = decisionItems.length + unfoldedCommitments.length;
  if (total === 0) return null;

  return (
    <SurfaceSection label={`DECISIONS & COMMITMENTS ${total}`}>
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows">
          {decisionItems.map((dec) => {
            // HS-172-03: proposal-derived decisions carry source=meeting
            const isProposal = dec.source === "meeting";
            const confirmedTime = dec.confirmedAt ? formatTimeShort(dec.confirmedAt) : "";
            const foldedCommitment = dec.commitmentId ? commitmentById.get(dec.commitmentId) : undefined;

            // Build WAS tokens from changed fields only (F5 ruling)
            const wasParts: string[] = [];
            if (dec.was) {
              if (dec.was.text) {
                const truncated = dec.was.text.length > 40
                  ? `${dec.was.text.slice(0, 40)}...`
                  : dec.was.text;
                wasParts.push(`WAS "${truncated}"`);
              }
              if (dec.was.due) wasParts.push(`WAS BY ${dec.was.due.toUpperCase()}`);
              if (dec.was.owner) wasParts.push(`WAS ${dec.was.owner}`);
            }

            if (isProposal) {
              // Merged caption: OWNER MAREK · BY FRI · CONFIRMED 09:15 + WAS tokens
              const ownerName = foldedCommitment?.owner;
              const dueDateRaw = foldedCommitment?.dueAt;
              // Format due as short day name (FRI) when within ~7 days, else date
              const dueLabel = dueDateRaw ? formatDueShort(dueDateRaw) : "";

              return (
                <RoomDecisionRow
                  dec={dec}
                  key={`dec-${dec.id}`}
                  data-testid="decision-row"
                  lead="MTG"
                  primary={<span className="surface-primary">{dec.text}</span>}
                  wrap
                  cells={
                    <>
                      {ownerName ? (
                        <span className="surface-token">OWNER {ownerName.toUpperCase()}</span>
                      ) : null}
                      {dueLabel ? (
                        <span className="surface-token">BY {dueLabel.toUpperCase()}</span>
                      ) : null}
                      {dec.done ? (
                        // PHILO-15 B70: a done action reads DONE, not CONFIRMED.
                        <span className="surface-token room-confirmed-token" data-testid="done-state">
                          {dec.doneAt ? `DONE · ${formatTimeShort(dec.doneAt)}` : "DONE"}
                        </span>
                      ) : (
                        <span className="surface-token room-confirmed-token" data-testid="confirmed-state">
                          CONFIRMED {confirmedTime}
                        </span>
                      )}
                      {wasParts.map((w, wi) => (
                        <span key={wi} className="surface-token room-was-token">{w}</span>
                      ))}
                    </>
                  }
                />
              );
            }

            return (
              <RoomDecisionRow
                dec={dec}
                key={`dec-${dec.id}`}
                data-testid="decision-row"
                primary={
                  <>
                    <span className="room-dc-verb">Decided</span>
                    {" · "}{dec.text}{" · "}{humanTime(dec.at)}
                  </>
                }
                wrap
                trailing={
                  dec.url ? (
                    <Button dense variant="ghost" onClick={() => window.open(dec.url!, "_blank", "noopener")}>Open source</Button>
                  ) : undefined
                }
              />
            );
          })}
          {unfoldedCommitments.map((c) => (
            <SurfaceLedgerRow
              key={`com-${c.id}`}
              primary={
                <>
                  <span className="room-dc-verb">You owe</span>
                  {" · "}{c.text}
                  {c.dueAt ? <>{" · by "}{humanTime(c.dueAt)}</> : null}
                </>
              }
              wrap
              trailing={
                <Button dense variant="ghost" onClick={() => openPrimitive(`commitment:${c.id}`)}>Open commitment</Button>
              }
            />
          ))}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}


/** BRIEFS — the kept preparation briefs, attached to this Project (HS-200-11
 *  AC4).  Absent at zero (A.8). */
function RoomBriefsSection({ prepare }: { prepare: PrepareController }) {
  const { kept } = prepare;
  if (kept.length === 0) return null;
  return (
    <SurfaceSection label={countLabel("BRIEFS", kept.length)}>
      <SurfaceLedger count="" cols="room">
        <ul className="surface-ledger-rows" data-testid="room-briefs">
          {kept.map((brief) => {
            const coverage = coverageToken(brief.manifest.coverage);
            const keptAt = clockToken("KEPT", brief.keptAt);
            return (
              <SurfaceLedgerRow
                key={brief.id}
                data-testid="room-brief-row"
                lead={<span className="prepare-emblem" aria-hidden="true">BRF</span>}
                primary={<span className="surface-primary">{brief.purpose}</span>}
                cells={
                  <span className="prepare-source-cells">
                    {keptAt ? <span className="surface-token" data-chip>{keptAt}</span> : null}
                    {coverage ? (
                      <StateChip state={brief.manifest.coverage.complete ? "success" : "warning"} label={coverage} />
                    ) : null}
                  </span>
                }
                trailing={
                  <Button dense variant="ghost" aria-label={`Open: ${brief.purpose}`} data-testid="room-brief-open" onClick={() => void prepare.openBrief(brief)}>
                    Open
                  </Button>
                }
                wrap
                open
                expands={false}
              />
            );
          })}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

