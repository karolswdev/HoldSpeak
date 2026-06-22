# HSM-14-10 — Models, front and center (import + manage, AirDrop-ready)

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress (the Models screen + import + AirDrop open-in are built + device-built; on-device import/AirDrop proof = owner verification)
- **Depends on:** HSM-5-03 (the Providers `ModelStore`)
- **Owner:** unassigned

## Vision (owner)

> "Why not just AirDrop it? … Add that feature of importing a model. That should be front and
> center."

The user should **own their models** — no Mac tether, no `devicectl`. AirDrop a `.gguf` to the
iPad, or pick one from Files, and it lands in the app where the on-device runtime loads it.

## Why AirDrop alone isn't enough (the real constraint)

iOS sandboxes each app: AirDrop drops a file into **Files**, but the runtime loads only from
the app's **own container**. So AirDrop needs the app to either (a) register as a `.gguf`
open-in handler ("Save to HoldSpeak") or (b) offer an in-app **Import** picker. This story does
both — turning AirDrop/Files into a real model path.

## Scope

- **In:** a **Models** screen (`ModelsView`) — front-and-center entry on the home — that lists
  installed `.gguf` models (name, size, language-model vs vision-projector), an **Import a
  model** button (`.fileImporter` over the security-scoped picker), and delete; the app
  **registered as a `.gguf` open-in handler** (Info.plist `CFBundleDocumentTypes` +
  `UTImportedTypeDeclarations`) so AirDrop/Files offer **"Save to HoldSpeak"**, with
  `onOpenURL` copying the incoming file into the container. All file ops delegate to the tested
  Providers `ModelStore` (HSM-5-03) pointed at the runtime's `Documents` directory.
- **Out:** an in-app model **catalog/download** UI (HF download exists in `ModelDownloader`;
  surfacing it is a follow-up). Per-model "active" selection UI (the runtime picks the first
  `.gguf` today). Model verification/checksums.

## Acceptance criteria

- [x] A **Models** screen lists installed models with size + type, reachable front-and-center
      from the home; **Import** opens the Files picker and copies the chosen `.gguf` into the
      container; delete works. Builds + signs for device.
- [x] The app is a **`.gguf` open-in handler** — AirDrop / Files "Save to HoldSpeak" routes to
      `onOpenURL`, which copies the file into the container (Info.plist declares the type).
- [ ] **Owner-verified on the iPad:** AirDrop a `.gguf` → Save to HoldSpeak → it appears in
      Models and the runtime can load it; and the in-app Import picker works.

## Evidence

`apple/App/MeetingCaptureApp.swift` (`ModelFiles` wrapper over Providers `ModelStore`,
`ModelsView`, the home `modelsCta`, `onOpenURL`) + `apple/App/Capture-Info.plist` (the `.gguf`
document type). **Device build SUCCEEDED.**

## Notes

- Reuses the HSM-5-03 `ModelStore` (installed/import/delete) rather than duplicating it —
  pointed at `Documents` (where `localGGUF()` + the dev `devicectl` push land), so the UI and
  the runtime see the same models.
- This is the proper **shipping** path the dev `push-model-device.sh` always flagged ("Files
  sideload + HF download"). It also surfaces the Gemma 4 + Qwen models already on the device.
