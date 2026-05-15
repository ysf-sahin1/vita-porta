# Vita Porta — Project Explorer & Health Analysis

**Son güncelleme:** 2026-05-16 | **Proje durumu:** 7.5/8 faz tamamlandı (~94%)

---

## 📊 Sağlık Özeti

| Metrik | Değer | Durum |
| --- | --- | --- |
| **Faz tamamlanması** | 7.5/8 (94%) | ✅ İleri |
| **E2E çalışır mı?** | Evet (gerçek webcam + mock veri) | ✅ Canlı |
| **Backend + Gateway test coverage** | 27/27 pass | ✅ Yeşil |
| **Frontend derlemesi** | `tsc --noEmit` clean | ✅ Temiz |
| **Görsel ajan sayısı** | **5/5** (gait/skin/respiration/thermal/expression) | ✅ Tam |
| **Hazır demo senaryoları** | 3 (kırmızı/sarı/yeşil) | ✅ Çalışır |
| **Hemşire giriş ekranı** | localStorage-tabanlı, KVKK-uyumlu | ✅ Devrede |

---

## 🏗️ Proje Yapısı

```
Vita Porta/
├── docs/                            # Dokümantasyon
│   ├── pitch.md                    # Ürün tanıtımı
│   ├── teknik_rapor.md             # Teknik tasarım (5 ajan)
│   ├── PROGRESS.md                 # Faz-faz ilerleme özeti
│   └── gelisme_ilerlemesi.md       # Tur-tur detaylı değişiklik kaydı
│
├── orchestration/                   # Karar motoru (LangGraph)
│   ├── schemas.py                  # Pydantic — 5 ajanlı AgentBundle
│   ├── config.py                   # Env tabanlı yapılandırma
│   ├── supervisor.py               # Triaj kararı verici (retrieve_rag→ask_llm→validate)
│   ├── llm.py                      # LLM soyutlama (Anthropic/OpenAI/Mock — 5 ajan weights)
│   ├── demo.py                     # 3 senaryo (red/yellow/green) + 5 ajan observations
│   ├── prompts/
│   │   └── supervisor.py           # ESI tabanlı sistem prompt (termal + expression özel kuralları)
│   ├── rag/
│   │   ├── esi_cases.py            # 5 tohum vaka
│   │   ├── retriever.py            # ChromaDB / In-Memory RAG
│   │   └── seed.py                 # RAG loader
│   └── tests/
│       └── test_supervisor.py      # 5/5 ✅
│
├── backend_api/                     # FastAPI sunucusu
│   └── app/
│       ├── main.py                 # /healthz, /api/triage/run, /api/triage/stream, /api/triage/demo
│       └── event_bus.py            # asyncio.Queue tabanlı pub/sub
│
├── frontend/                        # Next.js dashboard
│   ├── app/
│   │   ├── layout.tsx              # Inter font (next/font/google)
│   │   ├── page.tsx                # SessionGate → Dashboard
│   │   └── globals.css             # 16px base, gradient zemin, tabular-nums
│   ├── components/
│   │   ├── Header.tsx              # Hemşire bilgisi + status pilleri + canlı saat + çıkış
│   │   ├── LoginScreen.tsx         # Ad/Soyad/Hastane formu (glassmorphism)
│   │   ├── SessionGate.tsx         # Root wrapper + React Context (useNurseSession)
│   │   ├── TriageCard.tsx          # Büyük triaj kartı (pulse-ring, per-agent ağırlık 5 sütun, NurseVerdict)
│   │   ├── AgentPanel.tsx          # xl+ AnatomicalRadial / altı grid; AgentCard export
│   │   ├── AnatomicalRadial.tsx    # Silüet merkezde, 5 ajan vücudun bölgesinde, SVG bağlantı çizgileri
│   │   ├── PostureSilhouette.tsx   # Mevcut çöp adam (gait kartında)
│   │   ├── NurseVerdict.tsx        # Onayla / Reddet / Değiştir
│   │   ├── HistoryList.tsx         # Tıklanabilir, verdict ikonlu, tabular-nums saat
│   │   ├── HistoryDetailModal.tsx  # 5 ajan snapshot + verdict reuse
│   │   ├── Tooltip.tsx             # Sıfır bağımlılık tooltip
│   │   ├── DemoControls.tsx        # 4 demo butonu (collapse içinde)
│   │   └── useTriageStream.ts      # SSE hook + verdict map + history snapshot
│   ├── lib/
│   │   ├── types.ts                # Backend ile birebir, agent Literal 5'li
│   │   ├── api.ts                  # playDemo, streamUrl
│   │   ├── cn.ts                   # Tailwind utility
│   │   ├── session.ts              # localStorage helpers (KVKK-uyumlu)
│   │   ├── signalLabels.ts         # Türkçe sinyal etiketleri (expression_state, consciousness_hint dahil)
│   │   └── agentReasons.ts         # info/warn/error reason pill'leri (5 ajan)
│   └── tailwind.config.ts          # Triage renkleri + 6 animasyon (pulseRing, statusGlow, lineFlow, silhouettePulse, silhouetteSway, chestBreathe)
│
├── gateway_agents/                  # 5 görsel ajan + IO + runner
│   ├── agents/
│   │   ├── base.py                 # Agent ABC + AnalysisWindow
│   │   ├── gait.py                 # MediaPipe Pose (sway, asymmetry, posture)
│   │   ├── skin.py                 # OpenCV Haar Cascade + HSV (skin_tone)
│   │   ├── respiration.py          # Frame-diff + peak detection (breaths_per_minute, pattern)
│   │   ├── thermal.py              # MediaPipe Face Detection + LAB warmth (temp_estimate_c, fever_flag, hypothermia_flag)
│   │   └── expression.py           # **MediaPipe Face Mesh** (EAR, PSPI proxy, face_asymmetry, consciousness_hint)
│   ├── io/
│   │   ├── webcam.py               # cv2.VideoCapture (macOS AVFoundation default, Windows CAP_DSHOW fallback)
│   │   ├── video_file.py           # VideoFileSource (loop desteği)
│   │   └── mqtt.py                 # MqttSource (paho-mqtt, lazy import)
│   ├── runner.py                   # 5 ajan paralel (ThreadPoolExecutor max_workers=5)
│   └── tests/
│       ├── test_agents.py          # 4 sınıf × 3 test + 4 schema conformance = 16 ✅
│       └── test_runner.py          # 6 ✅
│
├── edge_firmware/                   # ESP32-CAM (BAŞLANMADI — Faz 6)
│   └── vita_porta_cam.ino          # (TODO: MQTT frame yayım)
│
├── infrastructure/                  # Docker & DevOps (BAŞLANMADI — Faz 6)
│   ├── docker-compose.yml          # (TODO: Mosquitto + ChromaDB)
│   └── mosquitto/
│       └── mosquitto.conf          # (TODO: MQTT config)
│
└── [Kök dosyalar]
    ├── README.md
    ├── pyproject.toml              # mediapipe==0.10.18 pinli (kritik)
    ├── .env.example
    └── .gitignore
```

