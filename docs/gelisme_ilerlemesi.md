# Vita Porta — Geliştirme İlerlemesi

Bu dosya geliştirme oturumlarının kaldığı yerden devam edebilmesi için tutulur. Her faz: durum, neyin tamamlandığı, neyin kaldığı, ilgili dosyalar ve doğrulama yöntemi.

**Genel durum:** 7.5/8 faz tamamlandı + **Faz 4.5 (Frontend yenileme)** + **Faz 4.6 (login + radyal)** + **Faz 5 tamamen kapandı** (5 ajan) + **Faz 5.7 (verdict persistance + mesai history + RAG deneyim katmanı)** + **Faz 5.8 (tüm kararların kalıcı kaydı + sıfırlama akışı)** tamamlandı (2026-05-16). Sistem **gerçek webcam'den canlı çalışıyor**: **5 görsel ajan** (yürüyüş, ten rengi, solunum, termal, yüz ifadesi) paralel işliyor, supervisor RAG + geçmiş hemşire kararları ile karar üretiyor, dashboard SSE ile yayınlıyor. **Tüm triaj kararları kalıcı kaydediliyor** (`.decisions/decisions.jsonl`); hemşire ✓/✗/✎ verdict'leri ayrı bir store'da (`.feedback/feedbacks.jsonl`). Sayfa yenilense, hemşire değişse, oturum kapansa bile **hem genel hasta listesi hem de verdict'ler korunuyor**; istenirse "Sıfırla" butonu ile her ikisi de kalıcı olarak silinebiliyor. Yeni vaka geldiğinde benzer sinyalli geçmiş hemşire kararı bağlam olarak supervisor'a giriyor ve UI'da görünüyor. Kalan: edge firmware + Docker compose (Faz 6) ve pitch polish (Faz 8).

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

## Faz 5 — Görsel ajanlar · ✅ Tamamlandı + Termal Ajan Eklendi (2026-05-13) + Yüz İfadesi Ajanı (2026-05-16, Faz 5 resmi kapanışı)
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

## Faz 5.8 — Tüm kararların kalıcı kaydı + Sıfırlama akışı · ✅ Tamamlandı (2026-05-16)

**Bağlam:** Faz 5.7'de hemşire verdict'leri kalıcı hale geldi ama **verdict verilmemiş kararlar** hâlâ uçuyordu — sayfa yenilenince sadece ✓/✗/✎ yapılan vakalar geri geliyordu, geri kalan triaj kararları yok oluyordu. Aynı zamanda eski test verilerini temizlemek için bir yol yoktu. Bu turda iki şey eklendi:

1. **DecisionRecord store** — Her triaj kararı (verdict olsun olmasın) `.decisions/decisions.jsonl`'a yazılır.
2. **Sıfırlama akışı** — Header'sız, HistoryList üst başlığa "Sıfırla" linki + onay modal; backend `DELETE /api/triage/history` her iki dosyayı (decisions + feedback) temizler.

**Backend yeni dosyalar (1):**
- `orchestration/decisions_store.py` — `DecisionStore` Protocol + `JsonDecisionStore`:
  - Append-only `.decisions/decisions.jsonl`, thread-safe lock
  - `save(record)`, `list_all()` (decision_id başına son kayıt), `clear()` (dosyayı siler)
  - `FeedbackStore` ile birebir paralel yapı

**Backend güncellenen dosyalar (3):**
- `orchestration/schemas.py` — Yeni `DecisionRecord` model (decision_id, patient_id, decision, observations_snapshot).
- `orchestration/feedback_store.py` — `FeedbackStore` protocol'üne `clear()` eklendi, `JsonFeedbackStore.clear()` implementasyonu.
- `backend_api/app/main.py`:
  - Lifespan'da `decisions_store = build_default_decision_store()`
  - `_persist_decision(app, bundle, decision)` helper — `run_triage` ve `demo_triage` her decision üretildiğinde çağırır (observation snapshot da iliştirilir)
  - `GET /api/triage/history` shape değişti: artık `{decisions: list[DecisionRecord], feedback: list[NurseFeedback]}` döner
  - `DELETE /api/triage/history` (204 No Content) — her iki store'u `clear()` eder, geri alınamaz

