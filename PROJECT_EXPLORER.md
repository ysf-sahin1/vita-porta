# Vita Porta — Project Explorer & Health Analysis

**Son güncelleme:** 2026-05-12 | **Proje durumu:** 75% tamamlandı (6/8 faz)

---

## 📊 Sağlık Özeti

| Metrik | Değer | Durum |
| --- | --- | --- |
| **Faz tamamlanması** | 6/8 (75%) | 🟡 Orta |
| **E2E çalışır mı?** | Evet (mock veri) | ✅ Canlı |
| **Backend test coverage** | 5/5 pass | ✅ Güvenli |
| **Frontend derlemesi** | Temiz | ✅ Başarılı |
| **Bağımlılıklar** | Hepsi tanımlandı | ✅ Stabil |
| **Hazır demo** | Üç senaryo | ✅ Çalışır |

---

## 🏗️ Proje Yapısı

```
Vita Porta/
├── docs/                        # Dokümantasyon
│   ├── pitch.md               # Ürün tanıtımı
│   ├── teknik_rapor.md        # Teknik tasarım
│   └── PROGRESS.md            # Geliştirme ilerlemesi
│
├── orchestration/              # Karar motoru (LangGraph)
│   ├── schemas.py             # Pydantic veri yapıları
│   ├── config.py              # Ortam yapılandırması
│   ├── supervisor.py          # Triaj kararı verici
│   ├── llm.py                 # LLM soyutlama (Anthropic/OpenAI/Mock)
│   ├── demo.py                # Uçtan uca demo
│   ├── prompts/
│   │   └── supervisor.py      # ESI tabanlı sistem prompt
│   ├── rag/
│   │   ├── esi_cases.py       # Tohum vakalar
│   │   ├── retriever.py       # ChromaDB/In-Memory RAG
│   │   └── seed.py            # RAG loader
│   └── tests/
│       └── test_supervisor.py # Birim testler (5/5 ✅)
│
├── backend_api/                # FastAPI sunucusu
│   └── app/
│       ├── main.py            # /healthz, /api/triage/run, /api/triage/stream
│       └── event_bus.py       # asyncio.Queue tabanlı pub/sub
│
├── frontend/                   # Next.js dashboard
│   ├── app/
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Ana sayfa
│   │   └── globals.css        # Global stiller
│   ├── components/
│   │   ├── Header.tsx         # Başlık + canlı durum
│   │   ├── TriageCard.tsx     # Büyük triaj kartı (pulse animasyon)
│   │   ├── AgentPanel.tsx     # Üç ajan (gait/skin/resp)
│   │   ├── HistoryList.tsx    # Son 5 karar
│   │   ├── DemoControls.tsx   # Demo butonları
│   │   └── useTriageStream.ts # SSE hook
│   ├── lib/
│   │   ├── types.ts           # TypeScript şemaları
│   │   ├── api.ts             # Backend client
│   │   └── cn.ts              # Tailwind utilities
│   └── tailwind.config.ts     # Triage renkleri
│
├── gateway_agents/             # Görsel ajanlar (KISMEN YAPILDI)
│   ├── agents/
│   │   ├── base.py            # Soyut Agent sınıfı
│   │   ├── gait.py            # (TODO: MediaPipe Pose)
│   │   ├── skin.py            # (TODO: Renk analizi)
│   │   └── respiration.py      # (TODO: Optik akış)
│   ├── io/
│   │   ├── webcam.py          # (TODO: OpenCV WebcamSource)
│   │   ├── video_file.py       # (TODO: Test video oynatma)
│   │   └── mqtt.py            # (TODO: ESP32-CAM stream)
│   ├── runner.py              # (TODO: Frame toplama & orchestration)
│   └── tests/                 # (TODO: Sentetik framelerle birim testleri)
│
├── edge_firmware/              # ESP32-CAM (BAŞLANMADI)
│   └── vita_porta_cam.ino     # (TODO: MQTT frame yayım)
│
├── infrastructure/             # Docker & DevOps (BAŞLANMADI)
│   ├── docker-compose.yml     # (TODO: Mosquitto + ChromaDB)
│   └── mosquitto/
│       └── mosquitto.conf     # (TODO: MQTT config)
│
└── [Kök dosyalar]
    ├── README.md              # Genel tanıtım
    ├── pyproject.toml         # Python bağımlılıkları
    ├── .env.example           # Ortam şablonu
    └── .gitignore             # Git ignore kuralları
```

---

## ✅ Tamamlanan Bileşenler (6 Faz)

### **Faz 0 — Önhazırlık**
- NotebookLM entegrasyonu (`mendeburlale@gmail.com`)
- Notebook ID: `d9854800-b703-4b71-919f-6121bb3e05d8`
- Proje bağlamı her zaman NotebookLM'den çekilir

### **Faz 1 — Monorepo İskeleti**
- 7 ana klasör yapısı
- Kök yapılandırma dosyaları
- Pydantic şemaları: `TriageCategory`, `AgentObservation`, `AgentBundle`, `TriageDecision`, `TriageEvent`
- **Dosya sayısı:** 8 | **Doğrulama:** `pip install -e ".[dev]"` ✅

