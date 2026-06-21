#!/usr/bin/env ruby
# HSM-5-02 fully-local (Mode A) device harness generator. Like gen-inference-harness,
# it stages the package sources into ONE app module (SwiftPM can't emit a signed iOS
# .app) — but it ALSO stages Sources/InferenceLlama (the llama.cpp adapter) and adds a
# Swift Package dependency on LLM.swift so `import LLM` resolves and the native engine
# links. The result runs a GGUF entirely on the device (no network). Output:
# build/HoldSpeakLocalHarness.xcodeproj
#
# Usage: ruby apple/scripts/gen-local-harness.rb
require 'xcodeproj'
require 'fileutils'

ROOT  = File.expand_path('..', __dir__)            # apple/
BUILD = File.join(ROOT, 'build')
STAGE = File.join(BUILD, 'local-harness-sources')
PROJ_PATH = File.join(BUILD, 'HoldSpeakLocalHarness.xcodeproj')
TEAM = ENV.fetch('HS_TEAM', 'M84954HNL6')
BUNDLE_ID = 'dev.holdspeak.mobile'
DEPLOY = '17.0'

# Mode A needs the engine adapter too. KEEP `import LLM` (the external package);
# strip only the intra-package imports (everything merges into one module).
LAYER_DIRS = %w[Sources/Contracts Sources/Providers Sources/RuntimeCore Sources/InferenceLlama]
INTRA_IMPORT = /^import\s+(Contracts|Providers|RuntimeCore|InferenceLlama)\s*$/

FileUtils.rm_rf(STAGE)
FileUtils.mkdir_p(STAGE)

staged = []
seen = {}
LAYER_DIRS.each do |dir|
  Dir[File.join(ROOT, dir, '**', '*.swift')].sort.each do |src|
    base = File.basename(src)
    raise "name collision staging #{base} (#{src} vs #{seen[base]})" if seen[base]
    seen[base] = src
    text = File.read(src).gsub(INTRA_IMPORT, '')
    out = File.join(STAGE, base)
    File.write(out, text)
    staged << out
  end
end
app = File.join(ROOT, 'App/LocalHarnessApp.swift')
FileUtils.cp(app, File.join(STAGE, 'LocalHarnessApp.swift'))
staged << File.join(STAGE, 'LocalHarnessApp.swift')

FileUtils.rm_rf(PROJ_PATH)
project = Xcodeproj::Project.new(PROJ_PATH)
target = project.new_target(:application, 'HoldSpeakMobile', :ios, DEPLOY)

group = project.new_group('Sources', STAGE)
staged.each { |p| target.add_file_references([group.new_reference(p)]) }

# --- Swift Package dependency: LLM.swift (the llama.cpp engine) ---
pkg = project.new(Xcodeproj::Project::Object::XCRemoteSwiftPackageReference)
pkg.repositoryURL = 'https://github.com/eastriverlee/LLM.swift'
pkg.requirement = { 'kind' => 'upToNextMajorVersion', 'minimumVersion' => '2.1.0' }
project.root_object.package_references << pkg

dep = project.new(Xcodeproj::Project::Object::XCSwiftPackageProductDependency)
dep.package = pkg
dep.product_name = 'LLM'
target.package_product_dependencies << dep

build_file = project.new(Xcodeproj::Project::Object::PBXBuildFile)
build_file.product_ref = dep
target.frameworks_build_phase.files << build_file

info_plist = File.join(ROOT, 'App/Local-Info.plist')
target.build_configurations.each do |config|
  s = config.build_settings
  s['PRODUCT_BUNDLE_IDENTIFIER'] = BUNDLE_ID
  s['PRODUCT_NAME'] = 'HoldSpeakMobile'
  s['MARKETING_VERSION'] = '0.1.0'
  s['CURRENT_PROJECT_VERSION'] = '1'
  s['GENERATE_INFOPLIST_FILE'] = 'NO'
  s['INFOPLIST_FILE'] = info_plist
  s['TARGETED_DEVICE_FAMILY'] = '1,2'
  s['IPHONEOS_DEPLOYMENT_TARGET'] = DEPLOY
  s['SWIFT_VERSION'] = '6.0'
  s['CODE_SIGN_STYLE'] = 'Automatic'
  s['DEVELOPMENT_TEAM'] = TEAM
  s['CODE_SIGN_IDENTITY'] = 'Apple Development'
  s['SDKROOT'] = 'iphoneos'
  # NOTE: com.apple.developer.kernel.increased-memory-limit (App/Local.entitlements)
  # would raise the per-app RAM ceiling, but automatic dev signing can't add it —
  # the App ID needs the "Increased Memory Limit" capability enabled in the developer
  # portal first. Until then we run within the default ceiling, so keep the model at
  # ~4B Q4 on an 8GB iPad. Re-enable CODE_SIGN_ENTITLEMENTS once the capability is on.
end

project.save
puts "generated #{PROJ_PATH}"
puts "  staged #{staged.size} sources from #{LAYER_DIRS.join(', ')} + the local-harness app"
puts "  package=LLM.swift>=2.1.0 (product LLM) team=#{TEAM} bundle=#{BUNDLE_ID}"
