// amg8833_test.ino — AMG8833 standalone test + Wi-Fi heatmap web
// =================================================================
// Amaç: Sensörü PC bağlı değilken de tarayıcıdan canlı izlemek.
//   - Wi-Fi açılır, web sunucusu port 80'de.
//   - /        → renkli 8x8 heatmap + I2C diagnostik (her 1 sn'de fetch)
//   - /grid    → JSON: pixels[64], min/max/avg, termistor, i2c_scan, amg_status
//   - /rescan  → I2C bus'ı yeniden tarar ve amg.begin'i tekrar dener
//
// Gerekli kütüphane: Adafruit AMG88xx Library (Library Manager'dan)

#include <Wire.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Adafruit_AMG88xx.h>

// ============================================================
//  WI-FI BILGILERI
// ============================================================
const char* WIFI_SSID     = "FiberHGW_ZT73ZD";
const char* WIFI_PASSWORD = "DAbahR9PzRFY";
// ============================================================

// AI-Thinker ESP32-CAM'de GPIO 21/22 header'a çıkmamış (kamera dahili).
// 2 LED (kırmızı+yeşil) + AMG8833 birlikte çalışır:
//   - SDA = IO2  (strapping pin ama boot sonrası temiz)
//   - SCL = IO14 (eski mavi LED yeri — RGB B feda edildi)
//   - LED_ERR (kırmızı) = IO13 — hata göstergesi
//   - LED_OK  (yeşil)   = IO15 — sensör+Wi-Fi OK
// AMG8833 breakout'unda dahili pull-up var; ek direnç gerekmez.
#define LED_ERR_PIN     13
#define LED_OK_PIN      15
#define I2C_SDA_PIN      2
#define I2C_SCL_PIN     14

Adafruit_AMG88xx amg;
WebServer server(80);

float    pixels[AMG88xx_PIXEL_ARRAY_SIZE];
float    pmin_v = 0, pmax_v = 0, pavg_v = 0, thermistor_v = 0;
uint32_t read_count   = 0;
uint32_t last_read_ms = 0;
bool     amg_ok       = false;
String   i2c_scan     = "henuz taranmadi";
String   amg_status   = "henuz baslatilmadi";

// --- Cilt sıcaklığı çıkarımı (hot-blob segmentasyonu) ----------------
// AMG8833'ün 64 pikselinden insan sinyalini ortamdan ayıran algoritma.
// Çıktı: en büyük bağlı "sıcak bölge" + onun üst %50'sinin ortalaması.
#define SKIN_GRADIENT_C       2.5f   // max'dan bu kadar aşağıya kadar cilt sayılır
#define SKIN_MIN_PIXELS       3      // bu kadar az piksel → sinyal yetersiz
#define SKIN_MAX_C            39.0f  // bu üstü cilt değil (ısı kaynağı / artefakt)
#define SKIN_MIN_GLOBAL_MAX_C 28.0f  // hiçbir piksel bu sıcaklıkta değilse "kimse yok"
#define SKIN_OFFSET_C         1.2f   // ham → gerçek cilt sıcaklığı düzeltmesi (kalibrasyonla ayarla)

float    skin_temp_raw_v = 0;     // blob top-%50 ortalaması, sensör ham değeri
float    skin_temp_v     = 0;     // skin_temp_raw + offset (rapor edilen değer)
float    ambient_v       = 0;     // blob dışı piksellerin medyanı
float    delta_t_v       = 0;     // skin_temp_raw - ambient
uint8_t  blob_size_v     = 0;     // blob piksel sayısı (0-64)
uint8_t  blob_mask_v[AMG88xx_PIXEL_ARRAY_SIZE] = {0};
bool     person_present  = false; // blob ≥ SKIN_MIN_PIXELS

void scanI2C() {
  i2c_scan = "";
  byte found = 0;
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      if (found) i2c_scan += ", ";
      char hex[8];
      snprintf(hex, sizeof(hex), "0x%02X", addr);
      i2c_scan += hex;
      found++;
    }
  }
  if (found == 0) i2c_scan = "HICBIR CIHAZ YOK";
  Serial.printf("[I2C scan] %s\n", i2c_scan.c_str());
}

