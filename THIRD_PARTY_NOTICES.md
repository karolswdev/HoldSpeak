# Third-party notices

HoldSpeak takes ideas, and in places code, from these projects. Each entry
names what was taken, where it is in HoldSpeak, and the license.

## Moonfold

- Project: Moonfold, https://github.com/Mr-Dark-debug/Moonfold
- License: MIT. Copyright (c) 2026 T3 Tools Inc. Copyright (c) 2026 Moonfold contributors.
- Taken: the idea of the provider handoff (an ordered fallback list of
  agents, a limit notice that offers "Continue in …", a deterministic handoff
  brief built from the thread's history without a model, redaction counted by
  kind, never twice for the same stopped turn, allowed providers per project,
  an optional usage warning). HoldSpeak's code is its own; no Moonfold code
  was copied.
- In HoldSpeak: `holdspeak/services/program_handoff.py`,
  `holdspeak/agent_context/usage_limit.py`, the PG19 parts of
  `holdspeak/services/program_runner.py` and `program_rules.py`
  (docs/internal/betterment/programs/PROGRAMS-DESIGN-2026-10-28.md, "PG19 Handoff").

MIT License text:

> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.
