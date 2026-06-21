import XCTest
@testable import Providers

/// HSM-13-04 — `WhisperText.clean` strips WhisperKit control tokens so the coder
/// receives clean prose. The leaked string is the exact one a real-metal run on the
/// iPad delivered into a tmux pane before the fix.
final class WhisperTextTests: XCTestCase {

    func testStripsTheRealMetalLeakedTokens() {
        let raw = "<|startoftranscript|><|en|><|transcribe|><|0.00|> I want very low TTL. Thank you.<|6.08|><|endoftext|>"
        XCTAssertEqual(WhisperText.clean(raw), "I want very low TTL. Thank you.")
    }

    func testStripsScatteredTimestampTokens() {
        let raw = "<|0.00|> Use Redis <|2.40|> with a low TTL <|5.00|>"
        XCTAssertEqual(WhisperText.clean(raw), "Use Redis with a low TTL")
    }

    func testLeavesCleanTextUntouched() {
        XCTAssertEqual(WhisperText.clean("Use Redis with a 24 hour TTL."), "Use Redis with a 24 hour TTL.")
    }

    func testCollapsesWhitespaceLeftByTokens() {
        XCTAssertEqual(WhisperText.clean("  hello   <|en|>   world  "), "hello world")
    }

    func testEmptyOrTokenOnlyBecomesEmpty() {
        XCTAssertEqual(WhisperText.clean("<|startoftranscript|><|endoftext|>"), "")
        XCTAssertEqual(WhisperText.clean("   "), "")
    }
}
