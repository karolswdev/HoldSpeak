import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14-19 — the bespoke PixelLab pixel-art sprites for the real DeskOS, loaded from the app bundle
// (the gen script bundles cassette/cartridge/mic/folder/note/robot.png as resources). `.interpolation
// (.none)` keeps them crisp; a Sig placeholder holds layout if a sprite is missing.

struct DeskSprite: View {
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
        RoundedRectangle(cornerRadius: 14).fill(Sig.s3).frame(width: size, height: size)
            .overlay(Text(name).font(.system(size: 10, weight: .bold)).foregroundStyle(Sig.faint))
    }
}