---

## ✅ Tamamlanan Bileşenler (7.5 Faz)

| Faz | Adı | Durum | Notlar |
| --- | --- | --- | --- |
| 0 | NotebookLM bağlantısı | ✅ | Notebook ID `d9854800-…` |
| 1 | Monorepo + Pydantic şemaları | ✅ | 5 ajanlı `AgentBundle` |
| 2 | Supervisor (LangGraph) + RAG | ✅ | 5/5 test, mock + provider-agnostic LLM |
| 3 | FastAPI backend + SSE | ✅ | `/healthz`, `/api/triage/run`, `/api/triage/stream`, `/api/triage/demo` |
| 4 | Next.js dashboard (ilk versiyon) | ✅ | Tailwind + lucide-react |
| **4.5** | **Health-OS redesign** | ✅ | Inter font, glassmorphism, hemşire onay akışı, Türkçe sinyaller |
| **4.6** | **Login + Anatomik Radyal** | ✅ | localStorage session, silüet merkezde + 5 ajan etrafta |
| 5 | **5 görsel ajan** | ✅ | gait + skin + respiration + thermal + **expression** |
| 5.5 | origin/main rewrite ile birleşme | ✅ | mertmrz → main, 27/27 pass |
| 5.6 | Yüz İfadesi ajanı (Faz 5 kapanışı) | ✅ | MediaPipe Face Mesh, EAR + PSPI proxy |
| 7 | Uçtan uca canlı demo | ✅ | Webcam → 5 ajan → backend → dashboard |

