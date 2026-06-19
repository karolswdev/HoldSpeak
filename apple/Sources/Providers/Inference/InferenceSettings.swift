import Foundation

/// Where a meeting's intelligence runs. The charter's three runtime modes
/// (CHARTER §"Runtime modes"), made a first-class user setting per the owner's
/// 2026-06-19 steer: local is the privacy default, but the same `ILLMProvider`
/// seam lets a meeting instead run against an always-available endpoint — a
/// laptop/homelab on the LAN, or any OpenAI-compatible service — so the iPad need
/// not spend unified memory on a resident model when a capable endpoint is right
/// there.
///
/// All three modes are implementations of the one `ILLMProvider` interface, so the
/// Runtime Core never learns which is in play. `local` (Mode A) is the on-device
/// GGUF engine (HSM-5-02); `homelab` (Mode B, recommended) and `endpoint` (Mode C)
/// both speak the OpenAI-compatible HTTP API and share ``OpenAIEndpointProvider`` —
/// the distinction is intent/default-target, not protocol.
public enum RuntimeMode: String, Sendable, CaseIterable, Codable {
    /// Mode A — fully on-device GGUF inference; no egress (HSM-5-02).
    case local
    /// Mode B — an OpenAI-compatible endpoint on your own LAN/homelab (recommended).
    case homelab
    /// Mode C — any configured OpenAI-compatible endpoint.
    case endpoint

    /// Whether the mode keeps all inference on the device (no network egress).
    public var isFullyLocal: Bool { self == .local }
}

/// Connection settings for an OpenAI-compatible endpoint (Modes B and C).
///
/// `baseURL` is the OpenAI API root the server exposes — e.g.
/// `http://192.168.1.43:8080/v1` for a self-hosted llama.cpp server. The provider
/// appends `chat/completions` to it.
public struct EndpointConfig: Sendable, Codable, Equatable {
    public var baseURL: URL
    /// Model name the server expects. Self-hosted servers often ignore this and
    /// serve whatever is loaded; it is still sent for OpenAI compatibility.
    public var model: String
    /// Optional bearer token. Held only here and attached at request time — never
    /// logged, never part of a persisted artifact.
    public var apiKey: String?
    public var temperature: Double
    public var timeout: TimeInterval

    public init(
        baseURL: URL,
        model: String,
        apiKey: String? = nil,
        temperature: Double = 0.2,
        timeout: TimeInterval = 120
    ) {
        self.baseURL = baseURL
        self.model = model
        self.apiKey = apiKey
        self.temperature = temperature
        self.timeout = timeout
    }
}

public enum InferenceSettingsError: Error, Equatable {
    /// Mode A was requested but this build has no on-device engine yet (HSM-5-02
    /// wires llama.cpp). Modes B/C are available now.
    case localEngineUnavailable
    /// An endpoint mode was requested without an `EndpointConfig`.
    case endpointNotConfigured
}

/// Resolves a `RuntimeMode` (+ optional endpoint config) into a concrete
/// `ILLMProvider`. The single place mode-selection becomes a provider, so the
/// host/UI flips one setting and the Runtime Core is unaffected.
public enum InferenceProviderFactory {
    public static func make(
        mode: RuntimeMode,
        endpoint: EndpointConfig? = nil,
        session: URLSession = .shared
    ) throws -> ILLMProvider {
        switch mode {
        case .local:
            // Mode A lands with the on-device GGUF engine (HSM-5-02). Until then a
            // caller selecting local gets a clear, recoverable signal — not a crash.
            throw InferenceSettingsError.localEngineUnavailable
        case .homelab, .endpoint:
            guard let endpoint else { throw InferenceSettingsError.endpointNotConfigured }
            return OpenAIEndpointProvider(config: endpoint, session: session)
        }
    }
}
