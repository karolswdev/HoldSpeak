# Evidence - HS-170-01

- **Story:** HS-170-01 - The census (every surface shot at 1440 + 393 on an isolated desk; the canon-violation scan across the web tree; one ranked table per face by Tuesday use × canon debt)
- **Status:** done
- **Date:** 2026-09-04

## Proof

### Captured run — 2026-09-05T04:51:23Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.JdonJQspAt uv run pytest -q tests/e2e/test_hs170_census_glass.py tests/unit/test_ux_canon_scan.py -p no:randomly -p no:cacheprovider`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 847192707f362dc5f445b88c733955d0fad01e62

```text
F..                                                                      [100%]
=================================== FAILURES ===================================
______________________________ test_census_glass _______________________________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-5820/test_census_glass0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x107dbb100>

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    @pytest.mark.timeout(900)
    def test_census_glass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """HS-170-01: shoot every surface at both widths and write the census table."""
        census = CensusResult()
        for width in WIDTHS:
            sub = tmp_path / str(width)
            sub.mkdir(parents=True, exist_ok=True)
>           _run_census(sub, monkeypatch, width, census)

tests/e2e/test_hs170_census_glass.py:523: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_hs170_census_glass.py:369: in _run_census
    _ensure_build()
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    def _ensure_build() -> None:
        """Build the web bundle if any web source is newer than the marker.
    
        Cross-process safe (fcntl lock under web/); once per process after
        the first check. Never trusts a marker older than the sources.
        """
        global _build_done
        if _build_done:
            return
        built_marker = REPO / "holdspeak" / "static" / "_built" / "index.html"
        lock_path = REPO / "web" / ".glass-build.lock"
        with open(lock_path, "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                # Trust the OLDEST built chunk, never index.html: the marker
                # can be touched by anything; a build that raced or failed
                # midway leaves stale chunks behind it (seen live 2026-09-03:
                # a fresh marker over 13-minute-old chunks).
                assets_dir = built_marker.parent / "assets"
                chunk_mtimes = [f.stat().st_mtime for f in assets_dir.glob("*.js")] if assets_dir.exists() else []
                built_mtime = min(chunk_mtimes) if (chunk_mtimes and built_marker.exists()) else 0.0
                if built_mtime >= _newest_web_source_mtime():
                    _build_done = True
                    return
                started = time.monotonic()
                result = subprocess.run(
                    ["npm", "--prefix", str(REPO / "web"), "run", "build"],
                    capture_output=True, text=True, timeout=300,
                )
>               assert result.returncode == 0, (
                       ^^^^^^^^^^^^^^^^^^^^^^
                    f"Web build failed:\n{result.stderr}\n{result.stdout}"
                )
E               AssertionError: Web build failed:
E               ✗ Build failed in 303ms
E               error during build:
E               [vite:esbuild] Transform failed with 1 error:
E               /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AttentionDrawer.tsx:274:10: ERROR: Expected ":" but found ")"
E               file: /Users/karol/dev/tools/HoldSpeak/web/src/desk/components/AttentionDrawer.tsx:274:10
E               
E               Expected ":" but found ")"
E               272 |              );
E               273 |            })()
E               274 |            ) : (
E                   |            ^
E               275 |              <>
E               276 |                <ol className="desk-attention-list">
E               
E                   at failureErrorWithLog (/Users/karol/dev/tools/HoldSpeak/web/node_modules/esbuild/lib/main.js:1748:15)
E                   at /Users/karol/dev/tools/HoldSpeak/web/node_modules/esbuild/lib/main.js:1017:50
E                   at responseCallbacks.<computed> (/Users/karol/dev/tools/HoldSpeak/web/node_modules/esbuild/lib/main.js:884:9)
E                   at handleIncomingPacket (/Users/karol/dev/tools/HoldSpeak/web/node_modules/esbuild/lib/main.js:939:12)
E                   at Socket.readFromStdout (/Users/karol/dev/tools/HoldSpeak/web/node_modules/esbuild/lib/main.js:862:7)
E                   at Socket.emit (node:events:519:28)
E                   at addChunk (node:internal/streams/readable:561:12)
E                   at readableAddChunkPushByteMode (node:internal/streams/readable:512:3)
E                   at Readable.push (node:internal/streams/readable:392:5)
E                   at Pipe.onStreamRead (node:internal/stream_base_commons:189:23)
E               
E               
E               > holdspeak-web@0.0.1 build
E               > vite build
E               
E               vite v7.3.6 building client environment for production...
E               transforming...
E               ✓ 113 modules transformed.

tests/e2e/glass_infra.py:80: AssertionError
=========================== short test summary info ============================
FAILED tests/e2e/test_hs170_census_glass.py::test_census_glass - AssertionErr...
1 failed, 2 passed in 0.98s
```
