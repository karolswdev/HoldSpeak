import CoreGraphics

/// HSM-14-13 deliverables 3–4 — pure layout math for the spatial workspace, host-tested away from
/// SwiftUI. `CardSize` bounds a card's width as it is corner-dragged; `WorkspaceTidy` re-flows the
/// loose cards into a readable grid (the one-tap "tidy", with the prior arrangement kept for undo).
public enum CardSize {
    public static let minWidth: CGFloat = 132
    public static let maxWidth: CGFloat = 320

    /// Clamp a dragged card width to the readable range (text reflows within it).
    public static func clampWidth(_ w: CGFloat) -> CGFloat {
        min(max(w, minWidth), maxWidth)
    }
}

public enum WorkspaceTidy {
    /// Re-flow `count` loose cards into a centered grid below `pinFloor`, inside `size`. Returns one
    /// center point per card, row-major, all on-screen and below the streaming strip — so the
    /// freedom of free-placement never becomes an unreadable mess. Pure + deterministic (undo just
    /// restores the prior centers the caller saved).
    public static func layout(count: Int, in size: CGSize, pinFloor: CGFloat,
                              cardW: CGFloat = 174, rowH: CGFloat = 96, gap: CGFloat = 16) -> [CGPoint] {
        guard count > 0 else { return [] }
        let usableW = max(cardW, size.width - 2 * gap)
        let cols = max(1, Int((usableW + gap) / (cardW + gap)))
        let top = pinFloor + gap + rowH / 2
        return (0..<count).map { i in
            let row = i / cols, col = i % cols
            let inRow = min(cols, count - row * cols)              // cards in this (possibly partial) row
            let rowWidth = CGFloat(inRow) * (cardW + gap) - gap
            let startX = (size.width - rowWidth) / 2 + cardW / 2   // center each row
            return CGPoint(x: startX + CGFloat(col) * (cardW + gap),
                           y: top + CGFloat(row) * (rowH + gap))
        }
    }
}
