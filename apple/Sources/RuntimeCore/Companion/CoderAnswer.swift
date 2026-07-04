import Foundation
import Providers

/// HSM-17-04 — answering a waiting coder from the desk. One flow for every
/// human-authored input mode (typed / spoken / dropped-context): compose the
/// reply, make the exact session the hub's active reply target, then deliver
/// over the proven Phase-13 inject (`/api/dictation/remote`). Never autonomous:
/// this runs only on an explicit human send/approve action, and a failure
/// throws — the desk keeps the question, nothing silently lost.
public enum CoderAnswer {

    /// Assemble the reply plus optional dropped-context grounding into the one
    /// injected payload. The grounding rides under a visible separator, cited
    /// by its source title, so the coder (and the human reviewing the composer)
    /// see exactly what context was attached.
    public static func compose(
        reply: String,
        groundingTitle: String? = nil,
        grounding: String? = nil
    ) -> String {
        let trimmedReply = reply.trimmingCharacters(in: .whitespacesAndNewlines)
        let trimmedGrounding = (grounding ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedGrounding.isEmpty else { return trimmedReply }
        let source = (groundingTitle ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        let header = source.isEmpty ? "Context:" : "Context (from \(source)):"
        guard !trimmedReply.isEmpty else { return "\(header)\n\(trimmedGrounding)" }
        return "\(trimmedReply)\n\n---\n\(header)\n\(trimmedGrounding)"
    }

    /// Select-then-send, the server-side-truth targeting the Companion board
    /// proved (HSM-13-03): `POST /api/coders/select {agent, session_id}` makes
    /// this session the active reply target, then the remote dictation lands in
    /// it. `raw` skips the hub pipeline (the approve keystroke path). Throws on
    /// an unreachable hub or a failed select — delivery is never guessed.
    public static func send(
        _ client: IDesktopClient,
        agent: String,
        sessionID: String,
        reply: String,
        groundingTitle: String? = nil,
        grounding: String? = nil,
        raw: Bool = false
    ) async throws -> RemoteDictationResult {
        try await client.selectCompanionTarget(agent: agent, sessionID: sessionID)
        let payload = compose(reply: reply, groundingTitle: groundingTitle, grounding: grounding)
        return try await client.sendRemoteDictation(text: payload, target: .agent, raw: raw)
    }

    /// Approve a blocking permission ask: the literal dialog keystroke ("1" =
    /// the Yes option in both coders' permission dialogs), delivered verbatim
    /// (`raw: true` — the hub pipeline must not rewrite a keystroke). Explicit
    /// by construction: only a human tap on the approval card reaches this.
    public static func approve(
        _ client: IDesktopClient,
        agent: String,
        sessionID: String
    ) async throws -> RemoteDictationResult {
        try await send(client, agent: agent, sessionID: sessionID, reply: "1", raw: true)
    }
}
