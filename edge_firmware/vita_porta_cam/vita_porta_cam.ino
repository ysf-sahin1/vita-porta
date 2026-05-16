// vita_porta_cam.ino — Aşama B: Kamera + Wi-Fi + MJPEG canlı yayın
// =================================================================
// Bu kart (AI-Thinker klonu, Robocombo) için ampirik en iyi ayarlar:
//   - xclk    16 MHz   (20MHz'de OV2640 kararsız, FPS düşüyor)
//   - fb_count 1       (fb_count=2'de PSRAM bandwidth çakışıyor, FPS çöküyor)
//   - quality 12       (12<x<=14 stabil; 18+ DSP'de tıkanıyor, FPS çöküyor)
//   - grab_mode WHEN_EMPTY  (kanonik CameraWebServer ile aynı, daha kararlı)
//
// Bu kombinasyon VGA'da ~10 FPS veriyor — bu kart için tavan.

#include "esp_camera.h"
#include "esp_http_server.h"
#include <WiFi.h>
#include <WebServer.h>

// ============================================================
//  ⚙️  WI-FI BİLGİLERİNİ BURAYA GİR
// ============================================================
const char* WIFI_SSID     = "WIFI_ADIN_BURAYA";
const char* WIFI_PASSWORD = "WIFI_SIFRESI_BURAYA";
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

WebServer server(80);
httpd_handle_t stream_httpd = NULL;

volatile uint32_t frames_sent     = 0;
volatile uint32_t bytes_sent      = 0;
volatile uint32_t last_frame_ms   = 0;
volatile float    measured_fps    = 0.0f;
volatile uint32_t current_w       = 0;
volatile uint32_t current_h       = 0;
volatile uint32_t last_frame_size = 0;

#define PART_BOUNDARY "vitaportaboundary"
static const char* STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* STREAM_BOUNDARY     = "\r\n--" PART_BOUNDARY "\r\n";
static const char* STREAM_PART_HEADER  = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

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
  json += "\"free_heap\":" + String(ESP.getFreeHeap());
  json += "}";
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", json);
}

void handleRoot() {
  String ip = WiFi.localIP().toString();
  String html =
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<title>Vita Porta — Canli Yayin</title>"
    "<style>"
    "body{font-family:sans-serif;background:#0a0a0a;color:#eee;text-align:center;margin:20px}"
    "h2{color:#6cf;margin-bottom:4px}"
    "img{max-width:95%;border:2px solid #444;border-radius:8px}"
    ".stats{display:inline-block;background:#1a1a1a;padding:10px 20px;border-radius:6px;margin:10px;font-family:monospace;font-size:13px;text-align:left}"
    ".stats span{color:#6cf}"
    "a{color:#6cf;text-decoration:none}a:hover{text-decoration:underline}"
    "</style></head>"
    "<body><h2>Vita Porta — Canli Kamera</h2>"
    "<img src='http://" + ip + ":81/stream' />"
    "<div class='stats' id='stats'>Istatistikler yukleniyor...</div>"
    "<p><a href='/capture' target='_blank'>Tek kare yakala</a> | "
    "<a href='/info' target='_blank'>/info (JSON)</a></p>"
    "<script>"
    "async function update(){"
    "try{const r=await fetch('/info');const d=await r.json();"
    "document.getElementById('stats').innerHTML="
    "'Cozunurluk: <span>'+d.resolution+'</span><br>'+"
    "'FPS (olculen): <span>'+d.measured_fps.toFixed(1)+'</span><br>'+"
    "'Kare boyutu: <span>'+(d.last_frame_size/1024).toFixed(1)+' KB</span><br>'+"
    "'Toplam kare: <span>'+d.frames_sent+'</span><br>'+"
    "'RSSI: <span>'+d.rssi_dbm+' dBm</span><br>'+"
    "'Free heap: <span>'+(d.free_heap/1024).toFixed(1)+' KB</span><br>'+"
    "'Uptime: <span>'+d.uptime_s+' s</span>';"
    "}catch(e){document.getElementById('stats').innerHTML='Stats hata: '+e}"
    "}setInterval(update,1000);update();"
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

  // ---------- KART İÇİN AMPİRİK EN İYİ AYARLAR ----------
  config.xclk_freq_hz = 16000000;            // 16 MHz: 20'de kart kararsız
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location  = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;

  if (psramFound()) {
    config.frame_size   = FRAMESIZE_VGA;     // 640x480
    config.jpeg_quality = 12;                // 12 sweet spot; 14+ DSP issues
    config.fb_count     = 1;                 // fb_count=2 PSRAM bandwidth çakıştırıyor
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

  // Minimal sensor ayarı — agresif post-processing OV2640'ı yavaşlatıyor
  sensor_t* s = esp_camera_sensor_get();
  if (s) {
    s->set_brightness(s, 0);
    s->set_contrast(s, 0);
    s->set_saturation(s, 0);
    s->set_whitebal(s, 1);
    s->set_awb_gain(s, 1);
    s->set_exposure_ctrl(s, 1);
    s->set_gain_ctrl(s, 1);
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

  Serial.print("[CAM] Baslatiliyor... ");
  if (!initCamera()) {
    Serial.println("DURDURULDU");
    while (true) delay(1000);
  }
  Serial.println("OK (VGA 640x480 @ 16MHz xclk, fb=1, q=12)");

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
  server.begin();
  Serial.println("[HTTP-80] Acildi: /, /capture, /info");

  startStreamServer();

  Serial.println();
  Serial.println("=========================================");
  Serial.printf(">>> Ana sayfa : http://%s/\n", WiFi.localIP().toString().c_str());
  Serial.printf(">>> Stream    : http://%s:81/stream\n", WiFi.localIP().toString().c_str());
  Serial.println("=========================================");
}

void loop() {
  server.handleClient();

  static uint32_t last_report = 0;
  if (millis() - last_report > 5000) {
    last_report = millis();
    Serial.printf("[STATS] FPS=%.1f  res=%ux%u  frames=%u  heap=%uKB  RSSI=%ddBm\n",
                  measured_fps, current_w, current_h,
                  (uint32_t)frames_sent, ESP.getFreeHeap() / 1024, WiFi.RSSI());
  }
  delay(1);
}
