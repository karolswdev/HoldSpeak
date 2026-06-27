import SwiftUI

// HSM-14 — THE ARCADE. Six council-built utility mini-games + Arkanoid, surfaced through one launcher and
// each played in a shared EPHEMERAL frosted window (the record-button philosophy: floats ON the desk, the
// desk reads through it). Each council game is a content-only `MG_*` View (init(), static title/icon) that
// fills the window body; this file owns the registry, the gallery picker, and the generic game window.

struct MiniGame: Identifiable { let id: String; let title: String; let icon: String; let make: () -> AnyView }

enum MiniGames {
    // the six the council built (each a self-contained DeskMiniGame_*.swift). MainActor-isolated because the
    // `make` closures build SwiftUI views.
    @MainActor static let all: [MiniGame] = [
        MiniGame(id: "reflex", title: MG_Reflex.title, icon: MG_Reflex.icon, make: { AnyView(MG_Reflex()) }),
        MiniGame(id: "memory", title: MG_Memory.title, icon: MG_Memory.icon, make: { AnyView(MG_Memory()) }),
        MiniGame(id: "logic",  title: MG_Logic.title,  icon: MG_Logic.icon,  make: { AnyView(MG_Logic()) }),
        MiniGame(id: "merge",  title: MG_Merge.title,  icon: MG_Merge.icon,  make: { AnyView(MG_Merge()) }),
        MiniGame(id: "word",   title: MG_Word.title,   icon: MG_Word.icon,   make: { AnyView(MG_Word()) }),
        MiniGame(id: "aim",    title: MG_Aim.title,    icon: MG_Aim.icon,    make: { AnyView(MG_Aim()) }),
        MiniGame(id: "zen",    title: MG_Zen.title,    icon: MG_Zen.icon,    make: { AnyView(MG_Zen()) }),
    ]
    @MainActor static func game(_ id: String) -> MiniGame? { all.first { $0.id == id } }
}


// a game's PixelLab cover, with a premium SF-symbol fallback until the art is bundled
struct GameCover: View {
    let id: String; let fallback: String; var size: CGFloat = 104
    var body: some View {
        #if canImport(UIKit)
        if let p = Bundle.main.path(forResource: "game_\(id)", ofType: "png"), let ui = UIImage(contentsOfFile: p) {
            Image(uiImage: ui).interpolation(.none).resizable().scaledToFit().frame(width: size, height: size)
                .shadow(color: .black.opacity(0.4), radius: 3, y: 2)
        } else { fallbackIcon }
        #else
        fallbackIcon
        #endif
    }
    private var fallbackIcon: some View {
        Image(systemName: fallback).font(.system(size: size * 0.4, weight: .bold)).foregroundStyle(.white).shadow(color: .black.opacity(0.4), radius: 2, y: 1)
    }
}

// THE GENERIC GAME WINDOW — the shared ephemeral frosted pane that hosts any council game. Draggable to pin,
// pin persisted; a minimal header (icon + title + close). The hosted MG_* view fills the body.
struct DioGameWindow: View {
    let game: MiniGame
    let onClose: () -> Void
    let screen: CGSize
    @Binding var pinNX: Double
    @Binding var pinNY: Double
    @State private var dragStart: CGPoint? = nil
    private let winW: CGFloat = 286, winH: CGFloat = 348, headerH: CGFloat = 40, pad: CGFloat = 8
    private var pin: CGPoint {
        CGPoint(x: min(max(CGFloat(pinNX) * screen.width, winW / 2 + 6), screen.width - winW / 2 - 6),
                y: min(max(CGFloat(pinNY) * screen.height, winH / 2 + 6), screen.height - winH / 2 - 6))
    }
    var body: some View {
        VStack(spacing: 0) {
            header
            game.make()
                .frame(width: winW - pad * 2, height: winH - headerH - pad)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                .padding(.horizontal, pad).padding(.bottom, pad)
        }
        .frame(width: winW, height: winH)
        .background(RoundedRectangle(cornerRadius: 22, style: .continuous).fill(.ultraThinMaterial)
            .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).fill(DioPal.violet.opacity(0.05)))
            .overlay(RoundedRectangle(cornerRadius: 22, style: .continuous).strokeBorder(.white.opacity(0.12), lineWidth: 0.5))
            .shadow(color: .black.opacity(0.3), radius: 14, y: 7))
        .position(pin)
    }
    private var header: some View {
        HStack(spacing: 9) {
            Image(systemName: game.icon).font(.system(size: 13, weight: .bold)).foregroundStyle(DioPal.violet)
            Text(game.title).font(.system(size: 14, weight: .heavy, design: .rounded)).foregroundStyle(DioPal.text)
            Spacer(minLength: 0)
            Button(action: onClose) {
                Image(systemName: "xmark").font(.system(size: 11, weight: .black)).foregroundStyle(DioPal.text.opacity(0.9))
                    .frame(width: 28, height: 28).background(Circle().fill(.white.opacity(0.1)))
            }.buttonStyle(.plain)
        }
        .padding(.horizontal, 14).frame(height: headerH).contentShape(Rectangle())
        .gesture(
            DragGesture(coordinateSpace: .global)
                .onChanged { v in
                    if dragStart == nil { dragStart = pin }
                    let nx = (dragStart!.x + v.translation.width) / screen.width
                    let ny = (dragStart!.y + v.translation.height) / screen.height
                    pinNX = Double(nx); pinNY = Double(ny)
                }
                .onEnded { _ in dragStart = nil }
        )
    }
}
