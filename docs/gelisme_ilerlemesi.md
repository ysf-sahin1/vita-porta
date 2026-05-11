# Vita Porta — Geliştirme İlerlemesi

Bu dosya geliştirme oturumlarının kaldığı yerden devam edebilmesi için tutulur. Her faz: durum, neyin tamamlandığı, neyin kaldığı, ilgili dosyalar ve doğrulama yöntemi.

**Genel durum:** 7/8 faz tamamlandı. Sistem **gerçek webcam'den canlı çalışıyor**: 3 görsel ajan paralel işliyor, supervisor karar üretiyor, dashboard SSE ile yayınlıyor. Kalan: edge firmware + Docker compose (Faz 6) ve uçtan uca demo doğrulaması (Faz 7).

**NotebookLM bağlantısı:** Notebook ID `d9854800-b703-4b71-919f-6121bb3e05d8`. Proje bağlamı her oturumda NotebookLM'den çekilir.

---

## Faz 0 — Ön hazırlık · ✅ Tamamlandı
- NotebookLM hesabı `mendeburlale@gmail.com` ile bağlandı.
- "Vita Porta: AI Emergency Triage Assistant" notebook'u oluşturuldu (pitch + teknik rapor yüklü).
- NotebookLM MCP `nlm login` ile bu projeye bağlandı.

## Faz 1 — Monorepo iskeleti · ✅ Tamamlandı
- `pyproject.toml` (Python 3.11+, dependencies pinli).
- `.env.example`, `.gitignore`, `README.md`, `docs/pitch.md`, `docs/teknik_rapor.md`.
- Klasör yapısı: `edge_firmware/`, `gateway_agents/`, `orchestration/`, `backend_api/`, `frontend/`, `infrastructure/`, `docs/`.

## Faz 2 — Orchestration çekirdek · ✅ Tamamlandı
- `orchestration/schemas.py` — Pydantic kontratları: `AgentObservation`, `AgentBundle`, `TriageDecision`, `TriageEvent`, `TriageCategory`.
- `orchestration/prompts/supervisor.py` — ESI protokol prompt'u + RAG snippet enjeksiyonu.
- `orchestration/llm.py` — LLM client soyutlaması; `MockLLMClient` deterministik fallback.
- `orchestration/supervisor.py` — LangGraph `retrieve_rag → ask_llm → validate` zinciri; LLM çağrısı başarısızsa otomatik mock fallback.
- `orchestration/rag/` — ChromaDB tabanlı retriever + ESI vaka örüntüleri seed.
- `orchestration/demo.py` — üç kanonik vaka: `critical_case`, `ambiguous_case`, `stable_case`.

**Doğrulama:** `python -m pytest orchestration/tests -v` → 5/5 PASS.

## Faz 3 — Backend API · ✅ Tamamlandı
- `backend_api/app/main.py` — FastAPI uygulaması.
  - `GET /healthz` — liveness
  - `POST /api/triage/run` — bundle al, karar dön
  - `GET /api/triage/stream` — SSE: ajan gözlemleri + karar yayını
  - `POST /api/triage/demo?scenario=red|yellow|green|all` — demo vakaları tetikle
- `backend_api/app/event_bus.py` — async pub/sub event bus.
- CORS açık, frontend localhost'tan tüketebiliyor.

## Faz 4 — Frontend dashboard · ✅ Tamamlandı
- `frontend/` — Next.js 14, Tailwind, shadcn-stil komponentler.
- `app/page.tsx` — ana sayfa düzeni.
- `components/`:
  - `TriageCard.tsx` — kategori + gerekçe + güven skoru
  - `AgentPanel.tsx` — her ajan için canlı gözlem kartı
  - `DemoControls.tsx` — kırmızı/sarı/yeşil senaryo tetikleyicileri
  - `HistoryList.tsx` — geçmiş kararlar
  - `Header.tsx`, `useTriageStream.ts` — SSE istemcisi
- `lib/api.ts`, `lib/types.ts` — backend kontratlarıyla birebir.

**Doğrulama:** Backend açıkken dashboard'da demo butonlarına basınca üç vaka sırayla görünür, ajan kartları dolar, triaj kartı renkli pulse ile gelir.

## Faz 5 — Görsel ajanlar · ✅ Tamamlandı (2026-05-11)
**Yapılanlar:**
- `gateway_agents/agents/base.py` — `Agent` soyut sınıfı + `AnalysisWindow` dataclass (frames + fps).
- `gateway_agents/agents/gait.py` — **MediaPipe Pose** ile:
  - Sway (gövde yatay salınımı, nose-x std)
  - Symmetry (omuz/kalça y-fark ortalaması)
  - Posture (omuz-kalça yükseklik farkı)
  - Confidence = detection_ratio
- `gateway_agents/agents/skin.py` — **OpenCV HSV/LAB** ile:
  - MediaPipe Face Detection ile yüz ROI; yoksa orta-üst dikdörtgen fallback
  - Pallor = 0.6 × low-saturation + 0.4 × low-redness