// 64 float üzerinde insertion sort — küçük n, yer kaplamasın diye in-place.
static void sortFloatsDesc(float* arr, int n) {
  for (int i = 1; i < n; i++) {
    float x = arr[i];
    int j = i - 1;
    while (j >= 0 && arr[j] < x) { arr[j + 1] = arr[j]; j--; }
    arr[j + 1] = x;
  }
}
static void sortFloatsAsc(float* arr, int n) {
  for (int i = 1; i < n; i++) {
    float x = arr[i];
    int j = i - 1;
    while (j >= 0 && arr[j] > x) { arr[j + 1] = arr[j]; j--; }
    arr[j + 1] = x;
  }
}

// Hot-blob: en sıcak pikselden başlayan, eşik üstündeki tek bağlı bölgeyi bulur.
// 8x8 ızgara, 4-komşu BFS. Çoklu bölge varsa en büyüğünü tutar.
void computeSkinTemp() {
  memset(blob_mask_v, 0, sizeof(blob_mask_v));
  blob_size_v     = 0;
  skin_temp_raw_v = 0;
  skin_temp_v     = 0;
  ambient_v       = pavg_v;
  delta_t_v       = 0;
  person_present  = false;

  if (!amg_ok) return;

  // Global max ve "ortamda insan sıcaklığı yok" erken çıkışı
  float gmax = pixels[0];
  for (int i = 1; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    if (pixels[i] > gmax) gmax = pixels[i];
  }
  if (gmax < SKIN_MIN_GLOBAL_MAX_C) {
    ambient_v = pavg_v;
    return;
  }

  // Cilt aday maskesi: [gmax - gradient, SKIN_MAX_C]
  float thresh = gmax - SKIN_GRADIENT_C;
  uint8_t candidate[AMG88xx_PIXEL_ARRAY_SIZE];
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    candidate[i] = (pixels[i] >= thresh && pixels[i] <= SKIN_MAX_C) ? 1 : 0;
  }

  // Tüm bağlı bileşenleri tara, en büyüğünü seç (BFS, 4-komşu)
  uint8_t visited[AMG88xx_PIXEL_ARRAY_SIZE] = {0};
  uint8_t best_mask[AMG88xx_PIXEL_ARRAY_SIZE] = {0};
  int     best_size = 0;
  int     queue[AMG88xx_PIXEL_ARRAY_SIZE];

  for (int start = 0; start < AMG88xx_PIXEL_ARRAY_SIZE; start++) {
    if (!candidate[start] || visited[start]) continue;

    uint8_t this_mask[AMG88xx_PIXEL_ARRAY_SIZE] = {0};
    int this_size = 0;
    int qhead = 0, qtail = 0;
    queue[qtail++] = start;
    visited[start] = 1;

    while (qhead < qtail) {
      int idx = queue[qhead++];
      this_mask[idx] = 1;
      this_size++;
      int r = idx >> 3;       // /8
      int c = idx & 0x7;      // %8
      const int dr[4] = {-1, 1, 0, 0};
      const int dc[4] = { 0, 0,-1, 1};
      for (int k = 0; k < 4; k++) {
        int nr = r + dr[k], nc = c + dc[k];
        if (nr < 0 || nr > 7 || nc < 0 || nc > 7) continue;
        int nidx = (nr << 3) | nc;
        if (candidate[nidx] && !visited[nidx]) {
          visited[nidx] = 1;
          queue[qtail++] = nidx;
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

  // Sinyal yetersiz: blob çok küçük → noise olabilir
  if (best_size < SKIN_MIN_PIXELS) {
    ambient_v = pavg_v;
    return;
  }
  person_present = true;

  // Blob piksellerini topla, en sıcak %50'nin ortalamasını skin_temp_raw yap
  float blob_vals[AMG88xx_PIXEL_ARRAY_SIZE];
  int   bn = 0;
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    if (best_mask[i]) blob_vals[bn++] = pixels[i];
  }
  sortFloatsDesc(blob_vals, bn);
  int top_n = (bn + 1) / 2;                // tavan(n/2): tek elemanda da iş gör
  float top_sum = 0;
  for (int i = 0; i < top_n; i++) top_sum += blob_vals[i];
  skin_temp_raw_v = top_sum / top_n;
  skin_temp_v     = skin_temp_raw_v + SKIN_OFFSET_C;

  // Ambient = blob dışı piksellerin medyanı (ortalama outlier'a hassas)
  float bg_vals[AMG88xx_PIXEL_ARRAY_SIZE];
  int   gn = 0;
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    if (!best_mask[i]) bg_vals[gn++] = pixels[i];
  }
  if (gn > 0) {
    sortFloatsAsc(bg_vals, gn);
    ambient_v = bg_vals[gn / 2];
  }
  delta_t_v = skin_temp_raw_v - ambient_v;
}

void readSensor() {
  if (!amg_ok) return;
  amg.readPixels(pixels);
  read_count++;

  float pmin = pixels[0], pmax = pixels[0], psum = 0;
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    if (pixels[i] < pmin) pmin = pixels[i];
    if (pixels[i] > pmax) pmax = pixels[i];
    psum += pixels[i];
  }
  pmin_v = pmin;
  pmax_v = pmax;
  pavg_v = psum / AMG88xx_PIXEL_ARRAY_SIZE;
  thermistor_v = amg.readThermistor();

  computeSkinTemp();
}

