# Vita Porta — Geliştirme İlerlemesi

Bu dosya geliştirme oturumlarının kaldığı yerden devam edebilmesi için tutulur. Her faz: durum, neyin tamamlandığı, neyin kaldığı, ilgili dosyalar ve doğrulama yöntemi.

**Genel durum:** 7.5/8 faz tamamlandı + **Faz 4.5 (Frontend yenileme)** tamamlandı. Sistem **gerçek webcam'den canlı çalışıyor**: 4 görsel ajan (yürüyüş, ten rengi, solunum, termal) paralel işliyor, supervisor karar üretiyor, dashboard SSE ile yayınlıyor. Frontend Health-OS stilinde komple yenilendi (`frontend-yenileme` branch, 2026-05-14): Inter font, glassmorphism, hemşire onay/red/değiştir akışı, history detay modal'ı, Türkçe sinyal etiketleri. **mertmrz branch'i ile origin/main (Yusuf'un Phase 5 rewrite'ı) birleştirildi ve tüm değişiklikler ana projeye (ysf-sahin1/vita-porta) push'landı** (2026-05-13). Kalan: edge firmware + Docker compose (Faz 6) ve pitch polish (Faz 8).

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

## Faz 4.5 — Frontend Yenileme (Health-OS Redesign) · ✅ Tamamlandı (2026-05-14)

**Bağlam:** `frontend-yenileme` branch'inde Next.js dashboard'u komple yenilendi. Tasarım yönü kullanıcı tarafından "Health-OS / Apple Health benzeri" seçildi (3 alternatif arasından). Hedefler: hemşire için göz yormayan glassmorphism, gerçek zamanlı saat damgaları, Güven/Ağırlık ayrımı, hemşire onay akışı, Türkçe sinyaller, geçmiş detay görünümü, cross-platform tutarlılık.

