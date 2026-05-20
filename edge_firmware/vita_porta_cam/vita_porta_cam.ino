// vita_porta_cam.ino — Kamera + Wi-Fi + MJPEG canlı yayın
//                       + AMG8833 termal sensör + ham cilt sıcaklığı ölçümü
// =================================================================
// Amaç: Vita Porta'nın 3 görsel ajanı (hareket/postür, yüz ifadesi, sıcaklık)
//       için canlı MJPEG + 8x8 termal grid + ham cilt sıcaklığı sayısı.
//
// Felsefe: Firmware veriyi ETİKETLEMEZ — sadece ham ölçüm yollar.
// Klinik karar (normal / şüpheli / anormal) ana bilgisayardaki LLM'e ait.
// Karar /verdict?level=... ile geri gelir, LED'i sürer.
//
// Çözünürlük: VGA (640x480) — face mesh ve pose detection için minimum.
// Hedef FPS: ~10 (bu klon için ampirik tavan).
//
// Endpoint'ler:
//   - Port 80  /          → ana sayfa (canlı görüntü + termal + istatistikler)
//   - Port 80  /capture   → tek JPEG kare yakala
//   - Port 80  /info      → JSON: çözünürlük, FPS, RSSI, uptime, thermal özet
//   - Port 80  /thermal   → JSON: ham 64 piksel + skin_temp + blob_mask (etiket YOK)
//   - Port 80  /verdict   → LLM kararını al, LED'i sür
//   - Port 81  /stream    → MJPEG canlı akış (gateway buradan çeker)

#include "esp_camera.h"
#include "esp_http_server.h"
#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_AMG88xx.h>
#include <Preferences.h>

// ============================================================
//  ⚙️  WI-FI BİLGİLERİNİ BURAYA GİR
// ============================================================
const char* WIFI_SSID     = "FiberHGW_ZT73ZD";
const char* WIFI_PASSWORD = "DAbahR9PzRFY";
// ============================================================

// ----- AI-Thinker ESP32-CAM pin haritası -----
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ----- LED + AMG8833 I2C pinleri -----
// RGB modülün mavi (B) bacağı IO14'ten ÇEKİLDİ — o pin AMG8833 SCL'e ayrıldı.
// Final eşleme: R=kırmızı (ateş/kritik), G=yeşil (normal), B=feda.
// "Yellow/şüpheli" durumu kırmızı blink ile gösterilir.
#define LED_R_PIN   13
#define LED_G_PIN   15
#define I2C_SDA_PIN  2
#define I2C_SCL_PIN 14

// AMG8833 cilt çıkarım sabitleri (v2: delta-gain kompansasyon)
//
// Fizik: her piksel kendi FOV koni içindeki tüm sıcaklıkların ağırlıklı ortalamasını
// verir. Alın bir pikselin %50-70'ini doldurursa: T_pixel ≈ f*T_skin + (1-f)*T_bg.
// Bu yüzden ham max 32-33°C okuyabilir oysa gerçek alın 36°C'dir. Düzeltme:
//     T_compensated = T_max + K_DELTA * (T_max - T_ambient) + BASE_OFFSET
// K_DELTA emisivite + pixel fill factor + mesafe etkilerini tek katsayıda toplar.
// Kalibrasyon: termometre ile bir kez /thermal/calibrate?ref=X çağır, K kaydedilir.
#define SKIN_GRADIENT_C        1.5f   // blob gradyanı (tighter — saç/kaş hariç tut)
#define SKIN_MIN_PIXELS        2      // 2 piksellik blob bile geçerli (uzak alın)
#define SKIN_MAX_C             40.0f
#define SKIN_MIN_GLOBAL_MAX_C  27.5f  // bu üstü piksel yoksa "kimse yok"
#define SKIN_TOP_K             2      // skin_temp_raw = en sıcak K pikselin ortalaması

// Kalibrasyon defaults (NVS'te yoksa bunlar kullanılır)
#define DEFAULT_K_DELTA       0.40f   // (raw - ambient) çarpanı
#define DEFAULT_BASE_OFFSET   0.80f   // emisivite + sabit ofset
#define DEFAULT_EWMA_ALPHA    0.30f   // temporal smoothing (1.0 = smoothing yok)

// --- Strict gating (gerçek alın algılanmadan ölçüm raporlama) ---
// Amaç: hot blob algılansa bile, kriterler yeterli "alın" sinyali değilse
// skin_temp raporlanmaz. El, kahve fincanı, kısa flaş gibi false positive'leri eler.
#define GATE_MIN_BLOB        4        // forehead minimum piksel sayısı (~2x2 blok)
#define GATE_MIN_RAW_C       30.5f    // bunun altı: el ya da rastgele sıcak yüzey
#define GATE_MIN_DELTA_C     5.0f     // alın-ortam kontrastı yeterli mi
#define GATE_STABILITY_N     3        // ardışık frame sayısı (200ms x N stabilite penceresi)
#define GATE_EXTERNAL_TTL_MS 5000     // bu süre içinde harici güncelleme yoksa face_gate stale

// --- Distance estimation + quality scoring ---
// AMG'nin sweet spot'unda ölçüm yapılsın. İki bağımsız sinyalle mesafe tahmini.
#define T_SKIN_EXPECTED_C        36.0f  // pixel-fill faktörü hesabı için referans
#define DEFAULT_K_SIZE           1800.0f // distance = sqrt(K_SIZE / blob_size)
#define DEFAULT_K_FILL           10.0f   // distance = K_FILL / sqrt(fill_ratio)
#define DISTANCE_OPTIMAL_MIN_CM  12.0f   // sweet spot alt sınırı
#define DISTANCE_OPTIMAL_MAX_CM  22.0f   // sweet spot üst sınırı
#define DISTANCE_MAX_CM          40.0f   // bunun üstünde signal-to-noise düşer
#define DISTANCE_MIN_CM           6.0f   // bunun altında piksel doygunluğu
#define QUALITY_GATE_MIN         0.60f   // birleşik Q skoru bu üstüyse gate açılır
#define QUALITY_THERMAL_W        0.35f   // alt skor ağırlıkları (toplam 1.0)
#define QUALITY_DISTANCE_W       0.25f
#define QUALITY_ALIGNMENT_W      0.25f
#define QUALITY_SHAPE_W          0.15f

// Klinik sınıflandırma firmware'den kaldırıldı — etiketleme (hipotermi/ateş/havale)
// karar zincirinin tek sahibi olan ana bilgisayar LLM'ine bırakıldı. Firmware sadece
// ham sayısal ölçüm yollar; karar `/verdict` endpoint'iyle geri gelir ve LED'i sürer.

WebServer server(80);
httpd_handle_t stream_httpd = NULL;
Adafruit_AMG88xx amg;
Preferences prefs;

// Akış metrikleri (basit, atomik olması gerekmiyor — sadece monitoring)
volatile uint32_t frames_sent     = 0;
volatile uint32_t bytes_sent      = 0;
volatile uint32_t last_frame_ms   = 0;
volatile float    measured_fps    = 0.0f;
volatile uint32_t current_w       = 0;
volatile uint32_t current_h       = 0;
volatile uint32_t last_frame_size = 0;

// AMG8833 durumu
float    amg_pixels[AMG88xx_PIXEL_ARRAY_SIZE];
float    amg_min_v = 0, amg_max_v = 0, amg_avg_v = 0, amg_thermistor_v = 0;
float    skin_temp_raw_v   = 0;   // top-K blob ortalaması (sensör ham)
float    skin_temp_comp_v  = 0;   // delta-gain sonrası, EWMA öncesi
float    skin_temp_v       = 0;   // final, EWMA smoothed (rapor edilen)
float    ambient_v         = 0;
float    delta_t_v         = 0;
uint8_t  blob_size_v       = 0;
uint8_t  blob_mask_v[AMG88xx_PIXEL_ARRAY_SIZE] = {0};
bool     person_present    = false;
bool     amg_ok            = false;
uint32_t amg_read_count    = 0;
uint32_t amg_last_read_ms  = 0;
String   amg_status        = "henuz baslatilmadi";

// Kalibrasyon parametreleri (NVS'ten yüklenir, runtime'da güncellenir)
float    cfg_k_delta       = DEFAULT_K_DELTA;
float    cfg_base_offset   = DEFAULT_BASE_OFFSET;
float    cfg_ewma_alpha    = DEFAULT_EWMA_ALPHA;
String   cfg_calibrated_at = "fabrika defaults";

// Gate durumu
bool     blob_detected     = false;   // ham blob var mı (debug için)
bool     gate_amg          = false;   // AMG sıkı kapı koşullarını geçti mi
bool     gate_external     = true;    // gateway face_present (default: AMG yetkili)
uint32_t gate_external_last_ms = 0;   // son harici güncelleme zamanı
uint8_t  gate_stability_count  = 0;   // ardışık geçerli frame sayısı
String   gate_reason       = "init";  // teşhis için "open" / "blob_kucuk" / vb.

// Blob geometrisi (computeBlobGeometry sonrası doldurulur)
float    blob_centroid_r   = 3.5f;    // 0..7
float    blob_centroid_c   = 3.5f;    // 0..7
uint8_t  blob_bbox_rmin    = 0;
uint8_t  blob_bbox_rmax    = 0;
uint8_t  blob_bbox_cmin    = 0;
uint8_t  blob_bbox_cmax    = 0;
float    blob_aspect       = 1.0f;    // max/min boyutu
float    blob_compactness  = 0.0f;    // size / (w*h)
float    blob_uniformity   = 0.0f;    // blob içi std (°C)

// Mesafe tahmini
float    distance_est_cm   = 0;       // birleştirilmiş tahmin (cm)
float    distance_from_size = 0;      // blob-size yöntemi
float    distance_from_fill = 0;      // pixel-fill yöntemi
float    distance_confidence = 0;     // iki yöntemin uyumu (0=çelişki, 1=mutabık)

// Quality score (0..1)
float    quality_score     = 0;
float    q_thermal         = 0;
float    q_distance        = 0;
float    q_alignment       = 0;
float    q_shape           = 0;
String   ux_hint           = "init";  // "yaklas", "merkezle", "iyi", vb.

