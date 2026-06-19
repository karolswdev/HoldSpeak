import Foundation

/// On-device LLM size tiers (charter §"Local model strategy"). HSM-5-03.
public enum InferenceModel: String, Sendable, CaseIterable {
    case fourB = "4B"
    case eightB = "8B"
    case twelveBPlus = "12B+"
}

public enum InferenceModelPolicy {
    /// Charter per-device defaults: iPhone → 4B, iPad → 8B.
    public static func defaultModel(for device: DeviceClass) -> InferenceModel {
        switch device {
        case .iPhone: return .fourB
        case .iPad: return .eightB
        }
    }

    /// 12B+ is experimental and allowed **only when plugged in** — never a device
    /// default. 4B / 8B are always allowed.
    public static func isAllowed(_ model: InferenceModel, pluggedIn: Bool) -> Bool {
        model == .twelveBPlus ? pluggedIn : true
    }
}