- `gateway_agents/agents/respiration.py` — **Frame-fark + tepe sayımı** ile (NotebookLM önerisi: tam optik akış hackathon için aşırı):
  - Göğüs ROI'sinden grayscale absdiff dizisi
  - Mean + 0.3·std eşiği üzerinden tepe sayımı → BPM tahmini
  - Pattern: `normal | hızlı | yavaş | düzensiz | apne_riski`
- `gateway_agents/io/webcam.py` — `WebcamSource` (DSHOW backend, hız sınırlandırma).
- `gateway_agents/io/video_file.py` — `VideoFileSource` (jüri için tekrarlanabilir fallback).
- `gateway_agents/runner.py` — orchestrator:
  - 3 ajanı `ThreadPoolExecutor` üzerinden paralel koşturur (CPU-bound, GIL serbest C kütüphaneleri)
  - `httpx` ile backend `/api/triage/run`'a POST
  - `--dry-run`, `--source webcam|video`, `--window`, `--fps`, `--loop` argümanları
- `gateway_agents/tests/test_agents_synthetic.py` — sentetik siyah/gürültülü frame'lerle birim testler.

**Bağımlılık pinleri:**
- `mediapipe>=0.10.14,<0.10.20` — **kritik:** 0.10.20+ Windows'ta sadece Tasks API; eski Solutions API'sini taşımıyor.
- `httpx>=0.27` eklendi.

**Doğrulama:**
- `python -m pytest gateway_agents/tests -v` → 6/6 PASS.
- `python -m gateway_agents.runner --source webcam --dry-run --window 2.5 --fps 12` → webcam açıldı, 3 ajan paralel çalıştı, bundle üretildi, log'a basıldı.

## Faz 6 — Edge firmware + Docker · 🔴 Başlanmadı
**Yapılacaklar:**
- `edge_firmware/vita_porta_cam.ino` — ESP32-CAM Arduino sketch'i:
  - I2S kamera başlat, Wi-Fi bağlan
  - MQTT broker'a (`vitaporta/frames` topic'i) JPEG frame yayımla
  - WS2812 LED halka (opsiyonel): triaj durumu görsel göstergesi
- `gateway_agents/io/mqtt.py` — `MqttSource` (ESP32'den MQTT akışı).
- `infrastructure/docker-compose.yml`:
  - Mosquitto MQTT broker
  - ChromaDB (opsiyonel; in-memory ile başlanabilir)
  - Backend + Frontend (production build)
- `infrastructure/mosquitto/mosquitto.conf` — anonymous allow, port 1883.

**Not:** Hackathon demosu için fiziksel ESP32-CAM şart değil. Webcam fallback yeterli. Donanım masa üzerinde "veri toplama konseptini" göstermek için durur. Docker compose hackathon submission için bonus puan.

## Faz 7 — Uçtan uca canlı demo doğrulaması · 🟡 Yarıda
**Yapıldı:**
- Webcam → 3 ajan → bundle akışı doğrulandı (`--dry-run` ile).

**Kalan:**
- Backend açıkken `runner` (dry-run'sız) ile webcam üzerinden gerçek POST.
- Frontend dashboard'da canlı kararın renkli pulse ile geldiğini görmek.
- Sallanarak, solgun görünmeye çalışarak, derin nefes alarak farklı karar varyasyonlarını test etmek.
- "Veri yetersiz" durumlarının (örn. kameradan çıkıldığında) dashboard'da doğru gösterildiğini doğrulamak.

## Faz 8 — Pitch + jüri sunumu polish · 🔴 Başlanmadı
- `docs/pitch.md` revizyonu (sunum scriptiyle birlikte).
- Demo videosu (yedek senaryo: webcam müsait değilse `VideoFileSource` ile önceden çekilmiş 5-10 saniyelik test videoları).
- ESP32-CAM fiziksel prop (lehimleme + kasa) — jüri masasında "veri toplama konsepti" objesi.

---

## Açık kararlar
- **Ajan sayısı:** Hackathon kapsamında **3 ajan** (yürüyüş, ten rengi, solunum). `docs/teknik_rapor.md` şu an 5 ajandan bahsediyor (termal + yüz ifadesi); NotebookLM kaynaklarındaki versiyon 3 ajan. Hizalama beklemede.
- **LLM provider:** `OPENAI_API_KEY` veya `ANTHROPIC_API_KEY` yoksa `MockLLMClient` otomatik devreye girer. Demo için API key olsa daha zengin gerekçe çıkar.

## Çalıştırma reçetesi
```bash
# Bağımlılıklar (mediapipe 0.10.14 pinli)
pip install -e ".[dev]"

# Testler
python -m pytest

# Backend (terminal 1)
python -m uvicorn backend_api.app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (terminal 2)
cd frontend && npm install && npm run dev

# Gateway runner (terminal 3) — gerçek webcam → backend → dashboard
python -m gateway_agents.runner --source webcam --window 3.0 --fps 15

# veya kuru deneme (backend'e POST etmeden):
python -m gateway_agents.runner --source webcam --dry-run

# veya test videosu üzerinden:
python -m gateway_agents.runner --source video --path data/demo/red.mp4 --loop
```
