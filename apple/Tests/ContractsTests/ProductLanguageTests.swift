import XCTest
@testable import Contracts

final class ProductLanguageTests: XCTestCase {
    private func registryData() throws -> Data {
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
        return try Data(contentsOf: root.appendingPathComponent("docs/product-language.json"))
    }

    private func registry() throws -> ProductLanguageRegistry {
        try HoldSpeakContracts.decoder().decode(ProductLanguageRegistry.self, from: registryData())
    }

    func testGoldenRegistryDecodesAndMatchesSwiftSnapshot() throws {
        let registry = try registry()
        XCTAssertEqual(registry.registryVersion, ProductLanguage.version)
        XCTAssertEqual(Set(registry.destinationClasses), Set(ProductDestinationClass.allCases))
        XCTAssertEqual(Set(registry.decisionKinds), Set(ProductDecisionKind.allCases))
        XCTAssertEqual(Set(registry.controlModes), Set(ControlMode.allCases))
        XCTAssertEqual(registry.lifecycleAxes, ProductLanguage.lifecycleAxes)
        XCTAssertEqual(registry.meetingProjections, ProductLanguage.meetingProjections)

        for term in CanonicalProductTerm.allCases {
            let source = try XCTUnwrap(registry.terms[term.rawValue])
            XCTAssertEqual(ProductLanguage.label(term), source.singular, term.rawValue)
            XCTAssertEqual(ProductLanguage.label(term, plural: true), source.plural, term.rawValue)
        }
        for (alias, target) in registry.legacyAliases {
            XCTAssertEqual(try registry.canonicalTerm(for: alias).rawValue, target)
            XCTAssertEqual(try ProductLanguage.canonicalTerm(for: alias).rawValue, target)
        }
    }

    func testUnknownValuesAreRejected() throws {
        XCTAssertThrowsError(try ProductLanguage.canonicalTerm(for: "thing"))
        XCTAssertThrowsError(try JSONDecoder().decode(
            ProductDestinationClass.self,
            from: Data("\"somewhere\"".utf8)
        ))
        XCTAssertThrowsError(try JSONDecoder().decode(
            ControlMode.self,
            from: Data("\"reckless\"".utf8)
        ))
    }
}
