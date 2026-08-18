# Evidence - HS-139-01

- **Story:** HS-139-01 - Kill the liars
- **Status:** done
- **Date:** 2026-08-17

## Proof

### Captured run — 2026-08-18T01:23:14Z

- **Command:** `HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.PCmVt3FHbu uv run pytest -q tests/unit/test_config.py tests/integration/test_web_server.py -k settings tests/integration/test_settings_version_guard.py tests/integration/test_web_settings_page.py tests/unit/test_mcp_phase133_settings.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_settings_wake_word.py tests/integration/test_web_settings_presence.py tests/integration/test_web_settings_secrets.py tests/integration/test_settings_placement_provenance.py tests/integration/test_settings_language_ui.py tests/integration/test_settings_spoken_symbols.py`
- **Cwd:** .
- **Exit code:** 127
- **Index-tree:** 8b92f7c93d1efa8af82115001be2896762f989b3

```text
(command could not be executed: [Errno 2] No such file or directory: 'HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.PCmVt3FHbu')
```

### Captured run — 2026-08-18T01:23:37Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/8cb4eee1-518d-4508-859c-1c60b6eb0e3b/scratchpad/run-139-01.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8b92f7c93d1efa8af82115001be2896762f989b3

```text
........................................................................ [ 84%]
.............                                                            [100%]
85 passed, 155 deselected in 29.26s
```
