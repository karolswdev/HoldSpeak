# Evidence - PHILO-13-13

- **Story:** PHILO-13-13 - C3 — A live Dock (AppIcons)
- **Status:** done
- **Date:** 2026-10-03

## Proof

### Captured run — 2026-10-03T06:00:08Z

- **Command:** `bash -o pipefail -c uv run pytest -q -n auto --ignore=tests/e2e/test_metal.py --junitxml=.tmp/c3-conditions/full-python.xml | tee .tmp/c3-conditions/full-python.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 1f248b4bcd57bf8cd1d6961b9dc5f96ceb4cc951

```text
bringing up nodes...
bringing up nodes...

.....s.................................................................. [  0%]
.......................................................................F [  1%]
..........................F...s.....s................................... [  1%]
........................................................................ [  2%]
........................................................................ [  2%]
.....................................................................sss [  3%]
sssssssssssssssssss..................................................... [  3%]
........................................................................ [  4%]
........................................................................ [  4%]
...............................................................F........ [  5%]
............................sss...................F..................... [  5%]
........................................................................ [  6%]
........................................................................ [  6%]
........................................................................ [  7%]
.............................F.......................................... [  7%]
........................................................................ [  8%]
........................................................................ [  8%]
........................................................................ [  9%]
................................................................ss...... [  9%]
........................................................................ [ 10%]
........................................................................ [ 10%]
........................................................................ [ 11%]
..............F..F........FFFEsF.....F.................................. [ 11%]
.......sssss............................................................ [ 12%]
........................................................................ [ 12%]
...F.................................F.................................. [ 13%]
.....F.................................s................................ [ 13%]
........................................................................ [ 14%]
.......................................FEF.......FF..................... [ 14%]
..............................FFE...FFFFEEEEEEFEEEEEEFEEEEEEEFFEEEFFEFFE [ 15%]
E.E..FEFEF......E.E...........................................EF.EFEFFFF [ 15%]
FF.FF..FEEEEE.EFF.F.EEEEEE.E.EFEFF.FFFEFEF.EFEEFE.EFE................... [ 16%]
......................................EEEE.EEEEE...........FEE.EE....... [ 16%]
...................E............EFEE..........EE........................ [ 17%]
........................................................................ [ 17%]
....................E...E..............................EE......EE....E.F [ 18%]
F...E....FEEEEEEEEEEEEEEEFEEEFEEEEEEEEEsEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE [ 18%]
EEEEEEEEEEEEEEEEEEEEEEEE.EE.F....................E.............FEEEEEEEE [ 19%]
EEEEEEEEEEEF.EEEF.FE.FFFFEEsEFEEEEEFEEEEEEEEEEEEEEEFssEEEE..EEEF..FF.... [ 19%]
F......................................FEEEFEEEEEEEEEEEEE.EE.EEEEEEEEE.E [ 20%]
EEEEEEEE.E...F..E...................F....E.Traceback (most recent call last):
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/bin/pytest", line 10, in <module>
    sys.exit(console_main())
             ~~~~~~~~~~~~^^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/_pytest/config/__init__.py", line 223, in console_main
    code = main()
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/_pytest/config/__init__.py", line 199, in main
    ret: ExitCode | int = config.hook.pytest_cmdline_main(config=config)
                          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/pluggy/_hooks.py", line 512, in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/pluggy/_manager.py", line 120, in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 167, in _multicall
    raise exception
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 121, in _multicall
    res = hook_impl.function(*args)
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/_pytest/main.py", line 365, in pytest_cmdline_main
    return wrap_session(config, _main)
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/_pytest/main.py", line 353, in wrap_session
    config.hook.pytest_sessionfinish(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        session=session, exitstatus=session.exitstatus
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/pluggy/_hooks.py", line 512, in __call__
    return self._hookexec(self.name, self._hookimpls.copy(), kwargs, firstresult)
           ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/pluggy/_manager.py", line 120, in _hookexec
    return self._inner_hookexec(hook_name, methods, kwargs, firstresult)
           ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 167, in _multicall
    raise exception
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 139, in _multicall
    teardown.throw(exception)
    ~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/_pytest/logging.py", line 873, in pytest_sessionfinish
    return (yield)
            ^^^^^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 139, in _multicall
    teardown.throw(exception)
    ~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/_pytest/terminal.py", line 960, in pytest_sessionfinish
    result = yield
             ^^^^^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 139, in _multicall
    teardown.throw(exception)
    ~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/_pytest/warnings.py", line 118, in pytest_sessionfinish
    return (yield)
            ^^^^^
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/pluggy/_callers.py", line 121, in _multicall
    res = hook_impl.function(*args)
  File "/Users/karol/dev/tools/wt-philo-13-13-astra/.venv/lib/python3.14/site-packages/_pytest/junitxml.py", line 644, in pytest_sessionfinish
    with open(self.logfile, "w", encoding="utf-8") as logfile:
         ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
OSError: [Errno 28] No space left on device: '/Users/karol/dev/tools/wt-philo-13-13-astra/.tmp/c3-conditions/full-python.xml'
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! KeyboardInterrupt !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
/Users/karol/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/lib/python3.14/threading.py:373: KeyboardInterrupt
(to show a full traceback on KeyboardInterrupt use --full-trace)
```
