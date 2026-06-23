import XCTest
@testable import RuntimeCore

/// The offline global-clustering pass (HSM-14-17): the fix for the online greedy over-split.
final class SpeakerClusteringTests: XCTestCase {
    private func axis(_ k: Int, jitter: Float = 0) -> [Float] {
        var v = [Float](repeating: 0, count: 64)
        v[k % 64] = 1
        if jitter != 0 { v[(k + 5) % 64] += jitter }
        return SpeakerMath.normalized(v)
    }

    func testGlobalClusteringIsOrderIndependentAndFindsTrueSpeakerCount() {
        // Two voices (axis 0 = A, axis 20 = B), INTERLEAVED: A B A A B A. The online greedy pass, judging
        // each against a database still filling, can over-split; the global pass must give exactly two.
        let embs = [axis(0), axis(20), axis(0, jitter: 0.1), axis(0), axis(20, jitter: 0.1), axis(0)]
        let labels = SpeakerClustering.cluster(embs, threshold: 0.6)
        XCTAssertEqual(Set(labels).count, 2, "two real voices ⇒ two speakers, regardless of order")
        // All A-segments share a label; all B-segments share a label; they differ.
        XCTAssertEqual([labels[0], labels[2], labels[3], labels[5]].reduce(Set()) { $0.union([$1]) }.count, 1)
        XCTAssertEqual(labels[1], labels[4])
        XCTAssertNotEqual(labels[0], labels[1])
        XCTAssertEqual(labels[0], 0, "earliest-spoken voice is Speaker 1 (label 0)")
    }

    func testSingleNoisyVoiceStaysOneSpeaker() {
        let embs = (0..<8).map { axis(3, jitter: Float($0) * 0.03) }   // one voice, gentle drift
        let labels = SpeakerClustering.cluster(embs, threshold: 0.6)
        XCTAssertEqual(Set(labels).count, 1, "one voice must not fragment into many speakers")
    }

    func testThreeDistinctVoices() {
        let embs = [axis(0), axis(20), axis(40), axis(0), axis(40), axis(20)]
        let labels = SpeakerClustering.cluster(embs, threshold: 0.6)
        XCTAssertEqual(Set(labels).count, 3)
    }

    func testEmptyIsEmpty() {
        XCTAssertTrue(SpeakerClustering.cluster([], threshold: 0.6).isEmpty)
    }
}
