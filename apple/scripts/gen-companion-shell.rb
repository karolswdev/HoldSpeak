#!/usr/bin/env ruby
# HSM-12-03 — the unified Companion shell. Stages Contracts + Providers + RuntimeCore
# into ONE app module (like the companion probe) — pure networking + SwiftUI, no engine
# packages (the shell presents nav + meetings + the board/local summaries; the deep
# voice content is the answer app). Output: build/HoldSpeakCompanionShell.xcodeproj
#
# SDKROOT is intentionally NOT pinned so the same project builds for device AND the
# iOS Simulator (screenshot-verification) via the xcodebuild -destination.
#
# Usage: ruby apple/scripts/gen-companion-shell.rb
require 'xcodeproj'
require 'fileutils'

ROOT  = File.expand_path('..', __dir__)            # apple/
BUILD = File.join(ROOT, 'build')
STAGE = File.join(BUILD, 'companion-shell-sources')
PROJ_PATH = File.join(BUILD, 'HoldSpeakCompanionShell.xcodeproj')
TEAM = ENV.fetch('HS_TEAM', 'M84954HNL6')
BUNDLE_ID = 'dev.holdspeak.mobile'
DEPLOY = '17.0'

LAYER_DIRS = %w[Sources/Contracts Sources/Providers Sources/RuntimeCore]
INTRA_IMPORT = /^import\s+(Contracts|Providers|RuntimeCore)\s*$/

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
app = File.join(ROOT, 'App/CompanionShellApp.swift')
FileUtils.cp(app, File.join(STAGE, 'CompanionShellApp.swift'))
staged << File.join(STAGE, 'CompanionShellApp.swift')

FileUtils.rm_rf(PROJ_PATH)
project = Xcodeproj::Project.new(PROJ_PATH)
target = project.new_target(:application, 'HoldSpeakMobile', :ios, DEPLOY)
group = project.new_group('Sources', STAGE)
staged.each { |p| target.add_file_references([group.new_reference(p)]) }

info_plist = File.join(ROOT, 'App/Shell-Info.plist')
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
  # No SDKROOT / CODE_SIGN_IDENTITY pin → device build signs, simulator build runs unsigned.
end

project.save
puts "generated #{PROJ_PATH}"
puts "  staged #{staged.size} sources from #{LAYER_DIRS.join(', ')} + the companion-shell app"
puts "  no package deps (nav shell) team=#{TEAM} bundle=#{BUNDLE_ID}"
