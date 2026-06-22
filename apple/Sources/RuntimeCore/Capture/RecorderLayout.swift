import CoreGraphics

/// HSM-14-13 — where the floating recorder lives on the capture surface, as a pure value so the
/// snap/dock decision and its persistence are host-testable, away from SwiftUI. `floating` keeps
/// the user's free position; `top`/`bottom` dock the (horizontal) capsule to a magnetic edge home.
/// Side-edge docking pairs naturally with the minimized orb and is a follow-up (the capsule is wide).
public enum RecorderDock: String, Codable, Sendable, CaseIterable {
    case floating, top, bottom
}

/// The recorder's persisted spatial state for a session: its dock, the last free center it was
/// dropped at (used while `floating`), and whether it is minimized to the compact orb.
public struct RecorderLayout: Codable, Sendable, Equatable {
    public var dock: RecorderDock
    public var freeCenter: CGPoint?
    public var minimized: Bool

    public init(dock: RecorderDock = .bottom, freeCenter: CGPoint? = nil, minimized: Bool = false) {
        self.dock = dock
        self.freeCenter = freeCenter
        self.minimized = minimized
    }
}

/// Pure snap/dock math (HSM-14-13 deliverable 1). Decides the dock from where the recorder was
/// dropped and resolves a dock to its resting center — no SwiftUI, fully unit-tested.
public enum RecorderSnap {
    /// Decide the dock from where the recorder was dropped (its center) inside `size`: if the drop
    /// is within `margin` points of the top or bottom edge, snap to that edge (the nearer wins);
    /// otherwise it floats free where it was let go.
    public static func dock(forCenter c: CGPoint, in size: CGSize, margin: CGFloat = 110) -> RecorderDock {
        let toTop = c.y, toBottom = size.height - c.y
        guard min(toTop, toBottom) <= margin else { return .floating }
        return toBottom <= toTop ? .bottom : .top
    }

    /// The recorder's resting center for a dock inside `size`, `inset` points from the edge. A
    /// `floating` dock uses the remembered `free` center (clamped by the caller), or a sensible
    /// bottom-center default if there is none yet.
    public static func home(for dock: RecorderDock, in size: CGSize, inset: CGFloat = 46,
                            free: CGPoint? = nil) -> CGPoint {
        switch dock {
        case .floating: return free ?? CGPoint(x: size.width / 2, y: size.height - inset)
        case .top:      return CGPoint(x: size.width / 2, y: inset)
        case .bottom:   return CGPoint(x: size.width / 2, y: size.height - inset)
        }
    }

    /// Keep a free center on-screen (the "never trap" rule): clamp it to `size` inset by `pad`.
    public static func clamp(_ c: CGPoint, in size: CGSize, pad: CGFloat = 40) -> CGPoint {
        CGPoint(x: min(max(c.x, pad), size.width - pad),
                y: min(max(c.y, pad), size.height - pad))
    }
}