// Ölçüm güveni — pixel-fill ve mesafe değerlendirmesi
// HIGH: f >= 0.4, distance 10-22cm, Q >= 0.75 → tıbbi karar verilebilir
// MEDIUM: f >= 0.25, distance <= 28cm           → bilgi amaçlı
// LOW: f < 0.25 veya distance > 28cm           → sapıtmış olabilir, "yaklas"
enum MeasureConfidence {
  CONF_NONE   = 0,
  CONF_LOW    = 1,
  CONF_MEDIUM = 2,
  CONF_HIGH   = 3,
};
MeasureConfidence measure_confidence = CONF_NONE;
String            confidence_label   = "yok";
float             pixel_fill_f       = 0;  // güncel pixel-fill tahmini (debug için JSON'a)

// --- Last confirmed measurement ---
// confidence >= MEDIUM olduğu anlardaki son ölçüm. Gateway bu değeri pull eder —
// anlık ölçümün düşük güvenli olduğu anlarda son emin değer korunur.
// Not: klinik sınıflandırma firmware'de yok; bu blok da etiket alanı taşımaz.
float       last_confirmed_skin_temp = 0;
float       last_confirmed_distance  = 0;
float       last_confirmed_quality   = 0;
uint8_t     last_confirmed_blob_size = 0;
uint8_t     last_confirmed_conf      = 0;
uint32_t    last_confirmed_ms        = 0;  // millis() at update time, 0 = never

// --- Supervisor verdict (LED'i süren state) ---
// Gateway supervisor LLM'i karar verince /verdict?level=red|yellow|green|insufficient
// çağırır. TTL içinde güncel kalmazsa "stale" sayılır, LED söner.
enum VerdictLevel {
  VERDICT_NONE         = 0,  // hiç set edilmemiş veya stale
  VERDICT_INSUFFICIENT = 1,
  VERDICT_GREEN        = 2,
  VERDICT_YELLOW       = 3,
  VERDICT_RED          = 4,
};
VerdictLevel verdict_level     = VERDICT_NONE;
uint32_t     verdict_last_ms   = 0;
String       verdict_source    = "";  // gateway'in opsiyonel context'i
#define VERDICT_TTL_MS         10000   // 10 sn — gateway bu süreye kadar yenilemeli

// Kalibrasyon — mesafe sabitleri (NVS'ten yüklenir)
float    cfg_k_size        = DEFAULT_K_SIZE;
float    cfg_k_fill        = DEFAULT_K_FILL;

#define PART_BOUNDARY "vitaportaboundary"
static const char* STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* STREAM_BOUNDARY     = "\r\n--" PART_BOUNDARY "\r\n";
static const char* STREAM_PART_HEADER  = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

// ---- Port 81: MJPEG akış handler + FPS ölçümü ----
static esp_err_t streamHandler(httpd_req_t* req) {
  camera_fb_t* fb = nullptr;
  char part_buf[64];

  esp_err_t res = httpd_resp_set_type(req, STREAM_CONTENT_TYPE);
  if (res != ESP_OK) return res;
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  httpd_resp_set_hdr(req, "X-Framerate", "30");

  uint32_t fps_window_start = millis();
  uint32_t fps_window_count = 0;

  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) {
      res = ESP_FAIL;
      break;
    }

    size_t hlen = snprintf(part_buf, sizeof(part_buf), STREAM_PART_HEADER, fb->len);
    res = httpd_resp_send_chunk(req, STREAM_BOUNDARY, strlen(STREAM_BOUNDARY));
    if (res == ESP_OK) res = httpd_resp_send_chunk(req, part_buf, hlen);
    if (res == ESP_OK) res = httpd_resp_send_chunk(req, (const char*)fb->buf, fb->len);

    // Metrikleri güncelle
    frames_sent++;
    bytes_sent += fb->len;
    last_frame_ms = millis();
    last_frame_size = fb->len;
    current_w = fb->width;
    current_h = fb->height;
    fps_window_count++;

    uint32_t elapsed = millis() - fps_window_start;
    if (elapsed >= 1000) {
      measured_fps = (fps_window_count * 1000.0f) / elapsed;
      fps_window_start = millis();
      fps_window_count = 0;
    }

    esp_camera_fb_return(fb);
    if (res != ESP_OK) break;
  }
  return res;
}

// ============================================================
//  AMG8833 — okuma + cilt sıcaklığı çıkarımı (hot-blob)
// ============================================================
static void sortFloatsDesc(float* arr, int n) {
  for (int i = 1; i < n; i++) {
    float x = arr[i]; int j = i - 1;
    while (j >= 0 && arr[j] < x) { arr[j + 1] = arr[j]; j--; }
    arr[j + 1] = x;
  }
}
static void sortFloatsAsc(float* arr, int n) {
  for (int i = 1; i < n; i++) {
    float x = arr[i]; int j = i - 1;
    while (j >= 0 && arr[j] > x) { arr[j + 1] = arr[j]; j--; }
    arr[j + 1] = x;
  }
}

// ============================================================
//  Blob geometri çıkarımı — centroid, bbox, aspect, compactness, uniformity
// ============================================================
void computeBlobGeometry() {
  // Default'lar (blob yoksa)
  blob_centroid_r = 3.5f;
  blob_centroid_c = 3.5f;
  blob_bbox_rmin = blob_bbox_rmax = blob_bbox_cmin = blob_bbox_cmax = 0;
  blob_aspect = 1.0f;
  blob_compactness = 0.0f;
  blob_uniformity = 0.0f;

  int n = 0;
  uint8_t rmin = 7, rmax = 0, cmin = 7, cmax = 0;
  float sum_r = 0, sum_c = 0, sum_t = 0, sum_t2 = 0;

  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    if (!blob_mask_v[i]) continue;
    int r = i >> 3, c = i & 0x7;
    if (r < rmin) rmin = r;
    if (r > rmax) rmax = r;
    if (c < cmin) cmin = c;
    if (c > cmax) cmax = c;
    sum_r += r; sum_c += c;
    sum_t += amg_pixels[i];
    sum_t2 += amg_pixels[i] * amg_pixels[i];
    n++;
  }
  if (n == 0) return;

  blob_centroid_r = sum_r / n;
  blob_centroid_c = sum_c / n;
  blob_bbox_rmin = rmin; blob_bbox_rmax = rmax;
  blob_bbox_cmin = cmin; blob_bbox_cmax = cmax;

  float w = (float)(cmax - cmin + 1);
  float h = (float)(rmax - rmin + 1);
  blob_aspect      = (w > h) ? (w / h) : (h / w);
  blob_compactness = (float)n / (w * h);

  // std dev (uniformity): blob piksellerinin sıcaklık dağılımı
  float mean = sum_t / n;
  float var  = (sum_t2 / n) - (mean * mean);
  blob_uniformity = (var > 0) ? sqrtf(var) : 0;
}

// ============================================================
//  Mesafe tahmini — iki bağımsız sinyal + confidence
// ============================================================
void computeDistance() {
  distance_est_cm = 0;
  distance_from_size = 0;
  distance_from_fill = 0;
  distance_confidence = 0;

  if (blob_size_v < 1) return;

  // Yöntem A — blob_size ∝ 1/d²
  // distance = sqrt(K_SIZE / blob_size)
  distance_from_size = sqrtf(cfg_k_size / (float)blob_size_v);

  // Yöntem B — pixel-fill faktörü
  // raw_max = f * T_skin + (1-f) * T_amb  →  f = (raw - amb) / (T_skin - amb)
  // distance = K_FILL / sqrt(f)
  float fill_denom = T_SKIN_EXPECTED_C - ambient_v;
  if (fill_denom > 1.0f) {
    float f = (skin_temp_raw_v - ambient_v) / fill_denom;
    f = constrain(f, 0.05f, 1.0f);
    distance_from_fill = cfg_k_fill / sqrtf(f);
  }

  // Birleştir — median'a yakın, iki yöntem mevcutsa ortalama
  if (distance_from_fill > 0) {
    distance_est_cm = (distance_from_size + distance_from_fill) * 0.5f;
    // Confidence: iki yöntem ne kadar uyumlu? |Δ| / mean
    float diff = fabsf(distance_from_size - distance_from_fill);
    float mean = distance_est_cm;
    distance_confidence = mean > 0 ? constrain(1.0f - (diff / mean), 0.0f, 1.0f) : 0;
  } else {
    distance_est_cm = distance_from_size;
    distance_confidence = 0.5f;  // tek sinyal — orta güven
  }
}

// ============================================================
//  Quality score — 4 alt skor + birleşik Q + UX hint
// ============================================================
// Bell curve: sweet spot içinde 1.0, kenarlara doğru azalır.
static float bell(float x, float lo, float hi, float min_x, float max_x) {
  if (x >= lo && x <= hi) return 1.0f;
  if (x < lo) {
    return constrain((x - min_x) / (lo - min_x), 0.0f, 1.0f);
  }
  return constrain((max_x - x) / (max_x - hi), 0.0f, 1.0f);
}

