# Katkı Kuralları · Beitragshinweise

Vita Porta — Yaşam Kapısı projesine katkıda bulunduğunuz için teşekkürler!
Bu belge katkı sürecini hem Türkçe hem Almanca özetler.

---

## 🇹🇷 Türkçe

### Davranış kuralları
Bu proje acil servis triaj asistanlığı yapan bir sağlık teknolojisidir. Tüm
katkılar hasta güvenliği ve "Vita Porta tanı koymaz, son karar hemşireye
aittir" ilkesine saygılı olmalıdır.

### Geliştirme ortamı
```bash
git clone https://github.com/ysf-sahin1/vita-porta
cd vita-porta
pip install -e ".[dev]"        # Python bağımlılıkları + test araçları
cd frontend && npm install     # dashboard
```

### Dallanma (branch) ve commit
- `main` daima çalışır durumda kalmalı; doğrudan `main`'e push yapmayın.
- Özellik dalı açın: `feature/<kisa-aciklama>`, hata düzeltmesi: `fix/<konu>`.
- Commit mesajları açıklayıcı ve emir kipinde olsun
  (ör. `gateway: termal ajan zaman aşımını düzelt`).

### Pull Request açmadan önce
1. **Testler geçmeli:** `pytest` (Python) ve `npm run build` (frontend).
2. **Kod stili:** Python için `ruff`/`black`, TypeScript için `eslint`.
3. **Gömülü kod (firmware):** `edge_firmware/` altındaki `.ino` dosyaları
   Arduino-ESP32 çekirdeği ile derlenebilmeli; ISR'lar `IRAM_ATTR` olmalı,
   uzun işler ISR içinde yapılmamalı.
4. PR açıklamasında neyi neden değiştirdiğinizi yazın; ilgili issue'ya bağlayın.

### Hata bildirimi
Issue açarken: donanım (Pi / ESP32-CAM / sensör), adımlar, beklenen ve
gerçekleşen davranış, seri/log çıktısı ekleyin.

---

## 🇩🇪 Deutsch

### Verhaltenskodex
Vita Porta ist ein Gesundheitstechnik-Projekt zur Triage-Unterstützung. Alle
Beiträge müssen die Patientensicherheit und den Grundsatz „Vita Porta stellt
keine Diagnose — die finale Entscheidung trifft das Pflegepersonal“ achten.

### Entwicklungsumgebung
```bash
git clone https://github.com/ysf-sahin1/vita-porta
cd vita-porta
pip install -e ".[dev]"
cd frontend && npm install
```

### Branches & Commits
- `main` bleibt stets lauffähig; keine direkten Pushes auf `main`.
- Feature-Branch `feature/<kurz>`, Bugfix `fix/<thema>`.
- Aussagekräftige Commit-Nachrichten im Imperativ.

### Vor einem Pull Request
1. **Tests grün:** `pytest` und `npm run build`.
2. **Codestil:** `ruff`/`black` (Python), `eslint` (TypeScript).
3. **Firmware:** `.ino` unter `edge_firmware/` muss mit dem Arduino-ESP32-Kern
   kompilieren; ISRs mit `IRAM_ATTR`, keine langen Operationen in der ISR
   (Deferred Interrupt Handling verwenden).
4. Beschreibe im PR, was und warum geändert wurde; verlinke das Issue.

### Fehlerberichte
Bitte Hardware (Pi / ESP32-CAM / Sensor), Reproduktionsschritte, erwartetes vs.
tatsächliches Verhalten und Log-Ausgaben angeben.

---

## Lisans · Lizenz
Katkılarınız projenin [MIT lisansı](LICENSE) altında yayımlanır.
Mit dem Beitrag stimmst du der Veröffentlichung unter der [MIT-Lizenz](LICENSE) zu.
