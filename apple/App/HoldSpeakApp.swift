import SwiftUI

// Minimal Gate-1 launch app: proves the runtime shell launches on iPhone + iPad
// (charter Gate 1). It is compiled together with the Contracts sources (see
// scripts/gate1-launch.sh), so the on-screen contract version comes from the real
// Contracts layer, not a literal. The full SwiftUI Hosts apps arrive in Phases
// 8 (iPad) and 9 (iPhone); this is the launchable foundation, not those.

@main
struct HoldSpeakApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: View {
    var body: some View {
        VStack(spacing: 12) {
            Text("HoldSpeak Mobile")
                .font(.largeTitle).bold()
            Text("Runtime foundation — Phase 1")
                .foregroundStyle(.secondary)
            Text("contracts v\(HoldSpeakContracts.contractVersion)")
                .font(.footnote.monospaced())
                .foregroundStyle(.secondary)
        }
        .padding()
    }
}
