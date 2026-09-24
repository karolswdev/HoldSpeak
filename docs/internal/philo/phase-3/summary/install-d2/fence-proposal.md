# D2 focused fence proposal

The earlier README-word assertion below is insufficient on its own: it checks
documentation wording, not the production import head. The executable probe in
`production-import-fence.log` is the stronger fence to carry into the settled
design.

The fence must protect the documented install path at the same seam the user relies on. It should run without a hub, microphone, keychain, endpoint, API key, or downloaded GGUF.

## Proposed focused test

Add one unit test (for example `tests/unit/test_meeting_install_contract.py`) that reads the source installation section and the optional dependency table, then asserts the documented meeting setup names the extra that owns both model clients. A concrete pre-fix version is:

```python
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[2]


def test_documented_meeting_install_has_both_model_clients() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    meeting = pyproject["project"]["optional-dependencies"]["meeting"]
    assert any(item.startswith("openai>=") for item in meeting)
    assert any(item.startswith("llama-cpp-python>=") for item in meeting)

    getting_started = (ROOT / "docs/GETTING_STARTED.md").read_text()
    assert "uv pip install -e '.[meeting]'" in getting_started

    # The primary source-install block must point a user who expects the
    # documented meeting capability at the extra that supplies its clients.
    readme = (ROOT / "README.md").read_text()
    assert "uv pip install -e '.[meeting]'" in readme
```

On the current tree, the final assertion fails because `README.md:23` contains `uv pip install -e .` and has no `.[meeting]` command. The failure is deterministic and requires no model or product process. After the minimal README install-surface fix, it passes and remains a focused guard against repeating D2.

If the product decision is to keep README's base install deliberately minimal, change the fence's final assertion to require an adjacent explicit sentence that meeting summaries need `uv pip install -e '.[meeting]'`; the required fact must still be asserted at the primary install entry point. The existing `docs/GETTING_STARTED.md:227` assertion proves the extra is documented, but does not fence the README path that currently advertises meeting review.

## Executed production import fence

The real production seam is the optional import in `holdspeak/intel/__init__.py`.
Run this exact probe against every isolated installation under test:

```sh
"$VENV/bin/python" -c 'from holdspeak.intel import OpenAI; print(f"OpenAI={OpenAI!r}"); assert OpenAI is not None, "production OpenAI client is unavailable"'
```

The current base installation fails with `OpenAI=None`, exit `1`; the current
`[meeting]` installation prints `OpenAI=<class 'openai.OpenAI'>`, exit `0`.
Those actual runs are retained in [production-import-fence.log](./production-import-fence.log).
This is an executable package/production import fence, not a pytest collection
claim. It requires no model, endpoint, key, hub, microphone, or keychain.

## Optional stronger environment check

Keep the isolated install logs in this folder as the D2 evidence. Do not make the normal unit suite create a networked venv. A separately invoked evidence check can run:

```sh
HOME=$(mktemp -d) VENV=$(mktemp -d) sh -c 'uv venv "$VENV" && . "$VENV/bin/activate" && uv pip install -e ".[meeting]" && python -c "from holdspeak.intel import OpenAI, Llama; assert OpenAI is not None and Llama is not None"'
```

This proves the package identity/import seam in a fresh environment; it is intentionally an evidence procedure, not a default pytest test.