void handleGrid() {
  String json = "{";
  json += "\"count\":"      + String(read_count) + ",";
  json += "\"min\":"        + String(pmin_v, 2) + ",";
  json += "\"max\":"        + String(pmax_v, 2) + ",";
  json += "\"avg\":"        + String(pavg_v, 2) + ",";
  json += "\"thermistor\":" + String(thermistor_v, 2) + ",";
  json += "\"ok\":"         + String(amg_ok ? "true" : "false") + ",";
  json += "\"i2c_scan\":\""   + i2c_scan + "\",";
  json += "\"amg_status\":\"" + amg_status + "\",";
  json += "\"sda_pin\":" + String(I2C_SDA_PIN) + ",";
  json += "\"scl_pin\":" + String(I2C_SCL_PIN) + ",";
  // --- Cilt sıcaklığı çıkarımı ---
  json += "\"person_present\":" + String(person_present ? "true" : "false") + ",";
  json += "\"skin_temp\":"      + String(skin_temp_v, 2) + ",";
  json += "\"skin_temp_raw\":"  + String(skin_temp_raw_v, 2) + ",";
  json += "\"skin_offset\":"    + String(SKIN_OFFSET_C, 2) + ",";
  json += "\"ambient\":"        + String(ambient_v, 2) + ",";
  json += "\"delta_t\":"        + String(delta_t_v, 2) + ",";
  json += "\"blob_size\":"      + String(blob_size_v) + ",";
  json += "\"blob_mask\":\"";
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    json += blob_mask_v[i] ? '1' : '0';
  }
  json += "\",";
  json += "\"pixels\":[";
  for (int i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
    if (i) json += ",";
    json += String(pixels[i], 2);
  }
  json += "]}";
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", json);
}

void handleRescan() {
  scanI2C();
  if (amg.begin(0x69))      { amg_ok = true;  amg_status = "OK @ 0x69 (rescan)"; }
  else if (amg.begin(0x68)) { amg_ok = true;  amg_status = "OK @ 0x68 (rescan)"; }
  else                      { amg_ok = false; amg_status = "0x69 ve 0x68'de YOK"; }
  digitalWrite(LED_OK_PIN,  amg_ok ? HIGH : LOW);
  digitalWrite(LED_ERR_PIN, amg_ok ? LOW  : HIGH);
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json",
              "{\"scan\":\"" + i2c_scan + "\",\"amg\":\"" + amg_status + "\"}");
}

