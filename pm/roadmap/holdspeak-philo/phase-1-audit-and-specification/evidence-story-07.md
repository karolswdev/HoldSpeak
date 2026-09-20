# Evidence - PHILO-1-07

- **Story:** PHILO-1-07 - Integrated audit and final verification
- **Status:** done
- **Date:** 2026-09-19

## Proof

### Captured run — 2026-09-20T02:40:46Z

- **Command:** `bash .tmp/philo/run_full.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b2bf9ce1b96cfdf6913970a932315a2498c806e3

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  0%]
........................................................................ [  1%]
..........................................................F............. [  1%]
........................................................................ [  2%]
........................................................................ [  3%]
........................................................................ [  3%]
........................................................................ [  4%]
........................................................................ [  5%]
........................................................................ [  5%]
...................................................................ss.ss [  6%]
sssssssssss.sssssssssssssss............................................. [  7%]
........................................ss.............................. [  7%]
........................................................................ [  8%]
........................................................................ [  8%]
.........................................ss............................. [  9%]
........................................................................ [ 10%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 12%]
........................................................................ [ 12%]
.................................................................s...... [ 13%]
........................................................................ [ 14%]
........................................................................ [ 14%]
............................................s........................... [ 15%]
........................................................................ [ 15%]
........................................................................ [ 16%]
...s.................................................................... [ 17%]
..ss...................ss............................................... [ 17%]
........................................................................ [ 18%]
...........................................................s............ [ 19%]
...................................................................s.... [ 19%]
........................................................................ [ 20%]
........................................................................ [ 21%]
..........................................s............................. [ 21%]
........................................................................ [ 22%]
...s.......................................................sssss........ [ 23%]
........................................................................ [ 23%]
..ss.s.................................................................. [ 24%]
........................................................................ [ 24%]
.............F.......................................................... [ 25%]
F.......F........F...................................................... [ 26%]
........................................................................ [ 26%]
........................................................................ [ 27%]
........................................................................ [ 28%]
.......................................ss............................... [ 28%]
........................................................................ [ 29%]
........................................................................ [ 30%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 31%]
........................................................................ [ 32%]
........................................................s............... [ 33%]
.....................................F.................................. [ 33%]
........................................................................ [ 34%]
...........................F............................................ [ 35%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 37%]
........................................................................ [ 37%]
........................................................................ [ 38%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 42%]
........................................................................ [ 42%]
........................................................................ [ 43%]
........................................................................ [ 44%]
........................................................................ [ 44%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................s............................................... [ 46%]
........................................................................ [ 47%]
........................................................................ [ 47%]
........................................................................ [ 48%]
........................................................................ [ 49%]
.............................s.......................................... [ 49%]
........................................................................ [ 50%]
........................................................................ [ 51%]
........................................................................ [ 51%]
........................................................................ [ 52%]
........................................................................ [ 53%]
........................................................................ [ 53%]
........................................................................ [ 54%]
........................................................................ [ 54%]
..........................................................F............. [ 55%]
..F....F..F...F......F....F...........F................................. [ 56%]
........................................................................ [ 56%]
........................................................................ [ 57%]
........................................................................ [ 58%]
........................................................................ [ 58%]
........................................................................ [ 59%]
........................................................................ [ 60%]
........................................................................ [ 60%]
........................................................................ [ 61%]
........................................................................ [ 62%]
........................................................................ [ 62%]
........................................................................ [ 63%]
........................................................................ [ 63%]
........................................................................ [ 64%]
........................................................................ [ 65%]
........................................................................ [ 65%]
........................................................................ [ 66%]
........................................................................ [ 67%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 69%]
........................................................................ [ 69%]
........................................................................ [ 70%]
........................................................................ [ 70%]
........................................s..............sss.............. [ 71%]
........................................................................ [ 72%]
........................................................................ [ 72%]
.................................................................s...... [ 73%]
........................................................................ [ 74%]
........................................................................ [ 74%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 76%]
........................................................................ [ 77%]
........................................................................ [ 77%]
........................................................................ [ 78%]
...........................................................s............ [ 79%]
........................................................................ [ 79%]
........................................................................ [ 80%]
........................................................................ [ 81%]
........................................................................ [ 81%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 83%]
........................................................................ [ 84%]
........................................................................ [ 85%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 86%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 88%]
........................................................................ [ 89%]
........................................................................ [ 90%]
........................................................................ [ 90%]
....................................s................................... [ 91%]
........................................................................ [ 92%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 93%]
........................................................................ [ 94%]
........................................................................ [ 95%]
............................................s........................... [ 95%]
........................................................................ [ 96%]
......................................................F................. [ 97%]
....................................ssssssssssss...........sssssssss.... [ 97%]
................................ssssssssss....ssss....ssssss...F........ [ 98%]
........................................................................ [ 99%]
................................................FF...................... [ 99%]
...............................                                          [100%]
=================================== FAILURES ===================================
_ TestTheScheduledOwnerReallyFires.test_the_sweep_is_driven_by_a_wall_clock_loop _
[gw3] darwin -- Python 3.14.2 /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python3

self = <tests.integration.test_phase200_recipe_catalog.TestTheScheduledOwnerReallyFires object at 0x112e0da70>

    def test_the_sweep_is_driven_by_a_wall_clock_loop(self) -> None:
        """Asserted on the compiled code object, not the source text.
    
        Counsel's P2-4: the first cut matched substrings like
        ``"sweep_interval" in driver``, which a reformat breaks and a
        gutted loop survives. Bytecode names and constants survive
        reformatting, comments and local renames, and disappear the moment
        the loop stops doing the thing.
        """
        from holdspeak.runtime.heartbeat import HeartbeatMixin
    
        loop = HeartbeatMixin._heartbeat_loop
        names = set(loop.__code__.co_names)
        # It reads the interval, decides, and sweeps.
        assert "get_settings" in names
        assert "run_sweep" in names
        # It is a loop over a stop event, not a one-shot call.
        assert {"is_set", "wait"} <= names
        # The tick is a real number of seconds.
        ticks = [
            c for c in loop.__code__.co_consts
            if isinstance(c, int) and not isinstance(c, bool) and c >= 10
        ]
>       assert ticks, loop.__code__.co_consts
E       AssertionError: ('Tick every 60 seconds; on each tick, check if a sweep is due.', None, ('get_database', 'get_observer'), ('Principal', 'PrincipalKind'), ('HeartbeatService',), ('observer',), ...)
E       assert []

tests/integration/test_phase200_recipe_catalog.py:652: AssertionError
_________ test_docs_do_not_restore_retired_inference_setup_vocabulary __________
[gw11] darwin -- Python 3.14.2 /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python3

    def test_docs_do_not_restore_retired_inference_setup_vocabulary() -> None:
        offenders: list[str] = []
        for path in _all_docs_and_readme():
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                match = _RETIRED_INFERENCE_VOCAB.search(line)
                if match:
                    offenders.append(f"{path.relative_to(_REPO)}:{lineno}: {match.group(0)!r}")
    
>       assert not offenders, (
            "Retired inference setup vocabulary returned to docs/ or README. Use "
            "Models for availability and Assignments for job selection instead:\n  "
            + "\n  ".join(offenders)
        )
E       AssertionError: Retired inference setup vocabulary returned to docs/ or README. Use Models for availability and Assignments for job selection instead:
E           docs/CONFIGURATION_REFERENCE.md:44: 'inference_target_id'
E       assert not ["docs/CONFIGURATION_REFERENCE.md:44: 'inference_target_id'"]

tests/unit/test_doc_drift_guard.py:121: AssertionError
________________ test_no_live_doc_has_a_dangling_relative_link _________________
[gw11] darwin -- Python 3.14.2 /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python3

    def test_no_live_doc_has_a_dangling_relative_link() -> None:
        offenders: list[str] = []
        for path in _maintained_docs():
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for target in _MD_LINK.findall(line):
                    target = target.strip()
                    # Skip external, anchor-only, and non-doc targets.
                    if target.startswith(("http://", "https://", "mailto:", "#", "<")):
                        continue
                    # Drop any #fragment / ?query suffix.
                    rel = target.split("#", 1)[0].split("?", 1)[0]
                    if not rel:
                        continue
                    resolved = (path.parent / rel).resolve()
                    if not resolved.exists():
                        offenders.append(
                            f"{path.relative_to(_REPO)}:{lineno}: -> {target}"
                        )
    
>       assert not offenders, (
            "A maintained doc links a path that does not exist (dangling relative link). "
            "Fix the path or the move:\n  " + "\n  ".join(offenders)
        )
E       AssertionError: A maintained doc links a path that does not exist (dangling relative link). Fix the path or the move:
E           docs/internal/philo/desktop-prototypes/electron/node_modules/@electron-internal/extract-zip/README.md:46: -> ./SECURITY.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/@electron-internal/extract-zip/README.md:49: -> ./SECURITY.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/debug/README.md:20: -> ./examples/node/app.js
E           docs/internal/philo/desktop-prototypes/electron/node_modules/debug/README.md:43: -> ./examples/node/worker.js
E           docs/internal/philo/desktop-prototypes/electron/node_modules/debug/README.md:252: -> ./examples/node/stdout.js
E           docs/internal/philo/desktop-prototypes/electron/node_modules/electron/README.md:33: -> docs/tutorial/installation.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/electron/README.md:34: -> docs/tutorial/electron-versioning.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/electron/README.md:91: -> CONTRIBUTING.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/README.md:14: -> ./CONTRIBUTING.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/README.md:381: -> ./docs/examples/README.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Agent.md:19: -> /docs/docs/api/Pool.md#parameter-pooloptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Agent.md:28: -> /docs/docs/api/Client.md#clientclosed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Agent.md:32: -> /docs/docs/api/Client.md#clientdestroyed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Agent.md:46: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Agent.md:50: -> /docs/docs/api/Dispatcher.md#parameter-dispatchoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Agent.md:62: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Agent.md:66: -> /docs/docs/api/Dispatcher.md#dispatcherpipelineoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Agent.md:84: -> /docs/docs/api/PoolStats.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Agent.md:84: -> /docs/docs/api/ClientStats.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/BalancedPool.md:5: -> /docs/docs/api/Pool.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/BalancedPool.md:18: -> /docs/docs/api/Pool.md#parameter-pooloptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/BalancedPool.md:31: -> /docs/docs/api/Client.md#clientclosed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/BalancedPool.md:35: -> /docs/docs/api/Client.md#clientdestroyed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/BalancedPool.md:39: -> /docs/docs/api/PoolStats.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/BalancedPool.md:69: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/BalancedPool.md:73: -> /docs/docs/api/Dispatcher.md#dispatcherpipelineoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/BalancedPool.md:91: -> /docs/docs/api/Dispatcher.md#event-connect
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/BalancedPool.md:95: -> /docs/docs/api/Dispatcher.md#event-disconnect
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/BalancedPool.md:99: -> /docs/docs/api/Dispatcher.md#event-drain
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/CacheStore.md:154: -> /docs/docs/api/CacheStore.md#cachestorevalue
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Client.md:119: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Client.md:123: -> /docs/docs/api/Dispatcher.md#dispatcherpipelineoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Client.md:161: -> /docs/docs/api/Dispatcher.md#event-connect
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Client.md:207: -> /docs/docs/api/Dispatcher.md#event-disconnect
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Client.md:252: -> /docs/docs/api/Dispatcher.md#event-drain
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/ClientStats.md:3: -> /docs/docs/api/Client.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Dispatcher.md:378: -> /docs/docs/api/Dispatcher.md#parameter-requestoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Dispatcher.md:468: -> /docs/docs/api/Dispatcher.md#parameter-dispatchoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Dispatcher.md:656: -> /docs/docs/api/Dispatcher.md#example-1-basic-get-stream-request
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Dispatcher.md:656: -> /docs/docs/api/Dispatch.md#example-2-stream-to-fastify-response
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Dispatcher.md:957: -> /docs/docs/api/RedirectHandler.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Dispatcher.md:975: -> /docs/docs/api/RetryHandler.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Dispatcher.md:1212: -> /docs/docs/api/CacheStore.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Dispatcher.md:1212: -> /docs/docs/api/CacheStore.md#memorycachestore
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Dispatcher.md:1276: -> /docs/docs/api/DiagnosticsChannel.md#undicirequestpending-requests
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Dispatcher.md:1324: -> /docs/docs/api/Client.md#clientdispatchoptions-handlers
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Dispatcher.md:1334: -> /docs/docs/api/Client.md#class-client
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/EnvHttpProxyAgent.md:21: -> /docs/docs/api/Agent.md#parameter-agentoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/EnvHttpProxyAgent.md:127: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/EnvHttpProxyAgent.md:131: -> /docs/docs/api/Dispatcher.md#parameter-dispatchoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/EnvHttpProxyAgent.md:143: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/EnvHttpProxyAgent.md:147: -> /docs/docs/api/Dispatcher.md#dispatcherpipelineoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Fetch.md:18: -> /docs/api/GlobalInstallation.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/H2CClient.md:94: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/H2CClient.md:98: -> /docs/docs/api/Dispatcher.md#dispatcherpipelineoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/H2CClient.md:136: -> /docs/docs/api/Dispatcher.md#event-connect
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/H2CClient.md:182: -> /docs/docs/api/Dispatcher.md#event-disconnect
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/H2CClient.md:227: -> /docs/docs/api/Dispatcher.md#event-drain
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockAgent.md:17: -> /docs/docs/api/Agent.md#parameter-agentoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockAgent.md:308: -> /docs/docs/api/Agent.md#parameter-agentdispatchoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockCallHistory.md:75: -> /docs/docs/api/MockCallHistory.md#filter-parameter
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockCallHistory.md:86: -> /docs/docs/api/MockCallHistory.md#filter-parameter
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockCallHistory.md:97: -> /docs/docs/api/MockCallHistory.md#filter-parameter
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockCallHistory.md:109: -> /docs/docs/api/MockCallHistory.md#filter-parameter
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockCallHistory.md:120: -> /docs/docs/api/MockCallHistory.md#filter-parameter
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockCallHistory.md:131: -> /docs/docs/api/MockCallHistory.md#filter-parameter
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockCallHistory.md:142: -> /docs/docs/api/MockCallHistory.md#filter-parameter
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockCallHistory.md:153: -> /docs/docs/api/MockCallHistory.md#filter-parameter
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockCallHistory.md:169: -> /docs/docs/api/MockCallHistory.md#filter-parameter
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockClient.md:5: -> /docs/docs/api/MockPool.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockClient.md:39: -> /docs/docs/api/MockPool.md#mockpoolinterceptoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockClient.md:43: -> /docs/docs/api/MockPool.md#mockpoolcleanmocks
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockClient.md:47: -> /docs/docs/api/MockPool.md#mockpoolclose
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockClient.md:51: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/MockPool.md:516: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Pool.md:5: -> /docs/docs/api/Client.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Pool.md:18: -> /docs/docs/api/Client.md#parameter-clientoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Pool.md:28: -> /docs/docs/api/Client.md#clientclosed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Pool.md:32: -> /docs/docs/api/Client.md#clientdestroyed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Pool.md:54: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Pool.md:58: -> /docs/docs/api/Dispatcher.md#dispatcherpipelineoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Pool.md:76: -> /docs/docs/api/Dispatcher.md#event-connect
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Pool.md:80: -> /docs/docs/api/Dispatcher.md#event-disconnect
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Pool.md:84: -> /docs/docs/api/Dispatcher.md#event-drain
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/PoolStats.md:3: -> /docs/docs/api/Pool.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/PoolStats.md:3: -> /docs/docs/api/BalancedPool.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/ProxyAgent.md:17: -> /docs/docs/api/Agent.md#parameter-agentoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/ProxyAgent.md:28: -> /docs/docs/api/Client.md#parameter-connectoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/ProxyAgent.md:29: -> /docs/docs/api/Client.md#parameter-connectoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/ProxyAgent.md:137: -> /docs/docs/api/Agent.md#parameter-agentdispatchoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RetryHandler.md:18: -> /docs/docs/api/Dispatcher.md#parameter-dispatchoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RetryHandler.md:48: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:5: -> /docs/docs/api/Client.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:7: -> /docs/docs/api/Pool.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:20: -> /docs/docs/api/Client.md#parameter-clientoptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:55: -> /docs/docs/api/BalancedPool.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:61: -> /docs/docs/api/Client.md#clientclosed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:65: -> /docs/docs/api/Client.md#clientdestroyed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:87: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:91: -> /docs/docs/api/Dispatcher.md#dispatcherpipelineoptions-handler
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:109: -> /docs/docs/api/Dispatcher.md#event-connect
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:113: -> /docs/docs/api/Dispatcher.md#event-disconnect
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:117: -> /docs/docs/api/Dispatcher.md#event-drain
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:142: -> /docs/docs/api/Pool.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/RoundRobinPool.md:143: -> /docs/docs/api/BalancedPool.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Socks5ProxyAgent.md:18: -> /docs/docs/api/Pool.md#parameter-pooloptions
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/Socks5ProxyAgent.md:211: -> /docs/docs/api/Dispatcher.md#dispatcherdispatchoptions-handlers
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/WebSocket.md:12: -> /docs/docs/api/Dispatcher.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/WebSocket.md:19: -> /docs/docs/api/Dispatcher.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:3: -> /docs/docs/api/Client.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:61: -> /docs/docs/api/Client.md#clientdispatchoptions-handlers
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:61: -> /docs/docs/api/Client.md#clientupgradeoptions-callback
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:61: -> /docs/docs/api/Client.md#pending
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:61: -> /docs/docs/api/Client.md#processing
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:63: -> /docs/docs/api/Client.md#clientclosecallback
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:63: -> /docs/docs/api/Client.md#destroyed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:67: -> /docs/docs/api/Client.md#event-connect
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:69: -> /docs/docs/api/Client.md#clientclosecallback
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:69: -> /docs/docs/api/Client.md#processing
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:69: -> /docs/docs/api/Client.md#destroyed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:71: -> /docs/docs/api/Client.md#clientdestroyerror-callback
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:71: -> /docs/docs/api/Client.md#destroyed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:75: -> /docs/docs/api/Client.md#running
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:75: -> /docs/docs/api/Client.md#clientdispatchoptions-handlers
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:75: -> /docs/docs/api/Client.md#closing
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:75: -> /docs/docs/api/Client.md#destroyed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:79: -> /docs/docs/api/Client.md#busy
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:79: -> /docs/docs/api/Client.md#closing
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:79: -> /docs/docs/api/Client.md#clientclosecallback
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:79: -> /docs/docs/api/Client.md#processing
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:79: -> /docs/docs/api/Client.md#pending
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:79: -> /docs/docs/api/Client.md#idle
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:83: -> /docs/docs/api/Client.md#running
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:87: -> /docs/docs/api/Client.md#clientclosecallback
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/api/api-lifecycle.md:87: -> /docs/docs/api/Client.md#destroyed
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/mocking-request.md:3: -> /docs/docs/api/MockAgent.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/mocking-request.md:76: -> /docs/docs/api/MockAgent.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/mocking-request.md:126: -> /docs/docs/api/MockAgent.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/mocking-request.md:128: -> /docs/docs/api/MockCallHistory.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/mocking-request.md:130: -> /docs/docs/api/MockCallHistoryLog.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/proxy.md:5: -> /docs/docs/api/ProxyAgent.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/undici-vs-builtin-fetch.md:60: -> /docs/api/GlobalInstallation.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/undici-vs-builtin-fetch.md:210: -> /docs/api/GlobalInstallation.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/undici-vs-builtin-fetch.md:219: -> /docs/api/Fetch.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/undici-vs-builtin-fetch.md:220: -> /docs/api/Client.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/undici-vs-builtin-fetch.md:221: -> /docs/api/Pool.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/undici-vs-builtin-fetch.md:222: -> /docs/api/ProxyAgent.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/undici-vs-builtin-fetch.md:223: -> /docs/api/MockAgent.md
E           docs/internal/philo/desktop-prototypes/electron/node_modules/undici/docs/docs/best-practices/undici-vs-builtin-fetch.md:224: -> /docs/api/GlobalInstallation.md
E       assert not ['docs/internal/philo/desktop-prototypes/electron/node_modules/@electron-internal/extract-zip/README.md:46: -> ./SECUR.../internal/philo/desktop-prototypes/electron/node_modules/electron/README.md:33: -> docs/tutorial/installation.md', ...]

tests/unit/test_doc_drift_guard.py:269: AssertionError
_______________ test_no_user_facing_doc_leaks_roadmap_vocabulary _______________
[gw11] darwin -- Python 3.14.2 /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python3

    def test_no_user_facing_doc_leaks_roadmap_vocabulary() -> None:
        offenders: list[str] = []
        for path in _user_facing_docs():
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if _ROADMAP_VOCAB.search(line):
                    offenders.append(f"{path.relative_to(_REPO)}:{lineno}: {line.strip()}")
    
>       assert not offenders, (
            "A user-facing doc leaks internal roadmap vocabulary (Phase NN / HS-NN-NN / "
            "PMO / 'the current roadmap'). User-facing docs speak in "
            "product-tense; the internal corpus (docs/internal, docs/evidence, "
            "docs/assets, pm/roadmap) is where that vocabulary belongs. Reword these in "
            "product-tense, see docs/internal/DOCS_STYLE.md:\n  " + "\n  ".join(offenders)
        )
E       AssertionError: A user-facing doc leaks internal roadmap vocabulary (Phase NN / HS-NN-NN / PMO / 'the current roadmap'). User-facing docs speak in product-tense; the internal corpus (docs/internal, docs/evidence, docs/assets, pm/roadmap) is where that vocabulary belongs. Reword these in product-tense, see docs/internal/DOCS_STYLE.md:
E           docs/WHAT_IS_HOLDSPEAK.md:55: [Phase 201](../pm/roadmap/holdspeak/phase-201-one-meeting-result/current-phase-status.md).
E       assert not ['docs/WHAT_IS_HOLDSPEAK.md:55: [Phase 201](../pm/roadmap/holdspeak/phase-201-one-meeting-result/current-phase-status.md).']

tests/unit/test_doc_drift_guard.py:454: AssertionError
_________________ test_no_user_facing_doc_uses_dashes_in_prose _________________
[gw11] darwin -- Python 3.14.2 /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python3

    def test_no_user_facing_doc_uses_dashes_in_prose() -> None:
        offenders = []
        for doc in _user_facing_docs():
            for lineno, line in _prose_lines(doc):
                if "—" not in line and "–" not in line:
                    continue
                if any(marker in line for marker in _VERBATIM_UI_QUOTES):
                    continue
                offenders.append(f"{doc.relative_to(_REPO)}:{lineno}: {line.strip()[:80]}")
>       assert not offenders, (
            "Em/en dashes in user-facing prose (use a period, comma, colon, or "
            "parentheses — see docs/internal/POSITIONING.md voice rules; verbatim "
            "UI quotes belong in _VERBATIM_UI_QUOTES):\n  " + "\n  ".join(offenders)
        )
E       AssertionError: Em/en dashes in user-facing prose (use a period, comma, colon, or parentheses — see docs/internal/POSITIONING.md voice rules; verbatim UI quotes belong in _VERBATIM_UI_QUOTES):
E           docs/ACTUATOR_DEVELOPMENT.md:12: (`holdspeak/plugins/actuators.py::ActuatorProposal`, lines 41–84). It never
E           docs/ACTUATOR_DEVELOPMENT.md:49: lines 50–86). Repeating the same source and content returns the same proposal;
E           docs/ACTUATOR_DEVELOPMENT.md:57: run (`holdspeak/plugins/actuator_executor.py::execute`, lines 102–208). The
E           docs/AGENTS_AND_THREADS.md:11: (`holdspeak/db/threads.py::ThreadRepository`, lines 183–887). The HTTP surface
E           docs/AGENTS_AND_THREADS.md:32: 300–558). The stream emits `thread_turn_started`, deltas, tool pending/result,
E           docs/AGENTS_AND_THREADS.md:35: `_TOOL_DEADLINE_S`, lines 61–65). A model tool palette is resolved once at
E           docs/AGENTS_AND_THREADS.md:61: `holdspeak/services/thread_tools.py::resolve_tool_decision` (lines 407–445).
E           docs/AGENTS_AND_THREADS.md:62: `ThreadToolExecutor.admit`, `decide`, `execute` and `cancel` (lines 496–815)
E           docs/AGENTS_AND_THREADS.md:85: 10–49). Its palette is the intersection of the section allow-list and the
E           docs/AGENTS_AND_THREADS.md:86: registered MCP catalogue (`InterviewService.palette`, lines 109–119).
E           docs/AGENTS_AND_THREADS.md:92: 79–91). `InterviewService.command` requires the owner, an expected revision,
E           docs/AGENTS_AND_THREADS.md:96: 142–190). A People section is a protected handoff; ThreadService refuses to
E           docs/AGENTS_AND_THREADS.md:101: (`holdspeak/mcp/families/interview.py::TOOLS`, lines 21–42). Suggestions are
E           docs/AGENTS_AND_THREADS.md:112: `holdspeak/web/routes/mcp_http.py::mcp_http_endpoint` (lines 71–198). It is
E           docs/AGENTS_AND_THREADS.md:130: (lines 602–668). It accepts meetings, artifacts, qualified references and
E           docs/AGENTS_AND_THREADS.md:134: 24–26). The result records `selection`, `matched_count`, and `overflow_count`.
E           docs/AGENTS_AND_THREADS.md:139: `holdspeak/grounding_rails.py::hydrate_rails_refs` (lines 100–166). It asks the
E           docs/AGENTS_AND_THREADS.md:145: (`holdspeak/db/memory.py::MemoryRepository.search`, lines 166–227 and the
E           docs/AGENTS_AND_THREADS.md:148: (`holdspeak/services/memory_service.py::MemoryService.search`, lines 18–48).
E           docs/AGENTS_AND_THREADS.md:157: and `::recall_for_prompt`, lines 45–96). `clear_memory` is explicit. Memory
E           docs/AGENTS_AND_THREADS.md:168: 16–74). The native runner is
E           docs/CODER_INTEGRATION.md:26: (lines 14–172); tmux inspection and delivery are in
E           docs/CODER_INTEGRATION.md:28: `::deliver_keys` (lines 136–225, 331–476, 793–836). Factory effects are
E           docs/CODER_INTEGRATION.md:29: `holdspeak/coder_factory.py::spawn`, `::rename`, and `::kill` (lines 41–182).
E           docs/CODER_INTEGRATION.md:93: (lines 27–40). The connector pack rejects writes such as `pr merge`,
E           docs/COMPANIONS_ARCHITECTURE.md:30: | dictation capture and review | Swift `VoiceNoteComposer.startRecording`, `stop
E           docs/COMPANIONS_ARCHITECTURE.md:31: | meeting start/stop and archive | `HTTPDesktopClient.startMeeting`, `stopMeetin
E           docs/COMPANIONS_ARCHITECTURE.md:44: lines 71–115). WebSocket auth uses the `holdspeak.v1` subprotocol and does not
E           docs/DESK_ARCHITECTURE.md:1: # Desk architecture — current contract
E           docs/GATE.md:11: (`holdspeak/coder_gate.py::GateConfig`, `::gate_matches`, lines 45–130).
E           docs/GATE.md:26: invalidation (`holdspeak/coder_gate.py::run_hook`, lines 273–377).
E           docs/GATE.md:50: lines 115–205). Every state flip goes through `_transition`, guarded on
E           docs/GATE.md:52: `gate_audit` (`_transition`, lines 209–249). Legal states are `held`,
E           docs/GATE.md:76: `holdspeak/coder_gate.py`, lines 150–228). The preview is truncation, not secret
E           docs/INTEGRATIONS.md:11: (`holdspeak/connector_sdk.py::ConnectorManifest` and protocols, lines 97–190,
E           docs/INTEGRATIONS.md:12: 713–779). The registry loads first-party packs from
E           docs/INTEGRATIONS.md:46: (`holdspeak/connector_runtime.py::PermissionGate`, lines 115–245).
E           docs/INTEGRATIONS.md:80: (lines 41–84). `ActuatorProposalService._propose` validates text, destination
E           docs/INTEGRATIONS.md:83: 50–100). The concrete desk routes are:
E           docs/INTEGRATIONS.md:97: lines 91–232). The statuses are proposed, approved, rejected/failed and
E           docs/IPAD.md:38: 15–119). The source comments explicitly avoid a second transcription path:
E       assert not ['docs/ACTUATOR_DEVELOPMENT.md:12: (`holdspeak/plugins/actuators.py::ActuatorProposal`, lines 41–84). It never', 'docs...lt,', 'docs/AGENTS_AND_THREADS.md:35: `_TOOL_DEADLINE_S`, lines 61–65). A model tool palette is resolved once at', ...]

tests/unit/test_doc_drift_guard.py:574: AssertionError
__________ TestSettingsRemoteAccess.test_remote_on_issue_revoke[393] ___________
[gw1] darwin -- Python 3.14.2 /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python3

self = <tests.e2e.test_hs174_remote_settings_glass.TestSettingsRemoteAccess object at 0x10c3b16e0>
width = 393

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_remote_on_issue_revoke(self, width: int) -> None:
        """Turn ON, issue a credential, verify token visible once,
        reload -> no token, NEVER USED; then revoke -> row gone."""
        from playwright.sync_api import sync_playwright
    
        errors: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 900})
            page.emulate_media(reduced_motion="reduce")
            page.on("pageerror", lambda err: errors.append(str(err)))
    
>           _navigate_to_settings_hub(page, self.base)

tests/e2e/test_hs174_remote_settings_glass.py:157: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_hs174_remote_settings_glass.py:47: in _navigate_to_settings_hub
    page.locator(".prefs-hub-headline").wait_for(timeout=10_000)
.venv/lib/python3.14/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.14/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.14/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x122839050>
cb = <function Channel.send.<locals>.<lambda> at 0x1269aab90>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator(".prefs-hub-headline") to be visible

.venv/lib/python3.14/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
__________ test_real_http_executor_receipt_and_sigkill_cursor_replay ___________
[gw2] darwin -- Python 3.14.2 /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python3

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-9008/popen-gw2/test_real_http_executor_receip0')

    def test_real_http_executor_receipt_and_sigkill_cursor_replay(tmp_path: Path) -> None:
        home = tmp_path / "home"
        config = home / ".config" / "holdspeak" / "config.json"
        config.parent.mkdir(parents=True)
        config.write_text(
            json.dumps({"config_version": 1, "meeting": {"web_auth_token": _OWNER_TOKEN}}),
            encoding="utf-8",
        )
        node_store = home / ".holdspeak" / "node_auth_tokens.json"
        node_store.parent.mkdir(parents=True)
        node_store.write_text(
            json.dumps(
                {
                    "node_tokens_schema": 1,
                    "nodes": {
                        "proof": {
                            "node_id": "node_kernel_proof",
                            "token": _NODE_TOKEN,
                            "revoked": False,
                            "created_at": "proof",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        os.chmod(node_store, 0o600)
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        env = os.environ.copy()
        env.update(HOME=str(home), HOLDSPEAK_WEB_PORT=str(port), PYTHONUNBUFFERED="1")
    
        def request(
            method: str, path: str, body: Any = None, *, token: str = _OWNER_TOKEN,
            node: bool = False,
        ) -> tuple[int, dict[str, Any]]:
            data = None if body is None else json.dumps(body).encode()
            headers = {"content-type": "application/json"}
            if node:
                headers["x-holdspeak-node-token"] = token
            else:
                headers["authorization"] = f"Bearer {token}"
            outgoing = urllib.request.Request(
                base + path, data=data, headers=headers, method=method
            )
            try:
                with urllib.request.urlopen(outgoing, timeout=10) as response:
                    return response.status, json.load(response)
            except urllib.error.HTTPError as exc:
                return exc.code, json.load(exc)
    
        def start() -> subprocess.Popen[str]:
            process = subprocess.Popen(
                [sys.executable, "-m", "holdspeak.main", "web", "--no-open"],
                cwd=_REPO,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for _ in range(100):
                if process.poll() is not None:
                    output = process.stdout.read() if process.stdout else ""
                    raise AssertionError(f"spawned hub exited early:\n{output}")
                try:
                    with urllib.request.urlopen(base + "/health", timeout=0.2):
                        return process
                except Exception:
                    time.sleep(0.1)
            process.kill()
            output = process.stdout.read() if process.stdout else ""
            raise AssertionError(f"spawned hub did not become healthy:\n{output}")
    
>       process = start()
                  ^^^^^^^

tests/integration/test_kernel_real_hub.py:124: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    def start() -> subprocess.Popen[str]:
        process = subprocess.Popen(
            [sys.executable, "-m", "holdspeak.main", "web", "--no-open"],
            cwd=_REPO,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for _ in range(100):
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise AssertionError(f"spawned hub exited early:\n{output}")
            try:
                with urllib.request.urlopen(base + "/health", timeout=0.2):
                    return process
            except Exception:
                time.sleep(0.1)
        process.kill()
        output = process.stdout.read() if process.stdout else ""
>       raise AssertionError(f"spawned hub did not become healthy:\n{output}")
E       AssertionError: spawned hub did not become healthy:

tests/integration/test_kernel_real_hub.py:122: AssertionError
_ TestNotificationTransitions.test_a_changed_item_with_the_same_count_notifies _
[gw8] darwin -- Python 3.14.2 /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python3

self = <tests.unit.test_phase200_attention.TestNotificationTransitions object at 0x115ca47d0>
db = <holdspeak.db.core.Database object at 0x11c3dd090>

    def test_a_changed_item_with_the_same_count_notifies(self, db: Database) -> None:
        """The audit's defect: 3 -> 3 with one item swapped was silent."""
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
        first = _sweep(svc, _agg([_row("a"), _row("b"), _row("c")]))
>       assert first["outcome"] == "sent"
E       AssertionError: assert 'held_quiet_hours' == 'sent'
E         
E         - sent
E         + held_quiet_hours

tests/unit/test_phase200_attention.py:508: AssertionError
_ TestNotificationTransitions.test_mute_silences_a_room_and_unmute_renotifies_only_what_arrived_meanwhile _
[gw8] darwin -- Python 3.14.2 /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python3

self = <tests.unit.test_phase200_attention.TestNotificationTransitions object at 0x11565f100>
db = <holdspeak.db.core.Database object at 0x11c3dd1d0>

    def test_mute_silences_a_room_and_unmute_renotifies_only_what_arrived_meanwhile(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
>       assert _sweep(svc, _agg([_row("a", "p1"), _row("x", "p2")]))["outcome"] == "sent"
E       AssertionError: assert 'held_quiet_hours' == 'sent'
E         
E         - sent
E         + held_quiet_hours

tests/unit/test_phase200_attention.py:556: AssertionError
_________ TestNotificationTransitions.test_restart_renotifies_nothing __________
[gw8] darwin -- Python 3.14.2 /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python3

self = <tests.unit.test_phase200_attention.TestNotificationTransitions object at 0x115f94ef0>
db = <holdspeak.db.core.Database object at 0x11c3dd950>

    def test_restart_renotifies_nothing(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc1 = _service(db, calls)
        items = _agg([_row("a"), _row("b"), _row("c")])
>       assert _sweep(svc1, items)["outcome"] == "sent"
E       AssertionError: assert 'held_quiet_hours' == 'sent'
E         
E         - sent
E         + held_quiet_hours

tests/unit/test_phase200_attention.py:575: AssertionError
_ TestNotificationTransitions.test_recovery_after_a_failed_source_is_never_an_all_clear_and_renotifies_nothing _
[gw8] darwin -- Python 3.14.2 /Users/karol/dev/tools/HoldSpeak-Philo/.venv/bin/python3

self = <tests.unit.test_phase200_attention.TestNotificationTransitions object at 0x115ffd6a0>
db = <holdspeak.db.core.Database object at 0x11c3ddbd0>

    def test_recovery_after_a_failed_source_is_never_an_all_clear_and_renotifies_nothing(self, db: Database) -> None:
        calls: list[tuple[str, str]] = []
        svc = _service(db, calls)
>       assert _sweep(svc, _agg([_row("a", "p1"), _row("b", "p1")]))["outcome"] == "sent"
E       AssertionError: assert 'held_quiet_hours' == 'sent'
E         
E         - sent
E         + held_quiet_hours

tests/unit/test_phase200_attention.py:590: AssertionError
_ TestNotificationT
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-20T03:23:08Z

- **Command:** `.venv/bin/python .tmp/philo/rerun_runtime.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** fdbd0e5ba9f51d7620312f1e783a461a8a6269fc