void computeQuality() {
  // Thermal contrast skoru — 8°C delta = mükemmel
  q_thermal = constrain(delta_t_v / 8.0f, 0.0f, 1.0f);

  // Distance skoru — sweet spot [12, 22] cm
  q_distance = bell(distance_est_cm,
                    DISTANCE_OPTIMAL_MIN_CM, DISTANCE_OPTIMAL_MAX_CM,
                    DISTANCE_MIN_CM, DISTANCE_MAX_CM);

  // Alignment skoru — centroid merkez (3.5, 3.5)'e ne kadar yakın
  float dr = blob_centroid_r - 3.5f;
  float dc = blob_centroid_c - 3.5f;
  float offset = sqrtf(dr * dr + dc * dc);
  q_alignment = constrain(1.0f - (offset / 3.5f), 0.0f, 1.0f);

  // Shape skoru — compactness yüksek + aspect makul
  float aspect_penalty = (blob_aspect > 2.5f) ? 0.0f : 1.0f - (blob_aspect - 1.0f) / 1.5f;
  aspect_penalty = constrain(aspect_penalty, 0.0f, 1.0f);
  q_shape = blob_compactness * aspect_penalty;

  // Birleşik Q
  quality_score = QUALITY_THERMAL_W   * q_thermal
                + QUALITY_DISTANCE_W  * q_distance
                + QUALITY_ALIGNMENT_W * q_alignment
                + QUALITY_SHAPE_W     * q_shape;

  // UX hint — en zayıf alt skoru bul, yönlendir
  if (blob_size_v < GATE_MIN_BLOB) {
    ux_hint = "yaklas (alin gorunmuyor)";
  } else if (q_distance < 0.5f && distance_est_cm > DISTANCE_OPTIMAL_MAX_CM) {
    ux_hint = "yaklas (" + String(distance_est_cm, 0) + "cm)";
  } else if (q_distance < 0.5f && distance_est_cm < DISTANCE_OPTIMAL_MIN_CM) {
    ux_hint = "uzaklas (cok yakin, doygunluk)";
  } else if (q_alignment < 0.5f) {
    String dir = "";
    if (blob_centroid_r < 2.5f) dir += "asagi ";
    else if (blob_centroid_r > 4.5f) dir += "yukari ";
    if (blob_centroid_c < 2.5f) dir += "saga";
    else if (blob_centroid_c > 4.5f) dir += "sola";
    if (dir.length() == 0) dir = "biraz";
    ux_hint = "merkezle (" + dir + ")";
  } else if (q_shape < 0.5f) {
    ux_hint = "alnini cevir / dik tut";
  } else if (q_thermal < 0.5f) {
    ux_hint = "kontrast az (alın yeterince sıcak değil mi?)";
  } else if (gate_stability_count < GATE_STABILITY_N) {
    ux_hint = "sabit tut (" + String(gate_stability_count) + "/" + String(GATE_STABILITY_N) + ")";
  } else if (quality_score >= 0.85f && distance_est_cm <= 22.0f) {
    ux_hint = "mukemmel (" + String((int)(quality_score * 100)) + "%)";
  } else if (quality_score >= 0.65f && distance_est_cm > 22.0f) {
    // Gate açıldı ama mesafe sweet spot dışı — kullanıcıyı uyar
    ux_hint = "iyi ama yaklas (" + String(distance_est_cm, 0) + "cm, daha kesin olabilir)";
  } else {
    ux_hint = "iyi (" + String((int)(quality_score * 100)) + "%)";
  }
}

// Ölçüm güvenini hesapla — pixel-fill, mesafe ve quality skoruna göre
void evaluateConfidence() {
  if (!person_present) {
    measure_confidence = CONF_NONE;
    confidence_label = "yok";
    return;
  }
  bool high = (pixel_fill_f >= 0.40f) &&
              (distance_est_cm >= 10.0f) && (distance_est_cm <= 22.0f) &&
              (quality_score >= 0.75f);
  bool medium = (pixel_fill_f >= 0.25f) && (distance_est_cm <= 28.0f);
  if (high) {
    measure_confidence = CONF_HIGH;
    confidence_label = "yuksek";
  } else if (medium) {
    measure_confidence = CONF_MEDIUM;
    confidence_label = "orta";
  } else {
    measure_confidence = CONF_LOW;
    confidence_label = "dusuk (uzak/sapma riski)";
  }
}

// Gate koşullarını değerlendir. Kapı kapanırsa skin_temp_v'yi söndürür ve sebebi yazar.
// Geri dönüş: true = gate açık, ölçüm raporlanabilir.
bool evaluateGate(int blob_size_local) {
  // AMG-iç temel koşullar (eski sıkı kapı)
  bool size_ok      = (blob_size_local >= GATE_MIN_BLOB);
  bool temp_ok      = (skin_temp_raw_v >= GATE_MIN_RAW_C);
  bool delta_ok     = (delta_t_v       >= GATE_MIN_DELTA_C);
  bool quality_ok   = (quality_score   >= QUALITY_GATE_MIN);
  bool frame_pass   = size_ok && temp_ok && delta_ok && quality_ok;

  if (frame_pass) {
    if (gate_stability_count < 255) gate_stability_count++;
  } else {
    gate_stability_count = 0;
  }
  gate_amg = (gate_stability_count >= GATE_STABILITY_N);

  // Harici (gateway) face gate: TTL içinde güncel mi
  bool ext_stale = (millis() - gate_external_last_ms) > GATE_EXTERNAL_TTL_MS;
  bool ext_open  = gate_external || ext_stale;

  bool gate_open = gate_amg && ext_open;

  // Sebep — Q tabanlı UX hint zaten daha detaylı, gate_reason kısa kategori
  if (!size_ok)              gate_reason = "blob_kucuk (" + String(blob_size_local) + "/" + String(GATE_MIN_BLOB) + ")";
  else if (!temp_ok)         gate_reason = "soguk_kaynak";
  else if (!delta_ok)        gate_reason = "kontrast_yetersiz";
  else if (!quality_ok)      gate_reason = "kalite_dusuk (Q=" + String(quality_score, 2) + ")";
  else if (!gate_amg)        gate_reason = "stabilite_bekleniyor (" + String(gate_stability_count) + "/" + String(GATE_STABILITY_N) + ")";
  else if (!ext_open)        gate_reason = "yuz_yok (gateway face_gate=0)";
  else                       gate_reason = "open";

  return gate_open;
}

void computeSkinTemp() {
  // Sıfırlamalar — kişi yoksa hepsi temiz başlangıç
  memset(blob_mask_v, 0, sizeof(blob_mask_v));
  blob_size_v       = 0;
  skin_temp_raw_v   = 0;
  skin_temp_comp_v  = 0;
  ambient_v         = amg_avg_v;
  delta_t_v         = 0;
  blob_detected     = false;
  person_present    = false;
  // Geometri/distance/quality default'ları
  computeBlobGeometry();  // blob_mask boş → default'lar geri gelir
  distance_est_cm = 0; quality_score = 0;
  q_thermal = q_distance = q_alignment = q_shape = 0;
  if (!amg_ok) {
    skin_temp_v = 0; gate_reason = "amg_yok"; ux_hint = "AMG sensor yok";
    return;
  }

  // 1) Global max — "kimse yok" erken çıkışı
  float gmax = amg_pixels[0];
  for (int i = 1; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    if (amg_pixels[i] > gmax) gmax = amg_pixels[i];
  }
  if (gmax < SKIN_MIN_GLOBAL_MAX_C) {
    skin_temp_v *= (1.0f - cfg_ewma_alpha);
    if (skin_temp_v < 1.0f) skin_temp_v = 0;
    gate_stability_count = 0;
    gate_amg = false;
    gate_reason = "ortam_soguk (max " + String(gmax, 1) + ")";
    ux_hint = "kimse algilanmadi";
    return;
  }

  // 2) Tighter blob: max'tan SKIN_GRADIENT_C içindeki pikseller (1.5°C — hair/brow exclude)
  float thresh = gmax - SKIN_GRADIENT_C;
  uint8_t candidate[AMG88xx_PIXEL_ARRAY_SIZE];
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    candidate[i] = (amg_pixels[i] >= thresh && amg_pixels[i] <= SKIN_MAX_C) ? 1 : 0;
  }

  // 3) En büyük bağlı bileşeni bul (BFS, 4-komşu)
  uint8_t visited[AMG88xx_PIXEL_ARRAY_SIZE] = {0};
  uint8_t best_mask[AMG88xx_PIXEL_ARRAY_SIZE] = {0};
  int     best_size = 0;
  int     queue[AMG88xx_PIXEL_ARRAY_SIZE];
  for (int start = 0; start < AMG88xx_PIXEL_ARRAY_SIZE; start++) {
    if (!candidate[start] || visited[start]) continue;
    uint8_t this_mask[AMG88xx_PIXEL_ARRAY_SIZE] = {0};
    int this_size = 0, qhead = 0, qtail = 0;
    queue[qtail++] = start; visited[start] = 1;
    while (qhead < qtail) {
      int idx = queue[qhead++];
      this_mask[idx] = 1; this_size++;
      int r = idx >> 3, c = idx & 0x7;
      const int dr[4] = {-1, 1, 0, 0};
      const int dc[4] = { 0, 0,-1, 1};
      for (int k = 0; k < 4; k++) {
        int nr = r + dr[k], nc = c + dc[k];
        if (nr < 0 || nr > 7 || nc < 0 || nc > 7) continue;
        int nidx = (nr << 3) | nc;
        if (candidate[nidx] && !visited[nidx]) {
          visited[nidx] = 1; queue[qtail++] = nidx;
        }
      }
    }
    if (this_size > best_size) {
      best_size = this_size;
      memcpy(best_mask, this_mask, sizeof(best_mask));
    }
  }
  blob_size_v = (uint8_t)best_size;
  memcpy(blob_mask_v, best_mask, sizeof(blob_mask_v));
  if (best_size < SKIN_MIN_PIXELS) {
    skin_temp_v *= (1.0f - cfg_ewma_alpha);
    if (skin_temp_v < 1.0f) skin_temp_v = 0;
    gate_stability_count = 0;
    gate_amg = false;
    gate_reason = "blob_yok";
    ux_hint = "kimse algilanmadi";
    return;
  }
  blob_detected = true;

  // 4) skin_temp_raw = blob'un EN SICAK K pikselinin ortalaması (spot-thermometer)
  float blob_vals[AMG88xx_PIXEL_ARRAY_SIZE];
  int bn = 0;
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    if (best_mask[i]) blob_vals[bn++] = amg_pixels[i];
  }
  sortFloatsDesc(blob_vals, bn);
  int top_k = bn < SKIN_TOP_K ? bn : SKIN_TOP_K;
  float top_sum = 0;
  for (int i = 0; i < top_k; i++) top_sum += blob_vals[i];
  skin_temp_raw_v = top_sum / top_k;

  // 5) Ambient = blob dışı piksellerin medyanı (outlier'a karşı robust)
  float bg_vals[AMG88xx_PIXEL_ARRAY_SIZE];
  int gn = 0;
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    if (!best_mask[i]) bg_vals[gn++] = amg_pixels[i];
  }
  if (gn > 0) {
    sortFloatsAsc(bg_vals, gn);
    ambient_v = bg_vals[gn / 2];
  }
  delta_t_v = skin_temp_raw_v - ambient_v;

  // 5.5) Geometri (centroid, bbox, aspect, compactness, uniformity)
  computeBlobGeometry();

  // 5.6) Mesafe tahmini (blob_size + pixel-fill bağımsız sinyallerinden)
  computeDistance();

  // 5.7) Quality score + UX hint
  computeQuality();

  // 6) Strict gate — boyut + raw + delta + Q ≥ 0.6 + stabilite + harici face
  bool gate_open = evaluateGate(best_size);
  if (!gate_open) {
    skin_temp_v *= (1.0f - cfg_ewma_alpha);
    if (skin_temp_v < 1.0f) skin_temp_v = 0;
    skin_temp_comp_v = 0;
    return;
  }
  person_present = true;

  // 7) Pixel-fill INVERSION kompansasyonu (mesafe-bağımsız doğru çözüm)
  //
  //    Sensör fiziği: T_raw = f·T_skin + (1-f)·T_ambient
  //    Tersine çevir: T_skin = (T_raw - (1-f)·T_ambient) / f
  //
  //    f, computeDistance içinde zaten tahmin edildi (skin_temp_raw_v / T_SKIN_EXPECTED_C
  //    oranıyla). Eski lineer delta-gain uzakta sapıyordu çünkü f hızlı düşerken
  //    formül onu yakalayamıyordu. Bu formül her mesafede tutarlı.
  float fill_denom = T_SKIN_EXPECTED_C - ambient_v;
  pixel_fill_f = 0;
  float t_skin_pf = skin_temp_raw_v;  // emniyet default
  if (fill_denom > 1.0f) {
    pixel_fill_f = constrain((skin_temp_raw_v - ambient_v) / fill_denom, 0.05f, 1.0f);
    if (pixel_fill_f >= 0.25f) {
      // Güvenli inversion bölgesi
      t_skin_pf = (skin_temp_raw_v - (1.0f - pixel_fill_f) * ambient_v) / pixel_fill_f;
    } else {
      // f çok küçük (çok uzak) → inversion patlar, lineer delta-gain'e geri düş
      // ama K_DELTA'yı agresif tut (1.0+) çünkü gerçekten uzaksak
      t_skin_pf = skin_temp_raw_v + 1.2f * delta_t_v + cfg_base_offset;
    }
  } else {
    // Ambient ≈ skin expected (alın oda sıcaklığında?) — anomali, raw'ı sun
    t_skin_pf = skin_temp_raw_v + cfg_base_offset;
  }

  // Residual kalibrasyon ofseti — kullanıcı termometre ile fine-tune ettiyse
  // cfg_base_offset post-inversion residual olarak yorumlanır
  skin_temp_comp_v = t_skin_pf + cfg_base_offset;

  // Fiziksel sanity clamp — termal yolda olabilecek aralık
  skin_temp_comp_v = constrain(skin_temp_comp_v, 28.0f, 43.0f);

  // 8) EWMA temporal smoothing
  if (skin_temp_v < 1.0f) {
    skin_temp_v = skin_temp_comp_v;
  } else {
    skin_temp_v = cfg_ewma_alpha * skin_temp_comp_v + (1.0f - cfg_ewma_alpha) * skin_temp_v;
  }

  // 9) Ölçüm güveni — pixel-fill + mesafe + Q skoruna göre LOW/MEDIUM/HIGH
  //    (Klinik sınıflandırma firmware'de yok; etiketleme gateway/LLM tarafında.)
  evaluateConfidence();

  // 10) "Son emin ölçüm" kaydet — sadece MEDIUM ve üstü güvende.
  //     Gateway pull ettiğinde anlık değer düşük güvenli olsa bile son emin değer korunur.
  if (measure_confidence >= CONF_MEDIUM) {
    last_confirmed_skin_temp = skin_temp_v;
    last_confirmed_distance  = distance_est_cm;
    last_confirmed_quality   = quality_score;
    last_confirmed_blob_size = blob_size_v;
    last_confirmed_conf      = (uint8_t)measure_confidence;
    last_confirmed_ms        = millis();
  }
}

