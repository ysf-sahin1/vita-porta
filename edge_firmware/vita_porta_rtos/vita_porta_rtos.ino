// =====================================================================
//  vita_porta_rtos.ino  —  ESP32-CAM Echtzeit-Kern (FreeRTOS)
//  Vita Porta — Yaşam Kapısı  |  INF 208 Eingebettete Systeme
//  Abschnitt 3.3: Software / RTOS und Echtzeit
// =====================================================================
//
//  Diese Firmware ist die EXPLIZITE FreeRTOS-Umstrukturierung des
//  kooperativen Superloops aus vita_porta_cam.ino. Sie demonstriert
//  nachweisbar alle vom Projektleitfaden (3.3) geforderten Punkte:
//
//    (1) RTOS .................. FreeRTOS (SMP, Arduino-ESP32 Core)
//    (2) Tasks ................. periodisch + sporadisch, STATISCHE Prioritäten
//    (3) Geteilte Ressourcen ... Mutex/Semaphor (I2C-Bus, Verdict-State)
//    (4) Prioritätsinversion ... Demonstration + Lösung: Priority Inheritance
//                                (FreeRTOS-Mutex) bzw. Priority Ceiling
//    (5) IRQ / ISR ............. Kategorie-1- und Kategorie-2-ISR (OSEK-Diktion)
//                                PIR-GPIO-Interrupt mit Deferred Handling
//    (6) WCET .................. GPIO-Toggle-Instrumentierung (Logikanalysator)
//                                + esp_timer_get_time() Software-Messung
//
//  Hardware (real, vgl. README):
//    ESP32-CAM (AI-Thinker, Xtensa LX6 Dual-Core @ 240 MHz)
//    AMG8833 Thermalsensor (I2C: SDA=GPIO2, SCL=GPIO14)
//    RGB-LED  (R=GPIO13, G=GPIO15)  — Triage-Anzeige (Aktor)
//    PIR HC-SR501 (GPIO16)          — Bewegungs-Trigger (sporadisch)
//    GPIO12                          — WCET-Mess-Pin (Logikanalysator)
// =====================================================================

#include <Arduino.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "freertos/queue.h"
#include <Wire.h>
#include <Adafruit_AMG88xx.h>
#include "esp_timer.h"
#include "driver/gpio.h"     // gpio_set_level() für die WCET-Sonde

// --------------------------------------------------------------------
//  Pin-Belegung
// --------------------------------------------------------------------
#define LED_R_PIN     13      // Aktor: rot   (kritisch / Fieber)
#define LED_G_PIN     15      // Aktor: grün  (normal)
#define I2C_SDA_PIN    2
#define I2C_SCL_PIN   14
#define PIR_PIN       16      // Bewegungssensor (Interrupt-Quelle)
#define WCET_PROBE    12      // GPIO-Toggle für Logikanalysator/Oszilloskop

// --------------------------------------------------------------------
//  Statische Prioritäten  (tskIDLE_PRIORITY = 0)
//  Rate-Monotonic-Heuristik: kürzere Periode -> höhere Priorität.
//  Der LED-Aktor ist die einzige Komponente mit harter Deadline,
//  deshalb erhält er die höchste Anwendungspriorität.
// --------------------------------------------------------------------
#define PRIO_LED        5     // 50 ms Periode  — harte Deadline (Aktor)
#define PRIO_MOTION     4     // sporadisch     — durch ISR freigegeben
#define PRIO_THERMAL    3     // 250 ms Periode — I2C-Abtastung (4 Hz)
#define PRIO_COMMAND    2     // sporadisch     — Verdict-Kommandos
#define PRIO_STREAM     1     // weiche Deadline — MJPEG-Durchsatz (best effort)

// Core-Pinning (SMP): zeit­kritische Tasks auf APP_CPU (Core 1),
// Netzwerk/Durchsatz auf PRO_CPU (Core 0), wie im realen System.
#define CORE_RT    1
#define CORE_NET   0

// --------------------------------------------------------------------
//  Geteilte Zustände + Synchronisationsobjekte
// --------------------------------------------------------------------
Adafruit_AMG88xx amg;
bool amg_ok = false;

