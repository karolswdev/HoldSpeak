# Evidence - HS-129-03

- **Story:** HS-129-03 - The Brief pathology and Intelligence polish
- **Status:** done
- **Date:** 2026-08-08

## Proof

### Captured run — 2026-08-08T21:27:27Z

- **Command:** `bash -lc cd web && npx vitest run src/desk/pullouts/IntelligencePullout.test.tsx src/desk/pullouts/IntelligenceWalk.test.tsx --maxWorkers=2 && npm run typecheck`
- **Cwd:** .
- **Exit code:** 134
- **Index-tree:** 61c3027f92fe53b31354746421f4279f709726ec

```text
dyld[99384]: Library not loaded: /opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib
  Referenced from: <BD9D65B7-B478-3E6C-8530-96FD5D1D2AF9> /opt/homebrew/Cellar/node/25.9.0/bin/node
  Reason: tried: '/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file)
bash: line 1: 99384 Abort trap: 6           npx vitest run src/desk/pullouts/IntelligencePullout.test.tsx src/desk/pullouts/IntelligenceWalk.test.tsx --maxWorkers=2
```

### Captured run — 2026-08-08T21:27:41Z

- **Command:** `zsh -lc cd web && npx vitest run src/desk/pullouts/IntelligencePullout.test.tsx src/desk/pullouts/IntelligenceWalk.test.tsx --maxWorkers=2 && npm run typecheck`
- **Cwd:** .
- **Exit code:** 134
- **Index-tree:** 61c3027f92fe53b31354746421f4279f709726ec

```text
dyld[99723]: Library not loaded: /opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib
  Referenced from: <BD9D65B7-B478-3E6C-8530-96FD5D1D2AF9> /opt/homebrew/Cellar/node/25.9.0/bin/node
  Reason: tried: '/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file)
```

### Captured run — 2026-08-08T21:27:58Z

- **Command:** `env PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:/usr/bin:/bin /bin/zsh -c cd web && npx vitest run src/desk/pullouts/IntelligencePullout.test.tsx src/desk/pullouts/IntelligenceWalk.test.tsx --maxWorkers=2 && npm run typecheck`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 61c3027f92fe53b31354746421f4279f709726ec

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  2 passed (2)
      Tests  10 passed (10)
   Start at  15:27:59
   Duration  1.38s (transform 614ms, setup 163ms, import 978ms, tests 616ms, environment 680ms)


> holdspeak-web@0.0.1 typecheck
> tsc --noEmit
```
