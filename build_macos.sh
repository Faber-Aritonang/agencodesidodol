#!/bin/bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
#  Dodol Agent — macOS Builder
#  Membuat .app bundle pakai PyInstaller
#
#  Cara pakai (di macOS):
#    chmod +x build_macos.sh
#    ./build_macos.sh
# ═══════════════════════════════════════════════════════════════

APP_NAME="dodol-agent"
DISPLAY_NAME="Dodol Agent"
VERSION="1.0.0"

echo "🍬 Dodol Agent — macOS Builder"
echo "═══════════════════════════════"

# ─── 1. Cek Python ───
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 tidak ditemukan. Install via: brew install python"
    exit 1
fi

# ─── 2. Install PyInstaller ───
echo "📥 Checking PyInstaller..."
python3 -m pip install --quiet pyinstaller 2>/dev/null || true

# ─── 3. Bersihkan build sebelumnya ───
echo "🧹 Cleaning..."
rm -rf build dist

# ─── 4. Build .app bundle ───
echo "🔨 Building .app bundle..."
python3 -m PyInstaller \
    --name "${APP_NAME}" \
    --windowed \
    --onefile \
    --clean \
    --hidden-import dotenv \
    --hidden-import groq \
    --hidden-import anthropic \
    --hidden-import openai \
    --hidden-import requests \
    --collect-all core \
    --collect-all agents \
    chat.py

# ─── 5. Rename .app ───
APP_BUNDLE="dist/${DISPLAY_NAME}.app"
if [ -d "dist/${APP_NAME}.app" ]; then
    mv "dist/${APP_NAME}.app" "${APP_BUNDLE}"
fi

# ─── 6. Update Info.plist ───
PLIST="${APP_BUNDLE}/Contents/Info.plist"
if [ -f "${PLIST}" ]; then
    # Update CFBundleName
    /usr/libexec/PlistBuddy -c "Set :CFBundleName '${DISPLAY_NAME}'" "${PLIST}" 2>/dev/null || true
    /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString '${VERSION}'" "${PLIST}" 2>/dev/null || true
fi

# ─── 7. Copy .env.example ───
mkdir -p "${APP_BUNDLE}/Contents/Resources"
cp .env.example "${APP_BUNDLE}/Contents/Resources/" 2>/dev/null || true

# ─── 8. Hasil ───
if [ -d "${APP_BUNDLE}" ]; then
    SIZE=$(du -sh "${APP_BUNDLE}" | cut -f1)
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "✅ Berhasil: ${APP_BUNDLE}"
    echo "📊 Ukuran: ${SIZE}"
    echo ""
    echo "🚀 Cara pakai:"
    echo "   open '${APP_BUNDLE}'"
    echo ""
    echo "📋 Install ke Applications:"
    echo "   cp -r '${APP_BUNDLE}' /Applications/"
    echo ""
    echo "📋 Setup .env:"
    echo "   mkdir -p ~/.dodol-agent"
    echo "   cp .env.example ~/.dodol-agent/.env"
    echo "   # lalu isi API key di ~/.dodol-agent/.env"
    echo "═══════════════════════════════════════════════════════════════"
else
    echo "❌ Build gagal — .app tidak ditemukan di dist/"
    exit 1
fi
