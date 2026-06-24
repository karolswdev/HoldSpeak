import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14 — bespoke PixelLab pixel-art primitives, bundled into the harness .app and loaded by name.
// `.interpolation(.none)` keeps the pixel art crisp at any scale. A placeholder holds the layout if a
// sprite hasn't been dropped into scripts/experience/assets/ yet.

struct Sprite: View {
    let name: String
    var size: CGFloat = 120
    var body: some View {
        #if canImport(UIKit)
        if let path = Bundle.main.path(forResource: name, ofType: "png"), let ui = UIImage(contentsOfFile: path) {
            Image(uiImage: ui).interpolation(.none).resizable().scaledToFit().frame(width: size, height: size)
        } else { placeholder }
        #else
        placeholder
        #endif
    }
    private var placeholder: some View {
        RoundedRectangle(cornerRadius: 14).fill(DS.s3)
            .frame(width: size, height: size)
            .overlay(Text(name).font(.system(size: 10, weight: .bold)).foregroundStyle(DS.faint))
    }
}

// A primitive on the desk: the bespoke sprite + a compact, legible label plate beneath it.
struct SpriteObject: View {
    let sprite: String
    var spriteSize: CGFloat = 124
    let title: String
    var subtitle: String = ""
    var tint: Color = DS.accent
    var body: some View {
        VStack(spacing: 8) {
            Sprite(name: sprite, size: spriteSize)
                .shadow(color: .black.opacity(0.45), radius: 14, y: 10)
            VStack(spacing: 2) {
                Text(title).font(.system(size: 14, weight: .heavy)).foregroundStyle(DS.text)
                if !subtitle.isEmpty {
                    Text(subtitle).font(.system(size: 10.5, weight: .bold)).foregroundStyle(DS.muted)
                }
            }
            .padding(.horizontal, 12).padding(.vertical, 7)
            .background(Capsule().fill(DS.s1.opacity(0.82)).overlay(Capsule().stroke(tint.opacity(0.3))))
        }
    }
}
