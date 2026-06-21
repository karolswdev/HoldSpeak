import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// HSM-14-01/03 — the "Tactile Sheets" hand-driven meeting + intelligence surface.
// Design system (Signal, native) + gesture-first components. The view takes simple
// presentation VMs; the real app maps Phase-0 `Artifact` → these.

// MARK: - Design system (Signal, native SwiftUI tokens)

enum DS {
    // Surfaces (deep dark, layered)
    static let bg    = Color(hex: 0x0E0F13)
    static let s1    = Color(hex: 0x16181F)
    static let s2    = Color(hex: 0x1D202A)
    static let s3    = Color(hex: 0x262A36)
    static let line  = Color.white.opacity(0.08)
    // Text
    static let text  = Color(hex: 0xF3F4F7)
    static let muted = Color(hex: 0x9CA3B2)
    static let faint = Color(hex: 0x6C7384)
    // Accents / semantics
    static let accent = Color(hex: 0xFF6B35)
    static let ok     = Color(hex: 0x39D98A)
    static let warn   = Color(hex: 0xF2A33C)
    static let local  = Color(hex: 0x5B8DEF)

    // Spacing rhythm
    static let xs: CGFloat = 6, sm: CGFloat = 10, md: CGFloat = 16, lg: CGFloat = 22, xl: CGFloat = 30
    // Radii
    static let rCard: CGFloat = 24, rSheet: CGFloat = 32, rBtn: CGFloat = 20
}

extension Color {
    init(hex: UInt32) {
        self.init(.sRGB, red: Double((hex >> 16) & 0xff) / 255,
                  green: Double((hex >> 8) & 0xff) / 255,
                  blue: Double(hex & 0xff) / 255, opacity: 1)
    }
}

func haptic(_ style: Int = 0) {
    #if canImport(UIKit)
    let gen = UIImpactFeedbackGenerator(style: style == 0 ? .light : .medium)
    gen.impactOccurred()
    #endif
}

// MARK: - Presentation models

struct ArtifactVM: Identifiable {
    enum Kind {
        case decisions, actions, risks, requirements
        var label: String {
            switch self {
            case .decisions: return "Decisions"; case .actions: return "Action items"
            case .risks: return "Risk register"; case .requirements: return "Requirements"
            }
        }
        var glyph: String {
            switch self {
            case .decisions: return "checkmark.seal.fill"; case .actions: return "bolt.fill"
            case .risks: return "exclamationmark.triangle.fill"; case .requirements: return "list.bullet.rectangle.fill"
            }
        }
        var tint: Color {
            switch self {
            case .decisions: return DS.ok; case .actions: return DS.accent
            case .risks: return DS.warn; case .requirements: return DS.local
            }
        }
    }
    let id = UUID()
    var kind: Kind
    var title: String
    var detail: String
    var reveal: CGFloat = 0   // screenshot: pre-reveal the swipe action on one card
}

struct MeetingVM {
    var title: String
    var when: String
    var duration: String
    var artifacts: [ArtifactVM]
}

// MARK: - Atoms

private struct Chip: View {
    let text: String
    var dot: Color? = nil
    var fill: Color = DS.s2
    var fg: Color = DS.muted
    var body: some View {
        HStack(spacing: 6) {
            if let dot { Circle().fill(dot).frame(width: 7, height: 7) }
            Text(text).font(.system(size: 13, weight: .semibold))
        }
        .foregroundStyle(fg)
        .padding(.horizontal, 11).padding(.vertical, 6)
        .background(fill, in: Capsule())
        .overlay(Capsule().stroke(DS.line, lineWidth: 1))
    }
}

private struct SectionLabel: View {
    let text: String
    var body: some View {
        Text(text).font(.system(size: 12, weight: .heavy)).tracking(1.8)
            .foregroundStyle(DS.faint)
    }
}

// MARK: - Swipeable artifact card (the hand-driven core)

struct SwipeableArtifactCard: View {
    let vm: ArtifactVM
    @State private var dragX: CGFloat = 0
    @State private var committed = false

