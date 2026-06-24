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
# HSM-14-19 "The Desk" decomposition: the app's own modules live in App/MeetingCapture/ (only THIS
# build stages them, so they never collide with the other harness @main files in App/).
Dir[File.join(ROOT, 'App/MeetingCapture', '**', '*.swift')].sort.each do |src|
  base = File.basename(src)
  raise "name collision staging #{base} (#{src} vs #{seen[base]})" if seen[base]
  seen[base] = src
  dst = File.join(STAGE, base)
  FileUtils.cp(src, dst)
  staged << dst
end

FileUtils.rm_rf(PROJ_PATH)
project = Xcodeproj::Project.new(PROJ_PATH)
target = project.new_target(:application, 'HoldSpeakMobile', :ios, DEPLOY)
group = project.new_group('Sources', STAGE)
staged.each { |p| target.add_file_references([group.new_reference(p)]) }

# Bundle offline resources: mermaid.js (real Mermaid rendering) + the HSM-14 pixel-art assets
# (Qlippy mascot, brass pushpin, waveform orb, the generation-theater plasma core) used across the
# craft surfaces. All optional — the UI falls back to SF Symbols if a file is missing — but
# bundling them lights up the craft.
res_group = project.new_group('Resources', File.join(ROOT, 'App'))
%w[mermaid.min.js qlippy.png pushpin.png waveorb.png theaterorb.png crystal.png cassette.png cassette2.png cartridge.png mic.png folder.png note.png robot.png].each do |name|
  path = File.join(ROOT, 'App', name)
  target.add_resources([res_group.new_reference(path)]) if File.exist?(path)
end

# HSM-14-17 — the on-device speaker-diarization Core ML model (audio→256-dim embedding). Added as a
# resource so Xcode compiles AudioEmbed.mlpackage → AudioEmbed.mlmodelc into the app bundle, where
# `AudioEmbedder` loads it from Bundle.main. The owner-proven 0.99993-vs-resemblyzer model.
ml_group = project.new_group('ML', File.join(ROOT, 'ml'))
audio_embed = File.join(ROOT, 'ml', 'AudioEmbed.mlpackage')
raise "AudioEmbed.mlpackage missing at #{audio_embed} (HSM-14-17 diarization model)" unless File.exist?(audio_embed)
target.add_resources([ml_group.new_reference(audio_embed)])

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
# HSM-15-10: the "Your Computer" Connect surface uses NWBrowser to discover the desktop
# (`_holdspeak._tcp`). NWBrowser silently no-ops on device without NSBonjourServices +
# NSLocalNetworkUsageDescription declared. Assert they survive `gen` (the plist is the
# source of truth, referenced verbatim) so a regenerated project never loses discovery.
plist_text = File.read(info_plist)
%w[NSBonjourServices NSLocalNetworkUsageDescription _holdspeak._tcp].each do |needle|
  raise "Capture-Info.plist missing #{needle} (NWBrowser discovery needs it) — see HSM-15-10" unless plist_text.include?(needle)
end
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
