#!/bin/sh
# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
mkdir -p dist/dmg
# Empty the dmg folder.
rm -r dist/dmg/*
# Copy the app bundle to the dmg folder.
cp -r "dist/qustomhys.app" dist/dmg
# If the DMG already exists, delete it.
test -f "dist/qustomhys.dmg" && rm "dist/qustomhys.dmg"
create-dmg \
  --volname "qustomhys-qt" \
  --volicon "data/chm_logo.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "qustomhys-qt.app" 175 120 \
  --hide-extension "qustomhys-qt.app" \
  --app-drop-link 425 120 \
  "dist/qustomhys-qt.dmg" \
  "dist/dmg/"