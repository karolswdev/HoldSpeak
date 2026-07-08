import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Contracts

// HSM-26-02 — the DeskOS belt reads the delivery rails from the hub's mission
// control (GET /api/missioncontrol/state), the SAME three-document relay the
// web conveyor consumes (Phase 82/86). Read-only, byte-honest: the belt renders
// what the rails said, never scrapes. New extension file by the equilibrium
// conflict rule — no edits to HTTPDesktopClient.swift. Own request helpers
// because the main file's are private (the +Ask precedent).

extension HTTPDesktopClient {

    /// `GET /api/missioncontrol/state` — one entry per configured rails repo,
    /// each carrying its state feed or a typed absence. The desk polls this to
    /// render the belt. A malformed payload throws so the surface shows an
    /// honest failure, never a fake-idle belt.
    public func missionControlState() async throws -> BeltState {
        let data = try await sendMC(makeMCRequest(path: "api/missioncontrol/state"))
        guard let state = try? HoldSpeakContracts.decoder().decode(BeltState.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return state
    }

    /// `GET /api/missioncontrol/rails/journal` — the ambient observer's journal
    /// of rail motion, newest first (Phase 88). Read-only; entries are notes.
    public func railsJournal(limit: Int = 50) async throws -> [RailsJournalEntry] {
        let data = try await sendMC(makeMCRequest(path: "api/missioncontrol/rails/journal?limit=\(limit)"))
        guard let dto = try? HoldSpeakContracts.decoder().decode(RailsJournalDTO.self, from: data) else {
            throw DesktopClientError.malformed
        }
        return dto.entries ?? []
    }

    struct RailsJournalDTO: Decodable { var entries: [RailsJournalEntry]? }

    // MARK: - internals (mirror the +Ask request helpers)

    private func sendMC(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
            throw DesktopClientError.http(http.statusCode)
        }
        return data
    }

    private func makeMCRequest(path: String) -> URLRequest {
        let base = config.baseURL.absoluteString.hasSuffix("/")
            ? String(config.baseURL.absoluteString.dropLast()) : config.baseURL.absoluteString
        var request = URLRequest(url: URL(string: "\(base)/\(path)") ?? config.baseURL)
        request.httpMethod = "GET"
        request.timeoutInterval = config.timeout
        if let token = config.token, !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return request
    }
}
