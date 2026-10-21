# Audio feedback about the interface

Start the desk with the feedback flag:

```sh
HOLDSPEAK_UI_FEEDBACK=1 holdspeak web --no-open
```

The flag is off by default. It is read by the running server; the web bundle does not need a special build.

1. Press **Feedback** in the title bar of the window you want to discuss.
2. Wait for **Recording**, then speak.
3. Press **Stop and save**. Wait for **Saved** before you move on.

To point to a specific element, use **Desk > Give feedback** (**Go > Give feedback** on a phone), then select the element. This press does not run the element's action.

The report keeps a PNG of the selected window, its current field values and text, the selected element and its position, the window identity and geometry, and your original WAV audio. After these files are saved, HoldSpeak transcribes the recording through your configured Speak engine and adds `transcript.txt`. Unsaved field values are included. Password and credential fields are excluded. The image and state are captured before recording; Save or Retry does not replace them with a later state.

Reports are local files under `~/.local/share/holdspeak/feedback/`. Each report has its own folder with `report.json`, `audio.wav`, `window.png`, `README.md` and, after transcription, `transcript.txt`. **Copy path** copies that folder's path so you can give it to the coding agent. Nothing is sent to GitHub or an agent service. Speech uses the same configured engine as Speak; the speech boundary is shown in the feedback strip. The original report is saved even when speech is unavailable.

Use localhost or HTTPS for browser microphone access. If another capture owns the microphone, stop that capture first. **Cancel** stops this feedback recording. If Save fails, **Retry** saves the same report. If transcription fails, **Saved** remains visible and **Retry transcription** retries the same saved recording. It does not capture the window or microphone again.

For implementation and checks, see [PLAN.md](PLAN.md).
