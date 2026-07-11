import XCTest
@testable import Contracts

final class TrustDestinationTests: XCTestCase {
    func testSetupStatusDecodesCanonicalDestinationInventory() throws {
        let data = #"{"trust":{"summary":"1 external destination enabled.","destinations":[{"id":"slack","name":"Slack","operation":"Send approved text","enabled":true,"destination":"Configured Slack workspace","boundary":"One configured webhook destination","data_class":"Preview text","authority_basis":"Per-action approval","background_ability":"No","revoke_action":"Delete the secret","last_receipt":null}]}}"#.data(using: .utf8)!
        let status = try HoldSpeakContracts.decoder().decode(SetupStatus.self, from: data)
        let destination = try XCTUnwrap(status.trust?.destinations?.first)
        XCTAssertEqual(destination.id, "slack")
        XCTAssertEqual(destination.operation, "Send approved text")
        XCTAssertEqual(destination.dataClass, "Preview text")
        XCTAssertEqual(destination.authorityBasis, "Per-action approval")
        XCTAssertEqual(destination.enabled, true)
    }
}
