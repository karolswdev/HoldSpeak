#!/usr/bin/env ruby
# HSM-3 + HSM-5 "Speak to it" harness generator. Stages the package sources into one
# app module (like gen-local-harness) and adds TWO Swift Package dependencies:
# LLM.swift (the on-device LLM, Mode A) AND WhisperKit (on-device transcription). The
# result records audio, transcribes it on-device, and runs the local model — the
# air-gapped notetaker on the user's own voice. Output:
# build/HoldSpeakSpeakHarness.xcodeproj
#
# Usage: ruby apple/scripts/gen-speak-harness.rb
require 'xcodeproj'
require 'fileutils'

ROOT  = File.expand_path('..', __dir__)
BUILD = File.join(ROOT, 'build')
STAGE = File.join(BUILD, 'speak-harness-sources')
PROJ_PATH = File.join(BUILD, 'HoldSpeakSpeakHarness.xcodeproj')
TEAM = ENV.fetch('HS_TEAM', 'M84954HNL6')
BUNDLE_ID = 'dev.holdspeak.mobile'
DEPLOY = '17.0'

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
app = File.join(ROOT, 'App/SpeakHarnessApp.swift')
FileUtils.cp(app, File.join(STAGE, 'SpeakHarnessApp.swift'))
staged << File.join(STAGE, 'SpeakHarnessApp.swift')

FileUtils.rm_rf(PROJ_PATH)
project = Xcodeproj::Project.new(PROJ_PATH)
target = project.new_target(:application, 'HoldSpeakMobile', :ios, DEPLOY)
group = project.new_group('Sources', STAGE)
staged.each { |p| target.add_file_references([group.new_reference(p)]) }

# --- Swift Package dependencies: LLM.swift (LLM) + WhisperKit (WhisperKit) ---
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

add_pkg(project, target, 'https://github.com/eastriverlee/LLM.swift',
        { 'kind' => 'upToNextMajorVersion', 'minimumVersion' => '2.1.0' }, 'LLM')
add_pkg(project, target, 'https://github.com/argmaxinc/WhisperKit',
        { 'kind' => 'exactVersion', 'version' => '0.11.0' }, 'WhisperKit')

info_plist = File.join(ROOT, 'App/Speak-Info.plist')
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
puts "  staged #{staged.size} sources + the speak-harness app"
puts "  packages: LLM.swift>=2.1.0 (LLM) + WhisperKit==0.11.0 (WhisperKit)"