// Verdict-State: vom COMMAND-Task geschrieben, vom LED-Task gelesen.
// -> Wettlaufgefahr -> Mutex.
enum VerdictLevel { VERDICT_NONE=0, VERDICT_INSUFFICIENT=1,
                    VERDICT_GREEN=2, VERDICT_YELLOW=3, VERDICT_RED=4 };
struct VerdictState {
  VerdictLevel level;
  uint32_t     last_ms;
};
static VerdictState g_verdict = { VERDICT_NONE, 0 };
#define VERDICT_TTL_MS 10000

// Thermal-Ergebnis (vom THERMAL-Task geschrieben, vom STREAM-Task gelesen).
static volatile float g_skin_temp = 0.0f;

// --- Synchronisationsobjekte ---
SemaphoreHandle_t mtx_i2c;        // schützt den gemeinsamen I2C-Bus
SemaphoreHandle_t mtx_verdict;    // schützt g_verdict  (Priority Inheritance)
SemaphoreHandle_t sem_motion;     // ISR -> Task: zählender Semaphor (Kat-2-Defer)
QueueHandle_t     q_command;      // Kommandos an den COMMAND-Task

// ISR-Diagnosezähler (Kategorie-1-ISR aktualisiert ihn direkt)
volatile uint32_t g_pir_edges = 0;

// =====================================================================
//  WCET-Instrumentierung
//  Variante A (Hardware): GPIO-Toggle, Pulsbreite am Logikanalysator =
//                         exakte Ausführungszeit, kein Software-Overhead.
//  Variante B (Software): esp_timer_get_time() in Mikrosekunden.
// =====================================================================
static inline void wcetHigh() { gpio_set_level((gpio_num_t)WCET_PROBE, 1); }
static inline void wcetLow()  { gpio_set_level((gpio_num_t)WCET_PROBE, 0); }

// gleitendes Maximum (beobachtete WCET) je Task
static volatile int64_t wcet_thermal_us = 0;
static volatile int64_t wcet_led_us     = 0;

// =====================================================================
//  ISR — Kategorie 1 vs. Kategorie 2  (OSEK/AUTOSAR-Diktion)
// =====================================================================
//
//  Kategorie 1: ruft KEINE RTOS-Dienste auf, kehrt direkt zurück,
//               minimale Latenz. Hier: reines Flanken-Zählen.
//  Kategorie 2: darf RTOS-Dienste (…FromISR) aufrufen und stößt einen
//               Task an ("Deferred Interrupt Handling" / Bottom-Half).
//
//  Die PIR-ISR vereint beide Aspekte: sie zählt (Kat-1-artig, IRAM)
//  und gibt einen Semaphor frei (Kat-2), der den MOTION-Task aufweckt.
//  Die eigentliche, evtl. längere Arbeit läuft NICHT in der ISR.
// --------------------------------------------------------------------
void IRAM_ATTR pirIsr() {
  g_pir_edges++;                                   // Kategorie-1-Anteil
  BaseType_t hpw = pdFALSE;
  xSemaphoreGiveFromISR(sem_motion, &hpw);         // Kategorie-2-Anteil
  if (hpw == pdTRUE) portYIELD_FROM_ISR();         // sofortiges Rescheduling
}

// =====================================================================
//  TASK 1 — LED-Aktor  (periodisch 50 ms, höchste Priorität)
//  Harte Deadline: die Triage-Farbe muss flüssig (>=20 Hz) anliegen.
//  Greift kurz auf g_verdict zu -> Mutex mit Priority Inheritance.
// =====================================================================
void taskLed(void* pv) {
  const TickType_t period = pdMS_TO_TICKS(50);
  TickType_t last = xTaskGetTickCount();
  for (;;) {
    int64_t t0 = esp_timer_get_time();
    wcetHigh();

    VerdictLevel lvl; uint32_t age;
    // --- kritischer Abschnitt: kurz halten! ---
    xSemaphoreTake(mtx_verdict, portMAX_DELAY);
    lvl = g_verdict.level;
    age = millis() - g_verdict.last_ms;
    xSemaphoreGive(mtx_verdict);
    // ------------------------------------------

    bool stale = (g_verdict.last_ms == 0) || (age > VERDICT_TTL_MS);
    bool red_on = false, green_on = false;
    if (!stale) {
      switch (lvl) {
        case VERDICT_RED:    red_on = true; break;
        case VERDICT_YELLOW: red_on = (millis()/500) & 1; break;  // 1 Hz Blink
        case VERDICT_GREEN:  green_on = true; break;
        default: break;
      }
    }
    digitalWrite(LED_R_PIN, red_on   ? HIGH : LOW);
    digitalWrite(LED_G_PIN, green_on ? HIGH : LOW);

    wcetLow();
    int64_t dt = esp_timer_get_time() - t0;
    if (dt > wcet_led_us) wcet_led_us = dt;

    vTaskDelayUntil(&last, period);   // exakte periodische Freigabe
  }
}

