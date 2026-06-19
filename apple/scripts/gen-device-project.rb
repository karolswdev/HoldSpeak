#!/usr/bin/env ruby
# HSM Gate 1 (real metal): generate a minimal, automatically-signed Xcode project
# for the Phase-1 runtime shell so it can be installed on a *physical* iPad/iPhone
# (the simulator path in gate1-launch.sh cannot reach a real device). The project
# compiles the same App/ shell + the real Contracts layer — a successful on-device
# launch exercises the contract layer on Apple hardware. Output: build/HoldSpeakMobile.xcodeproj
#
# Usage: ruby apple/scripts/gen-device-project.rb
require 'xcodeproj'
require 'fileutils'

ROOT = File.expand_path('..', __dir__)          # apple/
BUILD = File.join(ROOT, 'build')
PROJ_PATH = File.join(BUILD, 'HoldSpeakMobile.xcodeproj')
TEAM = ENV.fetch('HS_TEAM', 'M84954HNL6')   # account signed into Xcode; override with HS_TEAM
BUNDLE_ID = 'dev.holdspeak.mobile'
DEPLOY = '17.0'

FileUtils.mkdir_p(BUILD)
FileUtils.rm_rf(PROJ_PATH)

project = Xcodeproj::Project.new(PROJ_PATH)
target = project.new_target(:application, 'HoldSpeakMobile', :ios, DEPLOY)

# Source files: the App shell + the real Contracts layer (Foundation-only).
sources = Dir[File.join(ROOT, 'Sources/Contracts/*.swift')].sort +
          [File.join(ROOT, 'App/HoldSpeakApp.swift')]
group = project.new_group('Sources', ROOT)
sources.each do |path|
  ref = group.new_reference(path)
  target.add_file_references([ref])
end

# Signing + identity. Automatic provisioning so xcodebuild registers the device
# and mints a development profile for this bundle id on the personal team.
target.build_configurations.each do |config|
  s = config.build_settings
  s['PRODUCT_BUNDLE_IDENTIFIER'] = BUNDLE_ID
  s['PRODUCT_NAME'] = 'HoldSpeakMobile'
  s['INFOPLIST_KEY_CFBundleDisplayName'] = 'HoldSpeak'
  s['MARKETING_VERSION'] = '0.1.0'
  s['CURRENT_PROJECT_VERSION'] = '1'
  s['GENERATE_INFOPLIST_FILE'] = 'YES'
  s['INFOPLIST_KEY_UILaunchScreen_Generation'] = 'YES'
  s['TARGETED_DEVICE_FAMILY'] = '1,2'           # iPhone + iPad
  s['IPHONEOS_DEPLOYMENT_TARGET'] = DEPLOY
  s['SWIFT_VERSION'] = '6.0'
  s['CODE_SIGN_STYLE'] = 'Automatic'
  s['DEVELOPMENT_TEAM'] = TEAM
  s['CODE_SIGN_IDENTITY'] = 'Apple Development'
  s['SDKROOT'] = 'iphoneos'
end

project.save
puts "generated #{PROJ_PATH}"
puts "  sources: #{sources.map { |p| p.sub(ROOT + '/', '') }.join(', ')}"
puts "  team=#{TEAM} bundle=#{BUNDLE_ID} deploy=iOS #{DEPLOY}"
