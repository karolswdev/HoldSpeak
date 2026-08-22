# Evidence — HSEGHS001HS104-142-05 Model Setup Wizard

- Models now opens on a three-step Location → Model → Review flow.
- Device, OpenRouter, and Tool experiments are mutually exclusive views; the
  browser never mounts the entire catalog wall at once.
- Full model names and explanations wrap. The old ellipsis/nowrap rules were
  removed.
- Review contains the selected model and the sole lawful action; Change model
  and Change location navigate backward without mutation.

Verification:

- Focused Models component: 7 passed.
- Production web build: passed.
- Isolated-HOME 1440/393 Models glass: 2 passed.
- Screenshots inspected for initial Location and Hammer Review states at both
  widths.
