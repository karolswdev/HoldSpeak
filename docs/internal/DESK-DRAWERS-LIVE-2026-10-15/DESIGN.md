# Restore drawers and live backgrounds

Owner, 2026-10-15: "then change them?" This explicitly reverses the October 10
still-only atmosphere interpretation. Base bea522beb; worktree
wt-desk-drawers-live-20261015, branch feat/desk-drawers-live-20261015.
Tuesday: find existing folders, open their real contents, and see the selected
live wallpaper while all Desk controls remain usable. Tenets 3/5/6; Articles I/II.

## Settled design

Root folders are real Directory primitives, drawn as existing drawer DeskIcons.
Nested directories open from their parent; directory member refs stay canonical,
legacy bare refs remain supported. Filed items are not also loose on Desk.
Missing parents must not strand a folder. Do not modify shared world lookup,
storage, directory APIs, project Room navigation or the old Floor.
Phone retains Go; add the same root folders as a named Drawers section using
existing components. Opening uses the existing qualified directory pullout.
DirectoryPullout composes current Surface rows with actual child folders and
members; canonical open handlers, no zero count, raw button or dead Drop action.
Unknown members must not silently become an empty drawer. Keep the current
filing strip. No new drag/drop or folder data model.

Mount the existing Atmosphere behind the current Screen, lazy scene loading
and one renderer only. Preserve chosen still during loading or failed WebGL;
clear it only after the live canvas is ready. Quiet Desk stays plain and has
no scene allocation. Pointer events pass through scenery. Existing passive
pointer observer, visibility suspension, reduced-motion and explicit motion
preferences remain. Add an existing Motion CheckGadget in Wallpaper settings wired to the current persisted motion preference, after the choice grid. No sound opt-in or microphone access changes. Selection,
marquee, icons, windows and touch keep their current handlers. No second Floor,
new renderer framework or changes to individual scene visuals.

## Lanes and verification

Folders lane owns screen/compose.ts, screen/GoHome.tsx, pullouts/DirectoryPullout.tsx,
new pullouts/DirectoryPullout.test.tsx, screen/__tests__/Screen.test.tsx and
screen/__tests__/chairScreen.test.tsx only. Focused tests: those three files,
plus desk/__tests__/world.test.ts if present; inspect actual names first.
Background lane owns screen/Screen.tsx, screen/screen.css, gl/Atmosphere.tsx,
gl/__tests__/Atmosphere.test.tsx, gl/__tests__/atmosphereRuntime.test.ts and a
new screen/__tests__/screenAtmosphere.test.tsx, pages/cores/settingsWallpaper.tsx and its __tests__/settingsWallpaper.test.tsx only. Focused tests: those three
plus gl/__tests__/atmosphereRegistry.test.ts and settingsWallpaper.test.tsx. No touching folder lane files.
Review amendment: folder lane also owns verbRegistry.ts, objectMenu.ts and their existing exact two __tests__ files. The bounded source review found directory menu Open returning without action, canonical collision suppression from bare refs, and all roots hidden by a filing cycle. Restore Open through the existing canonical pullout; resolve each legacy ref to one canonical object; keep a deterministic root for each effective-parent cycle. No backend or filing writer changes. Both read TWO-BRAINS/CLAUDE fast cycle and canon, inspect anchors for drift.
Workers wait for root's canvas-read message before product edits. No install,
browser, build, staging or commits. Scoped tests only through root locked.py,
isolated HOME; collect before run, record real red/green output. HOLD FOR SHIP.
Root owns canvas, real browser observations at 1440/393, actual stored folder
producers, moving-pixel and pointer checks on registered scenes, scoped claims,
quick, PR/merge/status and normal local deployment. No test touches owner HOME,
DB, Keychain, clipboard, microphone, provider or native tmux.

Runtime seam amendment: the nested drawer shot exposed a misleading inherited
`Filed · Desk root` caption. Root corrects only DeskFilingStrip's summary lookup
to prefer the Directory's stored parent, with a new three-case focused test.
Existing filing controls and writers stay intact. This diagnosed correction is
outside the completed bounded source counsel and receives final drawer shots
at both widths, release TypeScript and the complete quick check.
