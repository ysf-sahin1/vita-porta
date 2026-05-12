# Vita Porta — Geliştirme İlerlemesi

Bu dosya geliştirme oturumlarının kaldığı yerden devam edebilmesi için tutulur. Her faz: durum, neyin tamamlandığı, neyin kaldığı, ilgili dosyalar ve doğrulama yöntemi.

**Genel durum:** 7/8 faz tamamlandı. Sistem uçtan uca canlı çalışıyor (mock + gerçek kamera). Edge firmware ve Docker infrastructure kaldı.

---

## Faz 0 — Önhazırlık

**Durum:** ✅ Tamamlandı

- NotebookLM hesabı `mendeburlale@gmail.com` ile bağlandı
- "Vita Porta: AI Emergency Triage Assistant" notebook'u oluşturuldu, pitch + teknik rapor yüklendi
- NotebookLM MCP üzerinden `nlm login` ile bu projeye bağlı
- Notebook ID: `d9854800-b703-4b71-919f-6121bb3e05d8`
- İş akışı: proje bağlamı her zaman NotebookLM'den çekilir, kullanıcı tekrar açıklamak zorunda kalmaz

---

## Faz 1 — Monorepo iskeleti + Pydantic şemaları

**Durum:** ✅ Tamamlandı

### Yapılanlar
- Klasör yapısı: `edge_firmware/`, `gateway_agents/`, `orchestration/`, `backend_api/`, `frontend/`, `infrastructure/`, `docs/`
- Kök dosyalar: `README.md`, `.gitignore`, `.env.example`, `pyproject.toml`
- Mevcut iki dokümantasyon (`pitch.md`, `teknik_rapor.md`) `docs/` altına taşındı
- `orchestration/schemas.py` — projenin omurgası:
  - `TriageCategory` enum (red/yellow/green/insufficient) + Türkçe etiket haritası
  - `AgentObservation` — bir ajanın tek bir gözlemi (confidence, summary_tr, signals)
  - `AgentBundle` — üç ajanın gözlem demeti
  - `TriageDecision` — supervisor çıktısı (kategori, gerekçe, ağırlıklar, RAG referansları, gecikme)
  - `TriageEvent` — SSE üzerinden gönderilen wire envelope
- `orchestration/config.py` — pydantic-settings ile env tabanlı yapılandırma

### Dosyalar
```
pyproject.toml
.env.example
.gitignore
README.md
orchestration/__init__.py
orchestration/schemas.py
orchestration/config.py
docs/pitch.md
docs/teknik_rapor.md
```

### Doğrulama
`pip install -e ".[dev]"` ile bağımlılıkların kurulması yeterli.

---

## Faz 2 — Supervisor (LangGraph) + RAG

**Durum:** ✅ Tamamlandı

### Yapılanlar
- `orchestration/prompts/supervisor.py` — ESI tabanlı sistem prompt'u:
  - Tanı koyma yasağı, ilaç önerme yasağı, son söz hemşirede
  - Düşük confidence (<0.5) ise sinyali ağırlığını düşür, "veri yetersiz" bildir
  - Çıktı kesin JSON formatı: `{category, rationale_tr, confidence, per_agent_weights}`
- `orchestration/llm.py` — provider-agnostic LLM client:
  - `AnthropicClient`, `OpenAIClient`, `MockLLMClient` (kural tabanlı fallback)
  - `build_llm_client()` env'e göre uygun istemciyi döner
  - Mock client: teknik raporda belirtilen "LLM API kesintisi → kural tabanlı yedek" gereksinimini karşılar
- `orchestration/supervisor.py` — LangGraph state graph:
  - `retrieve_rag → ask_llm → validate` üç düğümlü pipeline
  - LLM hatasında otomatik olarak MockLLMClient'a fallback
  - `latency_ms` ölçümü ekleniyor
- `orchestration/rag/` — RAG katmanı:
  - `esi_cases.py` — 5 ESI tohum vakası (2 kırmızı, 2 sarı, 1 yeşil)
  - `retriever.py` — `RagRetriever` protocol + `InMemoryRetriever` (default) + `ChromaRetriever` (lazy ChromaDB)
  - `seed.py` — ChromaDB persistent store'a tohum yüklemek için
- `orchestration/demo.py` — üç senaryolu uçtan uca demo (kritik/belirsiz/stabil)

### Dosyalar
```
orchestration/prompts/__init__.py
orchestration/prompts/supervisor.py
orchestration/llm.py
orchestration/supervisor.py
orchestration/demo.py
orchestration/rag/__init__.py
orchestration/rag/esi_cases.py
orchestration/rag/retriever.py
orchestration/rag/seed.py
orchestration/tests/__init__.py
orchestration/tests/test_supervisor.py
```

### Doğrulama
```bash
pytest orchestration/tests -v          # 5/5 pass
python -m orchestration.demo           # Kırmızı/Sarı/Yeşil üç senaryo çıktı verir
```

---

## Faz 3 — FastAPI backend + SSE

