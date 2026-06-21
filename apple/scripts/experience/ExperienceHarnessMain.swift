import SwiftUI

/// Screenshot harness for the HSM-14 "Tactile Sheets" experience — renders the recrafted
/// meeting + intelligence surface with mock data so the craft can be proven in the iOS
/// Simulator (no engine, no device needed).
@main
struct ExperienceHarnessApp: App {
    var body: some Scene {
        WindowGroup {
            MeetingExperienceView(vm: ExperienceMock.meeting)
        }
    }
}