### **Faz 2 — Supervisor (LangGraph) + RAG**
- `orchestration/supervisor.py`: 3 düğümlü LangGraph pipeline
  - `retrieve_rag` → `ask_llm` → `validate`
  - LLM hatalarında MockClient fallback
- `orchestration/llm.py`: Provider-agnostic (Anthropic/OpenAI/Mock)
- RAG: 5 tohum ESI vakası + ChromaDB desteği
- **Testler:** 5/5 ✅ | **Demo senaryoları:** 3 (Kırmızı/Sarı/Yeşil)

### **Faz 3 — FastAPI Backend + SSE**
- 3 endpoint:
  - `GET /healthz` — sağlık kontrol
  - `POST /api/triage/run` — tek triaj işlemi
  - `GET /api/triage/stream` — SSE canlı akış
  - `POST /api/triage/demo?scenario=red|yellow|green|all` — demo
- **Doğrulama:** Backend ve demo scenario'lar canlı ✅

### **Faz 4 — Next.js Dashboard**
- **React 18** + **Tailwind CSS** + **shadcn/ui ikonlar** (lucide-react)
- 6 bileşen:
  - Header (canlı durum noktası)
  - TriageCard (kırmızıda pulse-ring)
  - AgentPanel (üç ajan)
  - HistoryList (son 5 karar)
  - DemoControls (4 buton)
  - useTriageStream (SSE hook)
- **Derleme:** Temiz | **Dev sunucu:** http://127.0.0.1:3000 ✅

### **Faz 5 (Yarıda) — Görsel Ajanlar**
- ✅ **Yapıldı:**
  - `gateway_agents/agents/base.py` — `AnalysisWindow` + `Agent` abstract sınıfı
  - `gateway_agents/__init__.py` — modul yapısı
  
- 🔴 **Kaldı:**
  - `gait.py` — MediaPipe Pose (iskelet noktaları, simetri, adım analizi)
  - `skin.py` — Renk uzayı (HSV/LAB, solgunluk eşikleme)
  - `respiration.py` — Optik akış (göğüs hareketi, solunum hızı)
  - `io/webcam.py` — OpenCV WebcamSource
  - `io/video_file.py` — Test video oynatma
  - `io/mqtt.py` — MQTT stream (ESP32-CAM)
  - `runner.py` — Frame orchestration
  - Birim testleri

---

## 🔴 Başlanmamış Bileşenler (2 Faz)

### **Faz 6 — Edge Firmware + Docker**

**Edge Firmware (vita\_porta\_cam.ino):**
- [ ] ESP32-CAM I2S başlatma
- [ ] Wi-Fi bağlantısı
- [ ] MQTT frame yayımı (`vitaporta/frames` topic)
- [ ] Opsiyonel: WS2812 LED halka (triaj durumu göstergesi)

**Docker Infrastructure:**
- [ ] `docker-compose.yml`:
  - Mosquitto MQTT broker (port 1883)
  - ChromaDB container
  - Backend + Frontend servisler
- [ ] `mosquitto.conf` — anonymous allow

**Not:** Hackathon demosu için fiziksel ESP32-CAM **zorunlu değil**. Webcam fallback yeterli. Donanım "konsept gösterimi" için.

---

## 🚀 Başlangıç Rehberi (Mevcut Durum)

```bash
# Terminal 1: Backend
cd "C:\Users\yusuf\OneDrive\Masaüstü\Vita Porta"
python -m uvicorn backend_api.app.main:app --reload

# Terminal 2: Frontend
cd "C:\Users\yusuf\OneDrive\Masaüstü\Vita Porta\frontend"
npm run dev

# Tarayıcı
http://127.0.0.1:3000
# "Üçünü sırayla oynat" → Kırmızı/Sarı/Yeşil canlı görünür
```

---

## 🏛️ Mimari Akış

### **Mevcut (Mockla):**
```
MockBundle → FastAPI /api/triage/demo
              ↓
         EventBus (asyncio)
         /          \
        ↓            ↓
   Supervisor    SSE stream
  (LangGraph)       ↓
    ↓      ↓    Next.js dashboard
   LLM    RAG
 (Mock/
Anthropic/
 OpenAI)
```

### **Faz 5 Tamamlanınca:**
```
Webcam → AnalysisWindow → [Gait | Skin | Respiration] 
                               ↓
                        FastAPI /api/triage/run
                               ↓
                        (Supervisor → Dashboard)
```

### **Faz 6 Tamamlanınca:**
```
ESP32-CAM → MQTT → Gateway → (yukarıdaki akış)
```

---

## 📈 İlerleme Metrikleri

| Faz | Adı | Durum | Dosya | Test |
| --- | --- | --- | --- | --- |
| 0 | Önhazırlık | ✅ | 0 | - |
| 1 | Monorepo | ✅ | 8 | - |
| 2 | Supervisor+RAG | ✅ | 9 | 5/5 ✅ |
| 3 | Backend | ✅ | 4 | Manual ✅ |
| 4 | Frontend | ✅ | 13 | Manual ✅ |
| 5 | Görsel Ajanlar | 🟡 5% | 0 (base yapılı) | - |
| 6 | Edge+Docker | 🔴 0% | 0 | - |
| **TOPLAM** |  | **75%** | **34+** |  |

