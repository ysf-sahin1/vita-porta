#!/usr/bin/env bash
# pi_setup.sh — Vita Porta Raspberry Pi tek seferlik kurulum scripti
#
# Kullanım:
#   git clone https://github.com/ysf-sahin1/vita-porta
#   cd vita-porta
#   cp .env.example .env && nano .env   # API anahtarını gir
#   bash infrastructure/pi_setup.sh
#
# Gereksinim: Raspberry Pi OS (64-bit), internet bağlantısı mevcut olmalı.
# Kurulum sonrası Pi yeniden başlatılabilir; servisler otomatik başlar.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$REPO_DIR/.env"

# .env dosyasından değişken oku (varsa)
if [[ -f "$ENV_FILE" ]]; then
    # sadece HOTSPOT_* satırlarını güvenli biçimde yükle
    set -a
    # shellcheck disable=SC1090
    source <(grep -E '^(HOTSPOT_|PIR_|ESP_)' "$ENV_FILE" || true)
    set +a
fi

HOTSPOT_SSID="${HOTSPOT_SSID:-vita-porta}"
HOTSPOT_PASS="${HOTSPOT_PASS:-vitaporta2026}"

echo "======================================================"
echo "  Vita Porta — Raspberry Pi Kurulum Scripti"
echo "  Repo : $REPO_DIR"
echo "  SSID : $HOTSPOT_SSID"
echo "======================================================"
echo ""

# ── 1. Sistem paketleri ────────────────────────────────────────────────────
echo "[1/7] Sistem paketleri güncelleniyor..."
sudo apt-get update -qq
sudo apt-get install -y \
    python3 python3-venv python3-pip \
    libatlas-base-dev libopenblas-dev liblapack-dev \
    libgl1 libglib2.0-0 \
    nodejs npm \
    hostapd dnsmasq \
    git curl
echo "      ✓ Paketler hazır."

# ── 2. Python sanal ortamı ─────────────────────────────────────────────────
echo "[2/7] Python venv oluşturuluyor..."
python3 -m venv "$REPO_DIR/venv"
"$REPO_DIR/venv/bin/pip" install --upgrade pip -q
"$REPO_DIR/venv/bin/pip" install -e "$REPO_DIR" -q
echo "      ✓ Python bağımlılıkları kuruldu."

# gpiozero (sadece Pi'de gereken; kurulumu zararsız)
"$REPO_DIR/venv/bin/pip" install gpiozero -q
echo "      ✓ gpiozero kuruldu."

# ── 3. Frontend build ──────────────────────────────────────────────────────
echo "[3/7] Next.js frontend derleniyor (birkaç dakika sürebilir)..."
cd "$REPO_DIR/frontend"
npm ci --silent
npm run build --silent
cd "$REPO_DIR"
echo "      ✓ Frontend derlendi."

# ── 4. RAG vektör deposu ──────────────────────────────────────────────────
echo "[4/7] ChromaDB RAG seed yapılıyor..."
"$REPO_DIR/venv/bin/python" -m orchestration.rag.seed
echo "      ✓ RAG hazır."

# ── 5. WiFi Hotspot kurulumu ──────────────────────────────────────────────
echo "[5/7] WiFi Hotspot yapılandırılıyor..."

# hostapd: erişim noktası ayarları
sudo tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
interface=wlan0
driver=nl80211
ssid=$HOTSPOT_SSID
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$HOTSPOT_PASS
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# hostapd konfigürasyon dosyasını işaret et
sudo sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' \
    /etc/default/hostapd 2>/dev/null || true

# dnsmasq: DHCP sunucusu (192.168.4.2 – 192.168.4.20)
sudo tee /etc/dnsmasq.conf > /dev/null <<EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain-needed
bogus-priv
EOF

# wlan0 statik IP (dhcpcd)
if ! grep -q "interface wlan0" /etc/dhcpcd.conf; then
    sudo tee -a /etc/dhcpcd.conf > /dev/null <<EOF

# Vita Porta hotspot — wlan0 sabit IP
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
EOF
fi

sudo systemctl unmask hostapd 2>/dev/null || true
sudo systemctl enable hostapd dnsmasq
echo "      ✓ Hotspot yapılandırıldı: SSID=$HOTSPOT_SSID IP=192.168.4.1"

# ── 6. Systemd servisleri ──────────────────────────────────────────────────
echo "[6/7] Systemd servisleri yükleniyor..."
for svc in vita-porta-backend vita-porta-gateway vita-porta-frontend; do
    sudo cp "$REPO_DIR/infrastructure/systemd/${svc}.service" /etc/systemd/system/
done
sudo systemctl daemon-reload
sudo systemctl enable vita-porta-backend vita-porta-gateway vita-porta-frontend
echo "      ✓ Servisler etkinleştirildi (boot'ta otomatik başlar)."

# ── 7. gpio grubu ─────────────────────────────────────────────────────────
echo "[7/7] pi kullanıcısı gpio grubuna ekleniyor..."
sudo usermod -aG gpio pi 2>/dev/null || true
echo "      ✓ GPIO erişimi hazır."

# ── Özet ──────────────────────────────────────────────────────────────────
echo ""
echo "======================================================"
echo "  Kurulum tamamlandı!"
echo ""
echo "  Servisleri manuel başlatmak için:"
echo "    sudo systemctl start vita-porta-backend"
echo "    sudo systemctl start vita-porta-frontend"
echo "    sudo systemctl start vita-porta-gateway"
echo ""
echo "  Log takibi:"
echo "    journalctl -u vita-porta-gateway -f"
echo ""
echo "  Dashboard: http://192.168.4.1:3000"
echo "  Backend  : http://192.168.4.1:8000/healthz"
echo ""
echo "  ESP32 firmware'ine şu WiFi bilgilerini yaz:"
echo "    SSID : $HOTSPOT_SSID"
echo "    Şifre: $HOTSPOT_PASS"
echo ""
echo "  Pi'yi yeniden başlatmak servislerin otomatik açılmasını sağlar:"
echo "    sudo reboot"
echo "======================================================"
