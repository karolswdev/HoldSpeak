# Workbench meets Pop!_OS — shared shell, 2026-10-22

Owner direction: Ask still looks wrong; modernize the windows and common shell, “Workbench meets PopOS.” This is explicit authorization to evolve older Steel material prescriptions. The desktop, native object/window model, library components, real pixel icons, consent, voice and keyboard behavior remain the product. Tenets 3, 5, 6 and 7: can the architect comfortably read an answer and configure a tool on Tuesday?

Owner-started session; Setup-installed HoldSpeak MCP project.list has no HoldSpeak project, so project.get is inapplicable. memory.search read before edits; no newer visual brief. Source canon read in order: TWO-BRAINS, CLAUDE fast cycle, Constitution, UX-CANON, DESIGN_SYSTEM, orchestration. Latest CLAUDE fast cycle: build the direction, required quick, merge/deploy, owner judges live; mockups are directional, not acceptance gates.

## Settled direction before build

Canvas: canvases/modern-shell-2026-10-22.html. Reference: System76 COSMIC theming and UX (https://system76.com/cosmic/theming and https://system76.com/cosmic/ux), interpreted into our component framework, not copied app structure.

Light modern shell over a quiet slate desktop. Cool pale chrome, near-white paper, dark ink, a restrained Workbench blue primary/selection. Front windows have a fine blue edge and soft depth; resting windows have a quiet grey edge and reduced depth. No heavy black 4px casing, title hatching, hard offset drop or doubled bevels. Window radius 8, control radius 5, thin rules; keep pixel sprites and recognisable Workbench control placement. Desktop title bars 36px, narrow 44px. Titles 14px/600 sans; body 14, primary 15, display 26; mono 12 reserved for facts, hosts, keys and code. Normal library Buttons 32px desktop, primary 34+ as content requires; narrow actual/owned 44px remains a floor. Ghost is a quiet transparent action with visible hover/focus, secondary a light control with a fine border, primary blue with white text. Inputs white with thin borders and a quiet focus ring. No loss of focus, disabled or pressed distinctions.

One continuous shell: shared frame/head/footer, menubar/menu and dock material change together. Keep dock working-band geometry, drag/resize edges, window planes, menu keyboarding, reduced motion, egress/feedback controls and single microphone authority. Desktop becomes an untextured slate field with subtle tonal depth; keep existing place images when selected. Pixel-icon labels lose bright boxed labels in favor of readable quiet desktop labels. Content stays directly on window paper, never nested dashboard cards. Ask and Settings harmonize to shared chrome/paper; no local theme or independent design system.

## Lanes and scope

Worktree /Users/karol/dev/tools/wt-modern-shell-20261022, branch feat/modern-shell-20261022, base 448772a89422a861b166b604552b1acf79e944a9. Root owns direction/canvas, canon amendment, verification/tests, status and delivery. Workers implement settled CSS/tokens only in disjoint files. Anchors drift: locate symbols. Hold for SHIP; no staging or commits. No tests/build/typecheck until root freezes source. Root uses scripts/test_lock.py, isolated HOME and -n8; never metal or owner writes. Required quick before merge; post-merge review and background tape. Owner judges aesthetics live; technical checks do not claim flagship acceptance.

## Verification findings before delivery

The first rendered pass exposed the old --alive-paper literal overriding
shared paper: the common alias now follows --wb-paper instead. Thin frames
also exposed resize hit edges outside the frame, fixed by insetting their
existing 6px/14px regions. Full-width phone sheets retain their structural
zero-width border with the shared rounded focus edge. Functional/hit tests
remain strict. The old frame tests' stripe/26px/literal-blue expectations now
assert the new flat active-head token and 36px/44px heights. Two inherited
frame-menu failures on main used obsolete “Iconify”/“Close window” labels;
those now match the actual “Minimize”/“Close” producers while still checking
all entries, exact keycaps, withholding and 44px phone rows.

Token generation passes. The inherited raw-token gate reports 120 findings on
main and fewer on this branch, with zero branch-new file/match pairs; no
allow-list or ceiling is expanded. Baseline full tape 12 Python/10 browser reds
remain recorded in pm/STATUS.md. Owner aesthetic judgment stays live.

The second browser pass passed 15 of 17 cases. The remaining checks required the
head's pressed fill to use its shared token and measured a transparent pixel
outside a rounded window corner. Pressed fill now has one token authority;
window-plane probes follow the painted curve, while Button 9-point hit checks
stay unchanged. Head focus uses blue rather than white-on-pale chrome.
Settings selected categories now use the actual pale-blue token and a fine
blue outline; generic/primary/danger held controls retain readable contrast.

The required whole-desk sweep then caught shared regressions absent from the
focused pass: rounded-control hit corners, clipped labels, shelf/bar geometry
and faint/ember contrast. Those are corrected in shared material and layout;
Button ownership, contrast and clipping fences remain unchanged. Three stale
glyph exceptions are removed because the controls now meet the 12 px floor.