    var body: some View {
        let x = dragX + vm.reveal
        ZStack {
            // Trailing action revealed on left-swipe: Approve.
            HStack {
                Spacer()
                actionGlyph("checkmark", "Approve", DS.ok, active: x < -40)
                    .padding(.trailing, DS.lg)
            }
            // The card face slides over it.
            face
                .offset(x: min(0, x))
                .gesture(
                    DragGesture(minimumDistance: 8)
                        .onChanged { g in dragX = max(-150, min(0, g.translation.width)) }
                        .onEnded { g in
                            if g.translation.width < -90 { haptic(1); committed = true; withAnimation(.spring(response: 0.35, dampingFraction: 0.8)) { dragX = 0 } }
                            else { withAnimation(.spring(response: 0.3, dampingFraction: 0.85)) { dragX = 0 } }
                        }
                )
        }
        .opacity(committed ? 0.5 : 1)
    }

    private var face: some View {
        VStack(alignment: .leading, spacing: DS.sm) {
            HStack(spacing: DS.sm) {
                ZStack {
                    RoundedRectangle(cornerRadius: 11, style: .continuous).fill(vm.kind.tint.opacity(0.16))
                    Image(systemName: vm.kind.glyph).font(.system(size: 16, weight: .bold)).foregroundStyle(vm.kind.tint)
                }.frame(width: 38, height: 38)
                VStack(alignment: .leading, spacing: 2) {
                    Text(vm.kind.label).font(.system(size: 13, weight: .heavy)).tracking(0.5).foregroundStyle(vm.kind.tint)
                    Text(vm.title).font(.system(size: 17, weight: .bold)).foregroundStyle(DS.text)
                }
                Spacer()
                Image(systemName: "circle.dashed").font(.system(size: 15, weight: .semibold)).foregroundStyle(DS.faint)
            }
            Text(vm.detail).font(.system(size: 15)).foregroundStyle(DS.muted).lineSpacing(2).lineLimit(3)
            HStack(spacing: 7) {
                Image(systemName: "hand.draw").font(.system(size: 11, weight: .bold))
                Text("swipe to approve").font(.system(size: 12, weight: .semibold))
            }.foregroundStyle(DS.faint.opacity(0.8))
        }
        .padding(DS.md)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(DS.s1, in: RoundedRectangle(cornerRadius: DS.rCard, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: DS.rCard, style: .continuous).stroke(DS.line, lineWidth: 1))
        .shadow(color: .black.opacity(0.35), radius: 18, x: 0, y: 10)
    }

    private func actionGlyph(_ sys: String, _ label: String, _ tint: Color, active: Bool) -> some View {
        VStack(spacing: 5) {
            ZStack {
                Circle().fill(tint.opacity(active ? 1 : 0.22))
                Image(systemName: sys).font(.system(size: 19, weight: .heavy)).foregroundStyle(active ? .black : tint)
            }.frame(width: 46, height: 46)
            Text(label).font(.system(size: 11, weight: .bold)).foregroundStyle(tint)
        }
        .scaleEffect(active ? 1.08 : 1)
        .animation(.spring(response: 0.3, dampingFraction: 0.7), value: active)
    }
}

// MARK: - The screen

struct MeetingExperienceView: View {
    let vm: MeetingVM

