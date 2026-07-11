import Foundation
import SwiftUI
// Same staged module as the app (the gen script strips layer imports):
// MeshServeWorker / MeshRelayJob / HTTPDesktopClient resolve directly.

// HSM-25-02 — serving is consent: this store owns the worker's lifecycle for
// the one toggle. Off by default; stopping (toggle off, the app leaving the
// foreground, the app dying) just cancels the loop — the hub's liveness
// window reads this node offline within seconds, because polling IS liveness.
// Nothing to clean up on either side.
@MainActor final class MeshServeStore: ObservableObject {
    static let shared = MeshServeStore()

    @Published private(set) var serving = false
    @Published private(set) var jobsServed = 0
    @Published private(set) var lastOutcome = ""

    private var task: Task<Void, Never>?
    private var statsTask: Task<Void, Never>?
    private var worker: MeshServeWorker?

    /// The node name every surface agrees on: the SAME one the device's model
    /// manifest pushes on sync, so the hub's pickers, doctor line, and badges
    /// all name one string.
    var node: String { DeviceLabel.current }

    /// The at-the-door recursion guard (the desktop walk's design find): a
    /// device whose active profile runs elsewhere must not serve — nil means
    /// armable, else the named reason the card wears.
    var refusal: String? {
        let kind = InferenceConfigStore.shared.activeProfile.kind
        guard kind == .meshNode || kind == .desktop else { return nil }
        return "Serving failed. The selected Runs on destination is unavailable to this device. Choose a this-device model or configured endpoint."
    }

    /// Follow the consent flag (and the foreground): the toggle's didSet, the
    /// launch wiring, and the scenePhase observer all funnel here.
    func apply(on: Bool) {
        if on { start() } else { stop() }
    }

    private func start() {
        guard task == nil, refusal == nil,
              let client = DictatePeerStore.shared.client() else { return }
        let name = node
        let built = MeshServeWorker(
            node: name,
            client: client,
            makeProvider: {
                // resolution is the config store's job and it is MainActor;
                // the per-job guard mirrors the at-the-door one by design
                try await MainActor.run {
                    try InferenceConfigStore.shared.makeMeshServeProvider()
                }
            })
        worker = built
        serving = true
        task = Task { await built.run() }
        statsTask = Task { [weak self] in
            while !Task.isCancelled {
                if let w = self?.worker {
                    let s = await w.stats
                    self?.jobsServed = s.jobsServed
                    self?.lastOutcome = s.lastOutcome
                }
                try? await Task.sleep(nanoseconds: 2_000_000_000)
            }
        }
    }

    private func stop() {
        task?.cancel()
        statsTask?.cancel()
        task = nil
        statsTask = nil
        worker = nil
        serving = false
    }
}
