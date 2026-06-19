import XCTest
import Contracts
@testable import Providers

/// HSM-3-03 (language registry, at parity with desktop) + HSM-3-04 (transcription
/// -> Phase-0 Segment mapping) + the per-device model policy (HSM-3-01).
final class TranscriptionTests: XCTestCase {

    func testLanguageRegistryParityWithDesktop() {
        // Desktop holdspeak/languages.py registry (generated from it). The Swift
        // count must match desktop exactly.
        XCTAssertEqual(WhisperLanguage.count, 100)
        XCTAssertEqual(WhisperLanguage.names["de"], "German")
        XCTAssertEqual(WhisperLanguage.names["yue"], "Cantonese")
    }

    func testLanguageNormalize() throws {
        XCTAssertNil(try WhisperLanguage.normalize(nil))         // auto
        XCTAssertNil(try WhisperLanguage.normalize(""))          // auto
        XCTAssertNil(try WhisperLanguage.normalize("auto"))      // auto
        XCTAssertEqual(try WhisperLanguage.normalize("pl"), "pl")        // code
        XCTAssertEqual(try WhisperLanguage.normalize("Polish"), "pl")    // English name
        XCTAssertEqual(try WhisperLanguage.normalize("GERMAN"), "de")    // case-insensitive
        XCTAssertThrowsError(try WhisperLanguage.normalize("klingon")) { error in
            XCTAssertEqual(error as? WhisperLanguageError, .unknown("klingon"))
        }
    }

    func testPerDeviceModelDefaults() {
        XCTAssertEqual(WhisperModelPolicy.defaultModel(for: .iPhone), .base)   // charter
        XCTAssertEqual(WhisperModelPolicy.defaultModel(for: .iPad), .small)
    }

    func testTranscriberConfigAutoIsNil() throws {
        XCTAssertNil(try TranscriberConfig(model: .base).normalizedLanguage())  // default "auto"
        XCTAssertEqual(try TranscriberConfig(language: "de", model: .small).normalizedLanguage(), "de")
    }

    func testSegmentMappingIsSpeakerReady() {
        let raw = TranscribedSegment(text: "let's lock the schema", startTime: 10.0, endTime: 14.2)
        let seg: Segment = raw.asContractSegment(speaker: "Karol")

        XCTAssertEqual(seg.text, "let's lock the schema")
        XCTAssertEqual(seg.speaker, "Karol")
        XCTAssertNil(seg.speakerId)              // reserved slot — diarization fills it later
        XCTAssertEqual(seg.startTime, 10.0)
        XCTAssertEqual(seg.endTime, 14.2)
        XCTAssertFalse(seg.isBookmarked)
        XCTAssertNil(seg.deviceId)
    }
}