    var body: some View {
        ZStack(alignment: .bottom) {
            DS.bg.ignoresSafeArea()

            ScrollView {
                VStack(alignment: .leading, spacing: DS.lg) {
                    header
                    transcriptCard
                    VStack(alignment: .leading, spacing: DS.md) {
                        HStack {
                            SectionLabel(text: "INTELLIGENCE")
                            Spacer()
                            Chip(text: "Local", dot: DS.ok, fg: DS.ok)
                        }
                        ForEach(vm.artifacts) { SwipeableArtifactCard(vm: $0) }
                    }
                }
                .padding(.horizontal, DS.lg)
                .padding(.top, DS.md)
                .padding(.bottom, 180)   // room for the sheet
            }

            actionSheet
        }
        .preferredColorScheme(.dark)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: DS.sm) {
            HStack {
                circleButton("chevron.left")
                Spacer()
                circleButton("ellipsis")
            }
            Text(vm.title).font(.system(size: 32, weight: .heavy)).foregroundStyle(DS.text)
                .padding(.top, DS.xs)
            HStack(spacing: DS.sm) {
                Chip(text: vm.when)
                Chip(text: vm.duration, dot: nil)
                Chip(text: "4B on-device", fg: DS.muted)
            }
        }
    }

    private var transcriptCard: some View {
        HStack(spacing: DS.md) {
            ZStack {
                RoundedRectangle(cornerRadius: 13, style: .continuous).fill(DS.s3)
                Image(systemName: "waveform").font(.system(size: 20, weight: .bold)).foregroundStyle(DS.accent)
            }.frame(width: 46, height: 46)
            VStack(alignment: .leading, spacing: 3) {
                Text("Transcript").font(.system(size: 15, weight: .bold)).foregroundStyle(DS.text)
                Text("“…agreed, Friday it is — and bump the cache TTL.”")
                    .font(.system(size: 14)).foregroundStyle(DS.muted).lineLimit(1)
            }
            Spacer()
            Image(systemName: "chevron.right").font(.system(size: 14, weight: .bold)).foregroundStyle(DS.faint)
        }
        .padding(DS.md)
        .background(DS.s1.opacity(0.7), in: RoundedRectangle(cornerRadius: DS.rCard, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: DS.rCard, style: .continuous).stroke(DS.line, lineWidth: 1))
    }

    private var actionSheet: some View {
        VStack(spacing: DS.md) {
            Capsule().fill(DS.faint.opacity(0.5)).frame(width: 40, height: 5).padding(.top, 9)
            HStack(spacing: DS.sm) {
                sheetButton("sparkles", "Regenerate", primary: true)
                sheetButton("pencil.and.scribble", "Ink", primary: false)
            }
            .padding(.bottom, 8)
            // Egress is the one "Local" badge up top (POSITIONING canon: a badge, never
            // a privacy sentence). No prose here.
        }
        .padding(.horizontal, DS.lg)
        .padding(.bottom, 18)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: DS.rSheet, style: .continuous)
                .fill(DS.s2)
                .overlay(RoundedRectangle(cornerRadius: DS.rSheet, style: .continuous).stroke(DS.line, lineWidth: 1))
                .shadow(color: .black.opacity(0.5), radius: 30, x: 0, y: -8)
                .ignoresSafeArea(edges: .bottom)
        )
    }

    private func sheetButton(_ sys: String, _ label: String, primary: Bool) -> some View {
        HStack(spacing: 8) {
            Image(systemName: sys).font(.system(size: 16, weight: .bold))
            Text(label).font(.system(size: 16, weight: .heavy))
        }
        .foregroundStyle(primary ? .black : DS.text)
        .frame(maxWidth: .infinity).frame(height: 56)
        .background(primary ? DS.accent : DS.s3, in: RoundedRectangle(cornerRadius: DS.rBtn, style: .continuous))
        .overlay(primary ? nil : RoundedRectangle(cornerRadius: DS.rBtn, style: .continuous).stroke(DS.line, lineWidth: 1))
    }

    private func circleButton(_ sys: String) -> some View {
        Image(systemName: sys).font(.system(size: 16, weight: .bold)).foregroundStyle(DS.text)
            .frame(width: 42, height: 42)
            .background(DS.s2, in: Circle())
            .overlay(Circle().stroke(DS.line, lineWidth: 1))
    }
}

// MARK: - Mock data for the screenshot

enum ExperienceMock {
    static let meeting = MeetingVM(
        title: "Sprint Planning",
        when: "Today",
        duration: "22 min",
        artifacts: [
            ArtifactVM(kind: .decisions, title: "Ship Friday; bump cache TTL",
                       detail: "The team agreed to ship the release on Friday and raise the cache TTL to 24h to absorb the launch traffic.",
                       reveal: -74),   // mid-swipe: Approve peeks, card stays readable
            ArtifactVM(kind: .actions, title: "Email the vendor about pricing",
                       detail: "Karol to follow up with the vendor on the renewal pricing before the contract lapses next week."),
            ArtifactVM(kind: .risks, title: "Cache stampede on cold start",
                       detail: "If the TTL bump lands without warm-up, a cold start could stampede the origin. Mitigation owner TBD."),
        ])
}