---

## 🔴 Başlanmamış (1.5 Faz)

### **Faz 6 — Edge Firmware + Docker**

**Edge Firmware (`vita_porta_cam.ino`):**
- ESP32-CAM I2S kamera başlatma
- Wi-Fi bağlantısı
- MQTT frame yayımı (`vitaporta/frames` topic)
- Opsiyonel: WS2812 LED halka (triaj durumu görsel göstergesi)

**Docker Infrastructure:**
- `docker-compose.yml`: Mosquitto MQTT broker + ChromaDB + Backend + Frontend
- `mosquitto.conf` — anonymous allow

**Not:** Hackathon demosu için fiziksel ESP32-CAM **zorunlu değil**. Webcam fallback yeterli. Donanım "konsept gösterimi" için.

### **Faz 8 — Pitch + Jüri Polish**

- `docs/pitch.md` sunum scriptiyle revize
- Demo videosu (yedek senaryo: webcam yoksa `VideoFileSource`)
- ESP32-CAM fiziksel prop (lehim + kasa)

---

## 🚀 Hızlı Başlangıç (Mevcut Durum)

```bash
# Bağımlılıklar (mediapipe 0.10.18 pinli)
pip install -e ".[dev]"

# Backend (terminal 1)
python -m uvicorn backend_api.app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (terminal 2)
cd frontend && npm install && npm run dev

# Gerçek webcam → 5 ajan → backend (terminal 3, opsiyonel)
python -m gateway_agents.runner --webcam 0 --window 3.0

# Tarayıcı
http://127.0.0.1:3000
# İlk açılışta hemşire giriş ekranı çıkar (Ad / Soyad / Hastane)
# Dashboard'da "Demo senaryoları" → "Üçünü sırayla oynat" çalışır
```

---

## 🏛️ Mimari Akış (Mevcut)

```
Webcam / Test Video / MQTT (ESP32)
        │
        │ 3sn pencere (AnalysisWindow)
        ▼
ThreadPoolExecutor (5 paralel ajan)
   │      │       │        │         │
   ▼      ▼       ▼        ▼         ▼
 Gait  Skin   Resp.    Thermal   Expression
 (Pose)(Haar)(diff)   (LAB-proxy) (Face Mesh)
   │      │       │        │         │
   └──────┴───────┴────────┴─────────┘
                  │ AgentBundle
                  ▼
        FastAPI /api/triage/run
                  │
                  ▼
            EventBus (asyncio)
           /              \
          ▼                ▼
     Supervisor        SSE stream
     (LangGraph)             │
      │      │               ▼
      ▼      ▼      Next.js dashboard
     LLM   RAG       (hemşire girişli,
   (Anth./           radyal layout +
   OpenAI/           ✓/✗/✎ verdict)
    Mock)
```

---

## 📈 İlerleme Metrikleri

| Faz | Adı | Durum | Test |
| --- | --- | --- | --- |
| 0 | Önhazırlık | ✅ | — |
| 1 | Monorepo | ✅ | — |
| 2 | Supervisor + RAG | ✅ | 5/5 |
| 3 | Backend + SSE | ✅ | Manual + curl |
| 4 | Frontend (1. versiyon) | ✅ | Manual |
| 4.5 | Frontend redesign | ✅ | tsc clean |
| 4.6 | Login + Radyal | ✅ | tsc clean |
| 5 | 5 görsel ajan | ✅ | 16/16 agents + 6/6 runner |
| 5.5 | origin/main merge | ✅ | 27/27 |
| 5.6 | Expression eklendi (Faz 5 kapanışı) | ✅ | 27/27 |
| 7 | Uçtan uca canlı | ✅ | Manuel webcam testi |
| 6 | Edge + Docker | 🔴 | — |
| 8 | Pitch + polish | 🔴 | — |
| **TOPLAM** |  | **~94%** | **27/27 + tsc clean** |

