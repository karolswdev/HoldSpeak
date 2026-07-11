import XCTest
@testable import Contracts

final class RelationshipContractTests: XCTestCase {
    func testQualifiedRefRejectsAmbiguousIdentity() {
        XCTAssertNil(QualifiedRef(rawValue: "same"))
        XCTAssertEqual(QualifiedRef(rawValue: "note:same")?.rawValue, "note:same")
        XCTAssertNotEqual(
            QualifiedRef(rawValue: "note:same"),
            QualifiedRef(rawValue: "artifact:same")
        )
    }

    func testIndependentRelationshipBucketsRoundTrip() throws {
        let now = Date(timeIntervalSince1970: 1_700_000_000)
        let knowledge = KnowledgeMembership(
            knowledgeId: "k1", resourceRef: "note:n1",
            createdAt: now, lastModified: now
        )
        let project = ProjectRelationship(
            id: "p1|note:n1", projectId: "p1", resourceRef: "note:n1",
            relationship: "source", source: "manual", confidence: 1,
            createdAt: now, lastModified: now, deleted: false
        )
        let set = ChangeSet(
            knowledgeMemberships: [.live(
                knowledge, id: knowledge.id, kind: .knowledgeMembership,
                modifiedAt: now
            )],
            projectRelationships: [.live(
                project, id: project.id, kind: .projectRelationship,
                modifiedAt: now
            )],
            projects: [.live(
                Project(id: "p1", name: "Launch", createdAt: now, updatedAt: now),
                id: "p1", kind: .project, modifiedAt: now
            )]
        )
        let data = try HoldSpeakContracts.encoder().encode(set)
        let decoded = try HoldSpeakContracts.decoder().decode(ChangeSet.self, from: data)

        XCTAssertEqual(decoded, set)
        XCTAssertEqual(decoded.count, 3)
        XCTAssertEqual(decoded.knowledgeMemberships.first?.value?.resourceRef, "note:n1")
        XCTAssertEqual(decoded.projectRelationships.first?.value?.relationship, "source")
        XCTAssertEqual(decoded.projects.first?.value?.name, "Launch")
    }
}