**Durum:** ✅ Tamamlandı

### Yapılanlar
- `backend_api/app/event_bus.py` — in-process pub/sub (asyncio.Queue tabanlı, ileride Redis/NATS ile değişir)
- `backend_api/app/main.py`:
  - `GET /healthz`
  - `POST /api/triage/run` — `AgentBundle` alır, `TriageDecision` döner ve SSE bus'a basar
  - `GET /api/triage/stream` — SSE: heartbeat + agent_observation + decision olayları
  - `POST /api/triage/demo?scenario=all|red|yellow|green` — demo bundle'larını sıralı oynatır
- CORS açık (dev için `*`), lifespan ile EventBus + Supervisor singleton

### Dosyalar
```
backend_api/__init__.py
backend_api/app/__init__.py
backend_api/app/event_bus.py
backend_api/app/main.py
```

### Doğrulama
```bash
uvicorn backend_api.app.main:app --reload
curl http://127.0.0.1:8000/healthz
curl -X POST "http://127.0.0.1:8000/api/triage/demo?scenario=red"
```

---

## Faz 4 — Next.js hemşire dashboard'u

**Durum:** ✅ Tamamlandı

### Yapılanlar
- Next.js 14 + React 18 + Tailwind CSS + lucide-react ikonlar
- `frontend/lib/types.ts` — backend ile birebir TypeScript şemaları
- `frontend/lib/api.ts` — `playDemo()`, `streamUrl()`
- `frontend/lib/cn.ts` — clsx + tailwind-merge utility
- Bileşenler:
  - `components/Header.tsx` — başlık + canlı yayın durum noktası
  - `components/TriageCard.tsx` — büyük triaj kartı, kırmızıda pulse-ring animasyonu
  - `components/AgentPanel.tsx` — üç ajan kartı, gözlem yoksa "Veri bekleniyor"
  - `components/HistoryList.tsx` — son 5 karar
  - `components/DemoControls.tsx` — 4 demo butonu
  - `components/useTriageStream.ts` — SSE EventSource hook'u
- `app/page.tsx` — dashboard ana sayfa
- Tailwind theme: özel `triage.red/yellow/green/gray` renkleri + `animate-pulseRing` keyframe

### Dosyalar
```
frontend/package.json
frontend/next.config.js
frontend/tsconfig.json
frontend/postcss.config.js
frontend/tailwind.config.ts
frontend/app/globals.css
frontend/app/layout.tsx
frontend/app/page.tsx
frontend/components/{Header,TriageCard,AgentPanel,DemoControls,HistoryList,useTriageStream}.{tsx,ts}
frontend/lib/{api,cn,types}.ts
```

### Doğrulama
```bash
cd frontend
npm install
npm run build              # temiz derlendi
npm run dev                # http://127.0.0.1:3000
```

**Uçtan uca testi:** Backend açıkken dashboard'da "Üçünü sırayla oynat" butonuna basınca üç hasta sırayla görünür, her ajan kartı dolar, triaj kartı renkli pulse ile gelir, geçmiş listesi büyür.

---

## Faz 5 — Çoklu Modalite Ajanları (gait / skin / respiration / thermal / expression)

**Durum:** 🟡 Kısmen Tamamlandı (Temel ajanlar devrede, yeni ajanlar planlandı)

### Yapılanlar

**Mevcut Görsel Ajanlar** (`gateway_agents/agents/`):
- `base.py` — `AnalysisWindow` dataclass + soyut `Agent` sınıfı
- `gait.py` — `GaitAgent`: MediaPipe Pose, omuz/kalça x-std (sway eşiği 0.025), shoulder asymmetry (eşik 0.04). Confidence = visibility ortalaması (omuz + kalça landmarks). Lazy mediapipe import.
- `skin.py` — `SkinAgent`: OpenCV Haar Cascade yüz tespiti + HSV (S_pale<80, V_pale>120). Dim brightness (V<60) → confidence 0.5 cap. 5 frame örnekleme.
- `respiration.py` — `RespirationAgent`: Sabit göğüs ROI (40% × 30%), frame-diff (threshold 25), smoothed peak detection, BPM kategorileri (yavaş<10, normal 10-22, hızlı>22, düzensiz CV>0.5). Erratic motion (CV>1.0) → confidence 0.2.

### Yapılacaklar (Planlanan Yeni Ajanlar)
- 🔴 `thermal.py` — **Vücut Sıcaklığı Ajanı**: MLX90640 / FLIR Lepton termal kamera verilerini analiz ederek bölgesel sıcaklık istatistikleri (ateş > 37.5 °C veya hipotermi < 35.5 °C) çıkaracak.
- 🔴 `expression.py` — **Yüz İfadesi Ajanı**: MediaPipe Face Mesh ile ağrı, distres, anksiyete ve yüz simetrisi bozukluklarını saptayacak.

