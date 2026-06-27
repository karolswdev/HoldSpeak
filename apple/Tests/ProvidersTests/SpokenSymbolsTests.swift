import XCTest
@testable import Providers

/// HSM-18-04 — `SpokenSymbols` ports `holdspeak/text_processor.py` (Phase 59) to Swift so the
/// iPad's DICTATION path turns spoken commands into symbols, exactly as the hub does. Pins the
/// built-in tables, the attach-side spacing, the one-pass longest-first guarantee, and user-wins.
final class SpokenSymbolsTests: XCTestCase {

    func testAttachLeftRemovesSpaceBefore() {
        XCTAssertEqual(SpokenSymbols().process("hello period"), "hello.")
        XCTAssertEqual(SpokenSymbols().process("wait comma then go"), "wait, then go")
        XCTAssertEqual(SpokenSymbols().process("really question mark"), "really?")
    }

    func testAttachRightRemovesSpaceAfter() {
        XCTAssertEqual(SpokenSymbols().process("open paren hello"), "(hello")
    }

    func testAttachBothRemovesSurroundingSpace() {
        XCTAssertEqual(SpokenSymbols().process("self dash aware"), "self-aware")
    }

    func testNewlineCommands() {
        XCTAssertEqual(SpokenSymbols().process("line one new line line two"), "line one\nline two")
        XCTAssertEqual(SpokenSymbols().process("a new paragraph b"), "a\n\nb")
    }

    func testWordBoundaryDoesNotEatPartialWords() {
        // "periodic" must not match "period"
        XCTAssertEqual(SpokenSymbols().process("the periodic table"), "the periodic table")
    }

    func testCaseInsensitive() {
        XCTAssertEqual(SpokenSymbols().process("done PERIOD"), "done.")
    }

    func testPlainTextUntouched() {
        XCTAssertEqual(SpokenSymbols().process("just regular words here"), "just regular words here")
        XCTAssertEqual(SpokenSymbols().process(""), "")
    }

    func testUserSymbolWinsOverBuiltIn() {
        // a user remaps "dash" to an em dash; the built-in hyphen mapping must be replaced
        let s = SpokenSymbols(userSymbols: [.init(spoken: "dash", symbol: "—", attach: "both")])
        XCTAssertEqual(s.process("a dash b"), "a—b")
    }

    func testUserPlainSymbol() {
        let s = SpokenSymbols(userSymbols: [.init(spoken: "smiley", symbol: ":)")])
        XCTAssertEqual(s.process("hi smiley"), "hi :)")
    }

    func testLongestFirstAcrossTables() {
        // a longer user phrase that contains a shorter built-in must win as a whole
        let s = SpokenSymbols(userSymbols: [.init(spoken: "double colon", symbol: "::")])
        XCTAssertEqual(s.process("scope double colon name"), "scope :: name")
    }

    func testReplacementIsLiteralNotRegexTemplate() {
        // a user symbol containing $ and backslash must be inserted literally
        let s = SpokenSymbols(userSymbols: [.init(spoken: "money", symbol: "$1\\2")])
        XCTAssertEqual(s.process("give money now"), "give $1\\2 now")
    }
}
