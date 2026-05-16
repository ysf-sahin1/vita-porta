# Vita Porta — Geliştirme İlerlemesi

Bu dosya geliştirme oturumlarının kaldığı yerden devam edebilmesi için tutulur. Her faz: durum, neyin tamamlandığı, neyin kaldığı, ilgili dosyalar ve doğrulama yöntemi.

**Genel durum (2026-05-17):**
- ✅ **Faz 0–5** tamamlandı (5 ajan: gait / skin / respiration / thermal / expression)
- ✅ **Faz 4.5** (Health-OS frontend redesign) tamamlandı
- ✅ **Faz 4.6** (hemşire giriş ekranı + anatomik radyal layout) tamamlandı
- ✅ **Faz 5.5** (origin/main Phase 5 rewrite ile birleşme) tamamlandı
- ✅ **Faz 5.6** (yüz ifadesi ajanı eklenmesiyle Faz 5'in resmi kapanışı) tamamlandı
- ✅ **Faz 5.7** (hemşire verdict persistance + mesai history + RAG deneyim katmanı) tamamlandı
- ✅ **Faz 7** (uçtan uca canlı demo doğrulaması) tamamlandı
- 🟡 **Faz 6** Aşama B (ESP32-CAM canlı MJPEG yayını) tamamlandı; gateway entegrasyonu + MQTT/Docker kaldı
- 🔴 **Faz 8** (pitch polish + demo videosu yedek) başlanmadı

Sistem **gerçek webcam'den canlı çalışıyor**: 5 görsel ajan paralel işliyor, supervisor karar üretiyor, dashboard SSE ile yayınlıyor. Webcam yoksa demo butonlarıyla 3 senaryo (kırmızı/sarı/yeşil) tetiklenebilir. ESP32-CAM ayrı bir yayın kaynağı olarak da hazır (HTTP/MJPEG; gateway adapter'ı eklenecek).

Detaylı tur-tur değişiklik kayıtları için `docs/gelisme_ilerlemesi.md` dosyasına bakın.

---

## Faz 0 — Önhazırlık · ✅ Tamamlandı

- NotebookLM hesabı `mendeburlale@gmail.com` ile bağlandı
- "Vita Porta: AI Emergency Triage Assistant" notebook'u oluşturuldu, pitch + teknik rapor yüklendi
- NotebookLM MCP üzerinden `nlm login` ile bu projeye bağlı
- Notebook ID: `d9854800-b703-4b71-919f-6121bb3e05d8`

---

## Faz 1 — Monorepo iskeleti + Pydantic şemaları · ✅ Tamamlandı

- Klasör yapısı: `edge_firmware/`, `gateway_agents/`, `orchestration/`, `backend_api/`, `frontend/`, `infrastructure/`, `docs/`
- Kök dosyalar: `README.md`, `.gitignore`, `.env.example`, `pyproject.toml`
- `orchestration/schemas.py` — projenin omurgası:
  - `TriageCategory` enum (red/yellow/green/insufficient) + Türkçe etiket haritası
  - `AgentObservation` — bir ajanın tek gözlemi (agent, confidence, summary_tr, signals)
  - `AgentBundle` — **5 ajanın** gözlem demeti (gait / skin / respiration / thermal / expression)
  - `TriageDecision` — supervisor çıktısı (kategori, gerekçe, ağırlıklar, RAG referansları, gecikme)
  - `TriageEvent` — SSE üzerinden gönderilen wire envelope
- `orchestration/config.py` — pydantic-settings ile env tabanlı yapılandırma

**Doğrulama:** `pip install -e ".[dev]"` ile bağımlılıkların kurulması yeterli.

---

## Faz 2 — Supervisor (LangGraph) + RAG · ✅ Tamamlandı

