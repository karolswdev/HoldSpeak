import XCTest
@testable import Providers

/// HSM-18-04 — the persisted user dictionary + HSM-18-03 — the one language resolver.
/// Both read UserDefaults through an injectable suite, so these tests never touch the
/// real defaults.
final class SpokenSymbolsStoreTests: XCTestCase {

    private var defaults: UserDefaults!
    private let suite = "hs-tests-symbols-store"

    override func setUp() {
        super.setUp()
        defaults = UserDefaults(suiteName: suite)
        defaults.removePersistentDomain(forName: suite)
    }

    func testUserSymbolsRoundTripAndConfigure() {
        XCTAssertEqual(SpokenSymbols.loadUserSymbols(defaults: defaults), [])
        let mine = [SpokenSymbols.UserSymbol(spoken: "tilde", symbol: "~"),
                    SpokenSymbols.UserSymbol(spoken: "dash", symbol: "—", attach: "both")]
        SpokenSymbols.saveUserSymbols(mine, defaults: defaults)
        XCTAssertEqual(SpokenSymbols.loadUserSymbols(defaults: defaults), mine)

        // configured() honors user-wins: "dash" now yields the em dash, not the built-in hyphen.
        let processed = SpokenSymbols.configured(defaults: defaults).process("self dash aware tilde")
        XCTAssertEqual(processed, "self—aware ~")
    }

    func testCorruptStoreFallsBackToBuiltins() {
        defaults.set(Data("not json".utf8), forKey: SpokenSymbols.userSymbolsKey)
        XCTAssertEqual(SpokenSymbols.loadUserSymbols(defaults: defaults), [])
        XCTAssertEqual(SpokenSymbols.configured(defaults: defaults).process("hello period"), "hello.")
    }

    func testConfiguredLanguageCodeResolves() {
        XCTAssertNil(WhisperLanguage.configuredCode(defaults: defaults))          // absent = auto
        defaults.set("auto", forKey: WhisperLanguage.settingKey)
        XCTAssertNil(WhisperLanguage.configuredCode(defaults: defaults))
        defaults.set("pl", forKey: WhisperLanguage.settingKey)
        XCTAssertEqual(WhisperLanguage.configuredCode(defaults: defaults), "pl")
        defaults.set("Polish", forKey: WhisperLanguage.settingKey)
        XCTAssertEqual(WhisperLanguage.configuredCode(defaults: defaults), "pl")  // names resolve
        defaults.set("klingon", forKey: WhisperLanguage.settingKey)
        XCTAssertNil(WhisperLanguage.configuredCode(defaults: defaults))          // unknown -> auto, never a crash
    }
}
