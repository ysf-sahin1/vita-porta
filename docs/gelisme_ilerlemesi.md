# Vita Porta — Geliştirme İlerlemesi

Bu dosya geliştirme oturumlarının kaldığı yerden devam edebilmesi için tutulur. Her faz: durum, neyin tamamlandığı, neyin kaldığı, ilgili dosyalar ve doğrulama yöntemi.

**Genel durum:** 7.5/8 faz tamamlandı. Sistem **gerçek webcam'den canlı çalışıyor**: 4 görsel ajan (yürüyüş, ten rengi, solunum, termal) paralel işliyor, supervisor karar üretiyor, dashboard SSE ile yayınlıyor. **mertmrz branch'i ile origin/main (Yusuf'un Phase 5 rewrite'ı) birleştirildi ve tüm değişiklikler ana projeye (ysf-sahin1/vita-porta) push'landı** (2026-05-13). Kalan: edge firmware + Docker compose (Faz 6) ve pitch polish (Faz 8).

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

## Faz 5 — Görsel ajanlar · ✅ Tamamlandı + Termal Ajan Eklendi (2026-05-13)
**Yapılanlar:**
- `gateway_agents/agents/base.py` — `Agent` soyut sınıfı + `AnalysisWindow` dataclass (frames + fps).
- `gateway_agents/agents/gait.py` — **MediaPipe Pose** ile:
  - Sway (gövde yatay salınımı, nose-x std)
  - Symmetry (omuz/kalça y-fark ortalaması)
  - Posture (omuz-kalça yükseklik farkı)
  - Confidence = detection_ratio
  - **Bug düzeltme (2026-05-13):** import bloğunda indentation hatası giderildi.
- `gateway_agents/agents/skin.py` — **OpenCV HSV/LAB** ile:
  - MediaPipe Face Detection ile yüz ROI; yoksa orta-üst dikdörtgen fallback
  - Pallor = 0.6 × low-saturation + 0.4 × low-redness
- `gateway_agents/agents/respiration.py` — **Frame-fark + tepe sayımı** ile:
  - Göğüs ROI'sinden grayscale absdiff dizisi
  - Mean + 0.3·std eşiği üzerinden tepe sayımı → BPM tahmini
  - Pattern: `normal | hızlı | yavaş | düzensiz | apne_riski`