void handleRoot() {
  String html =
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<title>AMG8833 Heatmap - Vita Porta</title>"
    "<style>"
    "body{font-family:sans-serif;background:#0a0a0a;color:#eee;text-align:center;margin:20px}"
    "h2{color:#6cf;margin-bottom:4px}"
    ".big{display:inline-block;background:#1a1a1a;padding:14px 28px;border-radius:10px;margin:10px;"
        "min-width:280px;border:1px solid #333}"
    ".big .lbl{font-size:11px;color:#888;letter-spacing:2px;text-transform:uppercase}"
    ".big .val{font-size:48px;font-weight:bold;color:#6cf;font-family:monospace;line-height:1.1}"
    ".big .sub{font-size:12px;color:#aaa;font-family:monospace;margin-top:6px}"
    ".big.none .val{color:#555}"
    ".big.warm .val{color:#fa6}"
    ".big.hot .val{color:#f44}"
    ".grid{display:inline-grid;grid-template-columns:repeat(8,52px);grid-gap:2px;"
        "padding:10px;background:#1a1a1a;border-radius:8px;margin:14px}"
    ".cell{width:52px;height:52px;display:flex;align-items:center;justify-content:center;"
        "font-family:monospace;font-size:12px;font-weight:bold;color:#000;border-radius:4px;"
        "text-shadow:0 0 2px rgba(255,255,255,0.7);box-sizing:border-box;"
        "border:2px solid transparent}"
    ".cell.blob{border-color:#fff;box-shadow:0 0 10px rgba(255,255,255,0.8)}"
    ".stats{display:inline-block;background:#1a1a1a;padding:10px 20px;border-radius:6px;"
        "margin:10px;font-family:monospace;font-size:13px;text-align:left}"
    ".stats span{color:#6cf}"
    ".bad{color:#f66}"
    "button{background:#1a4a6a;color:#eee;border:0;padding:8px 16px;border-radius:6px;"
        "font-size:14px;cursor:pointer;margin:8px}"
    "button:hover{background:#2a6a9a}"
    "</style></head>"
    "<body><h2>AMG8833 Termal Grid + Cilt Cikarimi</h2>"
    "<div class='big' id='big'><div class='lbl'>Cilt Sicakligi</div>"
        "<div class='val' id='skin'>--</div>"
        "<div class='sub' id='skinsub'>baglanti bekleniyor</div></div>"
    "<br>"
    "<div class='stats' id='stats'>baglanti bekleniyor...</div>"
    "<div class='stats' id='diag' style='color:#ff6;display:none'></div>"
    "<div><button onclick=\"fetch('/rescan').then(r=>r.json()).then(d=>{alert('Tarama: '+d.scan+'\\nAMG: '+d.amg);tick()})\">YENIDEN TARA</button></div>"
    "<div class='grid' id='grid'></div>"
    "<div style='font-size:12px;color:#888'>Renk: min-max otomatik (sicak=kirmizi, soguk=mavi). Beyaz cerceveli hucreler = tespit edilen cilt blob'u.</div>"
    "<script>"
    "function color(t){t=Math.max(0,Math.min(1,t));const h=(1-t)*240;return 'hsl('+h+',100%,50%)';}"
    "const g=document.getElementById('grid');"
    "for(let i=0;i<64;i++){const c=document.createElement('div');c.className='cell';c.id='c'+i;g.appendChild(c)}"
    "async function tick(){"
    "try{const r=await fetch('/grid');const d=await r.json();"
    "const diag=document.getElementById('diag');"
    "if(!d.ok){"
    "document.getElementById('stats').innerHTML='<span class=bad>SENSOR YOK</span><br>AMG status: '+d.amg_status;"
    "diag.style.display='inline-block';"
    "diag.innerHTML='<b>I2C tarama:</b> '+d.i2c_scan+'<br><b>SDA pin:</b> GPIO'+d.sda_pin+'<br><b>SCL pin:</b> GPIO'+d.scl_pin+'<br><b>Beklenen adres:</b> 0x69 veya 0x68<br><i>0x69/0x68 listede yoksa: kablo/guc/voltaj sorunu. Listede var ama amg.begin basarisiz ise: dogru sensor degil veya AD0 ters.</i>';"
    "return;"
    "}"
    "diag.style.display='none';"
    "const range=Math.max(0.5,d.max-d.min);"
    "for(let i=0;i<64;i++){const p=d.pixels[i];const t=(p-d.min)/range;"
    "const el=document.getElementById('c'+i);"
    "el.style.background=color(t);el.textContent=p.toFixed(1);"
    "if(d.blob_mask&&d.blob_mask[i]=='1')el.classList.add('blob');else el.classList.remove('blob');}"
    "const big=document.getElementById('big');"
    "const skin=document.getElementById('skin');"
    "const skinsub=document.getElementById('skinsub');"
    "big.classList.remove('none','warm','hot');"
    "if(!d.person_present){"
    "big.classList.add('none');skin.textContent='--';"
    "skinsub.textContent='kimse algilanmadi (blob '+d.blob_size+'/64 px)';"
    "}else{"
    "skin.textContent=d.skin_temp.toFixed(1)+' C';"
    "if(d.skin_temp>=37.5)big.classList.add('hot');"
    "else if(d.skin_temp>=37.0)big.classList.add('warm');"
    "skinsub.textContent='blob '+d.blob_size+' px | raw '+d.skin_temp_raw.toFixed(1)+' +offset '+d.skin_offset.toFixed(1)+' | dT '+d.delta_t.toFixed(1)+' C';"
    "}"
    "document.getElementById('stats').innerHTML="
    "'Okuma: <span>#'+d.count+'</span><br>'+"
    "'Min: <span>'+d.min.toFixed(1)+' C</span> | '+"
    "'Max: <span>'+d.max.toFixed(1)+' C</span><br>'+"
    "'Ortalama: <span>'+d.avg.toFixed(1)+' C</span> | '+"
    "'Termistor: <span>'+d.thermistor.toFixed(2)+' C</span><br>'+"
    "'Ambient (medyan): <span>'+d.ambient.toFixed(1)+' C</span>'"
    "}catch(e){document.getElementById('stats').innerHTML='<span class=bad>Hata: '+e+'</span>'}"
    "}"
    "setInterval(tick,500);tick();"
    "</script></body></html>";
  server.send(200, "text/html", html);
}

