# PixelLab Documentation Assets

These assets were generated with the PixelLab MCP for HoldSpeak documentation
spot art and brand identity. Style anchor: the "Signal" web identity (dark-first,
signature orange `#FF6B35`). To regenerate any sprite, re-run its prompt against
the PixelLab MCP; for the *derived* card/icons (below) re-run
[`compose_og_card.py`](./compose_og_card.py) after the mark is regenerated.

## Brand identity (2026-06-03)

| File | PixelLab object ID | Prompt |
| --- | --- | --- |
| `holdspeak-mark.png` (128×128) | `52e0db41-4789-45b3-9136-1ee3e4e7838d` | App brand mark: a single glowing keyboard key being held/pressed down, with three rising curved soundwave arcs emanating from its top-right, signature warm orange (#FF6B35) key and waves, crisp clean modern pixel art logo for a local-first voice typing app, bold readable silhouette at small sizes, single color outline, transparent background. (view: side) |

**Derived from the mark** (composed by `compose_og_card.py`, not direct PixelLab
output — PixelLab makes ≤400px sprites, not wide banners):

| File | Derived from | Purpose |
| --- | --- | --- |
| `social-card.png` (1280×640) | `holdspeak-mark.png` + the workflow trio + Signal palette | GitHub social/OG preview card. **Manual step:** set it in repo *Settings → Social preview*. |
| `holdspeak-icon-256.png` (256×256) | `holdspeak-mark.png` | Square padded app icon. |
| `../../../web/public/apple-touch-icon.png` (180×180) | `holdspeak-mark.png` | Site apple-touch-icon (brand refresh). |

## Documentation spot art (2026-06-01)

These PNG assets were generated with the PixelLab MCP on 2026-06-01.

| File | PixelLab object ID | Prompt |
| --- | --- | --- |
| `hold-to-talk-microphone.png` | `bfc6e2ce-a455-41a9-8998-1088cfdc55ac` | Clean pixel art icon of a desktop microphone with a glowing hold-to-talk key and small sound wave lines, modern local-first voice app documentation asset, transparent background. |
| `meeting-intelligence-notebook.png` | `441f8cc0-888e-414f-9678-e0d1422f5ce8` | Clean pixel art icon of a meeting transcript notebook with two speaker bubbles, checkmark action items, and subtle AI sparkle, modern product documentation asset, transparent background. |
| `project-aware-typing.png` | `c6e192d8-6377-4aed-be25-db481a8463c8` | Clean pixel art icon of a code editor window connected to a small local knowledge folder and keyboard cursor, project-aware intelligent typing documentation asset, transparent background. |
| `aipi-lite-companion.png` | `c76b85ce-e780-4126-bc00-d004d885de3c` | Transparent background pixel art of a portable green ESPHome AI companion device inspired by AIPI-Lite hardware, handheld rectangular board with black screen, small microphone grille, two physical buttons, USB-C port, tiny Wi-Fi hotspot signal icon, meeting recording status glow, clean product documentation asset. |
| `operator-working-loop.gif` | object `4f082922-434b-49ef-9a1a-ced16274765f`, animation group `ee5f9031-47d1-45d1-929f-54c5ae13bc9b` | Base object: transparent background pixel art mini scene, charming video game operator character wearing a headset seated at a glowing terminal, small green AIPI-style companion device on the desk, floating transcript cards, code cards, and checkmark task cards around them. Animation: character types, monitor text scrolls softly, companion device blinks, floating cards bob, and checkmark task cards tick on one by one. |
