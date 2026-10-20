# Audio feedback about the interface

Start the desk with the feedback flag:

```sh
HOLDSPEAK_UI_FEEDBACK=1 holdspeak web --no-open
```

The flag is off by default. It is read by the running server; the web bundle does not need a special build.

1. Open **Desk > Give feedback** (**Go > Give feedback** on a phone).
2. Select the element you want to talk about. This press does not run the element's action.
3. Wait for **Recording**, then speak.
4. Press **Stop and save**. Wait for **Saved** before you move on.

The report keeps a PNG of the selected window, its current field values and text, the selected element and its position, the window identity and geometry, and your original WAV audio. Unsaved field values are included. Password and credential fields are excluded. The image and state are captured before recording; Save or Retry does not replace them with a later state.

Reports are local files under `~/.local/share/holdspeak/feedback/`. Each report has its own folder with `report.json`, `audio.wav`, `window.png` and `README.md`. **Copy path** copies that folder's path so you can give it to the coding agent. Nothing is sent to GitHub, an agent service or a speech provider. A speech model is not required to save the original audio.

Use localhost or HTTPS for browser microphone access. If another capture owns the microphone, stop that capture first. **Cancel** stops this feedback recording. If Save fails, **Retry** saves the same report.

For implementation and checks, see [PLAN.md](PLAN.md).
