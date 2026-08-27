#!/bin/bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
#  Dodol Agent — AppImage Builder
#  Membuat AppImage yang bisa didistribusikan tanpa install
# ═══════════════════════════════════════════════════════════════

APP_NAME="dodol-agent"
APP_VERSION="1.0.0"
ARCH="$(uname -m)"
BUILD_DIR="build"
APPDIR="${BUILD_DIR}/AppDir"

echo "🍬 Dodol Agent AppImage Builder"
echo "═══════════════════════════════"

# ─── 1. Bersihkan build sebelumnya ───
echo "🧹 Membersihkan build sebelumnya..."
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

# ─── 2. Download appimagetool ───
echo "📥 Downloading appimagetool..."
APPIMAGETOOL="${BUILD_DIR}/appimagetool"
if [ ! -f "${APPIMAGETOOL}" ]; then
    wget -q -O "${APPIMAGETOOL}" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage"
    chmod +x "${APPIMAGETOOL}"
fi

# ─── 3. Download base Python AppImage ───
echo "📥 Downloading base Python 3.12 AppImage..."
PYTHON_AI="${BUILD_DIR}/python3.12.AppImage"
if [ ! -f "${PYTHON_AI}" ]; then
    wget -q -O "${PYTHON_AI}" \
        "https://github.com/niess/python-appimage/releases/download/python3.12/python3.12.14-cp312-cp312-manylinux2014_${ARCH}.AppImage"
    chmod +x "${PYTHON_AI}"
fi

# ─── 4. Extract Python AppImage ───
echo "📦 Extracting Python AppImage..."
cd "${BUILD_DIR}"
if [ ! -d "squashfs-root" ]; then
    ./python3.12.AppImage --appimage-extract > /dev/null 2>&1 || true
fi
cd - > /dev/null

# ─── 5. Buat struktur AppDir dari Python AppImage ───
echo "📁 Membuat struktur AppDir..."
rm -rf "${APPDIR}"
cp -r "${BUILD_DIR}/squashfs-root" "${APPDIR}"

# ─── 6. Copy source code ───
echo "📋 Copying source code..."
APP_HOME="${APPDIR}/opt/dodol-agent"
mkdir -p "${APP_HOME}"

# Core modules
cp -r core "${APP_HOME}/"
cp -r agents "${APP_HOME}/"

# App files
cp chat.py cli.py conftest.py "${APP_HOME}/"

# Module files
for f in hitung.py matematika.py string_utils.py konversi.py kotak.py geometri.py; do
    [ -f "$f" ] && cp "$f" "${APP_HOME}/"
done

# Tests
cp -r tests "${APP_HOME}/"

# Docs
cp -r docs "${APP_HOME}/"

# Config
cp .gitignore "${APP_HOME}/" 2>/dev/null || true
cp requirements.txt "${APP_HOME}/" 2>/dev/null || true

# ─── 7. Install dependencies ke bundled Python ───
echo "📚 Installing dependencies..."
SITE_PACKAGES="${APPDIR}/opt/python3.12/lib/python3.12/site-packages"
PIP="${APPDIR}/opt/python3.12/bin/pip3.12"

# Install via pip bundled
if [ -f "${PIP}" ]; then
    "${PIP}" install --target="${SITE_PACKAGES}" \
        python-dotenv groq anthropic openai requests 2>&1 | tail -3
else
    # Fallback: copy dari venv
    if [ -d "venv/lib/python3.12/site-packages" ]; then
        echo "📋 Copying packages from venv..."
        for pkg in dotenv groq anthropic openai requests; do
            cp -rn "venv/lib/python3.12/site-packages/${pkg}"* "${SITE_PACKAGES}/" 2>/dev/null || true
            # Copy .dist-info too
            cp -rn "venv/lib/python3.12/site-packages/${pkg}"*.dist-info "${SITE_PACKAGES}/" 2>/dev/null || true
        done
    fi
fi

# ─── 8. Buat AppRun wrapper ───
echo "🔧 Creating AppRun wrapper..."
cat > "${APPDIR}/AppRun" << 'APPRUN'
#!/bin/bash
APPDIR="${APPDIR:-$(dirname "$(readlink -f "$0")")}"
export PYTHONPATH="${APPDIR}/opt/python3.12/lib/python3.12/site-packages:${APPDIR}/opt/dodol-agent"
cd "${APPDIR}/opt/dodol-agent"

# Load .env jika ada di home user
ENV_FILE="${HOME}/.dodol-agent/.env"
if [ -f "${ENV_FILE}" ]; then
    set -a
    source "${ENV_FILE}"
    set +a
fi

# Load .env dari working directory
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

exec "${APPDIR}/opt/python3.12/bin/python3.12" chat.py "$@"
APPRUN
chmod +x "${APPDIR}/AppRun"

# ─── 9. Copy metadata ───
echo "📋 Copying metadata..."
cp appimage/dodol-agent.desktop "${APPDIR}/dodol-agent.desktop"
cp appimage/dodol-agent.svg "${APPDIR}/dodol-agent.svg"
ln -sf dodol-agent.svg "${APPDIR}/.DirIcon" 2>/dev/null || true

# ─── 10. Build AppImage ───
echo "🔨 Building AppImage..."
OUTPUT="${APP_NAME}.AppImage"

ARCH=${ARCH} "${APPIMAGETOOL}" "${APPDIR}" "${OUTPUT}" 2>&1 | tail -5

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ AppImage berhasil dibuat: ${OUTPUT}"
echo "📊 Ukuran: $(du -h "${OUTPUT}" | cut -f1)"
echo ""
echo "🚀 Cara pakai:"
echo "   chmod +x ${OUTPUT}"
echo "   ./${OUTPUT}"
echo ""
echo "📋 Agar .env terbaca, buat file:"
echo "   mkdir -p ~/.dodol-agent"
echo "   cp .env.example ~/.dodol-agent/.env"
echo "   # lalu isi API key di ~/.dodol-agent/.env"
echo "═══════════════════════════════════════════════════════════════"
