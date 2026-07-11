import XCTest
@testable import Contracts

final class InferenceTargetTests: XCTestCase {
    private let now = Date(timeIntervalSince1970: 1_700_000_000)

    func testProfileAliasMapsAllDestinationClasses() {
        let rows = [
            RuntimeProfile(id: "local", name: "This iPad", kind: .onDevice,
                           modelFile: "q.gguf", createdAt: now, updatedAt: now),
            RuntimeProfile(id: "pair", name: "Studio", kind: .desktop,
                           model: "Qwen", createdAt: now, updatedAt: now),
            RuntimeProfile(id: "lan", name: "LAN", kind: .openAICompatible,
                           baseURL: "http://192.168.1.43:8000/v1", model: "Qwen",
                           createdAt: now, updatedAt: now),
            RuntimeProfile(id: "mesh", name: "Garage", kind: .meshNode,
                           node: "garage", createdAt: now, updatedAt: now),
            RuntimeProfile(id: "svc", name: "Vendor", kind: .openAICompatible,
                           baseURL: "https://example.com/v1", model: "Claude",
                           createdAt: now, updatedAt: now),
        ]
        XCTAssertEqual(rows.map { $0.inferenceTarget().kind }, [
            .thisDevice, .pairedDevice, .privateEndpoint, .meshNode, .externalService,
        ])
        XCTAssertEqual(rows[2].inferenceTarget().boundary, "private_network")
        XCTAssertEqual(rows[2].inferenceTarget().engine, "openai_compatible")
        XCTAssertEqual(rows[2].inferenceTarget().model, "Qwen")
    }

    func testMissingKeyAndStaleManifestAreUnavailableWithoutSecretMaterial() throws {
        let endpoint = RuntimeProfile(
            id: "svc", name: "Vendor", kind: .openAICompatible,
            baseURL: "https://example.com/v1", requiresKey: true,
            createdAt: now, updatedAt: now
        ).inferenceTarget(keyPresent: false)
        XCTAssertFalse(endpoint.readiness.available)
        XCTAssertEqual(endpoint.readiness.state, "needs_key")
        let wire = String(decoding: try JSONEncoder().encode(endpoint), as: UTF8.self)
        XCTAssertFalse(wire.contains("apiKey"))
        XCTAssertFalse(wire.contains("secret"))

        let paired = RuntimeProfile(
            id: "pair", name: "Studio", kind: .desktop, model: "Old model",
            createdAt: now, updatedAt: now
        ).inferenceTarget(paired: true, modelAdvertised: false)
        XCTAssertEqual(paired.readiness.state, "stale_manifest")
        XCTAssertTrue(paired.readiness.reason.contains("Old model"))
    }

    func testPlacementReceiptDecodesFromHubSnakeCase() throws {
        let data = Data("""
        {
          "target_id":"lan","target_name":"LAN box","target_kind":"private_endpoint",
          "boundary":"private_network","owner":"you","transport":"https",
          "data_classes":["instruction","generated_output"],
          "engine":"openai_compatible","model":"Qwen","fallback_reason":null
        }
        """.utf8)
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let receipt = try decoder.decode(InferencePlacementReceipt.self, from: data)
        XCTAssertEqual(receipt.targetId, "lan")
        XCTAssertEqual(receipt.boundary, "private_network")
        XCTAssertNil(receipt.fallbackReason)
    }
}
