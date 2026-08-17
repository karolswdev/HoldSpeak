# People PR1 visual evidence

Captured 2026-08-16 from the real assembled HoldSpeak hub and production Desk
bundle, using a disposable encrypted People sidecar and synthetic relationship data.
The screenshot process used the normal HTTP routes and kernel setup operation. The
disposable screenshot store used an injected in-memory key provider so it left no OS
credential behind; native macOS Keychain setup/restart/raw-byte behavior was proven
separately during the same implementation run.

- [Wide Desk](people-wide.png) — 1440×1000 relationship Now lens, trust facts, and
  an explicitly accepted manager commitment.
- [Narrow Desk](people-narrow.png) — 393×852 relationship 1:1 lens with a manual,
  shared-intent agenda item and no capture/model control.

These images are best-attempt implementation evidence, not exhaustive end-to-end
certification. The draft PR hands broad regression and production-device acceptance
to the maintainer explicitly.