- `gateway_agents/agents/thermal.py` — **YENİ (2026-05-13)** — RGB proxy ile vücut sıcaklığı tahmini:
  - MediaPipe Face Detection ile yüz ROI; yoksa orta-üst dikdörtgen fallback
  - LAB renk uzayı: a kanalı (kırmızılık) + b kanalı (sıcaklık tonu) → warmth indeksi
  - Warmth → tahmini °C: nötr ten = 36.5°C, ±1 birim warmth = ±2.5°C sapma
  - Çıktı sinyalleri: `temp_estimate_c`, `fever_flag` (>37.5°C), `hypothermia_flag` (<35.5°C), `warmth_score`, `sensor_type="rgb_proxy"`
  - Confidence maks. 0.60 (proxy modu; gerçek MLX90640/FLIR bağlandığında 0.95'e çıkacak)
- `gateway_agents/io/webcam.py` — **macOS uyumlu (2026-05-13):**
  - `CAP_DSHOW` (Windows-only backend) kaldırıldı
  - Frame okuma başarısız olunca generator'ı sonlandırmak yerine kamerayı yeniden açan resilient döngü eklendi
- `gateway_agents/io/video_file.py` — `VideoFileSource` (jüri için tekrarlanabilir fallback).
- `gateway_agents/runner.py` — orchestrator:
  - **4 ajanı** `ThreadPoolExecutor(max_workers=4)` üzerinden paralel koşturur
  - `httpx` ile backend `/api/triage/run`'a POST
  - `--dry-run`, `--source webcam|video`, `--window`, `--fps`, `--loop` argümanları
- `gateway_agents/tests/test_agents_synthetic.py` — sentetik siyah/gürültülü frame'lerle birim testler.

**Schema ve karar zinciri güncellemeleri (2026-05-13):**
- `orchestration/schemas.py`:
  - `AgentObservation.agent` Literal'ine `"thermal"` eklendi
  - `AgentBundle`'a `thermal: AgentObservation | None` alanı eklendi
  - `observations()` metodu thermal'i de döndürüyor
- `orchestration/prompts/supervisor.py`:
  - Sistem prompt'u 4 ajan için güncellendi
  - Termal özel kurallar: `fever_flag + başka anormallik → yellow`, `hypothermia + postür/solunum → red`
  - `per_agent_weights` ve `missing_agents` kontrolüne thermal eklendi
- `orchestration/llm.py` (MockLLMClient):
  - `weights` sözlüğü 4 ajan için (thermal dahil)
  - `fever_flag=True` → yellow_flag (proxy modunda tek başına kırmızıya çekmez)
  - `hypothermia_flag=True` → başka anormallikle birlikte red, tek başına yellow
  - Gerekçeye `[RGB proxy]` notu otomatik eklenir (jüri için şeffaflık)
  - **Bonus düzeltme:** Eski `pallor:bool` yerine gerçek ajan çıktısı `pallor_score:float` desteği; eski `rate_bpm` yerine `breath_per_minute` + pattern (`hızlı`, `apne_riski` vb.) desteği eklendi. Bu sayede MockLLM gerçek ajan sinyallerini doğru ağırlıklandırıyor.
- `frontend/lib/types.ts`: `AgentObservation.agent` tipine `"thermal"` eklendi
- `frontend/components/AgentPanel.tsx`: Turuncu/termometre ikonlu 4. kart; grid `md:grid-cols-4`'e geçti

**Bağımlılık pinleri:**
- `mediapipe==0.10.18` — **kritik:** 0.10.20+ Solutions API'sini kaldırdı; .venv'de 0.10.18 pinli.
- `httpx>=0.27` eklendi.

**Doğrulama:**
- `python -m pytest gateway_agents/tests orchestration/tests -v` → **11/11 PASS**.
- Webcam runner canlı çalıştı: backend'e POST, dashboard'da kararlar göründü (2026-05-13 oturumu).

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

## Faz 7 — Uçtan uca canlı demo doğrulaması · ✅ Tamamlandı (2026-05-13)
**Yapıldı:**
- Backend + Frontend + Webcam runner üçü birden canlı çalıştırıldı.
- Webcam → 4 ajan (gait/skin/respiration/thermal) → bundle → FastAPI POST → SSE → dashboard akışı doğrulandı.
- Dashboard'da her ~3.5 sn'de yeni triaj kararı (green) göründü.
- "Veri yetersiz" (insufficient) durumu kameradan çıkıldığında otomatik görüldü.
- Webcam yeniden bağlanma (resilient loop) başarıyla çalıştı.

**Kalan (Faz 8'e taşındı):**
- Farklı vücut pozisyonları (sallanma, eğilme, hızlı nefes) ile sarı/kırmızı kararları tetikleme testi.
- Demo videosu kaydı (yedek senaryo).

## Faz 8 — Pitch + jüri sunumu polish · 🔴 Başlanmadı
- `docs/pitch.md` revizyonu (sunum scriptiyle birlikte).
- Demo videosu (yedek senaryo: webcam müsait değilse `VideoFileSource` ile önceden çekilmiş 5-10 saniyelik test videoları).
- ESP32-CAM fiziksel prop (lehimleme + kasa) — jüri masasında "veri toplama konsepti" objesi.

## Faz 5.5 — origin/main ile birleşme + bug fix turu · ✅ Tamamlandı (2026-05-13 öğleden sonra)

**Bağlam:** `mertmrz` branch'i (termal ajan + macOS fix'leri) origin/main (Yusuf'un Phase 5 rewrite'ı) ile diverj etmişti. Yusuf'un commit'i `gait/skin/respiration/runner/io` üzerinde kapsamlı bir refactor getirmişti (sync Runner, `frames()`-tabanlı FrameSource, MQTT source, kapsamlı testler). Bu turda iki branch birleştirildi, integration bug'ları kapatıldı, ana projeye push'landı.

**Bug fix turu (commit `9ddf0cd`):**
- `gateway_agents/runner.py` — `--dry-run` log satırı sessizce thermal'i atlıyordu, eklendi.
- `frontend/components/TriageCard.tsx` — Per-agent ağırlık paneli 3 sütundu, thermal weight veride vardı ama hiç gösterilmiyordu. 4 sütuna (`grid-cols-2 md:grid-cols-4`) geçirildi.
- `frontend/components/useTriageStream.ts` — `PatientState.observations` tipi hâlâ 3 ajanlıydı (`gait | skin | respiration`), thermal eklendi.
- `orchestration/llm.py`, `orchestration/prompts/supervisor.py`, `orchestration/schemas.py` — Termal eklemesinden kalan ruff E501 (long line) ihlalleri temizlendi.

**Merge ve conflict çözümleri (commit `a099d15`):**
- `gateway_agents/io/webcam.py` çakışması → Yusuf'un sürümü tercih edildi. Önce varsayılan backend (macOS'ta AVFoundation) denenip ardından sadece Windows fallback olarak `CAP_DSHOW`'a düşüyor; macOS'ta zaten çalışıyor. Ayrıca canlı önizleme (`cv2.imshow`) eklemesi geliştiriciye kameranın gördüğünü anında izleme imkânı veriyor.
- `gateway_agents/runner.py` çakışması → Yusuf'un sync `Runner` mimarisi (context manager + `run_once`/`run_forever`) baz alındı, üzerine ThermalAgent paralel pipeline'a eklendi (`max_workers` 3→4, `_build_bundle` 4 ajan, `close()` thermal'i de kapatıyor).
- **Sinyal sözlüğü uyumsuzluğu — sessiz integration bug** → Yusuf'un yeni ajanları farklı sinyal isimleri çıkartıyor: `skin_tone="solgun"` (eski `pallor:bool`), `sway_detected` (eski `sway_score`), `breathing_pattern`/`breaths_per_minute` (eski `pattern`/`breath_per_minute`). `MockLLMClient` yalnızca eski isimleri tanıyordu → canlı webcam akışında hiçbir triaj flag'i tetiklenmeyecekti. Mock güncellendi: hem eski demo vocab'ını hem de yeni live-agent vocab'ını paralel olarak destekliyor (geriye dönük uyumlu).

**Test güncellemeleri:**
- `gateway_agents/tests/test_runner.py` — Yusuf'un eklediği testler `len(bundle.observations()) == 3` bekliyordu; 4-ajan beklentisine geçirildi, payload kontrolüne `thermal` eklendi.
- `gateway_agents/tests/test_agents_synthetic.py` (mertmrz'in) Yusuf'un commit'inde silinmiş; `test_agents.py` + `test_runner.py` ile değiştirilmiş. Otomatik merge bunu kabul etti.

**Doğrulama:**
- `python -m pytest gateway_agents/tests orchestration/tests -v` → **23/23 PASS** (Yusuf'un 12 agent testi + 6 runner testi + 5 supervisor testi).
- `npx tsc --noEmit` (frontend) → clean.
- Kalan 12 ruff uyarısı kozmetik (datetime.UTC vs timezone.utc, UP037, vs.) — tamamı pre-existing, bu turun değişikliklerinden değil.

**Git workflow:**
- Commit zinciri: `22fd6da` (önceki termal) → `9ddf0cd` (bug fix) → `a099d15` (Yusuf ile merge).
- `mertmrz` → `origin/mertmrz` push edildi (PR #1 güncel sürüme geldi).
- `main` ← `mertmrz` fast-forward → `origin/main` push edildi (Yusuf'un main'i merge'i içerdi, PR #1 otomatik "merged" işaretlendi).
- `mertmrz` branch'i hem local hem remote'tan silindi — bundan sonra her yeni iş `main`'den taze feature branch + PR akışıyla yapılacak.

**Açık takipler:**
- Yusuf'un yeni `SkinAgent`'ı Haar Cascade kullanıyor, termal ajan hâlâ MediaPipe Face Detection'a bağlı. Tutarsız ama her ikisi de çalışıyor; ileride tek yüz tespit mekanizması paylaşılabilir.
- Yusuf'un `WebcamSource`'unda `cv2.imshow` canlı önizleme açıyor — headless ortamlarda (Docker, CI) problem yaratabilir; gerektiğinde bir `--no-preview` flag'i eklenebilir.

---

## Açık kararlar
- **Ajan sayısı:** Hackathon kapsamında **3 ajan** (yürüyüş, ten rengi, solunum). `docs/teknik_rapor.md` şu an 5 ajandan bahsediyor (termal + yüz ifadesi); NotebookLM kaynaklarındaki versiyon 3 ajan. Hizalama beklemede.
- **LLM provider:** `OPENAI_API_KEY` veya `ANTHROPIC_API_KEY` yoksa `MockLLMClient` otomatik devreye girer. Demo için API key olsa daha zengin gerekçe çıkar.

## Açık kararlar (güncellendi)
- **Ajan sayısı:** Uygulama 4 ajan (gait, skin, respiration, thermal). `docs/teknik_rapor.md` hâlâ 5 ajandan (termal + yüz ifadesi) bahsediyor; yüz ifadesi ajanı kapsam dışı bırakıldı, teknik rapor hizalama beklemede.
- **LLM provider:** API key yoksa `MockLLMClient` otomatik devreye girer. Gerçek LLM için `.env`'e `ANTHROPIC_API_KEY` veya `OPENAI_API_KEY` girilmeli.
- **Termal kamera:** Şu an `rgb_proxy` modunda. Gerçek MLX90640/FLIR bağlandığında `ThermalAgent.analyze()`'a sıcaklık matrisi besleyecek ayrı bir `ThermalSource` yazılmalı.

## Çalıştırma reçetesi
```bash
# Bağımlılıklar (mediapipe 0.10.18 pinli — kritik)
pip install -e ".[dev]"

# Testler
python -m pytest

# Backend (terminal 1)
python -m uvicorn backend_api.app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (terminal 2)
cd frontend && npm install && npm run dev

# Gateway runner (terminal 3) — gerçek webcam → backend → dashboard
# CLI 2026-05-13 sonrası: --source/--path yerine --webcam / --video / --mqtt
python -m gateway_agents.runner --webcam 0 --window 3.0

# veya test videosu üzerinden:
python -m gateway_agents.runner --video data/demo/red.mp4 --loop

# veya MQTT (ESP32-CAM hazır olduğunda):
python -m gateway_agents.runner --mqtt
```
