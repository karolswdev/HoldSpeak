#!/usr/bin/env ruby
# HSM-5-06 device harness project generator. Builds a minimal, automatically-signed
# Xcode app that runs on-device meeting intelligence (Mode C) against an
# OpenAI-compatible endpoint. Unlike the Gate-1 shell (Contracts only), this app
# needs the Contracts + Providers + RuntimeCore code. SwiftPM cannot emit a signed
# iOS .app, so — mirroring the Gate-1 single-module approach — we stage every
# package source into ONE app module, stripping the intra-package `import` lines
# (the types are all in the same module once merged).
#
# Usage: ruby apple/scripts/gen-inference-harness.rb
require 'xcodeproj'
require 'fileutils'

ROOT  = File.expand_path('..', __dir__)            # apple/
BUILD = File.join(ROOT, 'build')
STAGE = File.join(BUILD, 'harness-sources')
PROJ_PATH = File.join(BUILD, 'HoldSpeakHarness.xcodeproj')
TEAM = ENV.fetch('HS_TEAM', 'M84954HNL6')
BUNDLE_ID = 'dev.holdspeak.mobile'
DEPLOY = '17.0'

# Package layers the harness needs (Hosts is excluded — placeholder + its own enum).
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
    text = File.read(src).gsub(INTRA_IMPORT, '')   # one module → drop intra-package imports
    out = File.join(STAGE, base)
    File.write(out, text)
    staged << out
  end
end
# The harness app file (already module-free by design).
harness = File.join(ROOT, 'App/InferenceHarnessApp.swift')
FileUtils.cp(harness, File.join(STAGE, 'InferenceHarnessApp.swift'))
staged << File.join(STAGE, 'InferenceHarnessApp.swift')

FileUtils.rm_rf(PROJ_PATH)
project = Xcodeproj::Project.new(PROJ_PATH)
target = project.new_target(:application, 'HoldSpeakMobile', :ios, DEPLOY)

group = project.new_group('Sources', STAGE)
staged.each { |p| target.add_file_references([group.new_reference(p)]) }

info_plist = File.join(ROOT, 'App/Harness-Info.plist')
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
  s['SWIFT_VERSION'] = '6.0'
end

project.save
puts "generated #{PROJ_PATH}"
puts "  staged #{staged.size} sources from #{LAYER_DIRS.join(', ')} + the harness app"
puts "  info=#{info_plist} team=#{TEAM} bundle=#{BUNDLE_ID}"
