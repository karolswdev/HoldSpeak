import XCTest
@testable import Contracts

final class DeskIntegrationProposalTests: XCTestCase {
    func testProposalCarriesQualifiedSourceIdentity() throws {
        let source = try XCTUnwrap(QualifiedRef(rawValue: "note:release"))
        let request = DeskIntegrationProposalRequest(
            text: "Ship after checks pass.",
            title: "Release checklist",
            sourceRef: source,
            sourceLabel: "Release checklist"
        )

        let object = try XCTUnwrap(
            JSONSerialization.jsonObject(with: JSONEncoder().encode(request))
                as? [String: String]
        )
        XCTAssertEqual(object["source_ref"], "note:release")
        XCTAssertEqual(object["source_label"], "Release checklist")
        XCTAssertEqual(object["text"], "Ship after checks pass.")
    }

    func testLegacyProposalOmitsSourceFields() throws {
        let request = DeskIntegrationProposalRequest(text: "Ship")
        let object = try XCTUnwrap(
            JSONSerialization.jsonObject(with: JSONEncoder().encode(request))
                as? [String: String]
        )
        XCTAssertNil(object["source_ref"])
        XCTAssertNil(object["source_label"])
        XCTAssertEqual(object["text"], "Ship")
    }
}