void readAMG() {
  if (!amg_ok) return;
  amg.readPixels(amg_pixels);
  amg_read_count++;
  float pmin = amg_pixels[0], pmax = amg_pixels[0], psum = 0;
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    if (amg_pixels[i] < pmin) pmin = amg_pixels[i];
    if (amg_pixels[i] > pmax) pmax = amg_pixels[i];
    psum += amg_pixels[i];
  }
  amg_min_v = pmin; amg_max_v = pmax;
  amg_avg_v = psum / AMG88xx_PIXEL_ARRAY_SIZE;
  amg_thermistor_v = amg.readThermistor();
  computeSkinTemp();
}

// NVS'ten kalibrasyon parametrelerini yükle (yoksa default'lar kullanılır)
void loadCalibration() {
  prefs.begin("vp_thermal", true);  // read-only
  cfg_k_delta       = prefs.getFloat("k_delta",  DEFAULT_K_DELTA);
  cfg_base_offset   = prefs.getFloat("base_off", DEFAULT_BASE_OFFSET);
  cfg_ewma_alpha    = prefs.getFloat("alpha",    DEFAULT_EWMA_ALPHA);
  cfg_k_size        = prefs.getFloat("k_size",   DEFAULT_K_SIZE);
  cfg_k_fill        = prefs.getFloat("k_fill",   DEFAULT_K_FILL);
  cfg_calibrated_at = prefs.getString("note",    "fabrika defaults");
  prefs.end();
  Serial.printf("[CAL] K_delta=%.3f base=%.3f alpha=%.2f K_size=%.0f K_fill=%.1f (%s)\n",
                cfg_k_delta, cfg_base_offset, cfg_ewma_alpha,
                cfg_k_size, cfg_k_fill, cfg_calibrated_at.c_str());
}

void saveCalibration(const String& note) {
  prefs.begin("vp_thermal", false);  // read-write
  prefs.putFloat("k_delta",  cfg_k_delta);
  prefs.putFloat("base_off", cfg_base_offset);
  prefs.putFloat("alpha",    cfg_ewma_alpha);
  prefs.putFloat("k_size",   cfg_k_size);
  prefs.putFloat("k_fill",   cfg_k_fill);
  prefs.putString("note",    note);
  prefs.end();
  cfg_calibrated_at = note;
  Serial.printf("[CAL] Kaydedildi: K_delta=%.3f base=%.3f alpha=%.2f K_size=%.0f K_fill=%.1f (%s)\n",
                cfg_k_delta, cfg_base_offset, cfg_ewma_alpha,
                cfg_k_size, cfg_k_fill, note.c_str());
}

bool initAMG() {
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  Wire.setClock(100000);
  Serial.printf("[I2C] SDA=GPIO%d, SCL=GPIO%d, 100kHz\n", I2C_SDA_PIN, I2C_SCL_PIN);
  return tryBeginAMG(false);
}

// Sensörü yeniden algılamayı dener. quiet=true ise Serial log basmaz (sessiz retry).
bool tryBeginAMG(bool quiet) {
  if (amg.begin(0x69)) {
    amg_ok = true; amg_status = "OK @ 0x69";
  } else if (amg.begin(0x68)) {
    amg_ok = true; amg_status = "OK @ 0x68";
  } else {
    amg_ok = false; amg_status = "AMG bulunamadi (0x69/0x68 yok)";
  }
  if (!quiet || amg_ok) Serial.printf("[AMG] %s\n", amg_status.c_str());
  return amg_ok;
}

// ---- Port 80: /thermal/rescan — manuel yeniden bulma ----
void handleThermalRescan() {
  bool ok = tryBeginAMG(false);
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json",
              "{\"ok\":" + String(ok ? "true" : "false") +
              ",\"status\":\"" + amg_status + "\"}");
}

// ---- Port 80: /thermal/calibrate?ref=36.7 — pixel-fill üstüne residual çöz ----
//
// Yeni semantik (pixel-fill inversion sonrası):
//   T_pf = (T_raw - (1-f)·T_amb) / f          ← pixel-fill inversion
//   T_reported = T_pf + base_offset            ← residual additive offset
//   ref = T_pf + base_offset
//   → base_offset = ref - T_pf
//
// Kullanıcı termometreyle ölçtüğü gerçek alın sıcaklığını verir, biz residual'ı
// yakalayıp NVS'e yazarız. Reset/flash sonrası kalır.
void handleThermalCalibrate() {
  if (!amg_ok) {
    server.send(503, "application/json", "{\"error\":\"AMG yok\"}");
    return;
  }
  if (!person_present) {
    server.send(400, "application/json",
                "{\"error\":\"once alnini sensorede sabit tut (gate kapali olabilir)\"}");
    return;
  }
  if (!server.hasArg("ref")) {
    server.send(400, "application/json",
                "{\"error\":\"ref parametresi yok. ornek: /thermal/calibrate?ref=36.7\"}");
    return;
  }
  float ref = server.arg("ref").toFloat();
  if (ref < 30.0f || ref > 42.0f) {
    server.send(400, "application/json",
                "{\"error\":\"ref makul aralikta degil (30-42 C)\"}");
    return;
  }

  // Pixel-fill inversion sonucunu yeniden hesapla (offset hariç)
  float fill_denom = T_SKIN_EXPECTED_C - ambient_v;
  if (fill_denom <= 1.0f) {
    server.send(400, "application/json",
                "{\"error\":\"ambient cok yuksek — daha soguk ortamda kalibre et\"}");
    return;
  }
  float f = constrain((skin_temp_raw_v - ambient_v) / fill_denom, 0.05f, 1.0f);
  if (f < 0.3f) {
    server.send(400, "application/json",
                "{\"error\":\"alnini biraz yaklastir (f=" + String(f, 2) + " < 0.3), kalibrasyon icin yuksek guven gerek\"}");
    return;
  }
  float t_pf = (skin_temp_raw_v - (1.0f - f) * ambient_v) / f;
  float new_offset = ref - t_pf;

  // Sanity — residual çok büyükse bir şey ters
  if (new_offset < -3.0f || new_offset > 3.0f) {
    server.send(400, "application/json",
                "{\"error\":\"residual offset cok buyuk, olcumler suphe icinde\",\"computed_offset\":"
                + String(new_offset, 3) + ",\"t_pf\":" + String(t_pf, 2) + "}");
    return;
  }
  cfg_base_offset = new_offset;

  char note[80];
  snprintf(note, sizeof(note), "ref=%.1f raw=%.1f amb=%.1f f=%.2f t_pf=%.1f",
           ref, skin_temp_raw_v, ambient_v, f, t_pf);
  saveCalibration(String(note));

  skin_temp_v = 0;  // EWMA reset → yeni offset hemen yansısın

  String json = "{";
  json += "\"saved\":true,";
  json += "\"ref\":"        + String(ref, 2) + ",";
  json += "\"t_pf\":"       + String(t_pf, 2) + ",";
  json += "\"f\":"          + String(f, 2) + ",";
  json += "\"raw\":"        + String(skin_temp_raw_v, 2) + ",";
  json += "\"ambient\":"    + String(ambient_v, 2) + ",";
  json += "\"new_offset\":" + String(cfg_base_offset, 3) + ",";
  json += "\"note\":\""     + cfg_calibrated_at + "\"";
  json += "}";
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", json);
}

