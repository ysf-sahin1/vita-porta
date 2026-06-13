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
| `benchmarking/` | Etiketli vaka çalıştırıcısı + güvenlik metrikleri + manifest desteği |
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

## Klinik Benchmark ve Ölçüm Ekranı

Benchmark altyapısı, etiketli vakalarda sistem önerisini beklenen uzman
kategorisiyle karşılaştırır. Dashboard'daki **Benchmark ve güvenlik ölçümleri**
paneli şu değerleri gösterir:

- Kırmızı vaka yakalama oranı (`red_sensitivity`)
- Kritik vaka kaçırma oranı
- Düşük öncelik ve aşırı öncelik verme oranları
- Veri yetersiz sonucu üretme oranı
- Ortalama ve P95 karar süresi
- Kırmızı / Sarı / Yeşil / Veri Yetersiz confusion matrix

Repoyla birlikte gelen 11 vakalık sentetik baseline'ı çalıştır:

```bash
python -m benchmarking.runner
```

Rapor `.benchmark/latest.json` dosyasına yazılır. Backend ve frontend açıksa aynı
baseline dashboard'daki **Sentetik baseline çalıştır** butonuyla da
çalıştırılabilir.

`.env` ile yapılandırılmış gerçek LLM sağlayıcısını ölçmek için:

```bash
python -m benchmarking.runner --engine configured
```

Kendi uzman etiketli bundle manifestini çalıştır:

```bash
python -m benchmarking.runner \
  --manifest benchmarking/manifest.example.json \
  --out .benchmark/expert-report.json
```

Video vakası eklemek için manifestte `bundle` yerine, manifest dosyasına göre
göreli veya mutlak bir `video_path` verilebilir:

```json
{
  "case_id": "expert-red-video-001",
  "expected_category": "red",
  "video_path": "../data/expert-red-video-001.mp4",
  "window_duration_s": 3.0,
  "tags": ["expert-labelled", "red"]
}
```

Video benchmarkı mevcut `VideoFileSource` ve üç görsel ajanı kullanır; ekstra
donanım gerektirmez. Sensör ve Raspberry Pi performansını ölçmek için aynı
senaryolar ayrıca gerçek ESP32-CAM + AMG8833 hattında çalıştırılmalıdır.

> **Önemli:** Repodaki sentetik baseline yalnızca benchmark altyapısını ve karar
> regresyonlarını doğrular. Klinik performans iddiası için vakaların yetkili
> klinik uzmanlarca etiketlenmesi, temsili bir veri seti kullanılması ve sonuçların
> bağımsız olarak incelenmesi gerekir.

Benchmark API uçları:

| Metot | Uç | Açıklama |
|-------|----|----------|
| `GET` | `/api/benchmark/latest` | Son kaydedilmiş raporu döndürür |
| `POST` | `/api/benchmark/run?engine=mock` | Tekrarlanabilir sentetik baseline çalıştırır |
| `POST` | `/api/benchmark/run?engine=configured` | Yapılandırılmış LLM ile baseline çalıştırır |

---

## Ekip

Yusuf Şahin · Mert Mirzaoğlu · Mert Korkmaz
