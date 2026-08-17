# Evidence - HS-135-06

- **Story:** HS-135-06 - The Chair is home
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-17T01:35:12Z

- **Command:** `bash -c cd /Users/karol/dev/tools/HoldSpeak/web && npx vitest run src/desk/chair/ChairHome.test.tsx src/desk/chair/Chair.test.tsx src/desk/__tests__/shell.test.tsx src/routes.test.ts src/desk/systemSprites.test.ts`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 56c5684976dc2cc5badc59425f180cbe541c0cbe

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web

stderr | src/desk/chair/ChairHome.test.tsx > ChairHome lane registry composition > renders with empty registry (all lanes commented out)
An update to FollowThroughLane inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://react.dev/link/wrap-tests-with-act
An update to FollowThroughLane inside a test was not wrapped in act(...).

When testing, code that causes React state updates should be wrapped into act(...):

act(() => {
  /* fire events that update state */
});
/* assert on the output */

This ensures that you're testing the behavior the user would see in the browser. Learn more at https://react.dev/link/wrap-tests-with-act

 ❯ src/desk/chair/ChairHome.test.tsx (5 tests | 1 failed) 22ms
     × renders with empty registry (all lanes commented out) 7ms

⎯⎯⎯⎯⎯⎯⎯ Failed Tests 1 ⎯⎯⎯⎯⎯⎯⎯

 FAIL  src/desk/chair/ChairHome.test.tsx > ChairHome lane registry composition > renders with empty registry (all lanes commented out)
TestingLibraryElementError: Unable to find an element with the text: Nothing yet. This could be because the text is broken up by multiple elements. In this case, you can provide a function for your text matcher to make your matcher more flexible.

Ignored nodes: comments, script, style
[36m<body>[39m
  [36m<div>[39m
    [36m<div[39m
      [33mclass[39m=[32m"chair"[39m
      [33mdata-testid[39m=[32m"chair"[39m
    [36m>[39m
      [36m<div[39m
        [33mclass[39m=[32m"chair-hero"[39m
        [33mdata-testid[39m=[32m"chair-hero"[39m
      [36m/>[39m
      [36m<div[39m
        [33mclass[39m=[32m"chair-lanes"[39m
        [33mdata-testid[39m=[32m"chair-lanes"[39m
      [36m>[39m
        [36m<div[39m
          [33mclass[39m=[32m"chair-lane"[39m
          [33mdata-lane[39m=[32m"follow-through"[39m
        [36m>[39m
          [36m<div[39m
            [33mclass[39m=[32m"surface-state"[39m
            [33mdata-kind[39m=[32m"loading"[39m
            [33mrole[39m=[32m"status"[39m
          [36m>[39m
            [36m<span[39m
              [33maria-hidden[39m=[32m"true"[39m
              [33mclass[39m=[32m"surface-state-glyph"[39m
            [36m>[39m
              [0m◌[0m
            [36m</span>[39m
            [36m<span[39m
              [33mclass[39m=[32m"sr-only"[39m
            [36m>[39m
              [0mLoading[0m
            [36m</span>[39m
          [36m</div>[39m
        [36m</div>[39m
      [36m</div>[39m
    [36m</div>[39m
  [36m</div>[39m
[36m</body>[39m
 ❯ Object.getElementError node_modules/@testing-library/dom/dist/config.js:37:19
 ❯ node_modules/@testing-library/dom/dist/query-helpers.js:76:38
 ❯ node_modules/@testing-library/dom/dist/query-helpers.js:52:17
 ❯ node_modules/@testing-library/dom/dist/query-helpers.js:95:19
 ❯ src/desk/chair/ChairHome.test.tsx:76:19
     74|       vi.advanceTimersByTime(300);
     75|     });
     76|     expect(screen.getByText("Nothing yet")).toBeInTheDocument();
       |                   ^
     77|     vi.useRealTimers();
     78|   });

⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯[1/1]⎯


 Test Files  1 failed | 4 passed (5)
      Tests  1 failed | 44 passed (45)
   Start at  19:35:13
   Duration  857ms (transform 513ms, setup 251ms, import 920ms, tests 307ms, environment 1.14s)
```

### Captured run — 2026-08-17T01:36:04Z

- **Command:** `bash -c cd /Users/karol/dev/tools/HoldSpeak/web && npx vitest run src/desk/chair/ChairHome.test.tsx src/desk/chair/Chair.test.tsx src/desk/__tests__/shell.test.tsx src/routes.test.ts src/desk/systemSprites.test.ts`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 56c5684976dc2cc5badc59425f180cbe541c0cbe

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  5 passed (5)
      Tests  45 passed (45)
   Start at  19:36:04
   Duration  874ms (transform 540ms, setup 249ms, import 960ms, tests 305ms, environment 1.16s)
```