- `orchestration/prompts/supervisor.py` — ESI tabanlı sistem prompt'u:
  - 5 ajan için yazıldı (yürüyüş / ten rengi / solunum / termal / yüz ifadesi)
  - Tanı koyma yasağı, ilaç önerme yasağı, son söz hemşirede
  - Düşük confidence (<0.5) ise sinyali ağırlığını düşür, "veri yetersiz" bildir
  - Termal proxy modu özel kuralları + Expression özel kuralları (ağrı / bilinç / felç şüphesi)
  - Çıktı kesin JSON formatı: `{category, rationale_tr, confidence, per_agent_weights}`
- `orchestration/llm.py` — provider-agnostic LLM client:
  - `AnthropicClient`, `OpenAIClient`, `MockLLMClient` (kural tabanlı fallback)
  - MockLLM tüm 5 ajan için weight + flag mantığı içeriyor; eski demo vocab + yeni live-agent vocab birlikte destekleniyor
- `orchestration/supervisor.py` — LangGraph state graph:
  - `retrieve_rag → ask_llm → validate` üç düğümlü pipeline
  - LLM hatasında otomatik MockLLMClient fallback
  - `latency_ms` ölçümü ekleniyor
- `orchestration/rag/` — RAG katmanı:
  - `esi_cases.py` — 5 ESI tohum vakası
  - `retriever.py` — `RagRetriever` protocol + `InMemoryRetriever` (default) + `ChromaRetriever` (lazy)
- `orchestration/demo.py` — üç senaryolu uçtan uca demo (kritik/belirsiz/stabil); 3 senaryoya da thermal + expression observations eklendi

**Doğrulama:** `pytest orchestration/tests -v` → 5/5 pass.

---

## Faz 3 — FastAPI backend + SSE · ✅ Tamamlandı

- `backend_api/app/event_bus.py` — in-process pub/sub (asyncio.Queue tabanlı)
- `backend_api/app/main.py`:
  - `GET /healthz`
  - `POST /api/triage/run` — `AgentBundle` alır, `TriageDecision` döner ve SSE bus'a basar
  - `GET /api/triage/stream` — SSE: heartbeat + agent_observation + decision olayları
  - `POST /api/triage/demo?scenario=all|red|yellow|green` — demo bundle'larını sıralı oynatır
- CORS açık (dev için `*`), lifespan ile EventBus + Supervisor singleton

**Doğrulama:**
```bash
uvicorn backend_api.app.main:app --reload
curl http://127.0.0.1:8000/healthz                                # {"status":"ok"}
curl -X POST "http://127.0.0.1:8000/api/triage/demo?scenario=red" # 200
```

---

## Faz 4 — Next.js hemşire dashboard'u · ✅ Tamamlandı

- Next.js 14 + React 18 + Tailwind CSS + lucide-react ikonlar
- `frontend/lib/{types,api,cn}.ts` — backend ile birebir şemalar, fetch helpers, tailwind merge utility
- Bileşenler: `Header`, `TriageCard`, `AgentPanel`, `HistoryList`, `DemoControls`, `useTriageStream`
- `app/page.tsx` — dashboard ana sayfa
- Tailwind theme: özel `triage.red/yellow/green/gray` renkleri + `animate-pulseRing`

**Faz 4.5 (Health-OS redesign — 2026-05-14):** Sayfa komple yenilendi:
- Inter font (`next/font/google`), cross-platform tutarlı render
- 16px base size, gradient zemin + glassmorphism kartlar (`bg-white/70 backdrop-blur-xl`)
- 2-kolon wide layout (sol triage+ajanlar, sağ history timeline)
- Yeni komponentler: `Tooltip`, `PostureSilhouette`, `NurseVerdict`, `HistoryDetailModal`
- `lib/agentReasons.ts` + `lib/signalLabels.ts` — Türkçe sinyal etiketleri, info/warn/error reason pill'leri
- Hemşire iş akışı: ✓ Onayla / ✗ Reddet / ✎ Değiştir + verdict map (paylaşılan state, ChromaDB persistance henüz wire yok)
- History tıklanabilir → modal'da o anki 4 ajan snapshot'ı + verdict
- Tooltip içerikleri: Güven vs Ağırlık ayrımı net şekilde anlatıldı

