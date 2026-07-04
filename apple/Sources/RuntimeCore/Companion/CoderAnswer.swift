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

// MARK: - HSM-17-05: AI-drafted answers (approve-then-inject)

public extension CoderAnswer {

    /// The draft prompt: the coder's question is the task, any dropped-context
    /// grounding rides as `[CONTEXT]` (the desk's `[ROLE]/[CONTEXT]/[TASK]`
    /// assembly convention). The model drafts AS the user — the human reviews,
    /// edits, and only an explicit approve injects (the 17-04 path).
    static func draftPrompt(
        agent: String,
        question: String,
        groundingTitle: String? = nil,
        grounding: String? = nil
    ) -> String {
        var blocks: [String] = [
            """
            [ROLE]
            You draft a short reply for the user to review and send back to a \(agent) \
            coding session that asked them a question. Write AS the user, first person, \
            decisive and concise. Answer only what was asked. Return only the reply text — \
            no preamble, no quotes, no markdown fences.
            """
        ]
        let trimmedGrounding = (grounding ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmedGrounding.isEmpty {
            let source = (groundingTitle ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
            let head = source.isEmpty ? "[CONTEXT]" : "[CONTEXT — \(source)]"
            blocks.append("\(head)\n\(String(trimmedGrounding.prefix(6_000)))")
        }
        blocks.append("[QUESTION FROM \(agent.uppercased())]\n\(question.trimmingCharacters(in: .whitespacesAndNewlines))")
        blocks.append("[TASK]\nDraft the user's reply.")
        return blocks.joined(separator: "\n\n")
    }

    /// One provider call → the draft. The provider is the RESOLVED engine
    /// (on-device LlamaProvider or the endpoint — the caller resolves it fresh
    /// per call, the Mode-A KV rule). This never touches the desktop client:
    /// a draft is composed, never sent — only the human's approve injects.
    static func draft(
        _ provider: ILLMProvider,
        agent: String,
        question: String,
        groundingTitle: String? = nil,
        grounding: String? = nil
    ) async throws -> String {
        let prompt = draftPrompt(agent: agent, question: question,
                                 groundingTitle: groundingTitle, grounding: grounding)
        let raw = try await provider.complete(prompt: prompt)
        return raw.trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
