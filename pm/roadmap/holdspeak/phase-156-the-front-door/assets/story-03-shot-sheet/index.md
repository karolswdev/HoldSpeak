# Shot sheet: HS-156-03 The Library Patterns

Gallery at /design/components with all v1 pattern states.
Captured from the live backend with headless Chrome.

| Component | State | Width | File | Reviewer | Verdict |
| --- | --- | --- | --- | --- | --- |
| Gallery (gadgets) | existing kit + buttons | 1440px | [gallery-top-1440.png](./gallery-top-1440.png) | | |
| Gallery (v1 patterns) | StateChip, ActionNotice, Disclosure, ProgressPlan, ChoiceCardGroup, Popover, ProvenanceChip, Receipt | 1440px | [gallery-patterns-1440.png](./gallery-patterns-1440.png) | | |
| Gallery (mid-scroll) | ActionNotice, Disclosure, ProgressPlan | 1440px | [gallery-mid-1440.png](./gallery-mid-1440.png) | | |
| Gallery (focus) | keyboard focus visible | 1440px | [gallery-focus-1440.png](./gallery-focus-1440.png) | | |
| Gallery (gadgets) | existing kit + buttons | 393px | [gallery-top-393.png](./gallery-top-393.png) | | |
| Gallery (v1 patterns) | StateChip, ActionNotice, Disclosure, ProgressPlan, ChoiceCardGroup, Popover, ProvenanceChip, Receipt | 393px | [gallery-patterns-393.png](./gallery-patterns-393.png) | | |
| Gallery (mid-scroll) | ActionNotice, Disclosure, ProgressPlan | 393px | [gallery-mid-393.png](./gallery-mid-393.png) | | |
| Gallery (focus) | keyboard focus visible | 393px | [gallery-focus-393.png](./gallery-focus-393.png) | | |


## Gate verdict

**Reviewer:** the orchestrator (Fable), 2026-08-31. **Verdict: PASS.**
Looked at gallery-patterns 1440 + 393: the patterns read as the desk's
own material (ProgressPlan failure/retry states, ChoiceCardGroup's
RECOMMENDED + separate APPLY verb, provenance/receipt footer slots);
393 stacks cleanly with zero overflow and legible states. Divergences
accepted: progressbar aria-label (a11y improvement), explicit
ChoiceCard props (no fragile cloneElement), Popover body-portal with
anchor positioning (in-flow to the eye). The owner sees this sheet in
the phase exhibit.
