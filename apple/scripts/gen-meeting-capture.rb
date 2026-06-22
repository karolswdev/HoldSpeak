#!/usr/bin/env ruby
# HSM-8-01 — the iPad on-device meeting-capture app. Stages Contracts + Providers +
# RuntimeCore into ONE app module and adds the WhisperKit package (on-device
# transcription). No LLM, no networking — capture + Whisper + SQLite all run on the
# device. Output: build/HoldSpeakMeetingCapture.xcodeproj
#
# Usage: ruby apple/scripts/gen-meeting-capture.rb
require 'xcodeproj'
require 'fileutils'

ROOT  = File.expand_path('..', __dir__)            # apple/
BUILD = File.join(ROOT, 'build')
STAGE = File.join(BUILD, 'meeting-capture-sources')
PROJ_PATH = File.join(BUILD, 'HoldSpeakMeetingCapture.xcodeproj')
TEAM = ENV.fetch('HS_TEAM', 'M84954HNL6')
BUNDLE_ID = 'dev.holdspeak.mobile'
DEPLOY = '17.0'

# Includes InferenceLlama (the llama.cpp adapter) so the meeting can generate Phase-6
# artifacts ON-DEVICE (Mode A) from its transcript for the HSM-8-04 review. `import LLM`
# (the external package) is kept; only intra-package imports are stripped.
LAYER_DIRS = %w[Sources/Contracts Sources/Providers Sources/RuntimeCore Sources/InferenceLlama]
INTRA_IMPORT = /^import\s+(Contracts|Providers|RuntimeCore|InferenceLlama)\s*$/

FileUtils.rm_rf(STAGE); FileUtils.mkdir_p(STAGE)
staged = []; seen = {}
LAYER_DIRS.each do |dir|
  Dir[File.join(ROOT, dir, '**', '*.swift')].sort.each do |src|
    base = File.basename(src)
    raise "name collision staging #{base} (#{src} vs #{seen[base]})" if seen[base]
    seen[base] = src
    File.write(File.join(STAGE, base), File.read(src).gsub(INTRA_IMPORT, ''))
    staged << File.join(STAGE, base)
  end
end
app = File.join(ROOT, 'App/MeetingCaptureApp.swift')
FileUtils.cp(app, File.join(STAGE, 'MeetingCaptureApp.swift'))
staged << File.join(STAGE, 'MeetingCaptureApp.swift')

FileUtils.rm_rf(PROJ_PATH)
project = Xcodeproj::Project.new(PROJ_PATH)
target = project.new_target(:application, 'HoldSpeakMobile', :ios, DEPLOY)
group = project.new_group('Sources', STAGE)
staged.each { |p| target.add_file_references([group.new_reference(p)]) }

# Bundle mermaid.js so the sketch surface renders real Mermaid in a WKWebView (offline).
mermaid_js = File.join(ROOT, 'App/mermaid.min.js')
if File.exist?(mermaid_js)
  res_group = project.new_group('Resources', File.join(ROOT, 'App'))
  target.add_resources([res_group.new_reference(mermaid_js)])
end

# --- Swift Package dependencies: WhisperKit (transcription) + LLM.swift (on-device LLM) ---
def add_pkg(project, target, url, requirement, product)
  pkg = project.new(Xcodeproj::Project::Object::XCRemoteSwiftPackageReference)
  pkg.repositoryURL = url
  pkg.requirement = requirement
  project.root_object.package_references << pkg
  dep = project.new(Xcodeproj::Project::Object::XCSwiftPackageProductDependency)
  dep.package = pkg
  dep.product_name = product
  target.package_product_dependencies << dep
  bf = project.new(Xcodeproj::Project::Object::PBXBuildFile)
  bf.product_ref = dep
  target.frameworks_build_phase.files << bf
end
add_pkg(project, target, 'https://github.com/argmaxinc/WhisperKit',
        { 'kind' => 'exactVersion', 'version' => '0.11.0' }, 'WhisperKit')
add_pkg(project, target, 'https://github.com/eastriverlee/LLM.swift',
        { 'kind' => 'upToNextMajorVersion', 'minimumVersion' => '2.1.0' }, 'LLM')
add_pkg(project, target, 'https://github.com/gonzalezreal/swift-markdown-ui',
        { 'kind' => 'upToNextMajorVersion', 'minimumVersion' => '2.0.0' }, 'MarkdownUI')

info_plist = File.join(ROOT, 'App/Capture-Info.plist')
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
end

project.save
puts "generated #{PROJ_PATH}"
puts "  staged #{staged.size} sources + the meeting-capture app"
puts "  package: WhisperKit==0.11.0 (on-device) team=#{TEAM} bundle=#{BUNDLE_ID}"
