import CoreGraphics

/// HSM-14-13 deliverable 2 — what a dragged live bubble becomes when it is dropped on the capture
/// surface. A pure decision so "free-place vs tack" is host-tested away from SwiftUI:
/// - dropped on the **tack zone** → `tack` (a marked moment that steers the on-device intelligence),
/// - dropped below the streaming strip → `loose` (just placed; no marked moment),
/// - dropped back up in the stream → `snapBack` (it returns to the bubble flow).
///
/// Tacking is the deliberate act (it has MIR consequences); plain placement is the easy default —
/// so the surface is an arrangeable workspace, and steering the intelligence stays intentional.
public enum BubbleDrop: String, Equatable, Sendable { case tack, loose, snapBack }

public enum BubblePlacement {
    public static func decide(at p: CGPoint, pinFloor: CGFloat, tackZone: CGRect) -> BubbleDrop {
        if tackZone.contains(p) { return .tack }      // the tack zone wins wherever it sits
        if p.y > pinFloor { return .loose }
        return .snapBack
    }
}
