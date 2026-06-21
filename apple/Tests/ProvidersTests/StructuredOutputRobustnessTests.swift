import XCTest
import Contracts
@testable import Providers

/// HSM-11-06 — the structured-output salvage hardened against real 4B drift: balanced
/// extraction, truncation recovery, conservative repair, array unwrap. Pure + model-free.
final class StructuredOutputRobustnessTests: XCTestCase {

    private struct Draft: Decodable, Equatable {
        let title: String
        let ok: Bool?
        let note: String?
    }
    private func decode(_ raw: String) throws -> Draft {
        try StructuredOutput.decode(Draft.self, from: raw)
    }

    // MARK: balanced extraction

    func testIgnoresTrailingProseWithStrayBrace() {
        let raw = #"{"title":"Ship it"} — and remember to close } your braces"#
        XCTAssertEqual(StructuredOutput.extractJSON(from: raw), #"{"title":"Ship it"}"#)
    }

    func testBraceInsideStringValueIsRespected() {
        let raw = #"prefix {"title":"use } and { with care","ok":true} suffix"#
        XCTAssertEqual(StructuredOutput.extractJSON(from: raw), #"{"title":"use } and { with care","ok":true}"#)
    }

    func testReturnsFirstOfTwoObjects() {
        XCTAssertEqual(StructuredOutput.extractJSON(from: #"{"title":"first"} {"title":"second"}"#),
                       #"{"title":"first"}"#)
    }

    func testNestedObjectBalances() {
        let raw = #"noise {"title":"x","meta":{"a":1,"b":[1,2]}} tail"#
        XCTAssertEqual(StructuredOutput.extractJSON(from: raw), #"{"title":"x","meta":{"a":1,"b":[1,2]}}"#)
    }

    // MARK: conservative repair

    func testTrailingCommaRepaired() throws {
        let d = try decode(#"{"title":"x","ok":true,}"#)
        XCTAssertEqual(d.title, "x"); XCTAssertEqual(d.ok, true)
    }

    func testPythonLiteralsRepaired() throws {
        let d = try decode(#"{"title":"x","ok":True,"note":None}"#)
        XCTAssertEqual(d.ok, true); XCTAssertNil(d.note)
    }

    func testRepairLeavesStringContentAlone() throws {
        // "True" and a comma/bracket sequence inside the body must NOT be repaired.
        let d = try decode(#"{"title":"It was True, indeed [1,2,]","ok":false}"#)
        XCTAssertEqual(d.title, "It was True, indeed [1,2,]")
        XCTAssertEqual(d.ok, false)
    }

    func testSmartQuotesRepaired() {
        let raw = "{\u{201C}title\u{201D}:\u{201C}x\u{201D}}"
        XCTAssertEqual(StructuredOutput.extractJSON(from: raw), #"{"title":"x"}"#)
    }

    // MARK: truncation salvage

    func testTruncatedNoCloserSalvaged() throws {
        let d = try decode(#"{"title":"shipped","ok":true"#)   // missing }
        XCTAssertEqual(d.title, "shipped"); XCTAssertEqual(d.ok, true)
    }

    func testTruncatedMidStringSalvaged() throws {
        let d = try decode(#"{"title":"the decision was to ship next fri"#)   // cut mid-string
        XCTAssertEqual(d.title, "the decision was to ship next fri")
    }

    func testTruncatedNestedSalvaged() throws {
        let d = try decode(#"{"title":"x","note":"deep"#)   // string + object both open
        XCTAssertEqual(d.title, "x"); XCTAssertEqual(d.note, "deep")
    }

    // MARK: array unwrap

    func testArrayWrappedObjectUnwraps() throws {
        let d = try decode(#"[{"title":"only","ok":true}]"#)
        XCTAssertEqual(d.title, "only"); XCTAssertEqual(d.ok, true)
    }

    // MARK: no regressions

    func testPureProseReturnsNil() {
        XCTAssertNil(StructuredOutput.extractJSON(from: "I could not find any decisions in this meeting."))
    }

    func testCleanObjectUnchanged() {
        XCTAssertEqual(StructuredOutput.extractJSON(from: #"{"title":"x"}"#), #"{"title":"x"}"#)
    }

    func testFencedWithLanguageTagStillWorks() {
        XCTAssertEqual(StructuredOutput.extractJSON(from: "```json\n{\"title\":\"x\"}\n```"), #"{"title":"x"}"#)
    }
}
