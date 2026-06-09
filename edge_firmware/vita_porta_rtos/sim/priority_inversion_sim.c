// =====================================================================
//  priority_inversion_sim.c
//  Vita Porta — Yaşam Kapısı | INF 208 | Abschnitt 3.3 (WCET via Simulation)
// =====================================================================
//  Deterministische Simulation eines präemptiven Fixed-Priority-Schedulers,
//  die das im Bericht (Abb. 2) beschriebene Drei-Task-Szenario nachbildet
//  und die BLOCKIERZEIT des hochprioren Tasks H misst:
//
//      L = command (Prio 2)  hält das Mutex (kritischer Abschnitt 50 us)
//      M = thermal (Prio 3)  reine Rechenlast 18 ms, nutzt das Mutex NICHT
//      H = led     (Prio 5)  will dasselbe Mutex -> blockiert
//
//  Zwei Läufe:  (1) OHNE Priority Inheritance  -> unbeschränkte Inversion
//               (2) MIT  Priority Inheritance  -> beschränkte Inversion
//
//  Der Leitfaden lässt WCET/Echtzeit-Nachweise per SIMULATION ausdrücklich zu.
//  Build & Run:   gcc -O2 -o pi_sim priority_inversion_sim.c && ./pi_sim
// =====================================================================
#include <stdio.h>
#include <stdint.h>

// ---- Mikro-Programm jeder Task: Folge von Operationen ----
typedef enum { OP_RUN, OP_LOCK, OP_UNLOCK, OP_END } OpType;
typedef struct { OpType type; int64_t dur_us; } Op;

typedef struct {
  const char* name;
  int   prio_base;     // statische Basispriorität
  int   prio_eff;      // effektive Priorität (kann durch Vererbung steigen)
  int64_t arrival_us;  // Freigabezeitpunkt
  const Op* prog;      // Mikro-Programm
  int   pc;            // Programmzähler
  int64_t seg_left;    // Restzeit des aktuellen RUN-Segments
  int   started;       // RUN-Segment geladen?
  int   finished;
  int   blocked;       // wartet auf Mutex?
  int   holds_mutex;
} Task;

// Szenario-Programme
static const Op progL[] = { {OP_LOCK,0}, {OP_RUN,50}, {OP_UNLOCK,0}, {OP_RUN,10}, {OP_END,0} };
static const Op progM[] = { {OP_RUN,18000}, {OP_END,0} };
static const Op progH[] = { {OP_RUN,20},  {OP_LOCK,0}, {OP_RUN,30}, {OP_UNLOCK,0}, {OP_END,0} };

typedef struct { int owner; int waiter; } Mutex;   // -1 = frei/keiner

static int64_t h_lock_request_us = -1, h_lock_acquire_us = -1;

// höchstpriore lauffähige Task (größere Zahl = höher); -1 falls keine
static int pick(Task* t, int n) {
  int best = -1;
  for (int i = 0; i < n; i++) {
    if (t[i].finished || t[i].blocked) continue;
    if (t[i].arrival_us > 0) continue;             // noch nicht freigegeben
    if (best < 0 || t[i].prio_eff > t[best].prio_eff) best = i;
  }
  return best;
}

