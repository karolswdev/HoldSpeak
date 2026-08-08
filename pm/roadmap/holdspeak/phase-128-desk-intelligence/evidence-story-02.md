# Evidence - HS-128-02

- **Story:** HS-128-02 - Brief view
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T02:26:20Z

- **Command:** `bash -c cd web && npm run typecheck`
- **Cwd:** .
- **Exit code:** 2
- **Index-tree:** c06d6d4eea77d547d321cb836029250823ae8e1c

```text

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit

src/desk/pullouts/views/ReceiptsView.tsx(166,19): error TS2322: Type '{ key: string; primary: string; lineLabel: string; onClick: () => void; cells: Element; }' is not assignable to type 'IntrinsicAttributes & { time?: ReactNode; lead?: ReactNode; primary: ReactNode; cells?: ReactNode; open?: boolean | undefined; ... 5 more ...; children?: ReactNode; }'.
  Property 'onClick' does not exist on type 'IntrinsicAttributes & { time?: ReactNode; lead?: ReactNode; primary: ReactNode; cells?: ReactNode; open?: boolean | undefined; ... 5 more ...; children?: ReactNode; }'.
src/desk/pullouts/views/ReceiptsView.tsx(208,38): error TS2322: Type '{ children: string; tone: string; }' is not assignable to type 'IntrinsicAttributes & { loading?: boolean | undefined; error?: string | undefined; empty?: boolean | undefined; emptyLabel?: string | undefined; emptyGlyph?: string | undefined; ... 4 more ...; children?: ReactNode; }'.
  Property 'tone' does not exist on type 'IntrinsicAttributes & { loading?: boolean | undefined; error?: string | undefined; empty?: boolean | undefined; emptyLabel?: string | undefined; emptyGlyph?: string | undefined; ... 4 more ...; children?: ReactNode; }'.
```

### Captured run — 2026-08-08T02:27:01Z

- **Command:** `bash -c cd web && npm run typecheck`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c06d6d4eea77d547d321cb836029250823ae8e1c

```text

> holdspeak-web@0.0.1 typecheck
> tsc --noEmit
```
