# Vita Porta — Yaşam Kapısı

Acil servis girişine konumlanan, hemşireye triaj asistanlığı yapan multi-agent yapay zekâ sistemi. Kapıdan giren her hastayı 3 saniye içinde gözleyerek; yürüyüş örüntüsü, ten rengi ve solunum hareketi gibi görsel sinyalleri analiz eder. Hemşireye gerekçeli ve açıklanabilir bir triaj kategorisi önerisi sunar.

> **Vita Porta tanı koymaz.** Sistem hemşirenin yerine geçmez. Son karar her zaman hemşireye aittir.

CODEX AI Hackathon 2026 · Tıp ve Sağlık Teknolojileri

## Monorepo yapısı

| Dizin | İçerik |
|-------|--------|
| `edge_firmware/` | ESP32-CAM Arduino sketch'i (kapı çerçevesi kamerası) |
| `gateway_agents/` | Python gateway: MQTT abone + üç görsel ajan (yürüyüş, ten rengi, solunum) |
| `orchestration/` | LangGraph supervisor + ESI prompt'ları + ChromaDB RAG |
| `backend_api/` | FastAPI + Server-Sent Events ile hemşire dashboard'una canlı yayın |
| `frontend/` | Next.js 14 hemşire dashboard'u (Tailwind + shadcn/ui) |
| `infrastructure/` | Docker Compose: Mosquitto broker, ChromaDB |
| `docs/` | Pitch, teknik rapor, ek dokümantasyon |

## Hızlı başlangıç

```bash
# 1. Python bağımlılıklarını kur
pip install -e ".[dev]"

# 2. Ortam değişkenlerini hazırla
cp .env.example .env
# .env içine LLM API anahtarınızı girin

# 3. RAG vektör deposunu hazırla
python -m orchestration.rag.seed

# 4. Supervisor mock demoyu çalıştır
python -m orchestration.demo

# 5. Backend API'yi başlat
uvicorn backend_api.app.main:app --reload

# 6. Frontend'i başlat
cd frontend && npm install && npm run dev
```

## Mimari özet

```
ESP32-CAM ─► MQTT ─► Gateway ─► [Gait | Skin | Respiration] ─► Supervisor ─► FastAPI/SSE ─► Dashboard
                                                                    ▲
                                                                ChromaDB (RAG)
```

Her ajan kendi modalitesinden bağımsız çalışır ve 0–1 arası güven skoru üretir. Supervisor (LangGraph) bu çıktıları ESI protokolü ile harmanlayarak Kırmızı / Sarı / Yeşil önerisi ve Türkçe gerekçe sunar.

## Ekip

Yusuf Şahin · Mert Mirzaoğlu · Mert Korkmaz
