#!/bin/bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════════
#  Dodol Agent — Installer
#  Membuat command 'dodol' agar bisa dijalankan dari mana saja
# ═══════════════════════════════════════════════════════════════

INSTALL_DIR="${HOME}/.local/bin"
AGENT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🍬 Dodol Agent Installer"
echo "═════════════════════════"

# ─── 1. Buat direktori install ───
mkdir -p "${INSTALL_DIR}"

# ─── 2. Buat wrapper script ───
cat > "${INSTALL_DIR}/dodol" << WRAPPER
#!/bin/bash
# Dodol Agent wrapper
cd "${AGENT_DIR}"
source venv/bin/activate 2>/dev/null || true

# Load .env
if [ -f ~/.dodol-agent/.env ]; then
    set -a; source ~/.dodol-agent/.env; set +a
fi
if [ -f .env ]; then
    set -a; source .env; set +a
fi

exec python chat.py "\$@"
WRAPPER

chmod +x "${INSTALL_DIR}/dodol"

# Buat symlink 'dodol-agent' juga
ln -sf "${INSTALL_DIR}/dodol" "${INSTALL_DIR}/dodol-agent"
echo "✅ Command 'dodol' dan 'dodol-agent' dibuat di ${INSTALL_DIR}/"

# ─── 3. Cek PATH ───
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    echo ""
    echo "⚠️  Direktori ${INSTALL_DIR} belum ada di PATH."
    echo "   Tambahkan ini ke ~/.bashrc atau ~/.zshrc:"
    echo ""
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

# ─── 4. Setup .env jika belum ada ───
ENV_FILE="${HOME}/.dodol-agent/.env"
if [ ! -f "${ENV_FILE}" ]; then
    mkdir -p "${HOME}/.dodol-agent"
    cp .env.example "${ENV_FILE}" 2>/dev/null || true
    echo ""
    echo "📋 File .env dibuat di: ${ENV_FILE}"
    echo "   Silakan edit dan isi API key kamu."
fi

# ─── 5. Selesai ───
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Instalasi selesai!"
echo ""
echo "🚀 Cara pakai:"
echo "   dodol-agent"
echo "   atau"
echo "   dodol"
echo ""
echo "   python chat.py"
echo ""
echo "📋 Jika command 'dodol' belum dikenal, jalankan:"
echo "   source ~/.bashrc"
echo "   # atau"
echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
echo "═══════════════════════════════════════════════════════════════"
