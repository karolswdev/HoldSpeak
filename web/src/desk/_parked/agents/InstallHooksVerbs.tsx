/* PARKED (Betterment AG1, 2026-10-18): unused; cut from
 * desk/conductor/ConductorWindow.tsx as it was. Not compiled (tsconfig and
 * vitest exclude _parked). */
// @ts-nocheck
/** PHILO-15 B34: with nothing selected, every ready agent that lacks hooks
 *  has its own Install hooks verb (it was hidden until a selection). */
export function InstallHooksVerbs({ agents }: { agents: AgentRow[] }) {
  const installing = useConductor((s) => s.installing);
  return (
    <>
      {agents.filter(needsHooks).map((row, index) => (
        <Button
          key={row.id}
          dense
          // Astra r1 (#1084): one primary per face; the next ones are secondary.
          variant={index === 0 ? "primary" : "secondary"}
          data-testid="conductor-install-hooks"
          loading={installing === row.id}
          disabled={Boolean(installing) && installing !== row.id}
          onClick={() => void useConductor.getState().installHooks(row.id)}
        >
          {`Install hooks · ${AGENT_NAME[row.id]}`}
        </Button>
      ))}
    </>
  );
}

