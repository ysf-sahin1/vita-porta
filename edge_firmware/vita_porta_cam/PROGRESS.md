# vita_porta_cam.ino — Gelişim Notları

ESP32-CAM (AI-Thinker klonu, OV2640, 4MB PSRAM) üzerinde çalışan Vita Porta edge firmware'inin baştan sona evrim notları. Kronolojik: hangi sorunla karşılaştık, neden o yola gittik, nasıl çözdük.

---

## Donanım

| Bileşen | Pin | Not |
|---|---|---|
| ESP32-CAM AI-Thinker klonu | — | Robocombo, 4MB PSRAM doğrulandı |
| Kırmızı LED (R) | GPIO 13 | ateş / kritik göstergesi |
| Yeşil LED (G) | GPIO 15 | normal göstergesi |
| AMG8833 SDA | GPIO 2 | strapping pin (flash sırasına dikkat) |
| AMG8833 SCL | GPIO 14 | eski mavi LED yeri |
| AMG8833 VIN | 3.3V | flashlamadan önce **çek**, sonra geri tak |
| AMG8833 GND | GND | RGB GND ile aynı raya |

**Neden bu pinler:** AI-Thinker klonunda GPIO 21/22 (varsayılan I2C) header'a çıkmamış — kamera dahili kullanıyor. Açık header pinleri arasından çakışmasız tek temiz kombinasyon `SDA=IO2 + SCL=IO14`. IO4 flash LED, IO12 boot brick riski. AMG breakout'unda dahili 10 kΩ pull-up var, ek direnç gerekmez.

**Karşılığı:** RGB modülün mavi (B) bacağı feda edildi — IO14 yeniden tahsis. Yellow/şüpheli durumu artık kırmızının yanıp sönmesi ile gösteriliyor.

---

## Aşama 1 — Temel kamera + Wi-Fi

İlk versiyon: VGA (640×480) MJPEG canlı yayın.

- `esp_http_server` port 81'de `/stream` (MJPEG multipart)
- `WebServer` port 80'de `/`, `/capture`, `/info`
- FPS ölçümü, bytes_sent, heap monitoring
- Wi-Fi `STA` mode, RSSI log

**Ampirik bulgu (kalıcı):** Bu klon için VGA tavanı ~10 FPS. `xclk=20MHz + fb_count=2` denendi → 3-4 FPS (PSRAM bandwidth tıkanıklığı). En iyi `xclk=20MHz`, `fb_count=2`, `jpeg_quality=10`, `CAMERA_GRAB_LATEST`. Daha yüksek FPS için resolution düşürmek gerekir (HVGA ~15 FPS, QVGA ~25 FPS).

---

## Aşama 2 — RGB LED test döngüsü

İlk olarak R/G/B'yi 1 sn'de bir sırayla yakan döngü kondu — kabloların doğru bağlandığını ve pinlerin sürdüğünü doğrulamak için. Bu döngü Aşama 5'te AMG entegrasyonuyla **kaldırıldı** (IO14 artık SCL).

---

## Aşama 3 — AMG8833 standalone test (`amg8833_test.ino`)

Sensörü ayrı bir sketch'le doğruladık önce. Tarayıcıdan 8×8 renkli heatmap, I2C tarama, AMG status, manuel rescan butonu.

**Çıkan veri:** 64 pikselin ortalaması alın sensöre dayalıyken bile 34.5°C civarı. Beklenenden çok düşük.

**Sebep (analiz):** AMG8833'ün 8 pikseli yatayda 60° FOV görüyor — pixel başına ~7.5° angular. 20 cm mesafede her piksel ~2.6 cm × 2.6 cm bir alana bakıyor. Alın o alanın yarısını doldurur, kalan yarısı duvar/saç/hava. Sonuç: `T_pixel ≈ 0.5·T_alın + 0.5·T_ortam`. Aritmetik doğru, hedefleme yanlış.

---

## Aşama 4 — Cilt sıcaklığı çıkarımı v1 (blob detection)

Ortalama atılır, **en sıcak bağlı bölge** bulunur.

```
1. Global max + early exit (max < 28°C → kimse yok)
2. Cilt aday maskesi: [gmax - SKIN_GRADIENT_C, SKIN_MAX_C] aralığı
3. 4-komşu BFS ile tüm bağlı bileşenleri tara, en büyüğü seç
4. blob < min piksel → sinyal yetersiz
5. skin_temp_raw = blob top-%50 ortalaması
6. ambient = blob dışı piksellerin medyanı (ortalama outlier'a hassas, medyan robust)
7. delta_t = raw - ambient
```