**Frontend yeni dosyalar (1):**
- `frontend/components/ResetConfirmDialog.tsx` — Glassmorphism onay modalı (`AlertTriangle` ikonu, rose-50 vurgulu, "İptal" + "Evet, sıfırla" butonları). Escape / backdrop click ile kapanır, body scroll lock, busy state ("Siliniyor…").

**Frontend güncellenen dosyalar (4):**
- `frontend/lib/types.ts` — `DecisionRecord` ve `HistoryResponse` interface'leri.
- `frontend/lib/api.ts` — `fetchHistory()` artık `HistoryResponse` döner; yeni `resetHistory()` (DELETE).
- `frontend/components/useTriageStream.ts`:
  - `restoreHistoryFromBackend()` artık iki listeyi merge ediyor: önce decisions (tüm kararlar entry olarak), sonra feedbacks (verdict + nurse meta + decisions'da olmayan eski feedback'ler için entry reconstruct fallback).
  - `decisionByKeyRef` artık restore'dan da popüle ediliyor (verdict POST'unda snapshot her zaman mevcut).
  - Yeni `resetHistory` action expose'lu: backend DELETE çağırır, local state'i tertemiz sıfırlar (history boşalır, verdict map'leri silinir, current görünüm korunur).
- `frontend/components/HistoryList.tsx`:
  - Yeni `onReset` prop'u + lokal `confirmOpen` state.
  - Üst başlıkta "Sıfırla" butonu (Trash2 ikonu, hover'da rose-50). Tıklayınca `ResetConfirmDialog` açılır.
  - Boş history durumunda da dialog render'lanır (modal görünebilir).
- `frontend/app/page.tsx`:
  - `resetHistory` hook'tan alınıyor, `HistoryList`'e `onReset` olarak iletiliyor.
  - Reset sonrası `setSelectedKey(null)` (varsa modal seçimi temizlenir).

**`.gitignore`** — `.decisions/` (zaten `.feedback/` vardı; `.decisions/` da eklendi).

**Veri akışı:**

```
Demo butonu / webcam runner → POST /api/triage/run
   ↓
Supervisor.decide() → TriageDecision
   ↓
SSE'ye gönder + _persist_decision() →
   DecisionRecord (.decisions/decisions.jsonl)

Hemşire ✓/✗/✎ → POST /api/triage/feedback
   ↓
NurseFeedback (.feedback/feedbacks.jsonl)

Sayfa yenile → GET /api/triage/history
   ↓
{decisions, feedback}
   ↓
useTriageStream restore:
   - Tüm kararlar (verdict olsun olmasın) entry olarak yüklenir
   - Verdict olanlara nurse meta + verdict badge eklenir

Hemşire "Sıfırla" → onay modalı → DELETE /api/triage/history
   ↓
JsonDecisionStore.clear() + JsonFeedbackStore.clear()
   ↓
useTriageStream.resetHistory():
   seenKeysRef = new Set(), decisionByKey = {},
   history = [], verdicts = {}, verdictNurses = {}
```

**Doğrulama:**
- `python -m pytest gateway_agents/tests orchestration/tests -v` → **27/27 PASS**
- `npx tsc --noEmit` → clean
- Backend curl round-trip:
  - `POST /api/triage/demo?scenario=yellow` → 200
  - `GET /api/triage/history` → `{decisions: [...1 kayıt], feedback: [...]}`
  - `DELETE /api/triage/history` → 204
  - `GET /api/triage/history` → `{decisions: [], feedback: []}`
- Frontend canlı: demo butonu → verdict vermeden hard refresh (Cmd+Shift+R) → karar history'de kalır (· geçmiş rozetiyle); "Sıfırla" → onay modalı → "Evet, sıfırla" → her şey siler; reset sonrası demo butonu → temiz state'le yeniden başlar.

**Açık takipler:**
- Reset onayı için yazılı tip-doğrulama (örn. "SİL" yazma) hackathon için fazla; modal yeterince blocking.
- Bulk-undo (sıfırlama sonrası geri al) yok — istenirse `.decisions/.bak` + `.feedback/.bak` yedeği alınabilir; şimdilik kapsam dışı.
- Reset butonu sadece HistoryList'te; gerekli olursa Header'a da küçük bir ikon eklenebilir, ama orası zaten dolu (kamera/API/LLM pilleri + saat + çıkış).

## Faz 5.7 — Verdict persistance + Mesai history + RAG deneyim katmanı · ✅ Tamamlandı (2026-05-16)

**Bağlam:** Faz 4.5'te hemşire ✓/✗/✎ UI'ı tamamlandı ama veriler sadece tarayıcı belleğindeydi — sayfa yenileyince kayboluyor, çıkış yapınca eski kararlar yok oluyor. Aynı zamanda RAG sadece ESI seed vakalarına bakıyordu; geçmişte aynı hastanedeki hemşirenin benzer vakaya nasıl yanıt verdiği sisteme yansımıyordu. Bu turda 3 katman birden eklendi:

1. **Verdict persistance** — JSON-tabanlı append-only store; backend reload veya sayfa yenileme veri kaybetmiyor.
2. **Mesai history** — Her verdict'te hemşire bilgisi (ad/soyad/hastane/saat) saklanır; HistoryList'te mesai değişikliği görsel marker ile gösterilir, farklı hemşirenin kararları italik fontla ayırt edilir.
3. **RAG deneyim katmanı** — Supervisor pipeline'ına yeni `retrieve_feedback` node eklendi; yeni vaka geldiğinde benzer sinyal örüntüsüne sahip geçmiş hemşire kararları prompt'a "Geçmiş Hemşire Kararları" bölümü olarak giriyor ve TriageCard / HistoryDetailModal'da kullanıcıya gösteriliyor.

**Backend yeni dosyalar (1):**
- `orchestration/feedback_store.py` — `FeedbackStore` Protocol + `JsonFeedbackStore`:
  - Append-only JSONL (`.feedback/feedbacks.jsonl`), thread-safe lock
  - `save(feedback)` — satır eklenir
  - `list_all()` — `decision_id` başına en yeni kayıt (override desteği)
  - `query_similar(signals_text, k=3)` — Jaccard token-overlap (RAG retriever ile aynı yaklaşım, tutarlı/deterministik)

**Backend güncellenen dosyalar (4):**
- `orchestration/schemas.py`:
  - Yeni `HistoricalFeedback` modeli (nurse_name, hospital, original_category, nurse_verdict, verdict_kind, rationale_tr, feedback_at, similarity_score)
  - Yeni `NurseFeedback` modeli (decision_id, patient_id, original_category, nurse_verdict, verdict_kind, rationale_tr, nurse_first_name/last_name/hospital, signals_summary, observations_snapshot, decided_at, feedback_at) + `to_historical()` helper
  - `TriageDecision.historical_feedback: list[HistoricalFeedback]` alanı + `from_category` parametresi
- `orchestration/supervisor.py`:
  - `Supervisor.feedback_store` alanı (default `build_default_store()`)
  - LangGraph'a yeni `retrieve_feedback` node — `retrieve_rag → retrieve_feedback → ask_llm → validate`
  - State'e `historical_feedback: list[HistoricalFeedback]` eklendi
  - `_validate` TriageDecision'a historical_feedback iliştirir
  - Store sorgu hataları defensive (RAG advisory; pipeline crash olmaz)
- `orchestration/prompts/supervisor.py`:
  - "Geçmiş Hemşire Kararları (deneyim katmanı)" bölümü eklendi: ESI önceliklidir, geçmiş kararlardan farklı yöne sapan varsa rationale'a NOTE eklenir, birden çok hemşire aynı yönde ise güçlü sinyal kabul edilir, liste boşsa varsayılan ESI mantığı.
  - `build_supervisor_user_prompt` artık 3. argüman `historical_feedback` alıyor, payload'a `historical_nurse_feedback` listesi olarak gidiyor.
- `backend_api/app/main.py`:
  - Lifespan'da `FeedbackStore` singleton + `Supervisor(feedback_store=...)`
  - `POST /api/triage/feedback` — `NurseFeedback` al, store'a yaz, `{saved: true, decision_id}` dön
  - `GET /api/triage/history` — `list[NurseFeedback]` dön (frontend ilk yüklemede çağırır)
- `.gitignore` — `.feedback/` eklendi (local data, KVKK uyumu için repo'ya gitmez).

**Frontend yeni komponent yok — sadece mevcut komponentler güncellendi.**

**Frontend güncellenen dosyalar (7):**
- `frontend/lib/types.ts` — `HistoricalFeedback` interface + `TriageDecision.historical_feedback` + `NurseFeedback` interface (backend ile birebir).
- `frontend/lib/api.ts` — `postFeedback(NurseFeedback)`, `fetchHistory()`.
- `frontend/components/useTriageStream.ts` (komple yeniden yazıldı):
  - `useNurseSession` ile session ref tutulur (her render'da en güncel).
  - Mount'ta `fetchHistory()` → verdicts + verdictNurses + history restore (decision_id bazlı tekrar-engelleme).
  - SSE decision geldiğinde `decisionByKeyRef` cache'lenir; aynı decision_id daha önce restore'dan gelmişse history'e tekrar eklenmez.
  - `setVerdict(key, verdict)` → state güncelle + otomatik `postFeedback()`. Verdict snapshot için decision + observations cache'ten alınır (history'den fallback).
  - `signals_summary` her ajan sinyalinden tek-string olarak inşa edilir (token-overlap için).
  - Yeni snapshot alanları: `verdictNurses: Record<key, NurseMeta>`.
  - `HistoryEntry`'ye `restored?: boolean` flag eklendi (UI'da "geçmiş" işareti için).
- `frontend/components/HistoryList.tsx`:
  - `verdictNurses` prop'u eklendi.
  - **Mesai değişikliği marker'ı**: önceki entry farklı hemşireden ise araya divider (`UserCog` ikonu + hemşire adı + saat).
  - **Hemşire ismi caption**: her entry'nin altında küçük satır "{Ad} {Soyad} · HH:MM:SS".
  - **Font vurgu**: şu anki session'dan farklı hemşirenin verdict'i italik + slate-600. Restore'dan gelen entry'lerde "· geçmiş" rozeti.
- `frontend/components/HistoryDetailModal.tsx`:
  - `nurse: NurseMeta | null` prop'u eklendi → verdict altında hemşire bilgisi satırı (`User` ikonu, ad-soyad, hastane, saat).
  - **`HistoricalFeedbackBlock`**: kararın `decision.historical_feedback` listesi varsa modal'ın altında "Geçmiş benzer hemşire kararları" kartları. Her kart: hemşire adı + hastane + verdict kind rozeti (Onayladı/Reddetti/Değiştirdi) + "Sistem önerisi: X · Hemşire kararı: Y" + rationale italic.
- `frontend/components/TriageCard.tsx`:
  - `HistoricalFeedbackBanner` — kartın altında sky-50 banner: "Geçmiş hemşire deneyimleri" + ilk 2 kayıt: "{Hemşire} · benzer sinyalde {Original}'i {onayladı/reddetti/X'e çevirdi}".
- `frontend/components/NurseVerdict.tsx`:
  - "Hemşire kararı ChromaDB'ye kaydedilecek" notu güncellendi: "Hemşire kararı kalıcı olarak kaydedilir; benzer sinyallere sahip bir sonraki hastada sistem bu kararı 'geçmiş deneyim' olarak referans alır."
- `frontend/app/page.tsx`:
  - `verdictNurses`, `selectedNurse` state'leri çekildi, HistoryList ve HistoryDetailModal'a geçildi.

**Veri akışı:**

```
Hemşire ✓ Onayla
   ↓
NurseVerdict.onChange → page.tsx handleVerdict
   ↓
useTriageStream.setVerdict
   ↓
   ├─→ verdicts + verdictNurses state güncelle (UI anında yansır)
   └─→ postFeedback() — backend'e POST /api/triage/feedback
              ↓
       JsonFeedbackStore.save() — .feedback/feedbacks.jsonl
              ↓
       (yeni vaka için RAG'a hazır)

Sayfa yenilendi / hemşire değişti:
   ↓
useTriageStream mount
   ↓
fetchHistory() → GET /api/triage/history
   ↓
verdicts + verdictNurses + history (restored=true) restore

Yeni vaka geldi:
   ↓
Supervisor.decide(bundle)
   ↓
LangGraph: retrieve_rag → retrieve_feedback → ask_llm → validate
                              ↓
                  FeedbackStore.query_similar(signals)
                              ↓
                  HistoricalFeedback[] state'e
                              ↓
                  Prompt'a "Geçmiş Hemşire Kararları" payload
                              ↓
                  LLM kararı verir; rationale'da geçmişe atıf yapabilir
                              ↓
TriageDecision.historical_feedback (frontend'e SSE)
   ↓
TriageCard → "Geçmiş hemşire deneyimleri" banner
HistoryDetailModal → "Geçmiş benzer hemşire kararları" kartları
```

**Doğrulama (manuel test edildi):**
- `python -m pytest gateway_agents/tests orchestration/tests -v` → **27/27 PASS**
- `npx tsc --noEmit` → clean
- Backend canlı testleri (curl):
  - `GET /api/triage/history` → `[]` (boş)
  - `POST /api/triage/feedback` (örnek payload) → `{saved: true, decision_id: ...}`
  - `GET /api/triage/history` → eklenen kayıt görünür
  - `POST /api/triage/demo?scenario=red` → decision payload'ında `historical_feedback` 1 kayıtla geliyor ("Ayşe Demir · Acıbadem Maslak · override · similarity 0.105")
- Frontend canlı akış: login → demo butonu → verdict ver → sayfa yenile (`Cmd+R`) → veri DURUYOR; çıkış → tekrar gir → veriler hâlâ var; ikinci kez aynı demo'yu tetikle → TriageCard'da "Geçmiş hemşire deneyimleri" banner'ı görünür.

**Açık takipler:**
- ChromaDB swap'ı için `FeedbackStore` protocol hazır; pilot fazında embedding-tabanlı similarity için `ChromaFeedbackStore` yazılabilir. Hackathon için JSON + Jaccard yeterli, deterministik.
- Hemşire kararı override edildiğinde rationale yazma alanı yok (UI'da yok); şimdilik boş string gönderiyor. Demo değerini artırmak için NurseVerdict'e küçük textarea eklenebilir.
- Verdict silme yok — yanlış verdict düzeltilirse aynı `decision_id` ile yeni POST atılır, `list_all()` son kaydı tutar (override mantığı).

## Faz 4.6 — Hemşire girişi + Anatomik radyal layout · ✅ Tamamlandı (2026-05-16)

**Bağlam:** 5. ajan eklendikten sonra frontend "canlılık" eksikliği vardı; ajanlar 5'li düz grid, statik. Kullanıcı oturumun başında yoktu, herkes anonim olarak dashboard'a düşüyordu. Bu turda iki şey yapıldı:
1. **Hemşire giriş ekranı** — ad / soyad / hastane adı zorunlu, localStorage'da hatırlanır.
2. **Anatomik radyal layout** — silüet ortada, 5 ajan vücudun gözlemlediği bölgeye yerleştirilmiş; bağlantı çizgileri dashed flow ile sürekli canlı, silüet kategori rengiyle soft pulse atar.

Mevcut tasarım iyiymiş diye kullanıcı sinyal pill'leri / güven yüzdeleri / sinyal Türkçeleştirmesini koruma istedi → **AgentCard içeriği değişmedi**, sadece dizilim değişti.

**Yeni dosyalar (4):**
- `frontend/lib/session.ts` — `NurseSession` tipi + `getSession/setSession/clearSession/displayName` helpers. localStorage key `vita_porta_session`. KVKK uyumu: hemşire ve hastane verisi cihazda kalır, backend'e gönderilmez.
- `frontend/components/LoginScreen.tsx` — glassmorphism kart, 3 alan (Ad / Soyad / Hastane), validation (min 2 karakter), invalid state'lerde rose-50 vurgu + altta uyarı. Mevcut zeminle uyumlu (gradient + Inter font). Footer'da "tanı koymaz" notu.
- `frontend/components/SessionGate.tsx` — root wrapper. `mounted` state ile hydration race önlenir (SSR mismatch yok). React Context (`useNurseSession`) ile alt komponentler session + logout erişir.
- `frontend/components/AnatomicalRadial.tsx` — `aspect-[5/3]` container, SVG arka plan (viewBox `0 0 100 60`):
  - Dekoratif yumuşak halka (radial gradient, kategori rengi)
  - 5 bağlantı çizgisi (dashed, ajan rengiyle, observation varsa `animate-lineFlow` ile sürekli akış, yoksa düşük opacity)
  - **Silüet vektörü** (inline SVG): büyük çöp adam — kafa, omuz, gövde, kollar, bacaklar. Gait sinyalleriyle dinamik: `sway_detected` → `silhouetteSway` rotate animasyonu, `symmetry_status="anormal"` → asimetrik omuz. Solunum confidence > 0.3 → göğüs çizgisi `chestBreathe` ile nefes alır gibi pulse. Kategori rengi outline; orta halka `silhouettePulse` ile genişleyip daralır.
  - 5 ajan kartı container içinde absolute yüzdelik pozisyonda:
    - **Expression** sol üst — kafa sol
    - **Thermal** sağ üst — alın
    - **Skin** sol orta — yanak
    - **Respiration** sağ orta — göğüs
    - **Gait** orta alt — bacaklar

**Güncellenen dosyalar (5):**
- `frontend/components/AgentPanel.tsx`:
  - `AgentCard` ve `Agent` / `AGENT_META` artık export'lu (AnatomicalRadial reuse eder).
  - Komponent responsive switch: `xl+` AnatomicalRadial, altında düz grid (mobile/tablet fallback).
  - Yeni `category` prop'u (silüet pulse rengi için).
- `frontend/components/Header.tsx`:
  - `useNurseSession()` ile hemşire bilgisi alınıyor.
  - Subtitle satırı "Hemşire triaj asistanı…" yerine ad-soyad + hastane (`User` + `Building2` ikonlarıyla).
  - Sağa "Çıkış" butonu (LogOut ikonu, hover'da rose-50). Canlı saat + 3 status pili korundu.
- `frontend/app/page.tsx`:
  - Page komponentı `<SessionGate><Dashboard /></SessionGate>` ile sarıldı.
  - Dashboard içeriği aynen kaldı; AgentPanel'e `category` geçildi (`current?.decision?.category ?? null`).
- `frontend/tailwind.config.ts` — 4 yeni animasyon:
  - `lineFlow` — dashed stroke offset (1.8s linear, bağlantı çizgileri için)
  - `silhouettePulse` — scale + opacity (3s ease-in-out, silüet halkası)
  - `silhouetteSway` — rotate ±1.5° (2.2s ease-in-out, sallantılı yürüyüşte silüet)
  - `chestBreathe` — strokeWidth 0.7↔1.1 (3s ease-in-out, göğüs nefes)

**Doğrulama:**
- `npx tsc --noEmit` → clean.
- Manuel doğrulama: dev server'da ilk açılışta login ekranı görünür, giriş yapıldıktan sonra ana ekran; tarayıcı kapatılıp tekrar açıldığında ana ekran direkt gelir (localStorage). Çıkış butonu → login'e döner. Radyal layout `xl` ve üstünde aktif; altında mevcut grid çalışır.

**Açık takipler:**
- Hemşire verdict persistance (backend `POST /api/triage/feedback`) hâlâ açık — Faz 5.6 dışı.
- Radyal layout sadece `xl+` (≥1280px). Daha küçük ekranda 5'li grid'e düşer; tablet için ayrı bir orta seviye gerekirse ilerleyen turda.
- Bağlantı çizgileri sabit yüzdelik koordinatlar — kart içerikleri büyürse silüetle hizalanma kayabilir. Şu an stabil; dinamik koordinat (ref-based) gerekirse ileride.

## Faz 5.6 — Yüz İfadesi Ajanı (5. ajan, Faz 5 resmi kapanışı) · ✅ Tamamlandı (2026-05-16)

**Bağlam:** `docs/teknik_rapor.md` baştan beri 5 ajandan bahsediyordu (yürüyüş, ten rengi, solunum, termal, **yüz ifadesi**). Termal 2026-05-13'te eklendi ama yüz ifadesi ajanı atlanmıştı. Bu turda 5. ajan eklendi, schema/prompt/mock/runner/test ve **component entegrasyonuna kadar** olan frontend güncellendi. Asıl redesign (yeni layout/stil) ayrı bir tura bırakıldı.

**Yeni dosya:**
- `gateway_agents/agents/expression.py` — **MediaPipe Face Mesh (468 landmark)** ile geometrik kural-tabanlı ajan:
  - **EAR (Eye Aspect Ratio):** Soldaki+sağdaki gözlerin dikey/yatay landmark mesafe oranı. ≥0.20 → uyanık, 0.10–0.20 → yarı uyanık, <0.10 → bilinç belirsiz.
  - **Pain score (PSPI basitleştirmesi):** Kaş içe-çatma mesafesi (landmark 55 ↔ 285, yüz genişliğine normalize) + göz kısma (1 − EAR). Gerçek PSPI 4 AU'nun toplamı; burada eğitilmiş classifier olmadan iki geometrik bileşen kullanılıyor.
  - **Face asymmetry:** 6 sol-sağ landmark çifti (göz, kaş, ağız köşesi, yanak) burun-orta-hattına göre yatay+düşey sapma → 0..1.
  - **expression_state:** `ağrı` (pain≥0.6) / `distres` (pain≥0.3) / `sakin` / `belirsiz`.
  - **consciousness_hint:** `uyanık` / `yarı_uyanık` / `belirsiz`.
  - **Confidence:** Geometrik proxy modunda max 0.55 (`sensor_type="geometric_proxy"`); trained model bağlandığında 0.95'e çıkar.

**Backend entegrasyonu:**
- `orchestration/schemas.py`:
  - `AgentObservation.agent` Literal'ine `"expression"` eklendi.
  - `AgentBundle`'a `expression: AgentObservation | None` alanı; `observations()` 5 ajanı döner.
- `orchestration/prompts/supervisor.py`:
  - Sistem prompt'u "beş bağımsız görsel ajan" olarak güncellendi.
  - Yüz İfadesi Ajanı Özel Kuralları bölümü eklendi: ağrı + başka anormallik → red; consciousness_hint=belirsiz + başka anormallik → red (bilinç kaybı şüphesi); face_asymmetry≥0.6 + başka anormallik → red (FAST/felç şüphesi).
  - `per_agent_weights` JSON şeması ve `missing_agents` set'i 5'lik.
- `orchestration/llm.py` MockLLMClient:
  - `weights` sözlüğü 5 anahtarlı.
  - Expression parsing bloğu: ağrı (pain≥0.6) tek başına sarı, başka anormallikle birleşirse kırmızı; asimetri/bilinç düşüklüğü başka anormallikle red'e katkı.
- `orchestration/demo.py` — 3 senaryoya expression observation eklendi:
  - Kırmızı: `expression_state="ağrı"`, pain=0.78, confidence=0.52.
  - Sarı: `expression_state="distres"`, pain=0.42, confidence=0.48.
  - Yeşil: `expression_state="sakin"`, pain=0.08, confidence=0.50.
- `gateway_agents/agents/__init__.py` — `ExpressionAgent` export.
- `gateway_agents/runner.py`:
  - `max_workers` 4→5.
  - `_analyze` 5. future submit eder; `_build_bundle` 5 ajan.
  - `close()` expression'ı da kapatır.

**Test güncellemeleri:**
- `gateway_agents/tests/test_agents.py`:
  - `TestExpressionAgent` sınıfı (3 test: empty/black/random frames).
  - Schema conformance parametrize'a `_expression_obs` eklendi.
- `gateway_agents/tests/test_runner.py`:
  - `test_run_once_returns_bundle_with_five_observations` (eski adı `four_observations`).
  - Payload kontrolü 5 ajan adı için.

**Frontend (sadece component entegrasyonu — redesign hariç):**
- `frontend/lib/types.ts` — `AgentObservation.agent` Literal'ine `"expression"`.
- `frontend/lib/signalLabels.ts` — Türkçe etiketler:
  - `expression_state` → Ağrı / Distres / Sakin / Belirsiz
  - `consciousness_hint` → Uyanık / Yarı Uyanık / Belirsiz
  - `pain_score`, `eye_openness`, `face_asymmetry` → yüzdelik display
  - `sensor_type` enum'ına `geometric_proxy` → "Geometrik Proxy", `trained_model` → "Eğitilmiş Model"
- `frontend/lib/agentReasons.ts` — Expression için reason hint'leri: geometric_proxy info pill, düşük face_ratio warn, düşük confidence warn.
- `frontend/components/AgentPanel.tsx`:
  - `AGENT_META`'ya expression (Smile ikonu, `text-violet-600` + `bg-violet-50`).
  - Grid `xl:grid-cols-4` → `xl:grid-cols-5`.
- `frontend/components/TriageCard.tsx`:
  - Per-agent ağırlık paneli `md:grid-cols-4` → `md:grid-cols-3 xl:grid-cols-5`.
  - 5. ajan etiketi "İfade" (kısa).
- `frontend/components/HistoryDetailModal.tsx`:
  - `AgentKey` 5'li.
  - `AGENT_META`'ya expression (Smile, violet).
- `frontend/components/useTriageStream.ts` — `AgentKey` 5'li.

**Doğrulama:**
- `python -m pytest gateway_agents/tests orchestration/tests -v` → **27/27 PASS** (eski 23 + 4 yeni: 3 ExpressionAgent + 1 schema conformance).
- `npx tsc --noEmit` → clean.

**Açık takipler (Faz 5 dışı — diğer fazlara taşındı):**
- Frontend tasarımı yenilenecek — kullanıcı mevcut Health-OS layout'tan tam memnun değil; yeni redesign turu ayrı planlanacak.
- `docs/teknik_rapor.md` 5 ajan iddiası artık koda uyumlu, hizalama tamamlandı (open karar listesinden çıkarılabilir).
- Eğitilmiş ağrı/mimik modeli (PSPI veya benzeri) entegrasyonu pilot fazına bırakıldı; hackathon kapsamı geometrik proxy ile yeterli.

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
- **Ajan sayısı:** Uygulama **5 ajan** (gait, skin, respiration, thermal, **expression** — 2026-05-16 eklendi). `docs/teknik_rapor.md`'deki 5 ajan iddiasıyla artık birebir hizalı.
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
