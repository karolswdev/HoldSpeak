import Foundation

/// The one egress grammar (HSM-21-01, POSITIONING canon).
///
/// Every surface states where data goes with the same three postures — a compact
/// label, never a reassurance sentence (the badge IS the privacy statement). The
/// type is pure data (label + SF Symbol name + a tint key) so the UI-free layers
/// can carry it and each app renders it with its own chrome:
///
///   - `.local`          → "This device"         (nothing leaves the device)
///   - `.mixed(target)`  → "Paired · \(target)" (work crosses to a named peer)
///   - `.cloud(target)`  → "Leaves device · \(target)" (work crosses to a named
///                          endpoint or external service)
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
        case .local: return "This device"
        case .mixed(let target): return "Paired · \(target)"
        case .cloud(let target): return "Leaves device · \(target)"
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