`/grid` JSON `person_present`, `skin_temp`, `blob_mask` ile genişledi. Heatmap UI'sında blob piksellerine beyaz çerçeve + glow.

**Sonuç:** ortamdan ayrışmış tek bir sayı çıktı, ama hâlâ 32-33°C okuyordu (gerçek alın 36-37 olmalı).

---

## Aşama 5 — Ana kamera sketch'ine entegrasyon

`amg8833_test.ino`'daki algoritma `vita_porta_cam.ino`'ya taşındı. Şimdi tek MCU, tek IP, tek sayfa:

- `:81/stream` MJPEG (mevcut)
- `:80/thermal` ham 64 pixel + skin çıkarım JSON (yeni)
- `:80/` ana sayfa: solda video + kamera istatistikleri, sağda termal grid + skin_temp göstergesi

LED test döngüsü silindi. Yeni davranış: `person_present && skin_temp ≥ 37.5` → kırmızı, normal cilt → yeşil, kimse yok → ikisi sönük.

### Sorun: Flash mode hatası (`Wrong boot mode detected (0xb)`)

İlk yüklemede `esptool` "wrong boot mode" döndü. Sebep: AMG SDA → IO2 strapping pini. AMG breakout'unda dahili pull-up IO2'yi HIGH'a çekiyor → ESP32 GPIO0=GND olmasına rağmen download mode'a giremiyor.

**Çözüm:** Flashlama sırasında AMG VIN kablosunu **geçici çek**. Sensör güçsüz kalınca dahili pull-up devre dışı, IO2 floating + GPIO0=GND → temiz download mode. Flash bitince VIN tekrar tak.

### Sorun: AMG sonradan takıldığında bulunmuyor

`initAMG()` sadece setup'ta bir kez çağrılıyordu. VIN sonradan takılınca firmware fark etmiyor → RST'siz tekrar bulamıyor.

**Çözüm:** Loop'a auto-rescan eklendi — `amg_ok=false` iken her 2 sn sessizce `amg.begin()` dener. Bulduğu an `[AMG] OK @ 0x69` yazar. Plus `GET /thermal/rescan` manuel tetik endpoint'i.

---

## Aşama 6 — Cilt sıcaklığı v2: delta-gain + EWMA + NVS kalibrasyon

Hâlâ 32-33 okuyordu çünkü top-50% ortalama hâlâ dilution içeriyordu ve sabit +1.2°C ofset uzaklığa adapte olmuyordu.

**Değişiklikler:**

1. **Top-2 max** (top-%50 yerine) — en "saf cilt" pikselleri, dilution minimum
2. **Delta-gain kompansasyon**: `T_comp = T_raw + K·(T_raw - T_ambient) + BASE` — soğuk oda + sıcak alın deltası büyük olunca düzeltme de büyür
3. **EWMA temporal smoothing** (α=0.30) — sensör titreşimini (~±0.5°C) söndür
4. **Tighter blob gradient** (2.5 → 1.5°C) — saç/kaş hariç tut
5. **NVS Preferences** ile kalibrasyon persist — reset/flash sonrası bile kalır (NVS ayrı partition)
6. **`/thermal/calibrate?ref=36.7`** — termometre ile bir kez çağır, K otomatik çözülür, NVS'e yazılır
7. **`/thermal/reset_calibration`** — fabrikaya dön

**Sonuç:** yakında doğru okuyor (35-37°C aralığı).

---

## Aşama 7 — Strict gating (sıkı kapı)

Algoritma blob bulduğu an ölçüm raporluyordu. El, kahve fincanı, sıcak yer de blob olabiliyordu.

**Sıkı koşullar:**
- `blob_size ≥ 4` piksel (forehead minimum, ~2×2 blok)
- `raw_max ≥ 30.5°C` (soğuk el filtresi)
- `ΔT ≥ 5°C` (yeterli kontrast)
- **3 ardışık frame** stabilite (600 ms pencere)
- Harici `/thermal/gate?face=1` (gateway face mesh, opsiyonel — TTL 5 sn, gateway susarsa AMG yetkili)

