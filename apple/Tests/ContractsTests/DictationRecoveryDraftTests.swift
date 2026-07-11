import Foundation
import XCTest
@testable import Contracts

final class DictationRecoveryDraftTests: XCTestCase {
    func testDraftSurvivesAStoreReopenWithTheSameDeliveryIdentity() throws {
        let suite = try XCTUnwrap(UserDefaults(suiteName: "DictationRecoveryDraftTests.reopen"))
        suite.removePersistentDomain(forName: "DictationRecoveryDraftTests.reopen")
        let store = DictationRecoveryStore(defaults: suite)
        let draft = DictationRecoveryDraft(
            text: "Words retained on this device.",
            deliveryID: "device:delivery-1",
            destination: "Studio Mac",
            updatedAt: Date(timeIntervalSince1970: 1_700_000_000)
        )

        store.save(draft)

        XCTAssertEqual(DictationRecoveryStore(defaults: suite).load(), draft)
    }

    func testEmptyDraftClearsThePersistedRecoveryRecord() throws {
        let suiteName = "DictationRecoveryDraftTests.clear"
        let suite = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        suite.removePersistentDomain(forName: suiteName)
        let store = DictationRecoveryStore(defaults: suite)
        store.save(DictationRecoveryDraft(
            text: "keep", deliveryID: "delivery-1", destination: "Mac"))

        store.save(DictationRecoveryDraft(
            text: "", deliveryID: "delivery-2", destination: "Mac"))

        XCTAssertNil(store.load())
    }
}
