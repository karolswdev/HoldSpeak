# Evidence - HS-129-09

- **Story:** HS-129-09 - One state grammar
- **Status:** done
- **Date:** 2026-08-08

## Proof

### Captured run — 2026-08-08T21:45:51Z

- **Command:** `bash -lc cd web && npx vitest run src/desk/__tests__/stateGrammar.test.tsx --maxWorkers=2 && npx tsc --noEmit`
- **Cwd:** .
- **Exit code:** 134
- **Index-tree:** efbb7c58399e9fb0a232bb70f1b2d0f9895c925b

```text
dyld[20845]: Library not loaded: /opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib
  Referenced from: <BD9D65B7-B478-3E6C-8530-96FD5D1D2AF9> /opt/homebrew/Cellar/node/25.9.0/bin/node
  Reason: tried: '/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file)
bash: line 1: 20845 Abort trap: 6           npx vitest run src/desk/__tests__/stateGrammar.test.tsx --maxWorkers=2
```

### Captured run — 2026-08-08T21:46:10Z

- **Command:** `bash -c cd web && npx vitest run src/desk/__tests__/stateGrammar.test.tsx --maxWorkers=2 && npx tsc --noEmit`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** efbb7c58399e9fb0a232bb70f1b2d0f9895c925b

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  1 passed (1)
      Tests  3 passed (3)
   Start at  15:46:11
   Duration  834ms (transform 52ms, setup 123ms, import 30ms, tests 5ms, environment 531ms)
```
