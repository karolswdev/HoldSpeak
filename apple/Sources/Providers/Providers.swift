import Foundation
import Contracts

// Layer 3 — provider abstractions (charter Architecture). The Runtime Core
// depends on these protocols, never on a concrete engine. Method surfaces are
// intentionally minimal placeholders for Phase 1; each fills out in its phase:
// ITranscriber (Phase 3), ILLMProvider (Phase 5), IAudioCapture (Phase 2),
// IStorage (Phase 4), ISyncProvider (Phase 10).

public protocol IAudioCapture: Sendable {
    /// Begin capture; `onChunk` is called with 16 kHz mono PCM16 chunks as audio
    /// streams in. HSM-2-01/02.
    func start(onChunk: @escaping @Sendable (AudioChunk) -> Void) throws
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
    func saveArtifact(_ artifact: Artifact) throws
    func loadArtifacts(meetingId: String) throws -> [Artifact]
}

public protocol ISyncProvider: Sendable {
    /// Push/pull contract objects across devices (Phase 10).
    func sync() async throws
}