**Faz 4.6 (Login + Anatomik Radyal — 2026-05-16):**
- Hemşire giriş ekranı: `lib/session.ts` (localStorage, KVKK-uyumlu), `LoginScreen`, `SessionGate` (React Context). Ad / Soyad / Hastane Adı zorunlu, min 2 karakter, validation. Bir kere girildiğinde hatırlanır.
- Header'da hemşire ad-soyad + hastane satırı + "Çıkış" butonu (canlı saat ve status pilleri korundu)
- **AnatomicalRadial.tsx** — yeni `xl+` layout:
  - Silüet ortada (çöp adam, kategori rengiyle outline + `silhouettePulse` dış halka)
  - 5 ajan kartı vücudun gözlemlediği bölgede absolute positioned:
    - Expression sol üst (kafa), Thermal sağ üst (alın)
    - Skin sol orta (yanak), Respiration sağ orta (göğüs)
    - Gait orta alt (bacaklar)
  - SVG bağlantı çizgileri ajan rengiyle dashed (`lineFlow` animasyonu)
  - Silüet dinamik: gait sallantı → `silhouetteSway` rotate, asimetri → omuz kayık, solunum → göğüs `chestBreathe` pulse
  - `xl` altında düz grid'e fallback (mobile/tablet)
- `tailwind.config.ts` — 4 yeni animasyon (`lineFlow`, `silhouettePulse`, `silhouetteSway`, `chestBreathe`)

**Doğrulama:**
```bash
cd frontend && npm install && npm run dev   # http://127.0.0.1:3000
npx tsc --noEmit                            # clean
```

**Uçtan uca test:** Login ekranı → giriş → dashboard. Backend açıkken "Demo senaryoları" → "Üçünü sırayla oynat" → 3 hasta sırayla görünür, 5 ajan kartı dolar, silüet kategoriye göre pulse atar, geçmiş listesi büyür.

---

## Faz 5 — 5 görsel ajan (gait / skin / respiration / thermal / expression) · ✅ Tamamlandı

**Ana yapı** (`gateway_agents/agents/`):
- `base.py` — `AnalysisWindow` dataclass + soyut `Agent` sınıfı
- `gait.py` — `GaitAgent`: MediaPipe Pose, omuz/kalça x-std (sway eşiği 0.025), shoulder asymmetry (eşik 0.04). Confidence = visibility ortalaması.
- `skin.py` — `SkinAgent`: OpenCV Haar Cascade yüz tespiti + HSV (`skin_tone` ∈ {solgun, belirsiz, normal}). Dim brightness → confidence cap.
- `respiration.py` — `RespirationAgent`: Sabit göğüs ROI, frame-diff, peak detection. `breathing_pattern` ∈ {hızlı, yavaş, düzensiz, apne_riski, normal}.
- `thermal.py` — `ThermalAgent` (2026-05-13): MediaPipe Face Detection ile yüz ROI + LAB renk uzayı warmth indeksi → tahmini °C. `sensor_type="rgb_proxy"` ile confidence max 0.60 (gerçek MLX90640/FLIR bağlanırsa 0.95).
- `expression.py` — `ExpressionAgent` (2026-05-16): **MediaPipe Face Mesh (468 landmark)** geometrik kural-tabanlı:
  - EAR (Eye Aspect Ratio) → `eye_openness`, `consciousness_hint`
  - PSPI'ın basitleştirilmesi (kaş içe-çatma + göz kısma) → `pain_score`, `expression_state`
  - 6 sol-sağ landmark çifti sapması → `face_asymmetry` (FAST/felç şüphesi girdisi)
  - `sensor_type="geometric_proxy"`, confidence max 0.55

**IO kaynakları** (`gateway_agents/io/`):
- `base.py` — `FrameSource` ABC
- `webcam.py` — `WebcamSource`: cv2.VideoCapture (Windows CAP_DSHOW fallback, macOS AVFoundation default). Resilient reconnect.
- `video_file.py` — `VideoFileSource`: native fps okur, `loop=True` desteği
- `mqtt.py` — `MqttSource`: paho-mqtt `loop_start`, JPEG decode (lazy import)

