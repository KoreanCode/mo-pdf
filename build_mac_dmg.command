#!/bin/zsh
set -euo pipefail

cd "$(dirname "$0")"
PROJECT_ROOT="$(pwd)"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "DMG creation requires macOS."
  exit 1
fi

for required_command in hdiutil iconutil sips; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    echo "$required_command was not found. Run this on macOS."
    exit 1
  fi
done

APP_NAME="O'range PDF Blur"
BUNDLE_ID="kr.orangefactory.pdfblur"
PYINSTALLER_NAME="OrangePdfBlur"
BUILD_ROOT=".macos-build"
APP_STAGE="$BUILD_ROOT/dmg-root"
BUILD_VENV="$BUILD_ROOT/build-venv"
PYINSTALLER_DIST="$BUILD_ROOT/pyinstaller-dist"
PYINSTALLER_WORK="$BUILD_ROOT/pyinstaller-work"
ICON_SOURCE="static/simbol_2.png"
ICONSET_DIR="$PROJECT_ROOT/$BUILD_ROOT/AppIcon.iconset"
ICON_FILE="$PROJECT_ROOT/$BUILD_ROOT/AppIcon.icns"

if [[ -f "../README.txt" ]]; then
  OUTPUT_DIR=".."
else
  OUTPUT_DIR="dist"
fi

DMG_PATH="$OUTPUT_DIR/O-range-PDF-Blur-macOS.dmg"

check_build_python() {
  "$1" -c 'import sys, tkinter, venv; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1
}

find_build_python() {
  local candidate
  for candidate in \
    "/Library/Frameworks/Python.framework/Versions/Current/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3" \
    "/opt/homebrew/bin/python3" \
    "/usr/local/bin/python3"
  do
    if [[ -x "$candidate" ]] && check_build_python "$candidate"; then
      echo "$candidate"
      return 0
    fi
  done

  candidate="$(command -v python3 || true)"
  if [[ -n "$candidate" && "$candidate" != "/usr/bin/python3" ]] && check_build_python "$candidate"; then
    echo "$candidate"
    return 0
  fi

  return 1
}

BUILD_PYTHON_SOURCE="$(find_build_python || true)"
if [[ -z "$BUILD_PYTHON_SOURCE" ]]; then
  echo "Build requires Python 3.10+ with tkinter and venv."
  echo "Install Python from python.org or Homebrew, then run this again."
  exit 1
fi

rm -rf "$BUILD_ROOT"
mkdir -p "$APP_STAGE" "$OUTPUT_DIR"

if [[ ! -f "$ICON_SOURCE" ]]; then
  echo "Icon source was not found: $ICON_SOURCE"
  exit 1
fi

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
iconutil -c icns "$ICONSET_DIR" -o "$ICON_FILE"

"$BUILD_PYTHON_SOURCE" -m venv "$BUILD_VENV"
BUILD_PYTHON="$BUILD_VENV/bin/python"
"$BUILD_PYTHON" -m pip install --upgrade pip
"$BUILD_PYTHON" -m pip install -r requirements.txt pyinstaller

"$BUILD_PYTHON" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "$PYINSTALLER_NAME" \
  --osx-bundle-identifier "$BUNDLE_ID" \
  --icon "$ICON_FILE" \
  --distpath "$PYINSTALLER_DIST" \
  --workpath "$PYINSTALLER_WORK" \
  --specpath "$BUILD_ROOT" \
  --add-data "$PROJECT_ROOT/templates:templates" \
  --add-data "$PROJECT_ROOT/static:static" \
  --hidden-import "fitz" \
  --hidden-import "PIL._tkinter_finder" \
  --collect-all "fitz" \
  "$PROJECT_ROOT/launcher.py"

APP_BUNDLE="$APP_STAGE/$APP_NAME.app"
cp -R "$PYINSTALLER_DIST/$PYINSTALLER_NAME.app" "$APP_BUNDLE"

/usr/bin/plutil -replace CFBundleName -string "$APP_NAME" "$APP_BUNDLE/Contents/Info.plist"
/usr/bin/plutil -replace CFBundleDisplayName -string "$APP_NAME" "$APP_BUNDLE/Contents/Info.plist"
/usr/bin/plutil -replace CFBundleShortVersionString -string "1.0.0" "$APP_BUNDLE/Contents/Info.plist"
/usr/bin/plutil -replace CFBundleVersion -string "1" "$APP_BUNDLE/Contents/Info.plist"

cat > "$APP_STAGE/README.txt" <<'README'
O'range PDF Blur 사용법

1. O'range PDF Blur.app을 실행합니다.
2. 런처에서 [서버 실행]을 누릅니다.
3. [접속하기]를 눌러 브라우저를 엽니다.
4. 다 사용하면 [서버 종료]를 누릅니다.

서버는 내 Mac에서만 실행됩니다.
README

if [[ -n "${APPLE_SIGNING_IDENTITY:-}" ]]; then
  codesign --force --deep --options runtime --timestamp --sign "$APPLE_SIGNING_IDENTITY" "$APP_BUNDLE"
fi

hdiutil create -volname "$APP_NAME" -srcfolder "$APP_STAGE" -ov -format UDZO "$DMG_PATH"

if [[ -n "${APPLE_SIGNING_IDENTITY:-}" ]]; then
  codesign --force --timestamp --sign "$APPLE_SIGNING_IDENTITY" "$DMG_PATH"
fi

if [[ -n "${APPLE_API_KEY:-}" && -n "${APPLE_API_ISSUER:-}" && -n "${APPLE_API_KEY_PATH:-}" ]]; then
  xcrun notarytool submit "$DMG_PATH" \
    --key "$APPLE_API_KEY_PATH" \
    --key-id "$APPLE_API_KEY" \
    --issuer "$APPLE_API_ISSUER" \
    --wait
  xcrun stapler staple "$DMG_PATH"
fi

echo "Created $DMG_PATH"