// ---- Port 80: /thermal/reset_calibration — defaults'a dön ----
void handleThermalResetCal() {
  cfg_k_delta     = DEFAULT_K_DELTA;
  cfg_base_offset = DEFAULT_BASE_OFFSET;
  cfg_ewma_alpha  = DEFAULT_EWMA_ALPHA;
  cfg_k_size      = DEFAULT_K_SIZE;
  cfg_k_fill      = DEFAULT_K_FILL;
  saveCalibration("fabrika defaults (reset)");
  skin_temp_v = 0;
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json",
              "{\"reset\":true,\"k_delta\":" + String(cfg_k_delta, 3) +
              ",\"base\":" + String(cfg_base_offset, 2) +
              ",\"alpha\":" + String(cfg_ewma_alpha, 2) +
              ",\"k_size\":" + String(cfg_k_size, 0) +
              ",\"k_fill\":" + String(cfg_k_fill, 2) + "}");
}

// ---- Port 80: /thermal/calibrate_distance?d=15 — bilinen mesafede K_SIZE/K_FILL çöz ----
//
// Kullanıcı alnını sensöre cetvelle X cm uzaklıkta tutar ve bu endpoint'i çağırır.
// O anki blob_size + fill ratio'dan K katsayılarını gerçek mesafeye yapıştırırız.
//   blob_size = K_SIZE / d²        →  K_SIZE = blob_size * d²
//   f = (raw - amb) / (T_skin - amb), distance = K_FILL / sqrt(f)
//                                  →  K_FILL = d * sqrt(f)
void handleThermalCalibrateDistance() {
  if (!amg_ok) {
    server.send(503, "application/json", "{\"error\":\"AMG yok\"}");
    return;
  }
  if (!blob_detected) {
    server.send(400, "application/json",
                "{\"error\":\"once alnini sensorede sabit tut (blob yok)\"}");
    return;
  }
  if (!server.hasArg("d")) {
    server.send(400, "application/json",
                "{\"error\":\"d parametresi yok. ornek: /thermal/calibrate_distance?d=15\"}");
    return;
  }
  float d = server.arg("d").toFloat();
  if (d < 5.0f || d > 50.0f) {
    server.send(400, "application/json",
                "{\"error\":\"d makul aralikta degil (5-50 cm)\"}");
    return;
  }

  // K_SIZE çöz
  float new_k_size = (float)blob_size_v * d * d;

  // K_FILL çöz (fill ratio'dan)
  float fill_denom = T_SKIN_EXPECTED_C - ambient_v;
  float new_k_fill = cfg_k_fill;  // default
  bool fill_solved = false;
  if (fill_denom > 1.0f) {
    float f = (skin_temp_raw_v - ambient_v) / fill_denom;
    f = constrain(f, 0.05f, 1.0f);
    new_k_fill = d * sqrtf(f);
    fill_solved = true;
  }

  // Sağlık kontrolü
  if (new_k_size < 100 || new_k_size > 10000) {
    server.send(400, "application/json",
                "{\"error\":\"K_SIZE mantiksiz\",\"computed\":" + String(new_k_size, 1) + "}");
    return;
  }

  cfg_k_size = new_k_size;
  if (fill_solved) cfg_k_fill = new_k_fill;

  char note[64];
  snprintf(note, sizeof(note), "d=%.0fcm blob=%d raw=%.1f", d, blob_size_v, skin_temp_raw_v);
  saveCalibration(String(note));

  String json = "{";
  json += "\"saved\":true,";
  json += "\"d\":"          + String(d, 1) + ",";
  json += "\"blob_size\":"  + String(blob_size_v) + ",";
  json += "\"new_k_size\":" + String(cfg_k_size, 1) + ",";
  json += "\"new_k_fill\":" + String(cfg_k_fill, 2) + ",";
  json += "\"note\":\""     + cfg_calibrated_at + "\"";
  json += "}";
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", json);
}

// ---- Port 80: /verdict?level=red|yellow|green|insufficient[&src=...] ----
//
// Supervisor LLM (gateway tarafı) karar verince çağırır. LED bu değere göre
// sürer. TTL içinde yenilenmezse stale → LED söner. Gateway saniyede 1 kez
// (veya her karar değişiminde) heartbeat olarak çağırmalı.
void handleVerdict() {
  if (!server.hasArg("level")) {
    server.send(400, "application/json",
                "{\"error\":\"level parametresi yok. ornek: /verdict?level=red\"}");
    return;
  }
  String lvl = server.arg("level");
  lvl.toLowerCase();
  VerdictLevel new_level = VERDICT_NONE;
  if      (lvl == "red")          new_level = VERDICT_RED;
  else if (lvl == "yellow")       new_level = VERDICT_YELLOW;
  else if (lvl == "green")        new_level = VERDICT_GREEN;
  else if (lvl == "insufficient") new_level = VERDICT_INSUFFICIENT;
  else {
    server.send(400, "application/json",
                "{\"error\":\"level red|yellow|green|insufficient olmali\"}");
    return;
  }
  verdict_level   = new_level;
  verdict_last_ms = millis();
  verdict_source  = server.hasArg("src") ? server.arg("src") : "supervisor";

  Serial.printf("[VERDICT] %s (src=%s)\n", lvl.c_str(), verdict_source.c_str());

  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json",
              "{\"level\":\"" + lvl + "\",\"ttl_ms\":" + String(VERDICT_TTL_MS) +
              ",\"src\":\"" + verdict_source + "\"}");
}

// ---- Port 80: /thermal/gate?face=0|1 — gateway face mesh kapısı ----
// Gateway face mesh sonucunu her saniye bildirmeli. TTL içinde güncel kalmazsa
// firmware "stale" sayar ve AMG-iç kapısına geri düşer (standalone çalışma).
void handleThermalGate() {
  if (!server.hasArg("face")) {
    server.send(400, "application/json",
                "{\"error\":\"face parametresi yok. ornek: /thermal/gate?face=1\"}");
    return;
  }
  int face = server.arg("face").toInt();
  gate_external = (face != 0);
  gate_external_last_ms = millis();
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json",
              "{\"gate_external\":" + String(gate_external ? "true" : "false") +
              ",\"ttl_ms\":" + String(GATE_EXTERNAL_TTL_MS) + "}");
}