```text
Command: .venv/bin/python -m pytest -q tests/e2e/test_hs174_remote_settings_glass.py::TestSettingsRemoteAccess::test_remote_on_issue_revoke[393] tests/integration/test_kernel_real_hub.py::test_real_http_executor_receipt_and_sigkill_cursor_replay tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_a_changed_item_with_the_same_count_notifies tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_mute_silences_a_room_and_unmute_renotifies_only_what_arrived_meanwhile tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_restart_renotifies_nothing tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_recovery_after_a_failed_source_is_never_an_all_clear_and_renotifies_nothing tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_a_resolved_item_from_an_observed_project_is_forgotten_and_can_return_as_new tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_escalation_fires_through_the_sweep_and_says_so tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_counsel_probe_2b_archived_project_ids_leave_the_settings tests/unit/test_phase200_attention.py::TestNotificationTransitions::test_the_policy_row_is_written_only_when_the_set_or_outcome_changed --junitxml=.tmp/philo/runtime-rerun.xml
..........                                                               [100%]
10 passed in 13.05s
```

### Captured run — 2026-09-20T03:23:58Z

- **Command:** `bash .tmp/philo/verify_final.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8b33e52f83a63af548c7b32f3141f162bcff9d0c

```text
........................................................................ [ 78%]
....................                                                     [100%]
92 passed in 54.48s
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
Repository census: 5 outputs verified.
API reference checked
Boundary candidate census checked
Doctor reference: 41 check functions
Configuration declaration reference is current
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
Architecture documentation checked (10 outputs).
Documentation coverage checked.
```

## Reproduction and interpretation

The original full suite failed. Later captures prove narrower repairs and reruns,
not a second green full suite. See docs/generated/DOCUMENTATION_AUDIT_REPORT.md
and docs/internal/philo/checks/baseline-failures.md for failure dispositions.

### Final documentation runner

```bash
#!/bin/bash
set -euo pipefail
source .tmp/philo/env.sh
export PATH="$PWD/.tmp/philo/mermaid/node_modules/bin:$PWD/.tmp/philo/mermaid/node_modules/.bin:$PATH"
export PUPPETEER_EXECUTABLE_PATH='/Users/karol/.cache/puppeteer/chrome/mac_arm-149.0.7827.22/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'
PHILO_TEST_HOME=$(mktemp -d)
HOME="$PHILO_TEST_HOME" uv run pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_philo_architecture.py tests/unit/test_philo_census.py tests/unit/test_phase200_doc_claims.py tests/unit/test_api_surface.py tests/e2e/test_mermaid_renders.py
.venv/bin/python scripts/check_docs.py
.venv/bin/python scripts/check_docs.py docs/internal/philo/*.md docs/internal/philo/adr/*.md docs/internal/philo/checks/*.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/*/SKILL.md
.venv/bin/python scripts/philo_repository_census.py --check
.venv/bin/python scripts/philo_api_reference.py --check
.venv/bin/python scripts/philo_boundary_census.py --check
.venv/bin/python scripts/philo_doctor_reference.py --check
.venv/bin/python scripts/philo_config_reference.py --check
.venv/bin/python scripts/validate_architecture.py
.venv/bin/python scripts/generate_capability_docs.py --check
.venv/bin/python scripts/check_doc_coverage.py --check
git diff --check
```

### Full suite runner

```bash
#!/bin/bash
set -euo pipefail
cd /Users/karol/dev/tools/HoldSpeak-Philo
source .tmp/philo/env.sh
export PATH="$PWD/.tmp/philo/mermaid/node_modules/.bin:$PATH"
export PUPPETEER_EXECUTABLE_PATH='/Users/karol/.cache/puppeteer/chrome/mac_arm-149.0.7827.22/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'
PHILO_TEST_HOME=$(mktemp -d)
printf '%s\n' "$PHILO_TEST_HOME" > .tmp/philo/full-suite-home.txt
PHILO_TEST_STATUS=0
env HOME="$PHILO_TEST_HOME" uv run pytest -q -n auto --ignore=tests/e2e/test_metal.py --junitxml=.tmp/philo/full-suite.xml > .tmp/philo/full-suite.log 2>&1 || PHILO_TEST_STATUS=$?
cat .tmp/philo/full-suite.log
exit "$PHILO_TEST_STATUS"
```

### Complete web quality output inspected by Astra

Command: `npm --prefix web run check` with the clone-local Node PATH from
`.tmp/philo/env.sh`. Exit code 0. The command includes token checks, architecture
guards, TypeScript, Vitest, production build and bundle gate. Relevant output:

```text
React architecture guard passed (772 source files; zero framework residue).
 Test Files  265 passed (265)
      Tests  2540 passed (2540)
   Duration  85.47s (transform 6.49s, setup 12.20s, import 32.80s, tests 52.45s, environment 52.14s)
✓ built in 4.99s
bundle gate passed (Desk JS 1303216 B; Desk CSS 318681 B; source maps 0)
```
