import Foundation

/// A streamed block of captured audio — 16-bit PCM, mono, 16 kHz canonical
/// (the transcriber contract). HSM-2-02.
public struct AudioChunk: Equatable, Sendable {
    public var samples: [Int16]
    public var sequence: Int

    public init(samples: [Int16], sequence: Int) {
        self.samples = samples
        self.sequence = sequence
    }

    public var frameCount: Int { samples.count }
}

/// Bounded accumulator: buffers chunks for a downstream consumer, capping the
/// retained frames so a stalled consumer cannot grow memory without bound — it
/// drops the oldest frames and counts the drops. The 1-hour stability gate
/// (HSM-2-04) leans on this bound. HSM-2-02.
public final class AudioAccumulator: @unchecked Sendable {
    private var buffer: [Int16] = []
    private let maxFrames: Int
    private let lock = NSLock()
    public private(set) var droppedFrames = 0
    public private(set) var totalFrames = 0

    /// - Parameter maxFrames: retained-frame cap (default ~60 s at 16 kHz).
    public init(maxFrames: Int = 16_000 * 60) {
        self.maxFrames = maxFrames
    }

    public func append(_ chunk: AudioChunk) {
        lock.lock(); defer { lock.unlock() }
        totalFrames += chunk.frameCount
        buffer.append(contentsOf: chunk.samples)
        if buffer.count > maxFrames {
            let overflow = buffer.count - maxFrames
            buffer.removeFirst(overflow)
            droppedFrames += overflow
        }
    }

    /// Take everything buffered so far, clearing the buffer.
    public func drain() -> [Int16] {
        lock.lock(); defer { lock.unlock() }
        let out = buffer
        buffer.removeAll(keepingCapacity: true)
        return out
    }

    public var retainedFrames: Int {
        lock.lock(); defer { lock.unlock() }
        return buffer.count
    }
}
