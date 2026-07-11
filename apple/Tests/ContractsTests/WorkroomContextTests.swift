import XCTest
@testable import Contracts

final class WorkroomContextTests: XCTestCase {
    func testDeskContextRoundTripsIdentityAndReturn() throws {
        let subject = try XCTUnwrap(QualifiedRef(rawValue: "workflow:wf-7"))
        let draft = try XCTUnwrap(QualifiedRef(rawValue: "note:draft-2"))
        let run = try XCTUnwrap(QualifiedRef(rawValue: "artifact:run-3"))
        let context = try XCTUnwrap(WorkroomContext(
            subjectRef: subject,
            action: "edit-workflow",
            draftRef: draft,
            runRef: run
        ))

        let decoded = try JSONDecoder().decode(
            WorkroomContext.self,
            from: JSONEncoder().encode(context)
        )
        XCTAssertEqual(decoded, context)
        XCTAssertEqual(decoded.returnRef, subject)
    }

    func testDecodeIgnoresFutureMetadata() throws {
        let data = Data(#"""
        {
          "version": 2,
          "origin": "desk",
          "subject_ref": "meeting:m1",
          "action": "review-meeting",
          "return_to": "desk",
          "future_hint": {"ignored": true}
        }
        """#.utf8)
        let context = try JSONDecoder().decode(WorkroomContext.self, from: data)
        XCTAssertEqual(context.version, 2)
        XCTAssertEqual(context.subjectRef?.rawValue, "meeting:m1")
    }

    func testDecodeRefusesAuthoredContent() {
        let data = Data(#"""
        {
          "version": 1,
          "origin": "desk",
          "action": "dictate",
          "return_to": "desk",
          "transcript": "private words"
        }
        """#.utf8)
        XCTAssertThrowsError(try JSONDecoder().decode(WorkroomContext.self, from: data))
    }

    func testActionIsABoundedIdentifier() {
        XCTAssertNil(WorkroomContext(action: "Write this private prompt"))
        XCTAssertNotNil(WorkroomContext(action: "dictate-about-subject"))
    }
}
