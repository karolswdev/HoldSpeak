# HS-140-03 browser acceptance — 2026-08-18

This sitting used a real loopback HoldSpeak hub in a fresh temporary `HOME`
for every run. It did not read or write the owner's normal state.

## Actually exercised

With Chromium's fake-device flag only to supply a capture device, the empty
isolated hub returned its real named **local transcription unavailable**
refusal. At both 1440×900 and 393×900 the FirstWords surface showed the
generic, honest Setup copy and the textarea accepted a typed fallback.

- [1440×900](./transcription-unavailable-real-1440x900.png)
- [393×900](./transcription-unavailable-real-393x900.png)

No page errors occurred in either state.

## Acceptance verdict

**PASS.** At both widths the one enabled recovery control is **Setup**; there
are zero enabled Retry controls, and the disabled mic label is neutral
(`Voice typing unavailable`). The typed fallback remains editable.

## Not claimed as physical-browser proof

Headless Chromium cannot supply a trustworthy physical microphone denial or a
real silent utterance on this host. A bounded injected `getUserMedia` denial
also stopped earlier at the browser's AudioWorklet support check, so it did not
exercise the app's permission-denied copy. The no-speech state was likewise
not captured as real-device evidence. Those two physical-capture legs remain
for the Story 06 cold-device walk; their contracts are covered by the focused
web tests.
