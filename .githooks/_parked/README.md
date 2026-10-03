# Parked git hooks

Parked 2026-10-03 by the owner's ruling: "I feel like we've been paying
the price of working under delivery workbench that has been bogging us
down BIG-FREAKIN'-TIME ... I want us to move fast. Super-fast."

`pre-commit`, `commit-msg` and `post-commit` were the Delivery Workbench
commit gate (contract, evidence pairing, one story flip per commit, PMO
trailers). They are parked, not deleted. Git does not run a hook in this
folder, so a plain `git commit` passes.

The `dw` CLI one level up still runs. Use it to read the old roadmap
under `pm/roadmap/` (`.githooks/dw context`, `.githooks/dw next`). The
product also reads roadmaps through it.

To bring the gate back: `git mv .githooks/_parked/{pre-commit,commit-msg,post-commit} .githooks/`.

Current rules: `CLAUDE.md`, "How we work now". Current status: `pm/STATUS.md`.