// ---- Port 80: /thermal — ham 64 pixel + cilt çıkarım + kalibrasyon JSON ----
void handleThermal() {
  String json = "{";
  json += "\"ok\":"          + String(amg_ok ? "true" : "false") + ",";
  json += "\"status\":\""     + amg_status + "\",";
  json += "\"count\":"       + String(amg_read_count) + ",";
  json += "\"min\":"         + String(amg_min_v, 2) + ",";
  json += "\"max\":"         + String(amg_max_v, 2) + ",";
  json += "\"avg\":"         + String(amg_avg_v, 2) + ",";
  json += "\"thermistor\":"  + String(amg_thermistor_v, 2) + ",";
  json += "\"person_present\":" + String(person_present ? "true" : "false") + ",";
  json += "\"blob_detected\":"  + String(blob_detected ? "true" : "false") + ",";
  json += "\"gate\":{";
  json += "\"open\":"           + String(person_present ? "true" : "false") + ",";
  json += "\"reason\":\""       + gate_reason + "\",";
  json += "\"amg_pass\":"       + String(gate_amg ? "true" : "false") + ",";
  json += "\"stability\":"      + String(gate_stability_count) + ",";
  json += "\"stability_target\":" + String(GATE_STABILITY_N) + ",";
  json += "\"external_face\":"  + String(gate_external ? "true" : "false") + ",";
  bool ext_stale = (millis() - gate_external_last_ms) > GATE_EXTERNAL_TTL_MS;
  json += "\"external_stale\":" + String(ext_stale ? "true" : "false");
  json += "},";
  json += "\"skin_temp\":"      + String(skin_temp_v, 2) + ",";
  json += "\"skin_temp_comp\":" + String(skin_temp_comp_v, 2) + ",";
  json += "\"skin_temp_raw\":"  + String(skin_temp_raw_v, 2) + ",";
  json += "\"ambient\":"     + String(ambient_v, 2) + ",";
  json += "\"delta_t\":"     + String(delta_t_v, 2) + ",";
  json += "\"blob_size\":"   + String(blob_size_v) + ",";
  json += "\"blob_mask\":\"";
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    json += blob_mask_v[i] ? '1' : '0';
  }
  json += "\",";
  json += "\"hint\":\""      + ux_hint + "\",";
  json += "\"confidence\":{";
  json += "\"level\":"       + String((int)measure_confidence) + ",";
  json += "\"label\":\""     + confidence_label + "\",";
  json += "\"pixel_fill\":"  + String(pixel_fill_f, 3);
  json += "},";
  // Son emin ölçüm — confidence>=MEDIUM olduğu son anda kaydedilmişti
  bool lc_set = (last_confirmed_ms > 0);
  uint32_t lc_age = lc_set ? (millis() - last_confirmed_ms) : 0;
  json += "\"last_confirmed\":{";
  json += "\"set\":"         + String(lc_set ? "true" : "false") + ",";
  json += "\"skin_temp\":"   + String(last_confirmed_skin_temp, 2) + ",";
  json += "\"distance_cm\":" + String(last_confirmed_distance, 1) + ",";
  json += "\"quality\":"     + String(last_confirmed_quality, 2) + ",";
  json += "\"blob_size\":"   + String(last_confirmed_blob_size) + ",";
  json += "\"conf\":"        + String(last_confirmed_conf) + ",";
  json += "\"age_ms\":"      + String(lc_age);
  json += "},";
  // Supervisor verdict — LED'i süren
  bool v_stale = (verdict_last_ms == 0) ||
                 ((millis() - verdict_last_ms) > VERDICT_TTL_MS);
  uint32_t v_age = verdict_last_ms > 0 ? (millis() - verdict_last_ms) : 0;
  const char* v_label;
  switch (verdict_level) {
    case VERDICT_RED:          v_label = "red";          break;
    case VERDICT_YELLOW:       v_label = "yellow";       break;
    case VERDICT_GREEN:        v_label = "green";        break;
    case VERDICT_INSUFFICIENT: v_label = "insufficient"; break;
    default:                   v_label = "none";         break;
  }
  json += "\"verdict\":{";
  json += "\"level\":\""     + String(v_label) + "\",";
  json += "\"stale\":"       + String(v_stale ? "true" : "false") + ",";
  json += "\"age_ms\":"      + String(v_age) + ",";
  json += "\"ttl_ms\":"      + String(VERDICT_TTL_MS) + ",";
  json += "\"src\":\""       + verdict_source + "\"";
  json += "},";
  json += "\"geometry\":{";
  json += "\"centroid_r\":"  + String(blob_centroid_r, 2) + ",";
  json += "\"centroid_c\":"  + String(blob_centroid_c, 2) + ",";
  json += "\"bbox\":[" + String(blob_bbox_rmin) + "," + String(blob_bbox_cmin) + ","
                       + String(blob_bbox_rmax) + "," + String(blob_bbox_cmax) + "],";
  json += "\"aspect\":"      + String(blob_aspect, 2) + ",";
  json += "\"compactness\":" + String(blob_compactness, 2) + ",";
  json += "\"uniformity\":"  + String(blob_uniformity, 2);
  json += "},";
  json += "\"distance\":{";
  json += "\"estimate_cm\":" + String(distance_est_cm, 1) + ",";
  json += "\"from_size\":"   + String(distance_from_size, 1) + ",";
  json += "\"from_fill\":"   + String(distance_from_fill, 1) + ",";
  json += "\"confidence\":"  + String(distance_confidence, 2) + ",";
  json += "\"optimal_min\":" + String(DISTANCE_OPTIMAL_MIN_CM, 1) + ",";
  json += "\"optimal_max\":" + String(DISTANCE_OPTIMAL_MAX_CM, 1);
  json += "},";
  json += "\"quality\":{";
  json += "\"score\":"       + String(quality_score, 3) + ",";
  json += "\"thermal\":"     + String(q_thermal, 2) + ",";
  json += "\"distance\":"    + String(q_distance, 2) + ",";
  json += "\"alignment\":"   + String(q_alignment, 2) + ",";
  json += "\"shape\":"       + String(q_shape, 2) + ",";
  json += "\"gate\":"        + String(QUALITY_GATE_MIN, 2);
  json += "},";
  json += "\"calibration\":{";
  json += "\"k_delta\":"     + String(cfg_k_delta, 3) + ",";
  json += "\"base_offset\":" + String(cfg_base_offset, 3) + ",";
  json += "\"ewma_alpha\":"  + String(cfg_ewma_alpha, 2) + ",";
  json += "\"k_size\":"      + String(cfg_k_size, 0) + ",";
  json += "\"k_fill\":"      + String(cfg_k_fill, 2) + ",";
  json += "\"note\":\""      + cfg_calibrated_at + "\"";
  json += "},";
  json += "\"pixels\":[";
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    if (i) json += ",";
    json += String(amg_pixels[i], 2);
  }
  json += "]}";
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", json);
}

void startStreamServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 81;
  config.ctrl_port   = 32768;
  config.stack_size  = 8192;

  httpd_uri_t stream_uri = {
    .uri      = "/stream",
    .method   = HTTP_GET,
    .handler  = streamHandler,
    .user_ctx = nullptr
  };

  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &stream_uri);
    Serial.println("[HTTP-81] MJPEG stream sunucu acildi");
  } else {
    Serial.println("[HTTP-81] BASLATILAMADI");
  }
}

// ---- Port 80: tek kare JPEG ----
void handleCapture() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    server.send(500, "text/plain", "Kamera frame alinamadi");
    return;
  }
  server.sendHeader("Content-Disposition", "inline; filename=capture.jpg");
  server.sendHeader("Connection", "close");
  server.setContentLength(fb->len);
  server.send(200, "image/jpeg", "");
  WiFiClient client = server.client();
  client.write(fb->buf, fb->len);
  esp_camera_fb_return(fb);
}

// ---- Port 80: JSON istatistik (+ termal özet) ----
void handleInfo() {
  uint32_t since = (last_frame_ms > 0) ? (millis() - last_frame_ms) : 0;
  String json = "{";
  json += "\"resolution\":\"" + String(current_w) + "x" + String(current_h) + "\",";
  json += "\"measured_fps\":" + String(measured_fps, 2) + ",";
  json += "\"frames_sent\":" + String((uint32_t)frames_sent) + ",";
  json += "\"bytes_sent\":" + String((uint32_t)bytes_sent) + ",";
  json += "\"last_frame_size\":" + String((uint32_t)last_frame_size) + ",";
  json += "\"ms_since_last_frame\":" + String(since) + ",";
  json += "\"rssi_dbm\":" + String(WiFi.RSSI()) + ",";
  json += "\"uptime_s\":" + String(millis() / 1000) + ",";
  json += "\"psram\":" + String(psramFound() ? "true" : "false") + ",";
  json += "\"free_heap\":" + String(ESP.getFreeHeap()) + ",";
  json += "\"thermal\":{";
  json += "\"ok\":"            + String(amg_ok ? "true" : "false") + ",";
  json += "\"person_present\":" + String(person_present ? "true" : "false") + ",";
  json += "\"skin_temp\":"     + String(skin_temp_v, 2) + ",";
  json += "\"ambient\":"       + String(ambient_v, 2) + ",";
  json += "\"blob_size\":"     + String(blob_size_v);
  json += "}";
  json += "}";
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", json);
}