Hiçbiri sağlanmazsa `skin_temp = 0`, `person_present = false`, ekran `--`, sebep Türkçe gösterilir (`"alnini yaklasti"`, `"soguk_kaynak"`, `"stabilite_bekleniyor"` vb.).

---

## Aşama 8 — Distance-aware quality + UX hints + klinik sınıflandırma

Sıkı gate iyi ama hâlâ mesafe körü. Yakın bir el (raw=33, dT=6) gate'i geçebilir. AMG'nin sweet spot'unu (12-22 cm) tanıyan, alnı diğer cisimlerden ayırt eden zenginleştirme:

### Yeni hesap katmanları

**Blob geometrisi** (yeni globaller `blob_centroid_r/c`, `blob_bbox_*`, `blob_aspect`, `blob_compactness`, `blob_uniformity`):
- Centroid alın merkeze yakın olmalı
- Aspect ratio: forehead 1.0-2.0, uzun streak 3+ → ceza
- Compactness: forehead dolu kutu (~0.7-1.0), çubuk seyrek (~0.3)

**Mesafe tahmini** — iki bağımsız sinyal:
- A) `blob_size ∝ 1/d²` → `d = sqrt(K_SIZE / blob_size)`
- B) Pixel-fill faktörü `f = (raw - amb) / (T_skin_expected - amb)` → `d = K_FILL / sqrt(f)`
- İkisinin ortalaması + confidence (uyum derecesi)

**Quality score** (Q ∈ [0,1]):
- 0.35·thermal + 0.25·distance + 0.25·alignment + 0.15·shape
- Gate yeni şartı: `Q ≥ 0.60`

**UX hints** — en zayıf alt skora göre yönlendirme:
- `"yaklas (28cm)"`, `"uzaklas (cok yakin, doygunluk)"`
- `"merkezle (asagi sola)"` — centroid yönü dahil
- `"alnini cevir / dik tut"`, `"sabit tut (2/3)"`
- `"iyi (78%)"`, `"mukemmel (94%)"`

**Klinik sınıflandırma** — 6 katman:

| Sınıf | Aralık (°C) | LED |
|---|---|---|
| HİPOTERMİ | < 35.5 | kırmızı steady |
| NORMAL | 35.5 – 37.4 | yeşil steady |
| HAFİF YÜKSEK (subfebril) | 37.5 – 37.9 | yeşil 1 Hz blink |
| ATEŞ | 38.0 – 38.9 | kırmızı steady |
| AŞIRI ATEŞ | 39.0 – 39.9 | kırmızı 2.5 Hz blink |
| **HAVALE RİSKİ** (hyperpyrexia) | ≥ 40.0 | kırmızı 5 Hz blink + glow |

### Yeni endpoint
`GET /thermal/calibrate_distance?d=15` — cetvelle bilinen mesafede çağır, `K_SIZE` ve `K_FILL` çözülür, NVS'e yazılır.

### HTML
- Klinik renk-kodlu pill (NORMAL yeşil / ATEŞ turuncu / HAVALE RİSKİ pulsing kırmızı glow)
- Hint kutusu (renkli, büyük punto)
- Mesafe çubuğu (0-40 cm, optimal bant 12-22 yeşil arka plan, marker pozisyon)
- Kalite çubuğu (0-100% gradient + 4 alt skor)

---

## Aşama 9 — Pixel-fill inversion (mesafe-bağımsız doğru kompansasyon)

**Sorun (kullanıcı raporu):** sensörü kendinden uzaklaştırınca `skin_temp = 35°C` → "hipotermi" yanılgısı. Yakında doğru, uzakta sapıyor.

**Kök neden:** delta-gain formülü lineer:
```
T_comp = T_raw + K·(T_raw - T_ambient) + BASE
```
Ama gerçek fizik **lineer değil**. Pixel-fill faktörü `f` mesafeyle hızla düşer (~1/d²), delta da düşer, K=0.40 yetmez. Uzakta f=0.3 olduğunda raw 28°C, delta 4 → comp ≈ 30 = hipotermi.

**Doğru çözüm:** pixel-fill mixing'i matematiksel olarak tersine çevir.
```
T_raw = f · T_skin + (1 - f) · T_ambient
↓
T_skin = (T_raw - (1 - f) · T_ambient) / f
```

`f`'yi `computeDistance` zaten tahmin ediyor. Her mesafede tutarlı sonuç:

