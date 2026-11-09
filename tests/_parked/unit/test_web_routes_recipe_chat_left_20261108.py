"""PARKED 20261108 (late evening): tests of routes parked in the left-routes pass.

From ``tests/unit/test_web_routes_recipe_chat.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""


def test_chat_alias_requires_text(env) -> None:
    """The alias requires non-blank text (question or text field)."""
    db, client = env
    _seed_persona(db)
    assert client.post("/api/recipes/recipe_scout/chat", json={}).status_code == 400
    assert client.post("/api/recipes/recipe_scout/chat", json={"question": "  "}).status_code == 400
    assert client.post("/api/recipes/recipe_scout/chat", json={"text": ""}).status_code == 400


# HS-151-04: test_chat_assembles_the_turn_and_persists_nothing DELETED —
# tested RecipeService.chat() body shape (block assembly, output, egress,
# context_ids); the alias creates a thread+turn, none of those apply.

# HS-151-04: test_chat_kb_honesty_marker_when_nothing_hydrates DELETED —
# tested RecipeService.chat() KB honesty marker in user_prompt.

# HS-151-04: test_chat_grounding_refuses_unknown_ids DELETED —
# the alias does not accept a grounding body; ref refusal is tested via
# ThreadService.start_turn(refs=...) in test_thread_service.py.




# ── Engine-off-the-loop regression for the chat alias ──────────────


class _LoopSpy:
    """Records whether the engine ran on the event loop's thread."""

    active_provider = "local"

    def __init__(self) -> None:
        self.on_loop: bool | None = None

    def run_prompt(self, *, system_prompt, user_prompt, temperature=None, max_tokens=None):
        try:
            asyncio.get_running_loop()
            self.on_loop = True
        except RuntimeError:
            self.on_loop = False
        return "SPY-RAN"


@pytest.fixture
def spy(monkeypatch) -> _LoopSpy:
    s = _LoopSpy()
    from holdspeak.kernel.inference_runner import InferenceRunner
    monkeypatch.setitem(InferenceRunner.__init__.__kwdefaults__, "engine_factory", lambda revision, **_kw: s)
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: s)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: s)
    return s


def test_chat_alias_creates_thread_and_returns_ids(env, spy) -> None:
    """The alias creates a thread, starts a turn, returns 201 with ids."""
    db, client = env
    _seed_persona(db)
    resp = client.post("/api/recipes/recipe_scout/chat", json={"question": "hi"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "thread_id" in body
    assert "user_message_id" in body
    assert "assistant_message_id" in body
    # The thread must be bound to the recipe.
    thread = db.threads.get(body["thread_id"])
    assert thread is not None
    assert thread.recipe_id == "recipe_scout"


def test_chat_alias_reuses_existing_thread(env, spy) -> None:
    """A second chat to the same recipe reuses the thread created by the first."""
    db, client = env
    _seed_persona(db)
    r1 = client.post("/api/recipes/recipe_scout/chat", json={"text": "first"})
    assert r1.status_code == 201
    r2 = client.post("/api/recipes/recipe_scout/chat", json={"text": "second"})
    assert r2.status_code == 201
    assert r1.json()["thread_id"] == r2.json()["thread_id"]


def test_chat_alias_engine_runs_off_the_loop(env, spy) -> None:
    """The engine dispatched by the chat alias runs off the event loop.

    Regression guard: the broken inline ThreadService construction passed
    broker=None, crashing the daemon thread. The shared factory wires the
    kernel broker, and the engine runs in a daemon thread (off the loop).
    """
    db, client = env
    _seed_persona(db)
    resp = client.post("/api/recipes/recipe_scout/chat", json={"question": "hi"})
    assert resp.status_code == 201
    # The turn runs on a daemon thread; wait for the spy to fire.
    for _ in range(100):
        if spy.on_loop is not None:
            break
        time.sleep(0.02)
    assert spy.on_loop is False, (
        "the engine ran ON the event loop -- the thread alias must dispatch "
        "the turn to a daemon thread so the request never blocks the loop"
    )
