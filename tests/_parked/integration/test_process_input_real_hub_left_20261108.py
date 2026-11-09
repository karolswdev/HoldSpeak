"""PARKED 20261108 (late evening): tests of routes parked in the left-routes pass.

From ``tests/integration/test_process_input_real_hub.py``. Not collected (tests/_parked). Restore with ``git revert``.
"""


@pytest.mark.skipif(shutil.which("tmux") is None, reason="tmux is required for real terminal proof")
def test_real_http_process_input_types_into_real_tmux(tmp_path: Path) -> None:
    home = tmp_path / "home"
    config = home / ".config" / "holdspeak" / "config.json"
    config.parent.mkdir(parents=True)
    config.write_text(
        json.dumps(
            {
                "config_version": 1,
                "control_mode": "yolo",
                "meeting": {"web_auth_token": _OWNER_TOKEN},
            }
        ),
        encoding="utf-8",
    )
    received = tmp_path / "received.txt"
    tmux_name = f"hs10605_{os.getpid()}"
    subprocess.run(
        [
            "tmux",
            "new-session",
            "-d",
            "-s",
            tmux_name,
            f"sh -c 'IFS= read -r line; printf %s \"$line\" > {received}; sleep 3'",
        ],
        check=True,
    )
    pane = subprocess.run(
        ["tmux", "display-message", "-p", "-t", f"{tmux_name}:0.0", "#{pane_id}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.update(HOME=str(home), HOLDSPEAK_WEB_PORT=str(port), PYTHONUNBUFFERED="1")

    def request(method: str, path: str, body: Any = None) -> tuple[int, dict[str, Any]]:
        data = None if body is None else json.dumps(body).encode()
        outgoing = urllib.request.Request(
            base + path,
            data=data,
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {_OWNER_TOKEN}",
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(outgoing, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc)

    hub = subprocess.Popen(
        [sys.executable, "-m", "holdspeak.main", "web", "--no-open"],
        cwd=_REPO,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        for _ in range(300):
            if hub.poll() is not None:
                output = hub.stdout.read() if hub.stdout else ""
                raise AssertionError(f"spawned hub exited early:\n{output}")
            try:
                with urllib.request.urlopen(base + "/health", timeout=0.2):
                    break
            except Exception:
                time.sleep(0.1)
        else:
            hub.kill()
            output = hub.stdout.read() if hub.stdout else ""
            raise AssertionError(f"spawned hub did not become healthy:\n{output}")

        status, target = request(
            "POST", "/api/delivery/terminal/targets", {"ref": f"pane:{pane}"}
        )
        assert status == 200 and target["pane_id"] == pane
        started = time.monotonic()
        status, delivered = request(
            "POST",
            "/api/delivery/terminal/commands",
            {
                "target_id": target["target_id"],
                "target_generation": target["target_generation"],
                "operation": {
                    "family": "coder_steering",
                    "verb": "terminal.text",
                },
                "payload": {
                    "text": "REAL_PROCESS_INPUT_106_05",
                    "session_key": "pane-proof",
                    "submit": True,
                    "agent": "claude",
                },
            },
        )
        latency_ms = (time.monotonic() - started) * 1000
        assert status == 200
        assert delivered["operation_id"].startswith("op_")
        assert delivered["receipt"]["outcome"] == "delivered"
        for _ in range(50):
            if received.exists():
                break
            time.sleep(0.05)
        assert received.read_text(encoding="utf-8") == "REAL_PROCESS_INPUT_106_05"
        status, projected = request(
            "GET",
            f"/api/kernel/read?refs=operation:{delivered['operation_id']}&view=receipt",
        )
        receipt = projected["objects"][0]["receipt"]
        assert status == 200 and receipt["state"] == "succeeded"
        print(
            json.dumps(
                {
                    "operation_id": delivered["operation_id"],
                    "pane": pane,
                    "received": received.read_text(encoding="utf-8"),
                    "receipt": receipt["state"],
                    "latency_ms": round(latency_ms, 2),
                },
                sort_keys=True,
            )
        )
    finally:
        hub.kill()
        hub.wait(timeout=10)
        subprocess.run(["tmux", "kill-session", "-t", tmux_name], check=False)
