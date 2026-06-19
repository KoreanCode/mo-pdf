#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "DMG creation requires macOS."
  exit 1
fi

if ! command -v hdiutil >/dev/null 2>&1; then
  echo "hdiutil was not found. Run this on macOS."
  exit 1
fi

APP_NAME="O'range PDF Blur"
BUNDLE_ID="kr.orangefactory.pdfblur"
EXECUTABLE_NAME="OrangePdfBlur"
BUILD_ROOT=".macos-build"
APP_STAGE="$BUILD_ROOT/dmg-root"
APP_BUNDLE="$APP_STAGE/$APP_NAME.app"
CONTENTS_DIR="$APP_BUNDLE/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
APP_SOURCE_DIR="$RESOURCES_DIR/app"

if [[ -f "../README.txt" ]]; then
  OUTPUT_DIR=".."
else
  OUTPUT_DIR="dist"
fi

DMG_PATH="$OUTPUT_DIR/O-range-PDF-Blur-macOS.dmg"

rm -rf "$BUILD_ROOT"
mkdir -p "$APP_SOURCE_DIR" "$MACOS_DIR" "$OUTPUT_DIR"

cp -R app.py pdf_blur.py requirements.txt templates static launcher.py "$APP_SOURCE_DIR/"

cat > "$CONTENTS_DIR/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>$EXECUTABLE_NAME</string>
  <key>CFBundleIdentifier</key>
  <string>$BUNDLE_ID</string>
  <key>CFBundleName</key>
  <string>$APP_NAME</string>
  <key>CFBundleDisplayName</key>
  <string>$APP_NAME</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0.0</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>11.0</string>
</dict>
</plist>
PLIST

cat > "$MACOS_DIR/$EXECUTABLE_NAME" <<'LAUNCHER'
#!/bin/zsh
set -e

RESOURCE_APP_DIR="$(cd "$(dirname "$0")/../Resources/app" && pwd)"
SUPPORT_DIR="$HOME/Library/Application Support/OrangePdfBlur"

mkdir -p "$SUPPORT_DIR"
ditto "$RESOURCE_APP_DIR" "$SUPPORT_DIR"
cd "$SUPPORT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display dialog "Python 3가 필요합니다. python.org에서 Python 3를 설치한 뒤 다시 실행하세요." buttons {"OK"} with icon caution'
  exit 1
fi

exec python3 launcher.py
LAUNCHER

chmod +x "$MACOS_DIR/$EXECUTABLE_NAME"

if [[ -f "../README.txt" ]]; then
  cp "../README.txt" "$APP_STAGE/README.txt"
elif [[ -f "README.md" ]]; then
  cp "README.md" "$APP_STAGE/README.md"
fi

if [[ -f "../USER_GUIDE_KO.txt" ]]; then
  cp "../USER_GUIDE_KO.txt" "$APP_STAGE/USER_GUIDE_KO.txt"
elif [[ -f "USER_GUIDE_KO.md" ]]; then
  cp "USER_GUIDE_KO.md" "$APP_STAGE/USER_GUIDE_KO.md"
fi

hdiutil create -volname "$APP_NAME" -srcfolder "$APP_STAGE" -ov -format UDZO "$DMG_PATH"
echo "Created $DMG_PATH"