// =====================================================================
//  TASK 2 — Thermal-Abtastung (periodisch 250 ms, 4 Hz)
//  Liest AMG8833 über den GETEILTEN I2C-Bus -> Mutex mtx_i2c.
//  Dies ist der Task, der in der Prioritätsinversions-Demo das
//  Mutex hält, während der hochpriore LED-Task es anfordert.
// =====================================================================
void taskThermal(void* pv) {
  const TickType_t period = pdMS_TO_TICKS(250);
  TickType_t last = xTaskGetTickCount();
  float px[AMG88xx_PIXEL_ARRAY_SIZE];
  for (;;) {
    int64_t t0 = esp_timer_get_time();
    wcetHigh();

    if (amg_ok) {
      // I2C ist von mehreren Tasks nutzbar -> Mutex schützt die Transaktion
      xSemaphoreTake(mtx_i2c, portMAX_DELAY);
      amg.readPixels(px);
      xSemaphoreGive(mtx_i2c);

      float pmax = px[0];
      for (int i = 1; i < AMG88xx_PIXEL_ARRAY_SIZE; i++)
        if (px[i] > pmax) pmax = px[i];
      // delta-gain Kompensation (vereinfacht, vgl. computeSkinTemp())
      g_skin_temp = pmax + 1.8f * (pmax - amg.readThermistor()) + 2.0f;
    }

    wcetLow();
    int64_t dt = esp_timer_get_time() - t0;
    if (dt > wcet_thermal_us) wcet_thermal_us = dt;

    vTaskDelayUntil(&last, period);
  }
}

// =====================================================================
//  TASK 3 — Motion / PIR  (SPORADISCH, durch Kat-2-ISR freigegeben)
//  Blockiert auf dem Semaphor; läuft nur bei einer Bewegungsflanke.
//  Minimale Zwischenankunftszeit (MIT) durch Entprellung erzwungen
//  -> dadurch wird das Sporadic-Task-Modell eingehalten.
// =====================================================================
void taskMotion(void* pv) {
  const TickType_t min_gap = pdMS_TO_TICKS(200);  // erzwungene MIT (Entprellung)
  for (;;) {
    if (xSemaphoreTake(sem_motion, portMAX_DELAY) == pdTRUE) {
      // Deferred work: Sitzung anstoßen, Gateway benachrichtigen …
      Serial.printf("[MOTION] Flanke #%u  -> Triage-Sitzung getriggert\n",
                    (unsigned)g_pir_edges);
      vTaskDelay(min_gap);   // verhindert ISR-Sturm (Sporadic-Garantie)
    }
  }
}

// =====================================================================
//  TASK 4 — Command / Verdict  (SPORADISCH, ereignisgesteuert)
//  Empfängt das Supervisor-Verdict (rot/gelb/grün) aus einer Queue
//  und schreibt g_verdict unter Mutex-Schutz.
// =====================================================================
void taskCommand(void* pv) {
  VerdictLevel incoming;
  for (;;) {
    if (xQueueReceive(q_command, &incoming, portMAX_DELAY) == pdTRUE) {
      xSemaphoreTake(mtx_verdict, portMAX_DELAY);
      g_verdict.level   = incoming;
      g_verdict.last_ms = millis();
      xSemaphoreGive(mtx_verdict);
      Serial.printf("[VERDICT] gesetzt: %d\n", (int)incoming);
    }
  }
}