**IO kaynakları** (`gateway_agents/io/`):
- `base.py` — `FrameSource` ABC (`fps`, `frames()`, `close()`, context manager)
- `webcam.py` — `WebcamSource`: cv2.VideoCapture (Windows CAP_DSHOW fallback), target_fps + width/height ayarları
- `video_file.py` — `VideoFileSource`: native fps okur, `loop=True` desteği (jüri fallback için)
- `mqtt.py` — `MqttSource`: paho-mqtt `loop_start`, JPEG decode, drop-oldest `Queue(maxsize=64)`. Lazy import.

**Runner** (`gateway_agents/runner.py`):
- `Runner(source, backend_url, window_duration_s=3.0, max_workers=3)`
- `ThreadPoolExecutor` ile üç ajan paralel
- `httpx.Client` ile `POST /api/triage/run` (10s timeout)
- Backend ulaşılamazsa warning + devam (loop crash etmez)
- `run_once()`, `run_forever()`, context manager support
- CLI: `python -m gateway_agents.runner [--webcam IDX | --video PATH | --mqtt]`

**Testler** (`gateway_agents/tests/`):
- `test_agents.py` — 12 test: empty window, black frames, periodic motion, schema conformance (parametrize)
- `test_runner.py` — 6 test: FakeFrameSource + monkeypatched httpx, partial window, backend unreachable, context manager

### Doğrulama

```bash
python -m pytest orchestration/tests gateway_agents/tests -v   # 23/23 ✅ (5 supervisor + 18 gateway)
python -m gateway_agents.runner --webcam 0                      # Canlı kamera demo
python -m gateway_agents.runner --video docs/test_clip.mp4      # Video dosyası fallback
```

### Notlar
- NotebookLM rehberi izlendi: solunum frame-fark ile basitleştirildi, gait + skin için kalibrasyon eşikleri NotebookLM önerilerine uygun.
- Mediapipe `>=0.10.14,<0.10.20` pinli (Windows'ta Solutions API son sürümleri).
- IO sözleşmesi: frame-emitting (`frames() -> Iterator[ndarray]`), runner window'u kendisi batchler.

---

## Faz 6 — Edge firmware + Docker infrastructure

**Durum:** 🔴 Başlanmadı

### Yapılacaklar
- `edge_firmware/vita_porta_cam.ino` — ESP32-CAM Arduino sketch'i:
  - I2S kamera başlat, Wi-Fi bağlan
  - MQTT broker'a (`vitaporta/frames` topic'ine) JPEG frame yayımla
  - WS2812 LED halka opsiyonel: triaj durumu görsel göstergesi (geri kanal)
- `infrastructure/docker-compose.yml`:
  - Mosquitto MQTT broker
  - ChromaDB (opsiyonel; in-memory ile başlanabilir)
  - Backend + Frontend servisleri (production build)
- `infrastructure/mosquitto/mosquitto.conf` — anonymous allow, port 1883

### Notlar
- Hackathon demosu için **fiziksel ESP32-CAM şart değil**. Webcam fallback yeterli. Donanım masa üzerinde "veri toplama konseptini" göstermek için durur.
- Docker compose hackathon submission için bonus puan.

---

## Hızlı başlatma (mevcut durum)

```bash
# 1. Backend
cd "Vita Porta"
python -m uvicorn backend_api.app.main:app --reload

# 2. Frontend (ayrı terminal)
cd "Vita Porta/frontend"
npm run dev

# 3. Tarayıcı
http://127.0.0.1:3000
# "Üçünü sırayla oynat" → kırmızı/sarı/yeşil canlı görünür
```

---

## Mimari özet (mevcut)

```
[mock demo bundle] ──► FastAPI /api/triage/demo
                              │
                              ▼
                       EventBus (asyncio)
                       /              \
                      ▼                ▼
                Supervisor          SSE stream
                (LangGraph)              │
                 │      │                ▼
                 ▼      ▼          Next.js dashboard
            LLM     RAG (in-mem)
          (mock /
         anthropic /
          openai)
```

**Faz 5 tamamlanınca:**
```
Webcam ──► AnalysisWindow ──► [Gait | Skin | Resp] ──► FastAPI /api/triage/run
```

**Faz 6 tamamlanınca:**
```
ESP32-CAM ──MQTT──► Gateway ──► (yukarıdaki akış)
```

---

## Notlar / Karar geçmişi

- **Middle-out yaklaşım** seçildi (NotebookLM tavsiyesi): önce supervisor + mock veriyle çalışan tam akış, sonra gerçek ajanlar takarken yerine geçer.
- **Provider-agnostic LLM**: env değişikliği ile Anthropic/OpenAI/Mock arasında geçiş. Production fallback (mock) teknik raporun "LLM kesintisi → kural tabanlı yedek" gereksinimini karşılar.
- **In-memory RAG** hackathon hızı için default; ChromaRetriever sınıfı yazıldı, sadece env ile etkinleşiyor.
- **Frontend tek bağımlılık dalında** kuruldu — shadcn/ui tam paket yerine Tailwind + lucide-react yeterli görüldü (boyut ve hız için).
