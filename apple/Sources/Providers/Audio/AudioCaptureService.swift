#if os(iOS)
import AVFoundation
import Foundation

/// The live `IAudioCapture` over `AVAudioEngine` + `AVAudioSession` (HSM-2-01).
/// Converts the hardware input to the canonical 16 kHz mono PCM16 format once, at
/// the seam, and streams `AudioChunk`s. Handles interruptions (call/Siri) and
/// route changes (headphones/Bluetooth) so a long recording survives them.
///
/// iOS-only (`AVAudioSession` is unavailable on macOS); the package's host build
/// + tests exercise the pure pieces (`AudioChunk`/`AudioAccumulator`/`WavWriter`)
/// and a fake capture. Live-mic + interruption behavior is device-verified
/// (defers with the Track-C hardware gate).
public final class AudioCaptureService: IAudioCapture, @unchecked Sendable {
    private let engine = AVAudioEngine()
    private var onChunk: (@Sendable (AudioChunk) -> Void)?
    private var converter: AVAudioConverter?
    private var sequence = 0
    private let targetFormat = AVAudioFormat(
        commonFormat: .pcmFormatInt16, sampleRate: 16_000, channels: 1, interleaved: true)!

    public init() {}

    public func start(onChunk: @escaping @Sendable (AudioChunk) -> Void) throws {
        self.onChunk = onChunk
        try configureSession()

        let input = engine.inputNode
        let inputFormat = input.outputFormat(forBus: 0)
        converter = AVAudioConverter(from: inputFormat, to: targetFormat)

        input.installTap(onBus: 0, bufferSize: 4096, format: inputFormat) { [weak self] buffer, _ in
            self?.handle(buffer)
        }
        engine.prepare()
        try engine.start()
        registerNotifications()
    }

    public func stop() throws {
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
        NotificationCenter.default.removeObserver(self)
    }

    // MARK: - Capture

    private func handle(_ buffer: AVAudioPCMBuffer) {
        guard let converter, let onChunk else { return }
        let ratio = targetFormat.sampleRate / buffer.format.sampleRate
        let capacity = AVAudioFrameCount(Double(buffer.frameLength) * ratio) + 1
        guard let out = AVAudioPCMBuffer(pcmFormat: targetFormat, frameCapacity: capacity) else { return }

        var fed = false
        var error: NSError?
        converter.convert(to: out, error: &error) { _, status in
            if fed { status.pointee = .noDataNow; return nil }
            fed = true
            status.pointee = .haveData
            return buffer
        }
        guard error == nil, let channel = out.int16ChannelData else { return }

        let count = Int(out.frameLength)
        let samples = Array(UnsafeBufferPointer(start: channel[0], count: count))
        guard !samples.isEmpty else { return }
        sequence += 1
        onChunk(AudioChunk(samples: samples, sequence: sequence))
    }

    // MARK: - Session + resilience

    private func configureSession() throws {
        let session = AVAudioSession.sharedInstance()
        // Bluetooth-input options are intentionally omitted here (the option name
        // shifted across SDKs); BT-mic support is device-phase follow-up work.
        try session.setCategory(.record, mode: .measurement)
        try session.setActive(true)
    }

    private func registerNotifications() {
        let nc = NotificationCenter.default
        nc.addObserver(self, selector: #selector(handleInterruption(_:)),
                       name: AVAudioSession.interruptionNotification, object: nil)
        nc.addObserver(self, selector: #selector(handleRouteChange(_:)),
                       name: AVAudioSession.routeChangeNotification, object: nil)
    }

    @objc private func handleInterruption(_ note: Notification) {
        guard let info = note.userInfo,
              let raw = info[AVAudioSessionInterruptionTypeKey] as? UInt,
              let type = AVAudioSession.InterruptionType(rawValue: raw) else { return }
        switch type {
        case .began:
            engine.pause()
        case .ended:
            try? AVAudioSession.sharedInstance().setActive(true)
            try? engine.start()
        @unknown default:
            break
        }
    }

    @objc private func handleRouteChange(_ note: Notification) {
        // A route change (e.g. headphones unplugged) can stop the engine; restart.
        if !engine.isRunning {
            try? AVAudioSession.sharedInstance().setActive(true)
            try? engine.start()
        }
    }
}
#endif