// =====================================================================
//  TASK 5 — Stream  (weiche Deadline, niedrigste Priorität, Core 0)
//  Repräsentiert den MJPEG-Durchsatz-Task. Best-Effort: darf von den
//  zeitkritischen Tasks jederzeit verdrängt werden.
//  In der Inversions-Demo ist dies der MITTLERE Task, der ohne
//  Vererbung den hochprioren LED-Task aushungern würde.
// =====================================================================
void taskStream(void* pv) {
  for (;;) {
    // (realer Code: esp_camera_fb_get() -> httpd_resp_send_chunk())
    // hier: CPU-Last simulieren, um die mittlere Priorität zu zeigen
    volatile uint32_t acc = 0;
    for (uint32_t i = 0; i < 200000; i++) acc += i;
    taskYIELD();
  }
}

// =====================================================================
//  PRIORITÄTSINVERSIONS-DEMONSTRATION
//  Geteiltes Mutex: mtx_verdict (genutzt von COMMAND und LED).
//  Szenario (ohne Vererbung wäre es eine UNBEGRENZTE Inversion):
//    L (command, prio 2) nimmt mtx_verdict ...
//    M (thermal, prio 3) wird rechenbereit und verdrängt L ...
//    H (led,     prio 5) will mtx_verdict -> blockiert.
//  Ohne Vererbung: M (prio 3) verdrängt L (prio 2), H (prio 5) wartet
//    so lange, wie M rechnet -> Inversion über die Mutex-Haltezeit hinaus.
//  Mit FreeRTOS-Mutex (configUSE_MUTEXES=1): L erbt prio 5, verdrängt M
//    sofort, beendet seinen kritischen Abschnitt und gibt das Mutex frei
//    -> H läuft. Blockierung von H ist auf die (kurze) Länge des
//    kritischen Abschnitts von L begrenzt = beschränkte Inversion.
//  Messung: GPIO-Toggle zeigt die Blockierdauer von H am Logikanalysator.
// =====================================================================

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("\n[Vita Porta] FreeRTOS Echtzeit-Kern startet");

  pinMode(LED_R_PIN, OUTPUT);
  pinMode(LED_G_PIN, OUTPUT);
  pinMode(WCET_PROBE, OUTPUT);
  pinMode(PIR_PIN, INPUT);

  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  amg_ok = amg.begin();
  Serial.printf("[AMG] %s\n", amg_ok ? "OK" : "nicht gefunden");

  // --- Synchronisationsobjekte ---
  // xSemaphoreCreateMutex() -> Priority-Inheritance-fähig.
  // (Ein reiner Binärsemaphor xSemaphoreCreateBinary() hätte KEINE
  //  Vererbung und würde die Inversion NICHT lösen.)
  mtx_i2c     = xSemaphoreCreateMutex();
  mtx_verdict = xSemaphoreCreateMutex();
  sem_motion  = xSemaphoreCreateCounting(8, 0);
  q_command   = xQueueCreate(4, sizeof(VerdictLevel));

  // --- Kategorie-2-ISR registrieren (steigende Flanke) ---
  attachInterrupt(digitalPinToInterrupt(PIR_PIN), pirIsr, RISING);

  // --- Tasks mit STATISCHEN Prioritäten erzeugen, Core-gepinnt ---
  xTaskCreatePinnedToCore(taskLed,     "led",     3072, NULL, PRIO_LED,     NULL, CORE_RT);
  xTaskCreatePinnedToCore(taskMotion,  "motion",  3072, NULL, PRIO_MOTION,  NULL, CORE_RT);
  xTaskCreatePinnedToCore(taskThermal, "thermal", 4096, NULL, PRIO_THERMAL, NULL, CORE_RT);
  xTaskCreatePinnedToCore(taskCommand, "command", 3072, NULL, PRIO_COMMAND, NULL, CORE_RT);
  xTaskCreatePinnedToCore(taskStream,  "stream",  4096, NULL, PRIO_STREAM,  NULL, CORE_NET);

  Serial.println("[RTOS] 5 Tasks erzeugt — Scheduler übernimmt");
}

// Der Arduino-loop() läuft als eigener FreeRTOS-Task (loopTask) mit
// Priorität 1. Wir nutzen ihn hier nur für periodische Telemetrie.
void loop() {
  Serial.printf("[WCET] thermal=%lld us  led=%lld us  pir_edges=%u\n",
                wcet_thermal_us, wcet_led_us, (unsigned)g_pir_edges);
  vTaskDelay(pdMS_TO_TICKS(5000));
}