**Tasarım sistemi (token'lar):**
- **Font:** Inter, `next/font/google` ile self-host'lu (Google CDN'e prod bağımlılığı yok, GDPR uyumlu, macOS/Windows/Linux'ta birebir aynı render).
- **Base size:** 14px → **16px** (hemşirenin 1m uzaktan okuyabilmesi için).
- **Zemin:** Radial cyan + emerald accent + linear `slate-50 → white → blue-50/30` gradient.
- **Kart yüzeyleri:** `bg-white/70 backdrop-blur-xl border-white/60 shadow-glass` (glassmorphism).
- **Köşeler:** ana kart `rounded-3xl`, alt kart `rounded-2xl`, etiket `rounded-full`.
- **Renkler:** mevcut `triage.red/yellow/green/gray` korundu; `redSoft/yellowSoft/greenSoft` soft tonlar eklendi; `status.live/warn/off` (emerald/amber/slate) eklendi.
- **Animasyonlar:** `pulseRing` (kırmızı), `statusGlow` (yeşil canlı pili), CSS `wobble` (postür sallantı), Tooltip fade-up.
- **Tabular-nums:** `font-variant-numeric: tabular-nums` utility — saatler/yüzdeler dikey hizalı kalsın.

**Layout:**
- `max-w-5xl` (1024px) → **`max-w-[1400px]`** wide-screen kullanımı.
- Wide breakpoint'te 2-kolon grid: sol `1fr` (triage + ajanlar), sağ `380px` (history timeline).
- Demo butonları üstten alta `<details>` collapse'a indi; gerçek hasta verisi geldiğinde (`patient_id` "demo-" ile başlamıyorsa) hiç render edilmiyor.

**Yeni komponentler:**
- `Header.tsx` (rewrite) — `text-3xl` başlık, gradient logo badge, 3 status pili (Kamera / API / LLM) + canlı saat. Kamera durumu son gözlem yaşından, LLM durumu son karar latency'sinden (>100ms gerçek, ≤100ms mock) çıkarılır.
- `Tooltip.tsx` (yeni) — sıfır bağımlılık, CSS hover + focus-within, Info ikonu default, `align="left|center|right"`. Tüm tooltip'ler glassmorphism slate-900/95 koyu kart.
- `PostureSilhouette.tsx` (yeni) — inline SVG çöp adam, 5 durum: dik / sallantılı (CSS wobble animasyonu) / asimetrik (omuz kayık) / öne eğik / bilinmiyor (dashed). Hem canlı schema (`sway_detected`, `symmetry_status`) hem demo schema (`sway`, `symmetry: float`) tanır.
- `NurseVerdict.tsx` (yeni) — Onayla (emerald) / Reddet (rose) / Değiştir (white) butonları + inline kategori dropdown'u + verdict banner + ChromaDB italic notu. `Verdict` tipi, `verdictIcon/verdictColorClass/formatVerdictTime` yardımcıları export.
- `HistoryDetailModal.tsx` (yeni) — backdrop blur + glassmorphism kart, kategori başlığı + saat + gerekçe + 4 ajan kompakt snapshot (Türkçe sinyaller) + NurseVerdict reuse. Escape / backdrop click / X ile kapanır, body scroll lock.

**Yeni lib helpers:**
- `lib/agentReasons.ts` — `inferAgentReason(obs)` ajanın signals + confidence'ından somut sebep çıkarır:
  - skin: `skin_tone="belirsiz"` → "Ortam ışığı yetersiz"; `face_detected_ratio < 0.3` → "Yüz net tespit edilemedi"
  - gait: `avg_visibility < 0.4` → "Vücut tam görünmüyor"
  - respiration: `movement_intensity < 0.5` → "Göğüs hareketi çok zayıf"
  - thermal: `sensor_type="rgb_proxy"` → her zaman info pill ("RGB proxy modu")
  - Severity: `info` (mavi), `warn` (amber), `error` (rose) renkli pill'ler
- `lib/signalLabels.ts` — `formatSignal(key, value)` ile tüm bilinen ajan sinyalleri Türkçeleştirildi:
  - Bool → "Var/Yok" (pallor, sway, fever_flag, hypothermia_flag)
  - String enum → "Solgun/Normal/Belirsiz", "Anormal/Normal", "Hızlı/Yavaş/Düzensiz/Apne Riski", "Yüksek/Hafif/Yok", "RGB Proxy/Termal"
  - Numerik → birimle: "Sıcaklık: 38.8°C", "Solunum Hızı: 28/dk", "Yüz Tespiti: %75"
  - Hem canlı schema hem demo schema anahtarları tanınır; bilinmeyen anahtar gizlenir (raw `key:value` gösterilmez).

**Komponent güncellemeleri:**
- `useTriageStream.ts` — `HistoryEntry { key, patientId, decision, observations }` yapısı; `observationsRef` ile o anki gözlemler yakalanıp decision geldiğinde snapshot olarak history'e eklenir. `verdicts: Record<string, Verdict>` paylaşılan map, `setVerdict(key, v)` action expose edilir. `entryKey(patientId, decidedAt)` unique key helper. `lastObservationAt` + `lastDecisionLatencyMs` Header için expose'lu. **History cap yok** (eskiden `slice(0,10)`, şimdi tüm session).
- `TriageCard.tsx` — Local verdict state kaldırıldı, `verdict + onVerdictChange` prop'tan alır. Sağ üstte "Güven" yanına (i) tooltip, "Ajan ağırlıkları" başlığı yanına (i) tooltip ("Güven ≠ Ağırlık" açıklaması). Karar saati caption: `HH:MM:SS · 248 ms`. NurseVerdict reuse.
- `AgentPanel.tsx` — Yeni `SignalPills` alt komponenti (`formatSignal` ile Türkçe). `ReasonHint` (agentReasons'tan). Her kartın güven satırına (i) tooltip. Gait kartında PostureSilhouette. Grid `md:grid-cols-2 xl:grid-cols-4` (wide ekranda 4 yan yana, orta ekranda 2x2).
- `HistoryList.tsx` — `HistoryEntry[]` shape'i, her satır `<button>` (tıklanabilir), `selectedKey` highlight (sky-50/70), verdict varsa sağda ✓/✗/✎ ikonu (verdictIcon/verdictColorClass). HH:MM:SS damgası tabular-nums. Header'da toplam karar sayacı. `max-h-[480px] overflow-y-auto`.
- `page.tsx` — `max-w-[1400px]`, lg 2-kolon grid, `selectedKey` state, `handleVerdict(key)` helper (verdict'i `formatVerdictTime()` ile zamanlayıp setVerdict'e iletir), `HistoryDetailModal` overlay'i. Empty state glassmorphism kart.
- `app/layout.tsx` — Inter font `next/font/google` ile yüklenip `--font-inter` CSS değişkeni `<html>`'e bağlandı.
- `app/globals.css` — 16px base, 3-stop radial+linear gradient zemin, `font-feature-settings: "cv11", "ss01", "ss03"` (Inter rakam okunabilirliği), tabular-nums utility.
- `tailwind.config.ts` — Inter font ailesi, soft triage tonları, `status.live/warn/off` renkleri, `shadow-glass/glassLg/ring`, `rounded-4xl`, `statusGlow` animasyonu.

**Backend tarafı destekleyici değişiklikler:**
- `orchestration/demo.py` — 3 senaryoya (red/yellow/green) `thermal=AgentObservation(...)` eklendi. Kırmızı: ateş 38.8°C + `fever_flag=True`, sarı: 37.7°C borderline ateş, yeşil: 36.6°C normal. `sensor_type="rgb_proxy"` tüm vakalarda. **Önce hiç thermal yoktu** → AgentPanel termal kartı her zaman "Veri bekleniyor" gösteriyordu, supervisor "termal için veri yetersiz" diyordu. Düzeldi.
- Backend artık `--reload` ile başlatılmalı (development): `python -m uvicorn backend_api.app.main:app --reload --host 127.0.0.1 --port 8000` — `demo.py` veya diğer Python kaynak değişiklikleri otomatik yüklenir.

**Hemşire iş akışı (yeni):**
- Her karar için 3 buton: ✓ Onayla / ✗ Reddet / ✎ Değiştir
- "Değiştir" inline kategori dropdown'u açar: Kırmızı / Sarı / Yeşil / İptal
- Verdict verildiğinde butonlar yerine durum banner'ı görünür (yeşil/kırmızı/amber)
- Banner'da seçilen kategori + saat damgası (HH:MM:SS)
- Italic gri ibare: "Hemşire kararı ChromaDB'ye kaydedilerek sistem öğrenmesinde kullanılacaktır."
- Verdict map paylaşılan state'te → aynı karar hem ana TriageCard'tan hem history modal'ından verdict verilebilir, ikisi de aynı görünür
- Geçmiş satıra tıkla → modal açılır → o anki 4 ajan snapshot'ı + verdict
- History satırlarında verdict varsa sağda mini ikon (✓ yeşil / ✗ kırmızı / ✎ amber)

**Tooltip içerikleri:**
- "Güven" (AgentPanel): "Ajanın kendi gözleminin kalitesine emniyeti. Yüz tespit edildi mi, ışık yeterli mi, sinyal kararlı mı — bu metrikten gelir."
- "Güven" (TriageCard): "Supervisor'ın bu karara olan toplam emniyeti. Ajan güvenleri ve ağırlıklı toplamından hesaplanır."
- "Ağırlık": "Supervisor'ın bu ajanı nihai karara ne kadar dahil ettiği. Düşük güvenli ajan otomatik düşük ağırlık alır. Güven ≠ Ağırlık: Güven ajanın kendi ölçümünden, ağırlık supervisor'ın değerlendirmesinden gelir."

**Sayfa header'da sistem durumu:**
- `KAMERA` pili: son `agent_observation` zamanı <5sn → emerald (canlı glow), <15sn → amber (uyarı), aksi → slate (off)
- `API` pili: SSE bağlantı durumu (live/connecting/offline)
- `LLM` pili: son `decision.latency_ms`'e göre — >100ms → "LLM" emerald (gerçek), ≤100ms → "LLM·mock" amber, hiç karar yoksa "LLM" off
- Sağ uçta siyah pill içinde HH:MM:SS canlı saat (1sn interval)

**Doğrulama:**
- `npx tsc --noEmit` → clean (frontend)
- Dev server (npm run dev) tüm modül compile ediyor, runtime error yok
- Demo butonlarıyla canlı test: termal görünüyor, postür silüeti sallantılı, tooltip'ler hover'da, verdict butonları çalışıyor, modal açılıyor, Türkçe sinyaller doğru görünüyor.
- 50+ demo tetiklemede history sınırsız büyüyor, scroll çalışıyor, seçili satır highlight olunca modal aynı snapshot'ı gösteriyor.

**Bug fix turu (oturum içinde):**
- `next build` dev mode'da çalıştırıldı, `.next/` dizinindeki dev chunk'larını ezdi → tüm statik dosyalar 404 → kullanıcı sitenin bozulduğunu gördü. `.next/` silinip `npm run dev` yeniden başlatılarak düzeltildi. Bundan sonra dev mode'da **sadece `npx tsc --noEmit`** ile tip kontrolü yapılacak; `next build` ya ayrı worktree'de ya da dev'i durdurarak çalıştırılacak.

**Yeni dosyalar (7):**
```
frontend/components/Tooltip.tsx
frontend/components/PostureSilhouette.tsx
frontend/components/NurseVerdict.tsx
frontend/components/HistoryDetailModal.tsx
frontend/lib/agentReasons.ts
frontend/lib/signalLabels.ts
```

**Yeniden yazılan/güncellenen (10):**
```
frontend/app/layout.tsx          # Inter font wiring
frontend/app/globals.css         # 16px base, gradient zemin, tabular-nums
frontend/app/page.tsx            # Wide layout, modal kontrolü, paylaşılan verdict
frontend/tailwind.config.ts      # Token genişletme
frontend/components/Header.tsx           # Büyük başlık, 3 status pili, canlı saat
frontend/components/TriageCard.tsx       # Verdict prop, tooltip'ler, karar saati
frontend/components/AgentPanel.tsx       # SignalPills, ReasonHint, PostureSilhouette
frontend/components/HistoryList.tsx      # Tıklanabilir + verdict ikonu + saat damgası
frontend/components/useTriageStream.ts   # HistoryEntry snapshot + verdicts map
orchestration/demo.py            # 3 senaryoya thermal observation
.gitignore                       # *.tsbuildinfo + kök package-lock.json
```

**Açık takipler / kalan iş:**
- **Backend `/api/triage/feedback` endpoint'i yok** — hemşire verdict'leri şu an sadece tarayıcı belleğinde, sayfa yenilenince kayboluyor. ChromaDB'ye yazımı için yeni endpoint + supervisor öğrenme döngüsü ileride yapılacak. UI hazır, sadece HTTP wire bekliyor.
- 3 saniyelik "Analiz ediliyor..." pencere animasyonu (orijinal Faz 1 planında vardı) henüz eklenmedi — şu an decision anlık görünüyor, observation/decision arası halka animasyonu yok. Backend event şarşt değil; frontend'te observation→decision timing'inden çıkarılabilir.
- `next build` dev mode'da çalıştırılma riski — geliştirici dökümanına / Makefile'a not düşülmeli.
- Termal ajan hâlâ proxy modunda (confidence ≤0.60); gerçek MLX90640/FLIR bağlandığında `ThermalAgent.analyze()`'a sıcaklık matrisi besleyecek `ThermalSource` yazılmalı (Faz 5'te belirlenmişti).

---

## Açık kararlar
- **Ajan sayısı:** Hackathon kapsamında **3 ajan** (yürüyüş, ten rengi, solunum). `docs/teknik_rapor.md` şu an 5 ajandan bahsediyor (termal + yüz ifadesi); NotebookLM kaynaklarındaki versiyon 3 ajan. Hizalama beklemede.
- **LLM provider:** `OPENAI_API_KEY` veya `ANTHROPIC_API_KEY` yoksa `MockLLMClient` otomatik devreye girer. Demo için API key olsa daha zengin gerekçe çıkar.

## Açık kararlar (güncellendi)
- **Ajan sayısı:** Uygulama 4 ajan (gait, skin, respiration, thermal). `docs/teknik_rapor.md` hâlâ 5 ajandan (termal + yüz ifadesi) bahsediyor; yüz ifadesi ajanı kapsam dışı bırakıldı, teknik rapor hizalama beklemede.
- **LLM provider:** API key yoksa `MockLLMClient` otomatik devreye girer. Gerçek LLM için `.env`'e `ANTHROPIC_API_KEY` veya `OPENAI_API_KEY` girilmeli.
- **Termal kamera:** Şu an `rgb_proxy` modunda. Gerçek MLX90640/FLIR bağlandığında `ThermalAgent.analyze()`'a sıcaklık matrisi besleyecek ayrı bir `ThermalSource` yazılmalı.
- **Hemşire verdict persistance:** Frontend'te Onayla/Reddet/Değiştir akışı tamamlandı (2026-05-14), ama backend'e POST yapılmıyor. Verdict'ler `useTriageStream` içindeki `verdicts` map'inde — tarayıcı belleğinde. `POST /api/triage/feedback` endpoint'i + ChromaDB persistance gerekiyor; supervisor öğrenmesi bu veriyi kullanacak.
- **Frontend dev mode'da `next build` riski:** Aynı `.next/` dizini paylaşıldığı için dev server ayaktayken `next build` çalıştırmak dev chunk'larını ezer (2026-05-14 oturumunda yaşandı). Doğrulama için sadece `npx tsc --noEmit` veya ayrı worktree'de build.

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