static int64_t run_scenario(int use_inheritance) {
  Task t[3] = {
    {"L-command", 2, 2, 0,    progL, 0, 0, 0, 0, 0, 0},
    {"M-thermal", 3, 3, 20,   progM, 0, 0, 0, 0, 0, 0},
    {"H-led",     5, 5, 40,   progH, 0, 0, 0, 0, 0, 0},
  };
  Mutex mtx = { -1, -1 };
  h_lock_request_us = h_lock_acquire_us = -1;

  int64_t now = 0;
  int last_running = -2;
  printf("  t(us)  | laufende Task (eff.Prio)\n");
  printf("  -------+--------------------------\n");

  for (int guard = 0; guard < 10000000; guard++) {
    // Freigaben fällig?
    for (int i = 0; i < 3; i++)
      if (t[i].arrival_us > 0 && t[i].arrival_us <= now) t[i].arrival_us = 0;

    int r = pick(t, 3);
    if (r < 0) {                       // niemand lauffähig -> Zeit zur nächsten Ankunft springen
      int64_t next = -1;
      for (int i = 0; i < 3; i++)
        if (!t[i].finished && t[i].arrival_us > 0)
          if (next < 0 || t[i].arrival_us < next) next = t[i].arrival_us;
      if (next < 0) break;             // fertig
      now = next; continue;
    }

    if (r != last_running) {
      printf("  %6lld | %s (P%d)\n", (long long)now, t[r].name, t[r].prio_eff);
      last_running = r;
    }

    Task* T = &t[r];
    const Op* op = &T->prog[T->pc];

    if (op->type == OP_RUN) {
      if (!T->started) { T->seg_left = op->dur_us; T->started = 1; }
      int64_t step = 1;                 // 1-us-Auflösung erlaubt Präemption
      now += step; T->seg_left -= step;
      if (T->seg_left <= 0) { T->pc++; T->started = 0; }
    }
    else if (op->type == OP_LOCK) {
      if (r == 2 && h_lock_request_us < 0) h_lock_request_us = now;  // H fragt an
      if (mtx.owner < 0) {                        // frei -> nehmen
        mtx.owner = r; T->holds_mutex = 1; T->pc++;
        if (r == 2) h_lock_acquire_us = now;
      } else {                                    // belegt -> blockieren
        T->blocked = 1; mtx.waiter = r;
        if (use_inheritance) {                    // Vererbung: Owner erbt eff.Prio
          if (t[mtx.owner].prio_eff < T->prio_eff)
            t[mtx.owner].prio_eff = T->prio_eff;
        }
      }
    }
    else if (op->type == OP_UNLOCK) {
      mtx.owner = -1; T->holds_mutex = 0; T->pc++;
      T->prio_eff = T->prio_base;                 // geerbte Priorität zurücksetzen
      if (mtx.waiter >= 0) {                       // Wartenden wecken + Mutex übergeben
        int w = mtx.waiter; mtx.waiter = -1;
        t[w].blocked = 0;
        mtx.owner = w; t[w].holds_mutex = 1; t[w].pc++;
        if (w == 2) h_lock_acquire_us = now;
      }
    }
    else { // OP_END
      T->finished = 1; last_running = -2;
    }

    int done = 1; for (int i=0;i<3;i++) if(!t[i].finished) done=0;
    if (done) break;
  }
  return h_lock_acquire_us - h_lock_request_us;   // Blockierzeit von H
}

int main(void) {
  printf("=====================================================\n");
  printf(" Vita Porta — Prioritaetsinversion: Simulation\n");
  printf(" Szenario: L(P2) haelt Mutex, M(P3) 18ms Last, H(P5) will Mutex\n");
  printf("=====================================================\n\n");

  printf("[Lauf 1] OHNE Priority Inheritance\n");
  int64_t b_without = run_scenario(0);
  printf("  -> H blockiert: %lld us  (= %.3f ms)\n\n", (long long)b_without, b_without/1000.0);

  printf("[Lauf 2] MIT Priority Inheritance\n");
  int64_t b_with = run_scenario(1);
  printf("  -> H blockiert: %lld us  (= %.3f ms)\n\n", (long long)b_with, b_with/1000.0);

  printf("=====================================================\n");
  printf(" ERGEBNIS\n");
  printf("   ohne Vererbung : %8lld us  (%.3f ms)  -> unbeschraenkt durch M\n",
         (long long)b_without, b_without/1000.0);
  printf("   mit  Vererbung : %8lld us  (%.3f ms)  -> nur krit. Abschnitt von L\n",
         (long long)b_with, b_with/1000.0);
  printf("   Reduktion      : Faktor %.0f\n", (double)b_without/(b_with>0?b_with:1));
  printf("=====================================================\n");
  return 0;
}