**Runner** (`gateway_agents/runner.py`):
- `Runner(source, backend_url, window_duration_s=3.0, max_workers=5)`
- `ThreadPoolExecutor` ile **5 ajan paralel**
- `httpx.Client` ile `POST /api/triage/run` (10s timeout)
- Backend ulaşılamazsa warning + devam (loop crash etmez)
- CLI: `python -m gateway_agents.runner [--webcam IDX | --video PATH | --mqtt]`

**Testler** (`gateway_agents/tests/`):
- `test_agents.py` — TestGaitAgent (3) + TestSkinAgent (3) + TestRespirationAgent (3) + TestExpressionAgent (3) + schema conformance (4 parametre)
- `test_runner.py` — 6 test: FakeFrameSource + monkeypatched httpx, 5-observation beklentisi, partial window, backend unreachable, context manager

**Doğrulama:**
```bash
python -m pytest gateway_agents/tests orchestration/tests -v   # 27/27 ✅
python -m gateway_agents.runner --webcam 0                      # Canlı kamera demo
python -m gateway_agents.runner --video docs/test_clip.mp4      # Video dosyası fallback
```

**Bağımlılık pinleri:**
- `mediapipe==0.10.18` — **kritik:** 0.10.20+ Solutions API'sini kaldırdı
- `httpx>=0.27`

---

## Faz 6 — Edge firmware + Docker infrastructure · 🟡 Kısmen Tamamlandı

### Yapılanlar — Aşama B: ESP32-CAM canlı MJPEG yayını (2026-05-17)

