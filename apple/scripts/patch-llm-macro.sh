#!/bin/bash
# Toolchain workaround (2026-06-26): the only Xcode on this machine is Xcode-beta, whose Swift 6.3
# dev-snapshot toolchain CANNOT build swift-syntax (any version: 602.0.0 or 603.0.2) — its
# `_SwiftSyntaxCShims` C target fails to resolve under both explicit and implicit module builds.
# swift-syntax is pulled in ONLY by LLM.swift's `@Generatable` macro, which our build never uses
# (we only need the `Generatable` PROTOCOL for `StructuredOutput<T: Generatable>`). So we sever the
# macro: resolve packages, then rewrite the freshly-cloned LLM.swift checkout to drop the macro +
# macro-impl targets and the swift-syntax/swift-testing/docc deps, keeping just the protocol.
#
# After this runs, build with `-disableAutomaticPackageResolution` so xcodebuild does NOT re-clone
# the unpatched package over the patch. Idempotent: re-running re-applies cleanly.
#
# Remove this once a non-broken Xcode (stable Swift toolchain) is installed, and restore the plain
# remote LLM.swift package + normal resolution.
#
# Usage: apple/scripts/patch-llm-macro.sh <derived-data-path> <xcodeproj-path> <scheme>
set -euo pipefail
DD="$1"; PROJ="$2"; SCHEME="$3"

echo "== resolve packages (clones LLM.swift fresh) =="
xcodebuild -project "$PROJ" -scheme "$SCHEME" -derivedDataPath "$DD" \
  -skipMacroValidation -resolvePackageDependencies >/dev/null

CK="$DD/SourcePackages/checkouts/LLM.swift"
[ -d "$CK" ] || { echo "!! LLM.swift checkout not found at $CK" >&2; exit 1; }
chmod -R u+w "$CK"

echo "== sever @Generatable macro in $CK =="
# Keep ONLY the protocol the LLM library actually references.
cat > "$CK/Sources/LLMMacros/Generatable.swift" <<'SWIFT'
// PATCHED (apple/scripts/patch-llm-macro.sh): the @Generatable macro pulls in swift-syntax, which
// the Xcode-beta Swift 6.3 dev-snapshot toolchain cannot build (_SwiftSyntaxCShims unresolved).
// Our build never uses the macro, only this protocol (StructuredOutput<T: Generatable>), so the
// macro + swift-syntax are severed. Restore the upstream package once a working Xcode is installed.
public protocol Generatable: Codable {
    static var jsonSchema: String { get }
}
SWIFT
# Drop any other macro-declaring file in the target (the upstream protocol+macro file may vary).
find "$CK/Sources/LLMMacros" -name '*.swift' ! -name 'Generatable.swift' -delete 2>/dev/null || true

# Rewrite the manifest: remove the .macro / macro-impl / test targets and the swift-syntax,
# swift-testing and docc dependencies. LLMMacros becomes a plain target (protocol only).
cat > "$CK/Package.swift" <<'SWIFT'
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "LLM",
    platforms: [
        .iOS(.v16), .macOS(.v13), .watchOS(.v9), .tvOS(.v16), .visionOS(.v1)
    ],
    products: [
        .library(name: "LLM", targets: ["LLM"])
    ],
    targets: [
        .binaryTarget(name: "llama", path: "llama.cpp/llama.xcframework"),
        .target(name: "LLMMacros", path: "Sources/LLMMacros"),
        .target(name: "LLM", dependencies: ["llama", "LLMMacros"], path: "Sources/LLM")
    ]
)
SWIFT
echo "== LLM.swift macro severed (build with -disableAutomaticPackageResolution) =="
