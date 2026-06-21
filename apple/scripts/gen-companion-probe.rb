#!/usr/bin/env ruby
# HSM-12-01 (real-metal probe) Companion seam device-harness generator. Stages the
# package sources into ONE app module (SwiftPM can't emit a signed iOS .app) so the
# CompanionProbe app imports no package modules. Unlike the local/speak harnesses this
# adds NO Swift Package dependency — the Companion seam is pure networking over the
# desktop's HTTP API (Contracts + Providers + RuntimeCore only; SQLite3 is a system
# module). The result points the iPad at a HoldSpeak desktop/homelab server and proves
# the HSM-12-01 seam on real metal: pairing -> handshake against /health +
# /api/runtime/status -> reachable / runtime-ready / honest egress. Output:
# build/HoldSpeakCompanionProbe.xcodeproj
#
# Usage: ruby apple/scripts/gen-companion-probe.rb
require 'xcodeproj'
require 'fileutils'

ROOT  = File.expand_path('..', __dir__)            # apple/
BUILD = File.join(ROOT, 'build')
STAGE = File.join(BUILD, 'companion-probe-sources')
PROJ_PATH = File.join(BUILD, 'HoldSpeakCompanionProbe.xcodeproj')
TEAM = ENV.fetch('HS_TEAM', 'M84954HNL6')
BUNDLE_ID = 'dev.holdspeak.mobile'
DEPLOY = '17.0'

# The Companion seam needs only the three pure layers — no engine, no Whisper. Strip
# the intra-package imports (everything merges into one module); there is no external
# `import` to keep.
LAYER_DIRS = %w[Sources/Contracts Sources/Providers Sources/RuntimeCore]
INTRA_IMPORT = /^import\s+(Contracts|Providers|RuntimeCore)\s*$/

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
app = File.join(ROOT, 'App/CompanionProbeApp.swift')
FileUtils.cp(app, File.join(STAGE, 'CompanionProbeApp.swift'))
staged << File.join(STAGE, 'CompanionProbeApp.swift')

FileUtils.rm_rf(PROJ_PATH)
project = Xcodeproj::Project.new(PROJ_PATH)
target = project.new_target(:application, 'HoldSpeakMobile', :ios, DEPLOY)

group = project.new_group('Sources', STAGE)
staged.each { |p| target.add_file_references([group.new_reference(p)]) }

info_plist = File.join(ROOT, 'App/Companion-Info.plist')
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
puts "  staged #{staged.size} sources from #{LAYER_DIRS.join(', ')} + the companion-probe app"
puts "  no package deps (pure networking seam) team=#{TEAM} bundle=#{BUNDLE_ID}"
