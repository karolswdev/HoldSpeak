# Evidence - HS-128-01

- **Story:** HS-128-01 - Intelligence pullout shell
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T02:21:47Z

- **Command:** `npx vitest run src/desk/pullouts/IntelligencePullout.test.tsx --maxWorkers=2`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** dea6899326d8f4672b10cfe84e0babeaf6d83be9

```text

 RUN  v4.1.10 /Users/karol/dev/tools/HoldSpeak

 ❯ web/src/desk/pullouts/IntelligencePullout.test.tsx (3 tests | 3 failed) 3ms
     × registers the Intelligence primitive in the pullout registry 2ms
     × opens on Brief and changes the active view 0ms
     × restores the last selected view after reopening 0ms

⎯⎯⎯⎯⎯⎯⎯ Failed Tests 3 ⎯⎯⎯⎯⎯⎯⎯

 FAIL  web/src/desk/pullouts/IntelligencePullout.test.tsx > HS-128-01 Intelligence pullout > registers the Intelligence primitive in the pullout registry
 FAIL  web/src/desk/pullouts/IntelligencePullout.test.tsx > HS-128-01 Intelligence pullout > opens on Brief and changes the active view
 FAIL  web/src/desk/pullouts/IntelligencePullout.test.tsx > HS-128-01 Intelligence pullout > restores the last selected view after reopening
ReferenceError: localStorage is not defined
 ❯ web/src/desk/pullouts/IntelligencePullout.test.tsx:14:33
     12|
     13| describe("HS-128-01 Intelligence pullout", () => {
     14|   beforeEach(() => localStorage.clear());
       |                                 ^
     15|
     16|   it("registers the Intelligence primitive in the pullout registry", (…

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/3]⎯


 Test Files  1 failed (1)
      Tests  3 failed (3)
   Start at  20:21:50
   Duration  422ms (transform 202ms, setup 0ms, import 335ms, tests 3ms, environment 0ms)
```

### Captured run — 2026-08-08T02:23:20Z

- **Command:** `bash -lc cd web && npx vitest run src/desk/pullouts/IntelligencePullout.test.tsx --maxWorkers=2`
- **Cwd:** .
- **Exit code:** 134
- **Index-tree:** 60c4734231f5aa0c9534c905d6b3d532fcc9dd4d

```text
dyld[19064]: Library not loaded: /opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib
  Referenced from: <BD9D65B7-B478-3E6C-8530-96FD5D1D2AF9> /opt/homebrew/Cellar/node/25.9.0/bin/node
  Reason: tried: '/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/opt/llhttp/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file), '/System/Volumes/Preboot/Cryptexes/OS/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file), '/opt/homebrew/Cellar/llhttp/9.4.1/lib/libllhttp.9.3.dylib' (no such file)
bash: line 1: 19064 Abort trap: 6           npx vitest run src/desk/pullouts/IntelligencePullout.test.tsx --maxWorkers=2
```

### Captured run — 2026-08-08T02:23:39Z

- **Command:** `sh -c cd web && npx vitest run src/desk/pullouts/IntelligencePullout.test.tsx --maxWorkers=2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 60c4734231f5aa0c9534c905d6b3d532fcc9dd4d

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  1 passed (1)
      Tests  3 passed (3)
   Start at  20:23:39
   Duration  777ms (transform 260ms, setup 39ms, import 397ms, tests 96ms, environment 173ms)
```
