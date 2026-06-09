Simulationsverzeichnis - Prioritaetsinversion (INF 208, Abschnitt 3.3)

Datei: priority_inversion_sim.c
Deterministische Simulation eines praeemptiven Fixed-Priority-Schedulers.

Bauen und ausfuehren:
  gcc -O2 -o pi_sim priority_inversion_sim.c
  ./pi_sim

Ergebnis: Blockierzeit des hochprioren Tasks H
  ohne Priority Inheritance: ca. 18 ms (unbeschraenkt durch M)
  mit  Priority Inheritance: ca. 0,03 ms (nur kritischer Abschnitt von L)
