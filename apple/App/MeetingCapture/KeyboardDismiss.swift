import SwiftUI
import UIKit

// Owner feedback (2026-07-06, build 7): "One thing I miss is the ability to hide
// the keyboard when done typing." On iPhone the system keyboard has no dismiss
// key, and none of the desk's fields offered one — once up, the keyboard stayed.
//
// One fix, three layers, ALL app-wide (no per-field wiring):
//   1. `keyboardDone()` — an accessory bar above the keyboard with a visible
//      hide-keyboard button (the affordance you can SEE). Attached at the app
//      root; SwiftUI collects keyboard toolbar items from any ancestor.
//   2. `.scrollDismissesKeyboard(.interactively)` at the root — dragging any
//      scrollable pulls the keyboard down, the platform-native way.
//   3. `KeyboardDismissInstaller` — a window-level swipe-down that ends editing.
//      The window is shared by every presentation (sheets included), so this
//      catches the surfaces toolbar propagation can't reach.

/// End editing everywhere — the first responder resigns, whatever it is.
@MainActor func hideKeyboard() {
    UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder),
                                    to: nil, from: nil, for: nil)
}

extension View {
    /// The visible hide-keyboard affordance: an accessory bar with one button.
    func keyboardDone() -> some View {
        toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                Button { hideKeyboard() } label: {
                    Image(systemName: "keyboard.chevron.compact.down")
                        .font(.system(size: 15, weight: .bold))
                }
                .accessibilityLabel("Hide keyboard")
            }
        }
    }
}

/// Installs ONE swipe-down recognizer on the app's window: swiping down while
/// typing puts the keyboard away, anywhere — desk cards, composers, sheets.
/// `cancelsTouchesInView = false` + simultaneous recognition: it never steals
/// a tap, a drag, or a scroll; it only ends editing alongside them.
struct KeyboardDismissInstaller: UIViewRepresentable {
    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeUIView(context: Context) -> UIView {
        let v = UIView(frame: .zero)
        v.isUserInteractionEnabled = false
        return v
    }

    func updateUIView(_ uiView: UIView, context: Context) {
        // The window exists only after attachment — install (once) from here.
        DispatchQueue.main.async {
            guard !context.coordinator.installed, let window = uiView.window else { return }
            let swipe = UISwipeGestureRecognizer(target: context.coordinator,
                                                 action: #selector(Coordinator.swiped))
            swipe.direction = .down
            swipe.cancelsTouchesInView = false
            swipe.delegate = context.coordinator
            window.addGestureRecognizer(swipe)
            context.coordinator.installed = true
        }
    }

    final class Coordinator: NSObject, UIGestureRecognizerDelegate {
        var installed = false
        @objc func swiped() { Task { @MainActor in hideKeyboard() } }
        func gestureRecognizer(_ gestureRecognizer: UIGestureRecognizer,
                               shouldRecognizeSimultaneouslyWith other: UIGestureRecognizer) -> Bool {
            true
        }
    }
}
