# HS-108-03 - Terminal input has one door

- **Project:** holdspeak
- **Phase:** 108
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-108-06
- **Owner:** unassigned

## The thesis

Every production text or key act reaching
`coder_steering.deliver`/`deliver_keys` first belongs to one claimed
`process.input@1` operation, including policy refusal.

## Recipe

1. Extend `ProcessInputCodec` with a typed `input_kind` union for text and
   keys, preserving content-free journal heads.
2. Adapt both web routes to `submit_process_input`.
3. Delete preflight-result and direct-delivery fallbacks.
4. Let a denied steering decision enter the claimed executor so its named
   refusal is audited and receipted without resolving or touching tmux.
5. Bind expected pane identity into the admitted payload.
6. Pin the only remaining production callers by AST.

## Acceptance

- Text, keys, delivery, refusal, and target failure each leave a terminal
  kernel receipt.
- The direct callers are exactly `holdspeak/delivery/commands.py`.
- A key sequence has a direct kernel-adapter test, not only a route mock.

## Test plan

`tests/unit/test_process_input_kernel.py`,
`tests/unit/test_web_routes_coders_steer.py`, and the effect fence.