// ---- Port 80: ana HTML sayfası (kamera + termal grid + cilt sıcaklığı) ----
void handleRoot() {
  String ip = WiFi.localIP().toString();
  String html =
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<title>Vita Porta — Canli Yayin + Termal</title>"
    "<style>"
    "body{font-family:sans-serif;background:#0a0a0a;color:#eee;text-align:center;margin:20px}"
    "h2{color:#6cf;margin-bottom:4px}"
    ".row{display:flex;flex-wrap:wrap;gap:20px;justify-content:center;align-items:flex-start;margin-top:14px}"
    ".col{display:flex;flex-direction:column;align-items:center;gap:10px}"
    "img{max-width:640px;width:100%;border:2px solid #444;border-radius:8px}"
    ".stats{background:#1a1a1a;padding:10px 16px;border-radius:6px;font-family:monospace;font-size:13px;text-align:left;min-width:260px}"
    ".stats span{color:#6cf}"
    ".big{background:#1a1a1a;padding:12px 24px;border-radius:10px;border:1px solid #333;min-width:260px}"
    ".big .lbl{font-size:11px;color:#888;letter-spacing:2px;text-transform:uppercase}"
    ".big .val{font-size:42px;font-weight:bold;color:#6cf;font-family:monospace;line-height:1.1}"
    ".big .sub{font-size:11px;color:#aaa;font-family:monospace;margin-top:4px}"
    ".big.none .val{color:#555}"
    ".bar{background:#0a0a0a;height:14px;border-radius:7px;overflow:hidden;position:relative;margin-top:4px}"
    ".bar .fill{height:100%;background:linear-gradient(90deg,#69f,#5f8,#fc6,#f66);transition:width 0.3s}"
    ".bar .marker{position:absolute;top:-2px;width:3px;height:18px;background:#fff;box-shadow:0 0 4px #fff}"
    ".bar .opt{position:absolute;top:0;height:14px;background:rgba(95,248,136,0.15);border-left:1px solid #5f8;border-right:1px solid #5f8}"
    ".hint{font-size:14px;color:#6cf;font-weight:bold;margin-top:8px;padding:6px;background:#0a1a2a;border-radius:6px}"
    ".hint.good{color:#5f8;background:#0a2a1a}"
    ".verdict{display:inline-block;padding:6px 14px;border-radius:18px;font-size:12px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;margin:8px 0;border:2px solid transparent}"
    ".verdict.none{background:#1a1a1a;color:#555;border-color:#333}"
    ".verdict.green{background:#0a3a1a;color:#5f8;border-color:#5f8;box-shadow:0 0 12px rgba(95,248,136,0.3)}"
    ".verdict.yellow{background:#3a3a0a;color:#fc6;border-color:#fc6;animation:vblink 1s infinite alternate}"
    ".verdict.red{background:#3a0a0a;color:#f44;border-color:#f44;box-shadow:0 0 14px rgba(255,68,68,0.5)}"
    ".verdict.insufficient{background:#1a1a3a;color:#88a;border-color:#88a}"
    "@keyframes vblink{from{opacity:0.6}to{opacity:1}}"
    ".lastcfm{background:#0a1a0a;border-left:3px solid #5f8;padding:8px 12px;border-radius:4px;margin-top:8px;font-size:12px;text-align:left}"
    ".lastcfm.stale{border-color:#666;opacity:0.6}"
    ".grid{display:inline-grid;grid-template-columns:repeat(8,32px);grid-gap:2px;padding:8px;background:#1a1a1a;border-radius:8px}"
    ".cell{width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-family:monospace;font-size:9px;font-weight:bold;color:#000;border-radius:3px;border:2px solid transparent;box-sizing:border-box}"
    ".cell.blob{border-color:#fff;box-shadow:0 0 6px rgba(255,255,255,0.7)}"
    "a{color:#6cf;text-decoration:none}a:hover{text-decoration:underline}"
    "</style></head>"
    "<body><h2>Vita Porta — Canli Kamera + Termal</h2>"
    "<div class='row'>"
      "<div class='col'>"
        "<img src='http://" + ip + ":81/stream' />"
        "<div class='stats' id='cstats'>kamera stats...</div>"
      "</div>"
      "<div class='col'>"
        "<div class='big' id='big'>"
          "<div style='font-size:10px;color:#888;letter-spacing:2px;text-transform:uppercase;margin-bottom:2px'>Supervisor Verdict</div>"
          "<div class='verdict none' id='vpill'>baglanti yok</div>"
          "<div class='lbl' style='margin-top:8px'>Cilt Sicakligi (anlik)</div>"
          "<div class='val' id='skin'>--</div>"
          "<div class='sub' id='skinsub'>baglanti bekleniyor</div>"
          "<div class='hint' id='hint'>...</div>"
          "<div class='lastcfm stale' id='lastcfm'>Son emin olcum yok</div>"
          "<div style='margin-top:10px;font-size:11px;color:#888'>Mesafe</div>"
          "<div class='bar'><div class='opt' id='distopt'></div><div class='fill' id='distfill' style='width:0%'></div><div class='marker' id='distmark' style='left:0%'></div></div>"
          "<div style='font-size:11px;color:#aaa;margin-top:2px' id='distlbl'>-- cm</div>"
          "<div style='margin-top:8px;font-size:11px;color:#888'>Kalite</div>"
          "<div class='bar'><div class='fill' id='qfill' style='width:0%'></div></div>"
          "<div style='font-size:11px;color:#aaa;margin-top:2px' id='qlbl'>--%</div>"
        "</div>"
        "<div class='grid' id='grid'></div>"
        "<div class='stats' id='tstats'>termal stats...</div>"
        "<div class='stats' style='background:#1a2a3a'>"
          "<b style='color:#6cf'>Kalibrasyon</b><br>"
          "<span style='font-size:11px'>1) termometre degerini ver:</span><br>"
          "<input id='refinput' type='number' step='0.1' placeholder='36.7' "
            "style='width:70px;padding:4px;background:#0a0a0a;color:#eee;border:1px solid #444;border-radius:4px'/>"
          " <button onclick='doCalibrate()'>Sıcaklık Kalibre</button><br>"
          "<span style='font-size:11px;margin-top:6px;display:inline-block'>2) cetvelle mesafe (cm):</span><br>"
          "<input id='dinput' type='number' step='1' placeholder='15' "
            "style='width:70px;padding:4px;background:#0a0a0a;color:#eee;border:1px solid #444;border-radius:4px'/>"
          " <button onclick='doCalDist()'>Mesafe Kalibre</button>"
          " <button onclick='doReset()' style='background:#4a1a1a'>Reset</button>"
          "<div id='calresult' style='font-size:11px;margin-top:6px;color:#aaa'></div>"
        "</div>"
      "</div>"
    "</div>"
    "<p style='margin-top:20px'>"
      "<a href='/capture' target='_blank'>Tek kare</a> | "
      "<a href='/info' target='_blank'>/info</a> | "
      "<a href='/thermal' target='_blank'>/thermal</a>"
    "</p>"
    "<script>"
    "function color(t){t=Math.max(0,Math.min(1,t));const h=(1-t)*240;return 'hsl('+h+',100%,50%)';}"
    "const g=document.getElementById('grid');"
    "for(let i=0;i<64;i++){const c=document.createElement('div');c.className='cell';c.id='c'+i;g.appendChild(c)}"
    "async function updateInfo(){"
      "try{const r=await fetch('/info');const d=await r.json();"
      "document.getElementById('cstats').innerHTML="
      "'Cozunurluk: <span>'+d.resolution+'</span><br>'+"
      "'FPS: <span>'+d.measured_fps.toFixed(1)+'</span> | '+"
      "'Kare: <span>'+(d.last_frame_size/1024).toFixed(1)+' KB</span><br>'+"
      "'Toplam: <span>'+d.frames_sent+'</span> | '+"
      "'RSSI: <span>'+d.rssi_dbm+' dBm</span><br>'+"
      "'Heap: <span>'+(d.free_heap/1024).toFixed(1)+' KB</span> | '+"
      "'Uptime: <span>'+d.uptime_s+' s</span>';"
      "}catch(e){}"
    "}"
    "async function updateThermal(){"
      "try{const r=await fetch('/thermal');const d=await r.json();"
      "const big=document.getElementById('big');"
      "const skin=document.getElementById('skin');"
      "const sub=document.getElementById('skinsub');"
      "big.classList.remove('none','warm','hot');"
      "if(!d.ok){skin.textContent='--';sub.textContent='AMG yok: '+d.status;big.classList.add('none');return}"
      "const range=Math.max(0.5,d.max-d.min);"
      "for(let i=0;i<64;i++){const p=d.pixels[i];const t=(p-d.min)/range;"
      "const el=document.getElementById('c'+i);"
      "el.style.background=color(t);el.textContent=p.toFixed(0);"
      "if(d.blob_mask&&d.blob_mask[i]=='1')el.classList.add('blob');else el.classList.remove('blob');}"
      "const hint=document.getElementById('hint');"
      "const vpill=document.getElementById('vpill');"
      "const lastcfm=document.getElementById('lastcfm');"
      // --- Supervisor verdict ---
      "const v=d.verdict||{level:'none',stale:true};"
      "vpill.classList.remove('none','green','yellow','red','insufficient');"
      "let vKey=v.stale?'none':(v.level||'none');"
      "if(vKey==='none'&&!v.stale)vKey='insufficient';"
      "vpill.classList.add(vKey);"
      "vpill.textContent=v.stale?'gateway bagli degil':(v.level==='red'?'ANORMAL':v.level==='yellow'?'SUPHELI':v.level==='green'?'NORMAL':v.level==='insufficient'?'YETERSIZ':v.level||'--');"
      // --- Last confirmed ---
      "const lc=d.last_confirmed||{set:false};"
      "lastcfm.classList.remove('stale');"
      "if(!lc.set){"
      "lastcfm.classList.add('stale');"
      "lastcfm.textContent='Son emin olcum yok — alnini sweet spot\\'a getir';"
      "}else{"
      "const ageS=(lc.age_ms/1000).toFixed(1);"
      "if(lc.age_ms>15000)lastcfm.classList.add('stale');"
      "lastcfm.innerHTML='<b>Son emin olcum:</b> '+lc.skin_temp.toFixed(1)+' C · '+lc.distance_cm.toFixed(0)+'cm · Q='+lc.quality.toFixed(2)+' · '+ageS+'s once';"
      "}"
      "hint.classList.remove('good');"
      "hint.textContent=d.hint||'--';"
      "if(d.hint&&(d.hint.startsWith('iyi')||d.hint.startsWith('mukemmel')))hint.classList.add('good');"
      // Mesafe çubuğu — 0..40cm skala
      "const dist=d.distance||{};"
      "const dcm=dist.estimate_cm||0;"
      "const dpct=Math.min(100,(dcm/40)*100);"
      "document.getElementById('distfill').style.width=dpct+'%';"
      "document.getElementById('distmark').style.left=dpct+'%';"
      "const optMin=((dist.optimal_min||12)/40)*100;"
      "const optMax=((dist.optimal_max||22)/40)*100;"
      "document.getElementById('distopt').style.left=optMin+'%';"
      "document.getElementById('distopt').style.width=(optMax-optMin)+'%';"
      "document.getElementById('distlbl').textContent=dcm.toFixed(0)+' cm (size '+(dist.from_size||0).toFixed(0)+', fill '+(dist.from_fill||0).toFixed(0)+', conf '+((dist.confidence||0)*100).toFixed(0)+'%)';"
      // Kalite çubuğu
      "const qual=d.quality||{};"
      "const Q=(qual.score||0)*100;"
      "document.getElementById('qfill').style.width=Q+'%';"
      "document.getElementById('qlbl').textContent=Q.toFixed(0)+'% (T '+((qual.thermal||0)*100).toFixed(0)+' / D '+((qual.distance||0)*100).toFixed(0)+' / A '+((qual.alignment||0)*100).toFixed(0)+' / S '+((qual.shape||0)*100).toFixed(0)+')';"
      // Cilt sıcaklığı veya kapı durumu
      "if(!d.person_present){"
      "skin.textContent='--';"
      "sub.textContent='gate kapali — '+(d.gate?d.gate.reason:'beklemede');"
      "}else{"
      "const conf=d.confidence||{level:0,label:''};"
      "const confBadge=conf.level>=3?'✓ yuksek':conf.level>=2?'~ orta':'! '+conf.label;"
      "skin.textContent=d.skin_temp.toFixed(1)+' C';"
      "sub.innerHTML='<span style=\"font-size:11px;padding:2px 6px;background:'+(conf.level>=3?'#1a4a2a':conf.level>=2?'#4a3a0a':'#5a1a0a')+';border-radius:4px;margin-right:6px\">'+confBadge+'</span>'+"
      "'blob '+d.blob_size+' | raw '+d.skin_temp_raw.toFixed(1)+' → pf '+d.skin_temp_comp.toFixed(1)+' | f='+(conf.pixel_fill||0).toFixed(2);"
      "}"
      "const c=d.calibration||{};"
      "document.getElementById('tstats').innerHTML="
      "'Okuma: <span>#'+d.count+'</span><br>'+"
      "'Min/Max: <span>'+d.min.toFixed(1)+' / '+d.max.toFixed(1)+' C</span><br>'+"
      "'Ortalama: <span>'+d.avg.toFixed(1)+' C</span> | '+"
      "'Ambient: <span>'+d.ambient.toFixed(1)+' C</span><br>'+"
      "'Termistor: <span>'+d.thermistor.toFixed(2)+' C</span><br>'+"
      "'K='+(c.k_delta||0).toFixed(2)+' base='+(c.base_offset||0).toFixed(1)+' α='+(c.ewma_alpha||0).toFixed(1)+'<br>'+"
      "'<span style=\"font-size:10px;color:#888\">'+(c.note||'')+'</span>';"
      "}catch(e){}"
    "}"
    "async function doCalibrate(){"
      "const v=document.getElementById('refinput').value;"
      "if(!v){alert('termometre degeri gir');return}"
      "const r=await fetch('/thermal/calibrate?ref='+v);"
      "const d=await r.json();"
      "document.getElementById('calresult').textContent="
      "d.saved?('offset = '+d.new_offset.toFixed(3)+' (raw '+d.raw.toFixed(1)+' → t_pf '+d.t_pf.toFixed(1)+' → ref '+d.ref.toFixed(1)+', f='+d.f.toFixed(2)+')'):('HATA: '+(d.error||JSON.stringify(d)));"
    "}"
    "async function doCalDist(){"
      "const v=document.getElementById('dinput').value;"
      "if(!v){alert('mesafe (cm) gir');return}"
      "const r=await fetch('/thermal/calibrate_distance?d='+v);"
      "const d=await r.json();"
      "document.getElementById('calresult').textContent="
      "d.saved?('K_size='+d.new_k_size.toFixed(0)+' K_fill='+d.new_k_fill.toFixed(1)+' (blob '+d.blob_size+' @ '+d.d+'cm)'):('HATA: '+(d.error||JSON.stringify(d)));"
    "}"
    "async function doReset(){"
      "if(!confirm('Tum kalibrasyon defaults\\'a donsun mu? (sicaklik + mesafe)'))return;"
      "const r=await fetch('/thermal/reset_calibration');"
      "const d=await r.json();"
      "document.getElementById('calresult').textContent='reset → K_delta='+d.k_delta.toFixed(2)+' K_size='+d.k_size.toFixed(0);"
    "}"
    "setInterval(updateInfo,1000);setInterval(updateThermal,500);"
    "updateInfo();updateThermal();"
    "</script></body></html>";
  server.send(200, "text/html", html);
}