---

## 🎯 Kritik Yol (Hackathon Tamamlama)

### **Öncelik 1 — Faz 5 (Görsel Ajanlar)**
Hackathon jürisine "canlı kamera + AI analiz" göstermek için gerekli.

**Yapılacak (NotebookLM tavsiyesi: 1-2 gün):**
1. `gait.py` — MediaPipe Pose (10-15 satır: iskelet noktaları, simetri, adım)
2. `skin.py` — HSV renk (5-10 satır: solgunluk eşikleme)
3. `respiration.py` — Frame-fark (10-15 satır: göğüs hareketi, hız)
4. `io/webcam.py` — OpenCV stream
5. `runner.py` — Üç ajanı paralel koşturan orchestrator
6. Birim testler (sentetik frameler)

**Çıktı:** `/api/triage/run` endpoint'i gerçek webcam frame'lerini kabul eder, üç ajan analiz sonucunu döner.

**Jüri gösterimi:**
```
Hackerland'de kamera aç → Dashboard'da canlı gözlemler → Kırmızı/Sarı/Yeşil triaj kartı
```

### **Öncelik 2 — Faz 6 (Edge Firmware + Docker)**
Teknik derinlik + deployment hazırlığı için.

**Minimum (4-6 saat):**
1. `docker-compose.yml` — Mosquitto + backend + frontend
2. `vita_porta_cam.ino` — Temel ESP32-CAM + MQTT (mock ya da gerçek)
3. `mqtt_source.py` — MQTT frame kaynak

**Çıktı:** Tek `docker compose up` ile full stack çalışır.

---

## ⚠️ Risk Değerlendirmesi

| Risk | Olasılık | Etki | Çözüm |
| --- | --- | --- | --- |
| **Faz 5 veri ajanları zaman aşan olur** | 🟡 Orta | 🔴 Yüksek | Solunum ajanını basit tutun (frame-fark), gait+skin'e odaklan |
| **MediaPipe performansı kötü** | 🟡 Orta | 🟡 Orta | Webcam yerine telefon kamerasını test et, frame çözünürlüğü düşür |
| **MQTT bağlantı sorunları** | 🟢 Düşük | 🟡 Orta | Websocket fallback yaz, broker kontrol et |
| **LLM API anahtarı eksik/geçersiz** | 🟡 Orta | 🔴 Yüksek | Mock client ile fallback (zaten implemented) |
| **Docker build hata verir** | 🟢 Düşük | 🟡 Orta | Node/Python versions'ı kontrol et, build stage'leri ekle |

---

## 🔧 Yapılandırma Kontrol Listesi

- [ ] `.env` dosyası oluşturuldu (`.env.example` kopyala)
- [ ] `OPENAI_API_KEY` **veya** `ANTHROPIC_API_KEY` ayarlandı
- [ ] `python -m pytest orchestration/tests -v` → 5/5 pass
- [ ] `npm install && npm run build` frontend'te temiz
- [ ] Backend + Frontend aynı anda çalışıyor, SSE akış görülüyor

---

## 📚 Önemli Karar Geçmişi

1. **Middle-out yaklaşım:** Supervisor + mock veriyle başla, gerçek ajanlar takarken değiştir → **Hız + stabilite**
2. **Provider-agnostic LLM:** Anthropic/OpenAI/Mock arasında env ile geç → **Esneklik + fallback**
3. **In-memory RAG default:** ChromaDB lazy-load → **Hızlı start**
4. **Minimal frontend bağımlılıkları:** Tailwind + lucide-react yeterli → **Boyut + hız**
5. **Webcam fallback:** Hackathon jürisine ESP32-CAM olmadan canlı demo → **Risk azaltma**

---

## 📞 İletişim & Notlar

**Proje sahibi:** Yusuf Şahin, Mert Mirzaoğlu, Mert Korkmaz
**Hackathon:** CODEX AI Hackathon 2026 — Tıp ve Sağlık Teknolojileri
**Deadline (tahmini):** Hackathon teslim tarihi

**NotebookLM Entegrasyonu:**
- Notebook ID: `d9854800-b703-4b71-919f-6121bb3e05d8`
- `nlm login` ile bağlı
- Proje bağlamı her zaman NotebookLM'den çekilir

---

## 🎬 Son Durumu Gözlemlemek

```bash
# Tüm testler geçiyor mu?
pytest orchestration/tests -v

# Frontend compile ediliyor mu?
cd frontend && npm run build

# Backend canlı mı?
curl http://127.0.0.1:8000/healthz

# SSE stream çalışıyor mu?
curl -N http://127.0.0.1:8000/api/triage/stream &
# (Başka terminalde) curl -X POST "http://127.0.0.1:8000/api/triage/demo?scenario=red"
# → Event stream'de "decision" event'i görülür
```

---

**Güncelleme tarihi:** 2026-05-12  
**Sonraki adım:** Faz 5 görsel ajanları tamamla → Hackathon demosu
