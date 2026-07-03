import Foundation

/// The one egress grammar (HSM-21-01, POSITIONING canon).
///
/// Every surface states where data goes with the same three postures — a compact
/// label, never a reassurance sentence (the badge IS the privacy statement). The
/// type is pure data (label + SF Symbol name + a tint key) so the UI-free layers
/// can carry it and each app renders it with its own chrome:
///
///   - `.local`          → "On device"          (nothing leaves the device)
///   - `.mixed(target)`  → "Local + \(target)"  (on-device work, plus a named
///                          target it talks to — e.g. dictation heard on-device,
///                          the text typed on your desktop)
///   - `.cloud(target)`  → "Cloud · \(target)"  (leaves the machine to a named
///                          target — e.g. an approved Slack send)
///
/// A `mixed` or `cloud` posture must NEVER wear the local treatment — that is
/// the drift this type exists to kill.
public enum EgressScope: Equatable, Sendable {
    case local
    case mixed(String)
    case cloud(String)

    /// The badge text — the same words on every surface.
    public var label: String {
        switch self {
        case .local: return "On device"
        case .mixed(let target): return "Local + \(target)"
        case .cloud(let target): return "Cloud · \(target)"
        }
    }

    /// The badge's SF Symbol.
    public var symbolName: String {
        switch self {
        case .local: return "lock.fill"
        case .mixed: return "desktopcomputer"
        case .cloud: return "arrow.up.forward.app.fill"
        }
    }

    /// The tint family ("local" calm, "leaves" attention) — mapped to each app's
    /// palette; the split is the honest line: anything that leaves the device is
    /// visually distinct from anything that does not.
    public var tintKey: String {
        switch self {
        case .local: return "local"
        case .mixed, .cloud: return "leaves"
        }
    }

    /// True when any data leaves the device under this posture.
    public var leavesDevice: Bool {
        if case .local = self { return false }
        return true
    }
}
