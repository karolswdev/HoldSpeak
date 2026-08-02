# Evidence - HS-108-03

- **Story:** HS-108-03 - Terminal input has one door
- **Status:** done
- **Date:** 2026-07-29

## Captured proof

```text
$ uv run --extra test pytest -q tests/unit/test_process_input_kernel.py tests/unit/test_web_routes_coders_steer.py
...............................................                          [100%]
47 passed in 5.74s
```

The group proves both text and key shapes bind into `process.input@1`,
content is absent from journal events, local success/failure and policy
denial close kernel receipts, and remote uncertainty reconciles by command
ID. A claimed or indeterminate retry is reconciliation-only, including a
payload-swap refusal; it cannot redispatch. The AST fence names exactly two remaining direct
`coder_steering.deliver*` callers, both in the claimed node executor.
