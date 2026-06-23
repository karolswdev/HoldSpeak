import XCTest
@testable import RuntimeCore

final class SpeakerMatcherTests: XCTestCase {
    // A normalised 256-dim embedding pointing mostly along axis `k`, with a little spread.
    private func emb(_ k: Int, jitter: Float = 0.0, seed: Int = 0) -> [Float] {
        var v = [Float](repeating: 0, count: 256)
        v[k % 256] = 1
        if jitter != 0 { v[(k + 7 + seed) % 256] += jitter; v[(k + 31 + seed) % 256] += jitter / 2 }
        return SpeakerMath.normalized(v)
    }

    func testCosineIdentityAndOrthogonal() {
        let a = emb(3)
        XCTAssertEqual(SpeakerMath.cosine(a, a), 1, accuracy: 1e-5)
        XCTAssertEqual(SpeakerMath.cosine(emb(3), emb(100)), 0, accuracy: 1e-5)   // orthogonal axes
    }

    func testTwoDistinctSpeakersSeparate() {
        let m = SpeakerMatcher(threshold: 0.75)
        let s1 = m.assign(emb(10))
        let s2 = m.assign(emb(200))          // far apart ⇒ a second speaker
        XCTAssertNotEqual(s1.id, s2.id)
        XCTAssertEqual(m.speakers.count, 2)
        XCTAssertEqual(s1.name, "Speaker 1")
        XCTAssertEqual(s2.name, "Speaker 2")
    }

    func testSameVoiceFoldsIntoOneSpeaker() {
        let m = SpeakerMatcher(threshold: 0.75)
        let first = m.assign(emb(10))
        for s in 1...4 { _ = m.assign(emb(10, jitter: 0.05, seed: s)) }   // same voice, slight variation
        XCTAssertEqual(m.speakers.count, 1, "near-identical embeddings must stay one speaker")
        XCTAssertEqual(m.speakers[0].id, first.id)
        XCTAssertEqual(m.speakers[0].sampleCount, 5)                      // EMA folded 4 more samples
    }

    func testCloseAboveThresholdMatchesFarBelowCreatesNew() {
        let m = SpeakerMatcher(threshold: 0.9)
        let a = m.assign(emb(10))
        let close = m.assign(emb(10, jitter: 0.05))      // cosine high ⇒ same speaker
        XCTAssertEqual(close.id, a.id)
        let far = m.assign(emb(10, jitter: 5.0))         // big jitter pushes cosine below 0.9
        XCTAssertNotEqual(far.id, a.id)
        XCTAssertEqual(m.speakers.count, 2)
    }

    func testEMAUpdateKeepsProfileNormalised() {
        let m = SpeakerMatcher(threshold: 0.6)
        _ = m.assign(emb(10))
        _ = m.assign(emb(10, jitter: 0.3))
        let norm = m.speakers[0].embedding.reduce(Float(0)) { $0 + $1 * $1 }.squareRoot()
        XCTAssertEqual(norm, 1, accuracy: 1e-4, "profile stays unit-length after EMA")
    }

    func testSeededKnownSpeakersAndRename() {
        let known = SpeakerProfile(id: "wei", name: "Wei", embedding: emb(10))
        let m = SpeakerMatcher(threshold: 0.75, known: [known])
        let hit = m.assign(emb(10, jitter: 0.05))        // matches the pre-seeded speaker (cross-meeting)
        XCTAssertEqual(hit.id, "wei")
        m.rename("wei", to: "Wei Zhang")
        XCTAssertEqual(m.speakers.first { $0.id == "wei" }?.name, "Wei Zhang")
        XCTAssertEqual(m.speakers.count, 1)
    }
}
