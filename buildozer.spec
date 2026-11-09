[app]
title = RuView
package.name = ruview
package.domain = org.ruvnet.ruview
source.dir = .
source.include_exts = py,png,jpg,kv,json
version = 1.0

# Dependencies
requirements = python3,kivy,openssl,requests,certifi

orientation = portrait
fullscreen = 0

# Android Permissions for WiFi sensing & Network streaming
android.permissions = INTERNET,ACCESS_WIFI_STATE,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 21
android.archs = arm64-v8a

android.accept_sdk_license = True
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
