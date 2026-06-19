import Foundation

/// Encodes 16-bit PCM mono samples into a WAV (RIFF) container at the transcriber
/// contract format (16 kHz mono PCM16 by default). Pure + deterministic. HSM-2-03.
///
/// Apple platforms are little-endian, matching WAV's LE sample layout.
public enum WavWriter {
    public static let bitsPerSample = 16

    public static func wavData(
        fromPCM16 samples: [Int16],
        sampleRate: Int = 16_000,
        channels: Int = 1
    ) -> Data {
        let blockAlign = channels * bitsPerSample / 8
        let byteRate = sampleRate * blockAlign
        let dataBytes = samples.count * MemoryLayout<Int16>.size

        var d = Data(capacity: 44 + dataBytes)
        func u32(_ v: UInt32) { var x = v.littleEndian; withUnsafeBytes(of: &x) { d.append(contentsOf: $0) } }
        func u16(_ v: UInt16) { var x = v.littleEndian; withUnsafeBytes(of: &x) { d.append(contentsOf: $0) } }

        d.append(contentsOf: Array("RIFF".utf8))
        u32(UInt32(36 + dataBytes))            // chunk size
        d.append(contentsOf: Array("WAVE".utf8))

        d.append(contentsOf: Array("fmt ".utf8))
        u32(16)                                 // PCM fmt subchunk size
        u16(1)                                  // audio format = PCM
        u16(UInt16(channels))
        u32(UInt32(sampleRate))
        u32(UInt32(byteRate))
        u16(UInt16(blockAlign))
        u16(UInt16(bitsPerSample))

        d.append(contentsOf: Array("data".utf8))
        u32(UInt32(dataBytes))
        samples.withUnsafeBytes { d.append(contentsOf: $0) }  // LE Int16 PCM
        return d
    }
}
