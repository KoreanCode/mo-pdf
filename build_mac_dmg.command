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

if ! command -v iconutil >/dev/null 2>&1; then
  echo "iconutil was not found. Run this on macOS."
  exit 1
fi

if ! command -v sips >/dev/null 2>&1; then
  echo "sips was not found. Run this on macOS."
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
ICON_SOURCE="static/simbol_2.png"
ICONSET_DIR="$BUILD_ROOT/AppIcon.iconset"
ICON_FILE="AppIcon.icns"

if [[ -f "../README.txt" ]]; then
  OUTPUT_DIR=".."
else
  OUTPUT_DIR="dist"
fi

DMG_PATH="$OUTPUT_DIR/O-range-PDF-Blur-macOS.dmg"

rm -rf "$BUILD_ROOT"
mkdir -p "$APP_SOURCE_DIR" "$MACOS_DIR" "$OUTPUT_DIR"

cp -R app.py pdf_blur.py requirements.txt templates static launcher.py "$APP_SOURCE_DIR/"

if [[ -f "$ICON_SOURCE" ]]; then
  mkdir -p "$ICONSET_DIR"
  sips -s format png -z 16 16 "$ICON_SOURCE" --out "$ICONSET_DIR/icon_16x16.png" >/dev/null
  sips -s format png -z 32 32 "$ICON_SOURCE" --out "$ICONSET_DIR/icon_16x16@2x.png" >/dev/null
  sips -s format png -z 32 32 "$ICON_SOURCE" --out "$ICONSET_DIR/icon_32x32.png" >/dev/null
  sips -s format png -z 64 64 "$ICON_SOURCE" --out "$ICONSET_DIR/icon_32x32@2x.png" >/dev/null
  sips -s format png -z 128 128 "$ICON_SOURCE" --out "$ICONSET_DIR/icon_128x128.png" >/dev/null
  sips -s format png -z 256 256 "$ICON_SOURCE" --out "$ICONSET_DIR/icon_128x128@2x.png" >/dev/null
  sips -s format png -z 256 256 "$ICON_SOURCE" --out "$ICONSET_DIR/icon_256x256.png" >/dev/null
  sips -s format png -z 512 512 "$ICON_SOURCE" --out "$ICONSET_DIR/icon_256x256@2x.png" >/dev/null
  sips -s format png -z 512 512 "$ICON_SOURCE" --out "$ICONSET_DIR/icon_512x512.png" >/dev/null
  sips -s format png -z 1024 1024 "$ICON_SOURCE" --out "$ICONSET_DIR/icon_512x512@2x.png" >/dev/null
  iconutil -c icns "$ICONSET_DIR" -o "$RESOURCES_DIR/$ICON_FILE"
else
  echo "Icon source was not found: $ICON_SOURCE"
  exit 1
fi

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
  <key>CFBundleIconFile</key>
  <string>AppIcon</string>
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

export SYSTEM_VERSION_COMPAT=0
export PATH="/Library/Frameworks/Python.framework/Versions/Current/bin:/Library/Frameworks/Python.framework/Versions/3.13/bin:/Library/Frameworks/Python.framework/Versions/3.12/bin:/Library/Frameworks/Python.framework/Versions/3.11/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

RESOURCE_APP_DIR="$(cd "$(dirname "$0")/../Resources/app" && pwd)"
SUPPORT_DIR="$HOME/Library/Application Support/OrangePdfBlur"

mkdir -p "$SUPPORT_DIR"
ditto "$RESOURCE_APP_DIR" "$SUPPORT_DIR"
cd "$SUPPORT_DIR"

find_python() {
  local candidate
  for candidate in \
    "/Library/Frameworks/Python.framework/Versions/Current/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3" \
    "/opt/homebrew/bin/python3" \
    "/usr/local/bin/python3"
  do
    if [[ -x "$candidate" ]] && check_python "$candidate"; then
      echo "$candidate"
      return 0
    fi
  done

  candidate="$(command -v python3 || true)"
  if [[ -n "$candidate" && "$candidate" != "/usr/bin/python3" ]] && check_python "$candidate"; then
    echo "$candidate"
    return 0
  fi

  return 1
}

is_arm64_mac() {
  [[ "$(sysctl -n hw.optional.arm64 2>/dev/null || echo 0)" == "1" ]]
}

check_python() {
  if is_arm64_mac; then
    /usr/bin/arch -arm64 "$1" -c 'import tkinter' >/dev/null 2>&1
  else
    "$1" -c 'import tkinter' >/dev/null 2>&1
  fi
}

run_python() {
  if is_arm64_mac; then
    exec /usr/bin/arch -arm64 "$@"
  fi
  exec "$@"
}

PYTHON_BIN="$(find_python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  osascript -e 'display dialog "Python 3가 필요합니다. python.org 또는 Homebrew로 Python 3를 설치한 뒤 다시 실행하세요." buttons {"OK"} with icon caution'
  exit 1
fi

run_python "$PYTHON_BIN" launcher.py
LAUNCHER

chmod +x "$MACOS_DIR/$EXECUTABLE_NAME"

cat > "$APP_STAGE/README.txt" <<'README'
O'range PDF Blur 사용법

1. O'range PDF Blur.app을 실행합니다.
2. 런처에서 [서버 실행]을 누릅니다.
3. [접속하기]를 눌러 브라우저를 엽니다.
4. 다 사용하면 [서버 종료]를 누릅니다.

서버는 내 Mac에서만 실행됩니다.
README

hdiutil create -volname "$APP_NAME" -srcfolder "$APP_STAGE" -ov -format UDZO "$DMG_PATH"
echo "Created $DMG_PATH"