`edge_firmware/vita_porta_cam/vita_porta_cam.ino` — AI-Thinker ESP32-CAM için canlı video yayını:
- Wi-Fi STA bağlantısı (kart açılırken bağlanır, IP Serial Monitor'da yazar)
- İki HTTP sunucu çalışıyor:
  - **Port 80** (Arduino `WebServer`): `/` canlı dashboard, `/capture` tek JPEG, `/info` JSON istatistik (FPS, RSSI, heap, uptime, kare boyutu)
  - **Port 81** (`esp_http_server`): `/stream` MJPEG akışı (`multipart/x-mixed-replace`) — tek TCP bağlantısı sürekli açık, IP kameralarla aynı protokol
- Tarayıcıda canlı önizleme + her saniye yenilenen metrikler
- Serial Monitor'da her 5 sn `[STATS] FPS=... heap=... RSSI=...` raporu

### Donanım için ampirik en iyi ayarlar (Robocombo AI-Thinker klonu, OV2640, 4MB PSRAM)

Bu klon kartın PSRAM'i muhtemelen 40 MHz QSPI'de takılı (resmi AI-Thinker 80 MHz). Yapılan ölçümlerle:

| Parametre | Değer | Neden |
|-----------|-------|-------|
| `xclk_freq_hz` | 16 MHz | 20 MHz'de OV2640 kararsız, FPS düşüyor |
| `frame_size` | FRAMESIZE_VGA (640×480) | MediaPipe Face Mesh + Pose için minimum |
| `jpeg_quality` | 12 | 14+ DSP'de tıkanma (FPS çöküyor) |
| `fb_count` | 1 | 2'de PSRAM bandwidth çakışıyor (FPS 10→3) |
| `grab_mode` | CAMERA_GRAB_WHEN_EMPTY | Kanonik CameraWebServer ile aynı |

**Ölçülen performans:** VGA 640×480 @ ~10 FPS, kare boyutu 25-35 KB, RSSI -39 dBm, heap 140-152 KB stabil. 3 sn pencere = 30 kare → MediaPipe Pose, Face Mesh ve optical flow respiration için yeterli.

### Aşama A — KY-016 RGB LED diagnostik (ertelendi)

KY-016 RGB LED'in triaj durum göstergesi olarak kullanılması için diagnostik kod yazıldı (IO13/14/15 + GND, flash LED IO4 GPIO testi). Donanım üzerinde LED tek başına ve ESP32 GPIO çıkışları sağlam olmasına rağmen breadboard üzerinden bağlantı kurulamadı (kablo/breadboard temas sorunu olduğu kuvvetle muhtemel). Vision agent entegrasyonu öncelikli olduğu için LED ertelendi; ileride **WS2812 LED halka** veya KY-016 ile triaj göstergesi tekrar ele alınacak.

### Dosyalar
```
edge_firmware/vita_porta_cam/vita_porta_cam.ino
docs/Ekran görüntüsü 2026-05-16 213536.png   (ESP32-CAM breadboard bağlantı referansı)
```

### Doğrulama

```bash
# Arduino IDE'de yükle (Board: AI Thinker ESP32-CAM, PSRAM auto-enabled).
# Serial Monitor (115200 baud) açıkken IP'yi gör, sonra:

curl http://<ESP32_IP>/info                  # JSON istatistik
# Tarayıcıda:
http://<ESP32_IP>/                           # canlı dashboard + metrikler
http://<ESP32_IP>:81/stream                  # ham MJPEG akışı (cv2.VideoCapture buradan tüketir)
```

### Yapılacaklar
- 🔴 `gateway_agents/io/esp_cam.py` — MJPEG stream consumer: `cv2.VideoCapture("http://<IP>:81/stream")` ile `FrameSource` sözleşmesini sağlar. Runner'a `--esp <IP>` parametresi eklenir.
- 🔴 `infrastructure/docker-compose.yml`:
  - Mosquitto MQTT broker (alternatif transport olarak)
  - ChromaDB (opsiyonel; in-memory ile başlanabilir)
  - Backend + Frontend servisleri (production build)
- 🔴 `infrastructure/mosquitto/mosquitto.conf` — anonymous allow, port 1883
- 🔴 `edge_firmware/README.md` — Wi-Fi config talimatı, Arduino IDE board ayarları, upload protokolü
- 🟡 LED halka (WS2812 veya KY-016) triaj göstergesi (öncelik düşük; kapı durumu UI'da zaten görünüyor)

### Notlar
- **Wi-Fi credentials repo'ya commit edilmiyor.** Sketch'te placeholder bırakıldı (`WIFI_ADIN_BURAYA`, `WIFI_SIFRESI_BURAYA`); geliştirme makinasında manuel doldurulur. İleride `secrets.h` + `.gitignore` ile düzgün ayrılacak.
- AI-Thinker klon kartlarda VGA için 10 FPS tavanı; gerçek üreticilerde (Espressif resmi, M5Stack) 18-25 FPS bekleniyor. Hackathon donanımı için kabul edilebilir.
- ESP32-CAM şart değil — webcam fallback (`WebcamSource`) çalışmaya devam ediyor. Hackathon demosu için fiziksel ESP32-CAM zorunlu değil; donanım masa üzerinde "veri toplama konseptini" göstermek için durur.
- Docker compose hackathon submission için bonus puan.

---

## Faz 7 — Uçtan uca canlı demo doğrulaması · ✅ Tamamlandı (2026-05-13)

- Backend + Frontend + Webcam runner üçü birden canlı çalıştırıldı
- Webcam → 5 ajan (gait/skin/respiration/thermal/expression) → bundle → FastAPI POST → SSE → dashboard akışı doğrulandı
- Dashboard'da her ~3.5 sn'de yeni triaj kararı (green) göründü
- "Veri yetersiz" (insufficient) durumu kameradan çıkıldığında otomatik görüldü
- Webcam yeniden bağlanma (resilient loop) başarıyla çalıştı

**Kalan (Faz 8'e taşındı):**
- Farklı vücut pozisyonları (sallanma, eğilme, hızlı nefes, ağrı mimiği) ile sarı/kırmızı kararları tetikleme testi
- Demo videosu kaydı (yedek senaryo)

---

## Faz 8 — Pitch + jüri sunumu polish · 🔴 Başlanmadı

- `docs/pitch.md` revizyonu (sunum scriptiyle birlikte)
- Demo videosu (yedek senaryo: webcam müsait değilse `VideoFileSource` ile önceden çekilmiş 5-10 saniyelik test videoları)
- ESP32-CAM fiziksel prop (lehimleme + kasa) — jüri masasında "veri toplama konsepti" objesi
- `docs/teknik_rapor.md` zaten 5 ajandan bahsediyor; artık kodla birebir hizalı (önceki "hizalama beklemede" notu kapandı)

---

## Hızlı başlatma (mevcut durum)

```bash
# Bağımlılıklar (mediapipe 0.10.18 pinli — kritik)
pip install -e ".[dev]"

# Testler
python -m pytest                                # 27/27 pass

# Backend (terminal 1)
python -m uvicorn backend_api.app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (terminal 2)
cd frontend && npm install && npm run dev

# Gateway runner (terminal 3) — gerçek webcam → backend → dashboard
python -m gateway_agents.runner --webcam 0 --window 3.0

# veya test videosu üzerinden:
python -m gateway_agents.runner --video data/demo/red.mp4 --loop

# veya MQTT (ESP32-CAM hazır olduğunda):
python -m gateway_agents.runner --mqtt
```

İlk açılışta hemşire giriş ekranı çıkar (Ad / Soyad / Hastane). localStorage'da hatırlanır, bir sonraki ziyarette doğrudan dashboard gelir. Sağ üstteki "Çıkış" ile oturum sonlandırılır.

---

## Mimari özet (mevcut)

```
Webcam / ESP32-CAM ──► AnalysisWindow (3sn pencere)
                              │
                              │ paralel
                              ▼
            [Gait | Skin | Respiration | Thermal | Expression]
                              │
                              │ AgentBundle (5 ajan)
                              ▼
                FastAPI /api/triage/run
                              │
                              ▼
                       EventBus (asyncio)
                       /              \
                      ▼                ▼
                Supervisor          SSE stream
                (LangGraph)              │
                 │      │                ▼
                 ▼      ▼          Next.js dashboard
            LLM     RAG (in-mem)   (hemşire girişli)
          (mock /
         anthropic /
          openai)
```

---

## Açık takipler (Faz 5 dışı, ilerleyen turlara)

- ✅ ~~Backend `/api/triage/feedback` endpoint'i~~ → **Faz 5.7'de tamamlandı** (JSON store, mesai history, supervisor RAG entegrasyonu).
- **3sn "Analiz ediliyor…" pencere animasyonu** — observation→decision arası halka, demo wow-factor için planlıydı.
- **Termal `ThermalSource`** — MLX90640/FLIR Lepton bağlanırsa proxy modundan çıkış adapter'ı.
- **Eğitilmiş ağrı/mimik modeli** — expression ajanı geometrik proxy modunda; PSPI veya DeepFace pain model pilot fazına bırakıldı.

---

## Karar geçmişi

- **Middle-out yaklaşım** (NotebookLM tavsiyesi): önce supervisor + mock veriyle çalışan tam akış, sonra gerçek ajanlar takarken yerine geçer.
- **Provider-agnostic LLM**: env değişikliği ile Anthropic/OpenAI/Mock arasında geçiş. Production fallback (mock) teknik raporun "LLM kesintisi → kural tabanlı yedek" gereksinimini karşılar.
- **In-memory RAG** hackathon hızı için default; ChromaRetriever sınıfı yazıldı, sadece env ile etkinleşiyor.
- **Frontend tek bağımlılık dalında** kuruldu — shadcn/ui tam paket yerine Tailwind + lucide-react yeterli görüldü.
- **Expression ajanı geometrik proxy modu**: Eğitilmiş PSPI classifier yerine MediaPipe Face Mesh + kural-tabanlı analiz. Hackathon için hızlı, deterministik, açıklanabilir. Confidence ≤0.55 ile transparanlık sağlandı.
- **Webcam fallback**: Hackathon jürisine ESP32-CAM olmadan canlı demo → risk azaltma.
- **Hemşire oturumu sadece istemci tarafında (localStorage)**: KVKK uyumluluğu için ad-soyad ve hastane verisi backend'e gönderilmez; sistem zaten anonim triaj amaçlı.