---

## ⚠️ Risk Değerlendirmesi

| Risk | Olasılık | Etki | Azaltma |
| --- | --- | --- | --- |
| Webcam MediaPipe yavaş | 🟢 Düşük | 🟡 Orta | Frame çözünürlüğü düşür, window 3s yeterli |
| MQTT bağlantı sorunları | 🟢 Düşük | 🟡 Orta | Webcam fallback always-on |
| LLM API key eksik | 🟡 Orta | 🟢 Düşük | MockLLMClient otomatik devreye girer |
| `next build` dev mode'da | 🔴 Yüksek (eğer çalıştırılırsa) | 🔴 Yüksek | Sadece `tsc --noEmit` kullan; build için ayrı worktree |
| Demo butonu çalışmıyor (backend kapalı) | 🟡 Orta | 🟡 Orta | Header'da API pili "off" gösterir; uvicorn'u başlat |
| Expression proxy modu yanlış sinyal | 🟢 Düşük | 🟡 Orta | Confidence ≤0.55 ile şeffaflık; supervisor'da tek başına kırmızıya çekmez |

---

## 🔧 Yapılandırma Kontrol Listesi

- [ ] `.env` dosyası oluşturuldu (`.env.example` kopyala)
- [ ] `OPENAI_API_KEY` **veya** `ANTHROPIC_API_KEY` ayarlandı (opsiyonel; yoksa mock devreye girer)
- [ ] `python -m pytest gateway_agents/tests orchestration/tests -v` → 27/27 pass
- [ ] `cd frontend && npx tsc --noEmit` → clean
- [ ] Backend + Frontend aynı anda çalışıyor, SSE akış görülüyor
- [ ] İlk girişte hemşire bilgileri girildi (localStorage'da hatırlanıyor mu?)

---

## 📚 Önemli Karar Geçmişi

1. **Middle-out yaklaşım:** Supervisor + mock veriyle başla, gerçek ajanlar takarken değiştir → **Hız + stabilite**
2. **Provider-agnostic LLM:** Anthropic/OpenAI/Mock arasında env ile geç → **Esneklik + fallback**
3. **In-memory RAG default:** ChromaDB lazy-load → **Hızlı start**
4. **Minimal frontend bağımlılıkları:** Tailwind + lucide-react yeterli → **Boyut + hız**
5. **Webcam fallback:** Hackathon jürisine ESP32-CAM olmadan canlı demo → **Risk azaltma**
6. **Expression ajanı geometrik proxy modu:** PSPI classifier eğitmek yerine MediaPipe Face Mesh + kural-tabanlı (EAR + kaş çatma + landmark simetri) → **Hackathon penceresinde uygulanabilir, açıklanabilir, deterministik**
7. **Hemşire oturumu localStorage'da:** Backend'e gönderilmez → **KVKK uyumluluğu** (sistem zaten anonim triaj amaçlı)
8. **Anatomik radyal layout:** Silüet merkezde + ajanlar vücudun gözlemlediği bölgede → **Klinik anlam görsele yansıyor**

---

## 🎬 Sağlık Kontrol Komutları

```bash
# Tüm testler geçiyor mu?
pytest gateway_agents/tests orchestration/tests -v          # 27/27

# Frontend tip kontrolü?
cd frontend && npx tsc --noEmit                              # clean

# Backend canlı mı?
curl http://127.0.0.1:8000/healthz                           # {"status":"ok"}

# SSE stream çalışıyor mu?
curl -N http://127.0.0.1:8000/api/triage/stream &
curl -X POST "http://127.0.0.1:8000/api/triage/demo?scenario=red"
# → Event stream'de heartbeat + 5 agent_observation + decision event'leri görülür
```

---

**Güncelleme tarihi:** 2026-05-16
**Sonraki adım:** Faz 6 (Docker compose) veya Faz 8 (pitch + demo videosu)
