import XCTest
import Contracts
import InferenceBridge
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

    private actor BridgeWire: AdmittedInferenceBridgeWire {
        private var begins = 0
        private var reconciliations: [AdmittedInferenceDisposition] = []

        func begin(authorization _: String) async throws { begins += 1 }

        func reconcile(
            authorization: String,
            disposition: AdmittedInferenceDisposition,
            result _: String?
        ) async throws -> AdmittedInferenceReceipt {
            reconciliations.append(disposition)
            return .init(attemptID: authorization, disposition: disposition, terminal: true)
        }

        func observed() -> (begins: Int, reconciliations: [AdmittedInferenceDisposition]) {
            (begins, reconciliations)
        }
    }

    private actor CountingProvider: ILLMProvider {
        private let response: String
        private var calls = 0

        init(response: String) { self.response = response }

        func complete(prompt _: String) async throws -> String {
            calls += 1
            return response
        }

        func callCount() -> Int { calls }
    }

    private func admitted(_ wire: BridgeWire) -> (AdmittedInferenceClient, AdmittedInferenceAttempt) {
        (
            AdmittedInferenceClient(wire: wire),
            .init(authorization: UUID().uuidString, transport: .init())
        )
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

    // MARK: admitted attempt bridge

    func testGenerateRequiresReservationBeforeProviderTransport() async {
        let provider = CountingProvider(response: #"{"title":"never"}"#)

        do {
            let _: Draft = try await StructuredOutput.generate(Draft.self, prompt: "draft", using: provider)
            XCTFail("expected reservation-required error")
        } catch let error as AdmittedInferenceClientError {
            XCTAssertEqual(error, .reservationRequired)
        } catch {
            XCTFail("wrong error: \(error)")
        }

        let callCount = await provider.callCount()
        XCTAssertEqual(callCount, 0)
    }

    func testGenerateUsesOneReservationForOneTransportAndSuccessReceipt() async throws {
        let wire = BridgeWire()
        let admitted = admitted(wire)
        let provider = CountingProvider(response: #"{"title":"Ship"}"#)

        let value: Draft = try await StructuredOutput.generate(
            Draft.self,
            prompt: "draft",
            using: provider,
            admittedClient: admitted.0,
            admittedAttempt: admitted.1
        )

        XCTAssertEqual(value.title, "Ship")
        let callCount = await provider.callCount()
        XCTAssertEqual(callCount, 1)
        let observed = await wire.observed()
        XCTAssertEqual(observed.begins, 1)
        XCTAssertEqual(observed.reconciliations, [.succeeded])
    }

    func testMalformedOutputReconcilesSameReservationWithoutLocalRetry() async {
        let wire = BridgeWire()
        let admitted = admitted(wire)
        let provider = CountingProvider(response: "not JSON")

        do {
            let _: Draft = try await StructuredOutput.generate(
                Draft.self,
                prompt: "draft",
                using: provider,
                admittedClient: admitted.0,
                admittedAttempt: admitted.1
            )
            XCTFail("expected malformed output")
        } catch StructuredOutputError.noJSON {
            // The decoding error remains visible while the bridge reports it once.
        } catch {
            XCTFail("wrong error: \(error)")
        }

        let callCount = await provider.callCount()
        XCTAssertEqual(callCount, 1)
        let observed = await wire.observed()
        XCTAssertEqual(observed.begins, 1)
        XCTAssertEqual(observed.reconciliations, [.malformedOutput])
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