void setup() {
  Serial.begin(115200);
  delay(800);
  Serial.println();
  Serial.println("=========================================");
  Serial.println("[AMG8833] Standalone + Web Heatmap");
  Serial.println("=========================================");

  pinMode(LED_ERR_PIN, OUTPUT);
  pinMode(LED_OK_PIN,  OUTPUT);
  digitalWrite(LED_ERR_PIN, LOW);
  digitalWrite(LED_OK_PIN,  LOW);

  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  Wire.setClock(100000);
  Serial.printf("[I2C] SDA=GPIO%d, SCL=GPIO%d, 100kHz\n", I2C_SDA_PIN, I2C_SCL_PIN);

  Serial.println("[I2C] Bus tarama:");
  scanI2C();

  Serial.print("[AMG] Baslatiliyor (0x69)... ");
  if (amg.begin(0x69)) {
    amg_ok = true;
    amg_status = "OK @ 0x69";
    Serial.println("OK");
  } else {
    Serial.print("HATA, 0x68 deniyor... ");
    if (amg.begin(0x68)) {
      amg_ok = true;
      amg_status = "OK @ 0x68";
      Serial.println("OK (0x68)");
    } else {
      amg_status = "0x69 ve 0x68'de YOK";
      Serial.println("YOK!");
    }
  }

  digitalWrite(LED_OK_PIN,  amg_ok ? HIGH : LOW);
  digitalWrite(LED_ERR_PIN, amg_ok ? LOW  : HIGH);

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
    digitalWrite(LED_OK_PIN, LOW);
    while (true) {
      digitalWrite(LED_ERR_PIN, HIGH); delay(200);
      digitalWrite(LED_ERR_PIN, LOW);  delay(200);
    }
  }
  Serial.print("[WIFI] Bagli. IP: ");
  Serial.println(WiFi.localIP());
  Serial.printf("[WIFI] RSSI: %d dBm\n", WiFi.RSSI());

  server.on("/",       handleRoot);
  server.on("/grid",   handleGrid);
  server.on("/rescan", handleRescan);
  server.begin();
  Serial.println("[HTTP] Acildi: /, /grid, /rescan");
  Serial.println();
  Serial.printf(">>> Tarayicidan ac: http://%s/\n", WiFi.localIP().toString().c_str());
  Serial.println("=========================================");
}

void loop() {
  server.handleClient();

  if (millis() - last_read_ms >= 200) {
    last_read_ms = millis();
    readSensor();
  }

  // 5 sn'de bir cilt çıkarım özeti
  static uint32_t last_skin_log = 0;
  if (amg_ok && millis() - last_skin_log >= 5000) {
    last_skin_log = millis();
    if (person_present) {
      Serial.printf("[SKIN] present=Y blob=%upx raw=%.2fC skin=%.2fC amb=%.2fC dT=%.2fC\n",
                    (unsigned)blob_size_v, skin_temp_raw_v, skin_temp_v,
                    ambient_v, delta_t_v);
    } else {
      Serial.printf("[SKIN] present=N blob=%upx max=%.2fC amb=%.2fC (esik %.1fC)\n",
                    (unsigned)blob_size_v, pmax_v, ambient_v, SKIN_MIN_GLOBAL_MAX_C);
    }
  }
}
