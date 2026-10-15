# Finished source review

Independent Sol review of the frozen three worker lanes. This is not
Muad'Dib's check or an Astra postmerge review. One review and one repair
recheck; root owns live verification and the combined quick check.

Initial verdict: RATIFY-WITH-CONDITIONS.

1. P2, Tenet 3: while a plain session's terminal is open, a new Speak answer
   request changes answerSeq but does not reveal the unmounted composer.
   SessionPullout.tsx:732/772/815 and steering.ts:321 at review time.
   The original test requested Speak after Back and missed this state.
2. P2, Tenets 3/7: preserved email key refs share keys[ref] across providers,
   while the backend key slot is provider:ref (channel_email.py:477).
   A SendGrid result can incorrectly enable a Resend edit using the same
   legacy ref. Destinations.tsx:145/172/174/203/488 at review time.
   The original tests covered one provider only.

Workers were asked to fix each seam and add a regression before SHIP.
Session's new request reveals the body; terminal-entry sequence suppression
still prevents replay on Back. Email presence must use provider plus exact
ref while preserving Slack's existing cache identity. See build reports for
executed red/green results. Recheck pending.

Initial Tuesday judgment: forms and readers support the job, but both
state seams need correction. Unknown in source review: live geometry,
pointer ownership, clipboard, microphone, native calendar and combined quick.

## One repair recheck

Final verdict RATIFY. No conditions remain from source review.

- New Speak reveals the composer from terminal; Back still suppresses
  replay. SessionPullout.tsx:740/776, parameterized question/direct regression
  sessionSpeakAnswer.f2.test.tsx:104.
- Email identity is provider plus exact ref for Check, display, validation,
  key save and list seeding. Destinations.tsx:116/163/175/206/468/486;
  cross-provider regression destinations.app.test.tsx:335 checks missing
  key, disabled Save and preservation of the first provider's result.

No additional finding within this bounded recheck. Reviewer ran no tests or
browser and did not verify worker green counts. Root retains that duty.

## Root live correction after source recheck

The production phone walk exposed Settings' legacy row specificity overriding
controlWidth=full in the nested destination form. Root directed use of the
existing GadgetRow wide flag, which those rules already honor; all twelve
full-width rows now carry it. No new CSS. Schedule's save-failure receipt was
visibly truncated at both widths; its text is shortened to Not saved · Kept.
The forms worker added a structural regression, reproduced both checks red,
and reran its three approved files green49. Root owns the subsequent layout
and unclipped-receipt assertions and shots. No third source review is claimed.

Root's final phone read also found the shared Pad mic overlapping address
text. The worker changed only shared CSS text reservation using existing
size/space tokens (28px desktop,52px phone). Root's final walk measures the
mic/content gap and complete auto-grown content at both widths; this is
layout proof, not a microphone test. The combined related-test run separately
caught Resend's removed dest-to test hook; its query now uses the existing
To label, with key/provider/payload assertions unchanged (focused4green).
The full quick is rerun after both corrections. No third source review.
