# Vita Porta — Yaşam Kapısı

Acil servis girişine konumlanan, hemşireye triaj asistanlığı yapan multi-agent yapay zekâ sistemi. Kapıdan giren her hastayı 3 saniye içinde gözleyerek; yürüyüş örüntüsü, ten rengi ve yüz ifadesi gibi görsel sinyalleri analiz eder. Hemşireye gerekçeli ve açıklanabilir bir triaj kategorisi önerisi sunar.

> **Vita Porta tanı koymaz.** Sistem hemşirenin yerine geçmez. Son karar her zaman hemşireye aittir.

CODEX AI Hackathon 2026 · Tıp ve Sağlık Teknolojileri

---

## Donanım

| Bileşen | Görev |
|---------|-------|
| **Raspberry Pi** | Tüm yazılım katmanlarını çalıştırır; WiFi hotspot açar |
| **ESP32-CAM** | Kapı çerçevesine monteli kamera + AMG8833 termal sensör |
| **PIR Sensörü** | Pi GPIO'suna bağlı hareket tetikleyici (HC-SR501) |
| **RGB LED** | ESP32 üzerinde — triaj kararını renk ile gösterir |

---

## Monorepo yapısı

| Dizin | İçerik |
|-------|--------|
| `edge_firmware/` | ESP32-CAM Arduino sketch'i (kamera + AMG8833 termal + WiFi) |
| `gateway_agents/` | Python gateway: PIR tetikleyici + üç görsel ajan (yürüyüş, termal, ifade) |
| `orchestration/` | LangGraph supervisor + ESI prompt'ları + ChromaDB RAG |
| `backend_api/` | FastAPI + Server-Sent Events ile hemşire dashboard'una canlı yayın |
| `frontend/` | Next.js 14 hemşire dashboard'u (Tailwind + shadcn/ui) |
| `infrastructure/` | Raspberry Pi kurulum scripti + systemd servis dosyaları |
| `docs/` | Pitch, teknik rapor, ek dokümantasyon |

---

## Mimari

```
[PIR Sensörü] ──→ Raspberry Pi (192.168.4.1)
                        │
         ┌──────────────┼──────────────────┐
         │              │                  │
   Backend API     Gateway Runner     Frontend
   (FastAPI :8000) (runner.py)     (Next.js :3000)
         │              │
         │    ESP32-CAM (192.168.4.x)
         │       ├── :81/stream  → MJPEG → Gait + Expression Agent
         │       ├── :80/thermal → AMG8833 → Thermal Agent
         │       └── :80/verdict ← Supervisor kararı → LED
         │
    LangGraph Supervisor
    ├── ChromaDB RAG (456 ESI vakası)
    └── Anthropic Claude (triaj kararı)
```

Her ajan kendi modalitesinden bağımsız çalışır ve 0–1 arası güven skoru üretir. Supervisor (LangGraph) bu çıktıları ESI protokolü ile harmanlayarak Kırmızı / Sarı / Yeşil önerisi ve Türkçe gerekçe sunar.

**Ağ mimarisi:** Pi kendi WiFi hotspot'unu açar (`vita-porta`). ESP32-CAM bu hotspot'a bağlanır; harici router gerekmez. Sistem tamamen bağımsız çalışır.

---

## Raspberry Pi — Hızlı Kurulum

```bash
# 1. Repoyu klonla
git clone https://github.com/ysf-sahin1/vita-porta
cd vita-porta

# 2. Ortam değişkenlerini hazırla
cp .env.example .env
nano .env   # ANTHROPIC_API_KEY gir

# 3. Tek komutla kur (venv + frontend build + RAG seed + hotspot + systemd)
bash infrastructure/pi_setup.sh

# 4. Servisleri başlat
sudo systemctl start vita-porta-backend vita-porta-frontend vita-porta-gateway

# 5. Dashboard: http://192.168.4.1:3000
```

ESP32'yi Pi hotspot'una bağlamak için firmware'deki `WIFI_NETWORKS` dizisine
`vita-porta` / `vitaporta2026` bilgileri zaten yazılıdır.

---

## Geliştirme Ortamı (PC)

Donanım olmadan test için:

```bash
# Bağımlılıkları kur
pip install -e ".[dev]"

# Terminal 1 — Backend
uvicorn backend_api.app.main:app --reload

# Terminal 2 — Gateway (webcam + sahte PIR)
python -m gateway_agents.runner --webcam 0 --mock-pir

# Terminal 3 — Frontend
cd frontend && npm run dev
# → http://localhost:3000
```

ESP32 bağlıysa gerçek donanımla çalıştır:

```bash
python -m gateway_agents.runner --esp 192.168.4.2 --pir-pin 17
```

---

## Ekip

Yusuf Şahin · Mert Mirzaoğlu · Mert Korkmaz
