import SwiftUI
import Foundation

// A throwaway probe: runs the REAL AudioCaptureService on the iOS simulator for a
// couple of seconds and prints how many frames it captured + the WAV size. Built
// standalone by scripts/capture-probe.sh (it compiles the Providers audio sources
// in). Proves the capture service actually runs on iOS, not just type-checks.

@main
struct CaptureProbeApp: App {
    var body: some Scene { WindowGroup { ProbeView() } }
}

struct ProbeView: View {
    @State private var status = "starting…"
    var body: some View {
        Text(status).padding().task { await run() }
    }

    func writeResult(_ s: String) {
        let dir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        try? s.write(to: dir.appendingPathComponent("probe-result.txt"),
                     atomically: true, encoding: .utf8)
    }

    func run() async {
        writeResult("PROBE_START")   // marker: the task ran at all
        let acc = AudioAccumulator(maxFrames: 16_000 * 10)
        let svc = AudioCaptureService()
        do {
            try svc.start { acc.append($0) }
            writeResult("PROBE_AFTER_START")
            try await Task.sleep(nanoseconds: 2_500_000_000)
            try svc.stop()
            writeResult("PROBE_AFTER_STOP frames=\(acc.totalFrames)")
            let frames = acc.totalFrames
            let wav = WavWriter.wavData(fromPCM16: acc.drain())
            let msg = "PROBE_RESULT totalFrames=\(frames) wavBytes=\(wav.count)"
            writeResult(msg); status = msg
        } catch {
            writeResult("PROBE_ERROR \(error)"); status = "error"
        }
    }
}