| d | T_raw | T_amb | f | Eski delta-gain | Yeni pixel-fill |
|---|---|---|---|---|---|
| 10 cm | 35.5 | 24 | 0.95 | 39.9 ❌ | 36.1 ✓ |
| 15 cm | 33.5 | 24 | 0.75 | 37.7 ✓ | 36.7 ✓ |
| 25 cm | 30.0 | 24 | 0.45 | 33.2 ❌ | 37.3 ✓ |
| 30 cm | 28.5 | 24 | 0.35 | 31.6 ❌ | 36.4 ✓ |

`f < 0.25` durumunda (çok uzak, ters çevirme patlar) **agresif lineer fallback** (`K=1.2`). Sonra **fiziksel clamp** `[28, 43]°C` sanity için.

### Bonus iyileştirmeler (aynı PR'da)

**Measurement confidence** — pixel-fill, mesafe ve Q'ya göre 3 seviye:
- HIGH: `f ≥ 0.40 + d ∈ [10,22] + Q ≥ 0.75` — tıbbi karar verilebilir
- MEDIUM: `f ≥ 0.25 + d ≤ 28` — bilgi amaçlı
- LOW: aksi — yaklaş

Sıcaklığın yanında küçük renkli badge: ✓ yüksek (yeşil), ~ orta (sarı), ! düşük (kırmızı).

**Classification hysteresis** — sınıf flickering'i önle:
- 35.4 ↔ 35.6 arası gidip gelmek pill'i değiştirmesin
- Sınır geçişine 0.3°C sticky margin (sadece gerçekten geçince güncelle)

**Kalibrasyon semantiği güncellendi:**
- Eski: `calibrate?ref=X` → K_DELTA çözer
- Yeni: `calibrate?ref=X` → pixel-fill inversion sonrası `T_pf` hesapla, `base_offset = ref - T_pf` (residual additive)
- Çok daha basit ve robust: tek bir ofset değeri kullanıcının termometresine yapışmayı sağlar

---

## Aşama 10 — Supervisor verdict entegrasyonu + son emin ölçüm

Firmware artık projenin geri kalanıyla konuşmaya hazır. İki temel değişiklik:

### `/verdict?level=red|yellow|green|insufficient`

Gateway supervisor LLM karar verince bu endpoint'i çağırır. LED **artık verdict-driven**:

- `RED` → kırmızı steady (anormal/kritik)
- `YELLOW` → kırmızı 1 Hz blink (şüpheli)
- `GREEN` → yeşil steady (normal)
- `INSUFFICIENT` → ikisi sönük (veri yetersiz)
- Stale (10 sn cevap yok) → ikisi sönük (gateway down açıkça görünür)

Eski klinik sınıflandırmaya dayalı LED davranışı **kaldırıldı**. (Aşama 11'de klinik sınıflandırma firmware'den tamamen çıkarıldı — bkz aşağı.)

### Last confirmed measurement

`confidence >= MEDIUM` olduğu her frame'de "son emin ölçüm" güncellenir:

```c
last_confirmed_skin_temp, last_confirmed_class, last_confirmed_label,
last_confirmed_distance, last_confirmed_quality, last_confirmed_ms
```

Gateway `/thermal` pull ettiğinde anlık değer **düşük güvenli** olsa bile **son emin değer** korunur. JSON'da `last_confirmed` bloğu + `age_ms` ile yaşı görünür. Kullanıcı momentary olarak kameradan çekildiğinde gateway "son ne biliyordum"u kaybetmiyor.

Ana sayfada büyük "Supervisor Verdict" pill (renkli, glow/pulse animasyon) + altta "Son emin ölçüm: 36.5°C (normal) · 17cm · Q=0.84 · 1.2s once" kutusu.

### Serial log

```
[SKIN] skin=36.45C raw=33.20 amb=24.30 dT=8.90 d=16cm Q=0.82 conf=3
[VERDICT] GREEN (age=420ms src=supervisor)
[LAST] skin=36.45C age=420ms d=16cm
```

---

## Aşama 11 — Klinik sınıflandırma tamamen kaldırıldı (firmware etiketsiz)

**Sorun (felsefe):** Aşama 8-10'da firmware skin_temp'i 6 klinik sınıfa (`hipotermi/normal/subfebril/ateş/aşırı ateş/havale riski`) bölüyor, `/thermal` JSON'unda `classification.label` ve `last_confirmed.label` olarak yolluyordu. LED artık verdict-driven olduğu için bu bilgi firmware için kullanılmıyordu; sadece gateway → LLM'e taşınıyordu.

