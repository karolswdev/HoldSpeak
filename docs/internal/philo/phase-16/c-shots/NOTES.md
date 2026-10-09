# Lane 16c shots: Runs on (the Models window as a Switchboard)

Taken by `tests/e2e/test_hs170_concierge_glass.py` on 2026-10-09 (isolated
HOME hub; a fake OpenAI-compatible server on 127.0.0.1; the LAN address
192.168.77.43 is answered by that server through the rig's network double;
a catalog download whose acquisition the rig advances). Compare each with
canvas Board 2 (`../01-canvas/compositor.html`, "Board 2 · the exemplar
internal app").

| Shot | What it shows | Board 2 counterpart |
|---|---|---|
| `c1-board-1440.png` | The board: seven jobs, three engines wired (Speech → Whisper, Thoughts & notes → Qwen 3.5 4B, Default for AI work → qwen3.8 27B on the LAN), the plugs in their state colours, FOUND · 1 with Use it, a preset with Download and its host chip, Add an engine | the window at rest |
| `c2-patched-1440.png` | After a drag of the LAN engine onto Meetings: the new solid wire (hot), the foot receipt `PATCHED <time> · MEETINGS → QWEN3.8 27B`, the host chip 192.168.77.43, Undo | `Patched 09:14 · Meetings → qwen3.8 27B` |
| `c3-try-it-1440.png` | Try it on Meetings after the `Try on 192.168.77.43` press: `REACHED · QWEN3.8 27B` (a model-list read, so REACHED, and no ms token when none was measured); Try it on Thoughts & notes, a real request through its route after its own press: `READY · QWEN3.5-4B · <ms> MS` | "Try it on Meetings" |
| `c4-found-1440.png` | The FOUND row (a loopback server the scan found) with Use it | `Found · 2` |
| `c5-after-use-it-1440.png` | After Use it: the engine joined "What you have" with no wire; receipt `ADDED <time> · LLAMA3.3` | "Use the found Ollama" |
| `c6-download-mid-bar-1440.png` | A download at 42 %: the bar fills on the engine's own plate; the foot chip names HUGGINGFACE.CO | "Download the vision file" |
| `c7-meaning-search-1440.png` | The body scrolled: Meaning search, the ratified row under the board, clear of the foot | (not on the canvas; ratified 2026-10-09) |
| `c3-meaning-search-393.png` | The same at 393 | |
| `c1-list-393.png` | 393: the board as the job list; the open job, its engine, the other jobs; Try it in the foot | the phone sheet |
| `c2-list-patched-393.png` | 393 after a tap patch: Meetings runs on the LAN engine, `Or` the alternatives, receipt and Undo in the foot | `Tap an engine to patch` |

REACHED versus READY (ruling 2026-10-09, A.10): READY only when a real
route ran (Thoughts & notes' Ask probe; Speech's HEARD); every other job's
Try reads the engine's model list and says REACHED.
