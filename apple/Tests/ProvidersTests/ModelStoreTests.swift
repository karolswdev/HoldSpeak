import XCTest
import Contracts
@testable import Providers

/// HSM-5-03 — the model catalog + store. Host-testable with temp dirs + dummy
/// files; no network, no real weights.
final class ModelStoreTests: XCTestCase {

    private func tempStore() throws -> ModelStore {
        let dir = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent("hsm-models-\(UUID().uuidString)", isDirectory: true)
        let store = ModelStore(root: dir)
        try store.ensureRoot()
        return store
    }

    private func writeDummy(_ name: String) throws -> URL {
        let url = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent(name)
        try Data("gguf".utf8).write(to: url)
        return url
    }

    func testCatalogPinsEveryTier() {
        for tier in InferenceModel.allCases {
            let a = ModelCatalog.artifact(for: tier)
            XCTAssertEqual(a.tier, tier)
            XCTAssertFalse(a.huggingFaceRepo.isEmpty)
            XCTAssertTrue(a.fileName.hasSuffix(".gguf"))
            XCTAssertEqual(a.quantization, "Q4_K_M")
        }
        XCTAssertEqual(ModelCatalog.defaultArtifact(for: .iPhone).tier, .fourB)   // per-device policy
        XCTAssertEqual(ModelCatalog.defaultArtifact(for: .iPad).tier, .eightB)
    }

    func testImportCopiesAndListsOnlyGGUF() throws {
        let store = try tempStore()
        let src = try writeDummy("sideloaded-\(UUID().uuidString).gguf")
        let notModel = try writeDummy("readme-\(UUID().uuidString).txt")
        _ = try store.importModel(from: src)
        _ = try store.importModel(from: notModel)   // copied, but not listed as a model

        let installed = try store.installedModels()
        XCTAssertEqual(installed.count, 1)
        XCTAssertEqual(installed.first?.pathExtension, "gguf")
    }

    func testResolveActiveFollowsPerDeviceDefault() throws {
        let store = try tempStore()
        XCTAssertNil(store.resolveActive(for: .iPad))      // nothing installed yet

        // Install the iPad default (8B) under its catalogued filename.
        let eightB = ModelCatalog.artifact(for: .eightB)
        try Data("gguf".utf8).write(to: store.root.appendingPathComponent(eightB.fileName))

        XCTAssertEqual(store.resolveActive(for: .iPad)?.lastPathComponent, eightB.fileName)
        XCTAssertNil(store.resolveActive(for: .iPhone))    // 4B not installed
        XCTAssertTrue(store.isInstalled(eightB))
    }

    func testDeleteRemoves() throws {
        let store = try tempStore()
        let dest = try store.importModel(from: writeDummy("m-\(UUID().uuidString).gguf"))
        XCTAssertEqual(try store.installedModels().count, 1)
        try store.delete(dest)
        XCTAssertEqual(try store.installedModels().count, 0)
    }
}
