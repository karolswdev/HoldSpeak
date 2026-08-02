# HS-108-02 - Confine the desktop primitives

- **Project:** holdspeak
- **Phase:** 108
- **Status:** done
- **Depends on:** HS-108-01
- **Unblocks:** HS-108-06
- **Owner:** unassigned

## The thesis

`holdspeak/typer.py` becomes incapable of typing by itself. The nine live
raw statements move behind the warrant server and A10 is deleted.

## Recipe

1. Move clipboard and keyboard code into the privileged driver module.
2. Replace `TextTyper` with a warrant-only proxy.
3. Bind the desktop codec to its executor at trusted startup.
4. Pass the claimed operation, exact raw request, and signed warrant from
   `desktop_typing` to the proxy.
5. Preserve native and kernel receipt pairing.
6. Delete the dormant AppleScript helper.
7. Prove one real marker in TextEdit through the child.

## Acceptance

- `typer.py` contains none of `pyperclip`, `pynput`, `Controller`, or
  `osascript`.
- A direct `TextTyper.type_text("x")` refuses by name.
- Only the warrant server imports the raw driver.
- The real-metal marker and both receipts succeed.

## Test plan

`tests/unit/test_typer.py`,
`tests/unit/test_desktop_type_text_kernel.py`, the fence, and
`scripts/phase108_desktop_metal.py`.