bool initCamera() {
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode    = CAMERA_GRAB_LATEST;
  config.fb_location  = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;

  if (psramFound()) {
    // VGA: face mesh, pose detection ve respiration için minimum yeterli.
    // ESP32-CAM bu boyutta 20-25 FPS rahat verir.
    config.frame_size   = FRAMESIZE_VGA;   // 640x480
    config.jpeg_quality = 10;              // 0-63, düşük=kaliteli (10 dengeli)
    config.fb_count     = 2;
  } else {
    config.frame_size   = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count     = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[CAM] Init HATASI, kod=0x%x\n", err);
    return false;
  }

  // Sensor ince ayar
  sensor_t* s = esp_camera_sensor_get();
  if (s) {
    s->set_brightness(s, 1);
    s->set_contrast(s, 1);
    s->set_saturation(s, 0);
    s->set_whitebal(s, 1);
    s->set_awb_gain(s, 1);
    s->set_exposure_ctrl(s, 1);
    s->set_gain_ctrl(s, 1);
    s->set_aec2(s, 1);             // AEC algoritma 2 — daha hızlı poz adaptasyonu
    s->set_dcw(s, 1);              // downsize/crop window — keskinlik için
    s->set_bpc(s, 1);              // black pixel correction
    s->set_wpc(s, 1);              // white pixel correction
    s->set_raw_gma(s, 1);          // gamma düzeltme
    s->set_lenc(s, 1);             // lens correction
  }
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println("=========================================");
  Serial.println("[Vita Porta] Asama B — VGA MJPEG Yayin");
  Serial.println("=========================================");
  Serial.printf("[BOOT] PSRAM: %s\n", psramFound() ? "VAR (4MB)" : "YOK");

  // LED pinleri — R + G (IO14 artık AMG SCL, B feda edildi)
  pinMode(LED_R_PIN, OUTPUT);
  pinMode(LED_G_PIN, OUTPUT);
  digitalWrite(LED_R_PIN, LOW);
  digitalWrite(LED_G_PIN, LOW);
  Serial.println("[LED] R=GPIO13, G=GPIO15 (B feda — IO14 = AMG SCL)");

  Serial.print("[CAM] Baslatiliyor... ");
  if (!initCamera()) {
    Serial.println("DURDURULDU");
    while (true) delay(1000);
  }
  Serial.println("OK (VGA 640x480)");

  // Kalibrasyon parametreleri NVS'ten (yoksa defaults)
  loadCalibration();

  // AMG8833 termal sensör
  if (!initAMG()) {
    Serial.println("[AMG] Sensor olmadan devam (termal endpoint bos donecek)");
  }

  Serial.printf("[WIFI] Baglaniliyor: %s ", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  WiFi.setSleep(false);
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 20000) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] BAGLANAMADI");
    while (true) delay(1000);
  }
  Serial.print("[WIFI] Bagli. IP: ");
  Serial.println(WiFi.localIP());
  Serial.printf("[WIFI] RSSI: %d dBm\n", WiFi.RSSI());

  server.on("/", handleRoot);
  server.on("/capture", handleCapture);
  server.on("/info", handleInfo);
  server.on("/thermal", handleThermal);
  server.on("/thermal/rescan", handleThermalRescan);
  server.on("/thermal/calibrate", handleThermalCalibrate);
  server.on("/thermal/calibrate_distance", handleThermalCalibrateDistance);
  server.on("/thermal/reset_calibration", handleThermalResetCal);
  server.on("/thermal/gate", handleThermalGate);
  server.on("/verdict", handleVerdict);
  server.begin();
  Serial.println("[HTTP-80] /, /capture, /info, /thermal[/rescan|/calibrate|/calibrate_distance|/reset_calibration|/gate], /verdict");

  startStreamServer();

  Serial.println();
  Serial.println("=========================================");
  Serial.printf(">>> Ana sayfa : http://%s/\n", WiFi.localIP().toString().c_str());
  Serial.printf(">>> Stream    : http://%s:81/stream\n", WiFi.localIP().toString().c_str());
  Serial.printf(">>> Info JSON : http://%s/info\n", WiFi.localIP().toString().c_str());
  Serial.printf(">>> Thermal   : http://%s/thermal\n", WiFi.localIP().toString().c_str());
  Serial.println("=========================================");
}

void loop() {
  server.handleClient();

  // AMG yoksa 2 sn'de bir sessizce yeniden dene (flash sonrası VIN takılınca otomatik bul)
  static uint32_t amg_retry_ms = 0;
  if (!amg_ok && millis() - amg_retry_ms >= 2000) {
    amg_retry_ms = millis();
    tryBeginAMG(true);
  }

  // AMG periyodik okuma — 200ms (~5Hz, AMG max 10Hz)
  if (amg_ok && millis() - amg_last_read_ms >= 200) {
    amg_last_read_ms = millis();
    readAMG();
  }

  // LED: supervisor LLM verdict'ine göre. Firmware sadece ham sıcaklık değeri
  // yollar (etiket yok); karar zincirinin sahibi ana bilgisayardaki LLM.
  //
  //   RED          → kırmızı steady   (anormal, kritik)
  //   YELLOW       → kırmızı 1Hz blink (şüpheli)
  //   GREEN        → yeşil steady     (normal)
  //   INSUFFICIENT → ikisi sönük       (veri yetmedi — supervisor da bilemedi)
  //   stale/NONE   → ikisi sönük       (gateway bağlantısı yok / hiç verdict gelmedi)
  static uint32_t last_led_update = 0;
  if (millis() - last_led_update >= 50) {
    last_led_update = millis();
    bool red_on = false, green_on = false;
    uint32_t t = millis();
    bool stale = (verdict_last_ms == 0) ||
                 ((t - verdict_last_ms) > VERDICT_TTL_MS);
    if (!stale) {
      switch (verdict_level) {
        case VERDICT_RED:
          red_on = true;
          break;
        case VERDICT_YELLOW:
          red_on = (t / 500) & 1;  // 1Hz blink
          break;
        case VERDICT_GREEN:
          green_on = true;
          break;
        case VERDICT_INSUFFICIENT:
        case VERDICT_NONE:
        default:
          break;
      }
    }
    digitalWrite(LED_R_PIN, red_on   ? HIGH : LOW);
    digitalWrite(LED_G_PIN, green_on ? HIGH : LOW);
  }

  // 5 sn'de bir serial özet (FPS + skin)
  static uint32_t last_report = 0;
  if (millis() - last_report > 5000) {
    last_report = millis();
    Serial.printf("[STATS] FPS=%.1f res=%ux%u frames=%u heap=%uKB RSSI=%ddBm\n",
                  measured_fps, current_w, current_h,
                  (uint32_t)frames_sent, ESP.getFreeHeap() / 1024, WiFi.RSSI());
    if (amg_ok) {
      if (person_present) {
        Serial.printf("[SKIN] skin=%.2fC raw=%.2f amb=%.2f dT=%.2f d=%.0fcm Q=%.2f conf=%d\n",
                      skin_temp_v, skin_temp_raw_v,
                      ambient_v, delta_t_v, distance_est_cm, quality_score,
                      (int)measure_confidence);
      } else {
        Serial.printf("[GATE] kapali hint='%s' Q=%.2f d=%.0fcm blob=%u\n",
                      ux_hint.c_str(), quality_score, distance_est_cm,
                      (unsigned)blob_size_v);
      }
      // Verdict + last confirmed özet
      bool v_stale = (verdict_last_ms == 0) ||
                     ((millis() - verdict_last_ms) > VERDICT_TTL_MS);
      if (v_stale) {
        Serial.println("[VERDICT] yok / stale — LED sonuk");
      } else {
        const char* vl;
        switch (verdict_level) {
          case VERDICT_RED:          vl = "RED";          break;
          case VERDICT_YELLOW:       vl = "YELLOW";       break;
          case VERDICT_GREEN:        vl = "GREEN";        break;
          case VERDICT_INSUFFICIENT: vl = "INSUFFICIENT"; break;
          default:                   vl = "NONE";         break;
        }
        Serial.printf("[VERDICT] %s (age=%lums src=%s)\n",
                      vl, (millis() - verdict_last_ms), verdict_source.c_str());
      }
      if (last_confirmed_ms > 0) {
        Serial.printf("[LAST] skin=%.2fC age=%lums d=%.0fcm\n",
                      last_confirmed_skin_temp,
                      (millis() - last_confirmed_ms),
                      last_confirmed_distance);
      }
    }
  }

  delay(1);
}