İki yerde karar mantığı tutmak (firmware sınıflandırır, LLM tekrar yorumlar) tek-doğruluk ilkesini bozuyor. LLM'in görmesi gereken **ham** sinyali firmware şekillendiriyor.

**Çözüm:** Sınıflandırma firmware'den tamamen çıkarıldı. Silinen kısımlar:

- `TempClass` enum (7 değer) + `temp_class`, `temp_class_label`, `temp_class_prev` globalleri
- `classifyTemp()` / `classifyRaw()` / `classLabel()` fonksiyonları
- Hysteresis state (`HYSTERESIS_C`, sınır geçişi mantığı)
- `TEMP_HYPOTHERMIA_C` … `TEMP_HIGH_FEVER_MAX_C` + `FEVER_THRESHOLD_C` define'ları
- `/thermal` JSON'unda `classification:{class,label}` bloğu
- `last_confirmed` içinde `class` ve `label` alanları
- Ana HTML sayfasında klinik renk-class CSS (`.big.hypothermia`, `.pill.fever`, …) ve `cls` span'ı, JS `classMap`
- Serial `[SKIN] / [LAST]` log'larındaki label prefix'i

**Sözleşme (gateway için):** Firmware artık sadece sayı yollar — `skin_temp`, `skin_temp_raw`, `skin_temp_comp`, `ambient`, `delta_t`, `blob_*`, `distance.*`, `quality.*`, `confidence.{level,label,pixel_fill}`, `last_confirmed.{skin_temp, distance_cm, quality, blob_size, conf, age_ms}`. Etiket gelmez.

**Akış (canonical):**
```
ESP32-CAM (görüntü + ham sıcaklık)
   │
   ▼
Gateway (3 ajan: hareket/postür + yüz ifadesi + sıcaklık)
   │
   ▼
Supervisor LLM (klinik yorum + verdict)
   │
   ▼
ESP /verdict?level=red|yellow|green|insufficient
   │
   ▼
LED (sadece verdict'in dışavurumu)
```

`evaluateConfidence()` ve `Q ≥ 0.60` gate koşulları firmware'de **kalır** — bunlar veri kalitesi/gürültü filtresi, klinik karar değil. Gateway "MEDIUM/HIGH confidence" değerini direkt sinyal kalitesi bilgisi olarak kullanabilir.

---

## Endpoint özeti

| Endpoint | Method | İş |
|---|---|---|
| `/` | GET | Ana sayfa (video + termal + kontroller) |
| `/capture` | GET | Tek JPEG kare |
| `/info` | GET | Kamera + thermal özet JSON |
| `:81/stream` | GET | MJPEG canlı akış |
| `/thermal` | GET | 64 pixel + skin + geometry + distance + quality + confidence (etiket YOK — sadece ham sayılar) |
| `/thermal/rescan` | GET | Manuel AMG yeniden bulma |
| `/thermal/calibrate?ref=X` | GET | Termometre değeriyle residual offset NVS'e yaz |
| `/thermal/calibrate_distance?d=X` | GET | Cetvel mesafesiyle K_SIZE/K_FILL NVS'e yaz |
| `/thermal/reset_calibration` | GET | Tüm kalibrasyonları fabrika defaultlarına |
| `/thermal/gate?face=0\|1` | GET | Gateway face mesh kapısı (TTL 5 sn) |
| `/verdict?level=red\|yellow\|green\|insufficient[&src=...]` | GET | Supervisor LLM kararı — LED'i sürer (TTL 10 sn) |

---

## Kullanım akışı (kullanıcı için)

1. **Flashlama**: AMG VIN kablosunu çek → upload → bitince VIN'i tak (auto-rescan 2 sn içinde bulur)
2. **İlk açılış**: tarayıcıdan IP'ye git, hint "kimse algilanmadi"
3. **Alın yaklaştır** ~15 cm: hint "stabilite_bekleniyor" → "iyi (78%)" → klinik pill belirir
4. **Mesafe kalibrasyonu** (opsiyonel ama önerilir): cetvelle 15 cm tut → input "15" → "Mesafe Kalibre" → K_size/K_fill kaydedilir, sonraki frame mesafe ölçümü cetvele yapışır
5. **Sıcaklık kalibrasyonu** (opsiyonel ama önerilir): termometre ile alın sıcaklığını ölç → input "36.7" → "Sıcaklık Kalibre" → residual offset kaydedilir, sonraki frame skin_temp termometreye yapışır

