import SwiftUI

/// The ONE width authority for every Apple surface (HSM-20-01).
///
/// The desk is a place, and a place has to fit through a doorway. There is ONE doctrine, not two
/// builds: the desk has a camera and screen width is the lens. `DeskCamera` is the single answer
/// to "how wide are we"; every view asks the camera instead of re-deriving width.
///
/// It is derived from `@Environment(\.horizontalSizeClass)` FIRST and geometry width SECOND.
/// The size class is the only correct iPhone-vs-iPad-split-view signal — a raw width read
/// (`UIScreen.main.bounds`, `geo.size.width < 500`) LIES on iPad multitasking, where the screen
/// is wide but your slice is narrow. Width is a tiebreaker within the regular size class, never
/// the primary signal.
///
/// The 500pt narrow/wide boundary is chosen to be byte-equivalent with the `w < 500` / `w >= 500`
/// checks this consolidation replaces — so the iPad renders identically at `.wide`/`.narrow`.
enum DeskCamera {
    /// iPad full width — the lit diorama (absolute-positioned, drag-to-arrange, lasso).
    case wide
    /// iPad split-view / medium — the rail (the compact pattern, generalized).
    case narrow
    /// iPhone (compact size class) — a single thumb-reachable card column.
    case lane

    /// Derive the camera. `sizeClass` is `@Environment(\.horizontalSizeClass)`; `width` is the
    /// live `GeometryReader` width. Size class wins: `.compact` is always the lane (iPhone, or an
    /// iPad slide-over slice). Within `.regular`, width below the tablet-split boundary is the
    /// rail; otherwise the full diorama.
    static func resolve(sizeClass: UserInterfaceSizeClass?, width: CGFloat) -> DeskCamera {
        if sizeClass == .compact { return .lane }
        return width < 500 ? .narrow : .wide
    }

    /// The diorama (absolute-positioned desk) vs the rail/lane reflows.
    var isWide: Bool { self == .wide }
    /// The one-thumb iPhone card column (a real renderer, not a free reflow).
    var isLane: Bool { self == .lane }
    /// The rail collapses behind an edge tab whenever we are not the full diorama
    /// (this is the `w < 500` rail-collapse, generalized to size class).
    var railCollapses: Bool { self != .wide }

    /// Clamp an ideal fixed card width so it never touches the edges on the lane; unchanged on
    /// `.wide`/`.narrow`. The single helper every fixed card uses to fit 390pt (handover §4b):
    /// a `width: 380` card becomes `min(380, width − 32)` on the lane, `380` everywhere else.
    func cardWidth(_ ideal: CGFloat, in width: CGFloat, margin: CGFloat = 16) -> CGFloat {
        guard isLane else { return ideal }
        return min(ideal, width - 2 * margin)
    }
}
