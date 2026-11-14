Parked: #2332 replaces this CSS snap policy with the shared wholeRows row-anchor fitter.

ObjectList owns scrolling for standalone lists and ListPane. A content refit keeps the
owner's scroll position. A changed selection, row order or list seat reveals the
complete selected row with nearest-edge scrolling. Measured scroll padding reserves
overlapping column and group headings. Proximity snap points land scrolling on row
edges; a short paper tail keeps the final snap reachable without changing the pane's
height. A fitting list shows every row whole; an overflowing list can show part of the
next row at the bottom. listShare allocates the list and inspector widths; it does not
change this scroll policy.