NVS sayesinde her iki kalibrasyon da reset/flash sonrası kalır.

---

## Bilinen sınırlar

- **AMG8833 datasheet doğruluğu**: ±2.5°C (tek piksel). Pixel-fill inversion + kalibrasyon ile pratik doğruluk ±0.5°C civarına çekilir, ama klinik onaylı bir cihaz değildir.
- **Hareket hassasiyeti**: alın titrek durursa EWMA smoothing'i (α=0.30) ~3 frame ile uyum sağlar (~600 ms). Sabit tutmak gerekir.
- **Çevresel termal kaynaklar**: alın yakınında çok sıcak başka bir kaynak (radyatör, lamba) blob'u kapabilir. Quality score `shape` skoru bunu kısmen eler ama %100 değil.
- **Hiperpyrexia kalibrasyon dışı**: 40°C üstü ölçümler pixel-fill modeli için outlier — `T_SKIN_EXPECTED=36` varsayımı bozulur. Bu aralıkta sapma artar (ama "havale riski" sınıfı yine de doğru tetiklenir, kesin değer ±1°C oynayabilir).
- **5G/Wi-Fi frame drop**: Wi-Fi RSSI < -70 dBm'de MJPEG akış tıkanabilir, termal JSON etkilenmez.

---

## Sonraki adımlar (firmware'in dışı)

- **Task #4 + #6 (gateway face mesh fusion)**: Backend `gateway_agents/agents/thermal.py` mevcut LAB-warmth proxy'sini ham AMG verisine geçir. MediaPipe Face Mesh alın landmark'larını AMG 8×8 ızgarasına homografi ile eşle. Alın altındaki AMG pikselleri direkt sample edilir, blob detection ROI olarak kullanılır. Firmware ham 64 pixel + features zaten publish ediyor.
- **Tier 2 ML fallback**: heuristic'ler yetmezse gateway'de scikit-learn küçük classifier (RandomForest ~50 ağaç) — 8×8 + features → (is_forehead, distance_cm) etiketli. Backend her frame'de `/thermal/gate?face=...` POST'la firmware'i besler. Firmware tarafında değişiklik gerekmez.
- **MQTT entegrasyonu**: Aşama 6 (PROJECT_EXPLORER.md'de "başlanmamış" olarak işaretli). `/thermal` JSON'ı HTTP yerine MQTT broker'a publish — gateway pull yerine push alır.
- **OTA firmware update**: kalibrasyonlar NVS'te kalır, sketch güncellenebilir hale gelir.

---

## Kod organizasyonu

Tek dosya: `vita_porta_cam.ino` (~1500 satır). Bölümler:

1. **Header** (include, define, globals) — satır 1-160
2. **Yardımcılar** (`sortFloatsDesc/Asc`, `bell`) — satır 240-265
3. **Algoritma fonksiyonları**:
   - `computeBlobGeometry()` — geometri
   - `computeDistance()` — 2-sinyal mesafe
   - `computeQuality()` — Q + UX hint
   - `classifyTemp()` + `classifyRaw()` + `classLabel()` — hysteresis ile sınıflandırma
   - `evaluateConfidence()` — güven seviyesi
   - `evaluateGate()` — sıkı kapı
   - `computeSkinTemp()` — ana pipeline (blob → geometry → distance → quality → gate → pixel-fill inversion → EWMA → classify)
4. **AMG yardımcıları**: `readAMG()`, `initAMG()`, `tryBeginAMG()`
5. **Kalibrasyon**: `loadCalibration()`, `saveCalibration()`
6. **HTTP handler'lar**: 10 endpoint
7. **Kamera + MJPEG**: `streamHandler`, `startStreamServer`, `handleCapture`, `initCamera`
8. **Ana sayfa**: `handleRoot` (CSS + JS gömülü)
9. **`setup()`** — Wi-Fi, kamera, AMG, NVS, route'lar
10. **`loop()`** — server.handleClient + periyodik AMG read + LED davranışı + 5 sn serial log

---

## Versiyon notu

Bu dosyanın güncel hali yukarıdaki tüm aşamaları içerir. Geri uyumluluk şart değildi — her aşamada en doğru mühendislik çözümü seçildi (eski hack'leri tutmaktansa baştan yaz).
