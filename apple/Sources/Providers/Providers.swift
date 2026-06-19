import Foundation
import Contracts

// Layer 3 — provider abstractions (charter Architecture). The Runtime Core
// depends on these protocols, never on a concrete engine. Method surfaces are
// intentionally minimal placeholders for Phase 1; each fills out in its phase:
// ITranscriber (Phase 3), ILLMProvider (Phase 5), IAudioCapture (Phase 2),
// IStorage (Phase 4), ISyncProvider (Phase 10).

public protocol IAudioCapture: Sendable {
    func start() throws
    func stop() throws
}

public protocol ITranscriber: Sendable {
    /// Produce contract `Segment`s from captured audio (speaker-ready).
    func transcribe() async throws -> [Segment]
}

public protocol ILLMProvider: Sendable {
    /// Run a completion; structured-output binding lands in Phase 5.
    func complete(prompt: String) async throws -> String
}

public protocol IStorage: Sendable {
    func saveMeeting(_ meeting: Meeting) throws
    func loadMeeting(id: String) throws -> Meeting?
}

public protocol ISyncProvider: Sendable {
    /// Push/pull contract objects across devices (Phase 10).
    func sync() async throws
}
