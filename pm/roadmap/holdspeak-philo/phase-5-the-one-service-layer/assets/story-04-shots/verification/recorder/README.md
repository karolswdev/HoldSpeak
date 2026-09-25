PHILO-5-04 recorder structural fences

Worktree: /Users/karol/dev/tools/wt-philo-5-04
Branch: feat/philo-5-04-his-words
Base: 9c653937

Baseline command (isolated HOME, warm Node path):

    PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH HOME=$(mktemp -d) uv run pytest -q tests/unit/test_philo5_rehearsal_capture.py tests/unit/test_philo5_codex_seams.py

Baseline result: 4 passed in 8.33s.

Each mutation used a disposable full-repository copy under /tmp and the same
isolated-HOME command. The mutation copies were not written back to this
worktree and no git worktree-moving command was used.

Mutation copies and exact command results (the `.out` files contain the
captured pytest output plus exit code):

* `/tmp/holdspeak-philo504-optout.4pit8h`: removed the `if
  record_rehearsal` opt-in guard; `mutation-optout.out` exits 1 at
  `assert plain.transcript_path is None`.
* `/tmp/holdspeak-philo504-path.iKvlug`: replaced
  `_guard_transcript_path(candidate, self.home)` with a plain `Path(candidate)`;
  `mutation-path.out` exits 1 at `pytest.raises(gw.Refused)`.
* `/tmp/holdspeak-philo504-body.lY4vJV`: added `request_body` to every
  recorder entry; `mutation-body.out` exits 1 because the health row has the
  extra `request_body: None` field.
* `/tmp/holdspeak-philo504-hash.oBboay`: removed the fixture citation block;
  `mutation-hash.out` exits 1 with `KeyError: 'fixture'`.

See the adjacent `.patch` and `.out` files for each mutation.
