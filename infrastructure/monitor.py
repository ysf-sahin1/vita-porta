#!/usr/bin/env python3
"""Vita Porta — sistem kaynak izleyici (CPU / RAM / sıcaklık).

Rapor kriteri **1C — Performans & Kararlılık** için kantitatif veri üretir:
demo çalışırken Raspberry Pi'nin (ve opsiyonel olarak ESP32-CAM'in) kaynak
kullanımını saniyede bir CSV'ye loglar, sonunda eşiklere göre PASS/FAIL özeti basar.

Eşikler (kriterden):  CPU < %70   ·   RAM < %80   ·   Sıcaklık < 80°C

Kullanım:
    # Pi üzerinde, demo (3 servis) çalışırken 2 dakika ölç:
    python infrastructure/monitor.py --duration 120 --out metrics.csv

    # ESP32-CAM heap + FPS de dahil:
    python infrastructure/monitor.py --duration 120 --esp 192.168.4.2

    # CSV'den grafik üret (laptop'ta da çalışır):
    python infrastructure/monitor.py --plot metrics.csv

Gereksinim:  pip install psutil           (grafik için ayrıca: pip install matplotlib)
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

try:
    import psutil
except ImportError:
    print("psutil gerekli:  pip install psutil", file=sys.stderr)
    sys.exit(1)

# Kriter eşikleri
CPU_LIMIT = 70.0   # %
RAM_LIMIT = 80.0   # %
TEMP_LIMIT = 80.0  # °C

# İzlenecek Vita Porta servisleri (cmdline eşleşmesi → process RAM dökümü)
_SERVICE_MATCHERS = {
    "backend":  ("uvicorn", "backend_api"),
    "gateway":  ("gateway_agents.runner",),
    "frontend": ("next", "node"),
}


def read_pi_temp() -> float:
    """Raspberry Pi SoC sıcaklığı (°C). Pi dışında 0.0 döner."""
    # En taşınabilir yol: sysfs (millidegree)
    zone = Path("/sys/class/thermal/thermal_zone0/temp")
    if zone.exists():
        try:
            return int(zone.read_text().strip()) / 1000.0
        except (ValueError, OSError):
            pass
    # Yedek: psutil sensörleri (Pi dışı Linux / bazı kartlar)
    try:
        temps = psutil.sensors_temperatures()
        for entries in temps.values():
            if entries:
                return float(entries[0].current)
    except (AttributeError, OSError):
        pass
    return 0.0


def service_ram_mb() -> dict[str, float]:
    """Vita Porta servislerinin process bazında RAM kullanımı (MB)."""
    out = {k: 0.0 for k in _SERVICE_MATCHERS}
    for proc in psutil.process_iter(["cmdline", "memory_info"]):
        try:
            cmd = " ".join(proc.info["cmdline"] or [])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        for name, needles in _SERVICE_MATCHERS.items():
            if any(n in cmd for n in needles):
                mem = proc.info["memory_info"]
                if mem:
                    out[name] += mem.rss / (1024 * 1024)
                break
    return out


def poll_esp(host: str) -> tuple[float, float]:
    """ESP32-CAM /info → (free_heap_kb, measured_fps). Hata olursa (0, 0)."""
    try:
        import httpx

        resp = httpx.get(f"http://{host}/info", timeout=1.5)
        data = resp.json()
        return data.get("free_heap", 0) / 1024.0, float(data.get("measured_fps", 0.0))
    except Exception:  # noqa: BLE001 — best-effort izleme
        return 0.0, 0.0


def run(duration: int, interval: float, out_path: str, esp_host: str | None) -> None:
    rows: list[dict] = []
    start = time.time()
    # İlk çağrı 0.0 döner; bir kez ısıt
    psutil.cpu_percent(interval=None)
    time.sleep(0.2)

    print(f"İzleme başladı — {duration}s, her {interval}s. Çıkmak için Ctrl+C.")
    print(f"{'t(s)':>6} {'CPU%':>6} {'RAM%':>6} {'RAM_MB':>8} {'°C':>6}")

    try:
        while time.time() - start < duration:
            elapsed = round(time.time() - start, 1)
            cpu = psutil.cpu_percent(interval=None)
            vm = psutil.virtual_memory()
            temp = read_pi_temp()
            svc = service_ram_mb()

            row = {
                "t_s": elapsed,
                "cpu_pct": round(cpu, 1),
                "ram_pct": round(vm.percent, 1),
                "ram_used_mb": round(vm.used / (1024 * 1024), 1),
                "temp_c": round(temp, 1),
                "backend_mb": round(svc["backend"], 1),
                "gateway_mb": round(svc["gateway"], 1),
                "frontend_mb": round(svc["frontend"], 1),
            }
            if esp_host:
                heap_kb, fps = poll_esp(esp_host)
                row["esp_heap_kb"] = round(heap_kb, 1)
                row["esp_fps"] = round(fps, 1)

            rows.append(row)
            print(
                f"{elapsed:>6} {row['cpu_pct']:>6} {row['ram_pct']:>6} "
                f"{row['ram_used_mb']:>8} {row['temp_c']:>6}"
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nKullanıcı durdurdu.")

    if not rows:
        print("Veri toplanmadı.")
        return

    # CSV yaz
    fields = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nCSV kaydedildi: {out_path}  ({len(rows)} örnek)")

    _summary(rows)


def _summary(rows: list[dict]) -> None:
    """Eşiklere göre PASS/FAIL özeti — rapora doğrudan konabilir."""
    def stat(key: str) -> tuple[float, float]:
        vals = [r[key] for r in rows if key in r]
        return (max(vals), sum(vals) / len(vals)) if vals else (0.0, 0.0)

    cpu_max, cpu_avg = stat("cpu_pct")
    ram_max, ram_avg = stat("ram_pct")
    temp_max, temp_avg = stat("temp_c")

    def verdict(maxv: float, limit: float) -> str:
        return "PASS" if maxv < limit else "FAIL"

    print("\n" + "=" * 52)
    print(" PERFORMANS & KARARLILIK ÖZETİ (1C)")
    print("=" * 52)
    print(f" {'Metrik':<14}{'Ort.':>8}{'Maks.':>8}{'Eşik':>8}{'Sonuç':>8}")
    print(f" {'CPU (%)':<14}{cpu_avg:>8.1f}{cpu_max:>8.1f}{CPU_LIMIT:>8.0f}{verdict(cpu_max, CPU_LIMIT):>8}")
    print(f" {'RAM (%)':<14}{ram_avg:>8.1f}{ram_max:>8.1f}{RAM_LIMIT:>8.0f}{verdict(ram_max, RAM_LIMIT):>8}")
    print(f" {'Sıcaklık (°C)':<14}{temp_avg:>8.1f}{temp_max:>8.1f}{TEMP_LIMIT:>8.0f}{verdict(temp_max, TEMP_LIMIT):>8}")
    print("=" * 52)


def plot(csv_path: str) -> None:
    """CSV'den zaman serisi grafiği üretir (rapora görsel)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib gerekli:  pip install matplotlib", file=sys.stderr)
        sys.exit(1)

    t, cpu, ram, temp = [], [], [], []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            t.append(float(r["t_s"]))
            cpu.append(float(r["cpu_pct"]))
            ram.append(float(r["ram_pct"]))
            temp.append(float(r["temp_c"]))

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.set_xlabel("Zaman (s)")
    ax1.set_ylabel("Kullanım (%)")
    ax1.plot(t, cpu, label="CPU %", color="#3b82c4")
    ax1.plot(t, ram, label="RAM %", color="#3f9e54")
    ax1.axhline(CPU_LIMIT, ls="--", color="#3b82c4", alpha=0.4)
    ax1.axhline(RAM_LIMIT, ls="--", color="#3f9e54", alpha=0.4)
    ax1.set_ylim(0, 100)

    ax2 = ax1.twinx()
    ax2.set_ylabel("Sıcaklık (°C)")
    ax2.plot(t, temp, label="Sıcaklık °C", color="#d9534f")
    ax2.axhline(TEMP_LIMIT, ls="--", color="#d9534f", alpha=0.4)
    ax2.set_ylim(0, 100)

    lines = ax1.get_lines()[:2] + ax2.get_lines()[:1]
    ax1.legend(lines, [l.get_label() for l in lines], loc="upper right")
    plt.title("Vita Porta — Kaynak Kullanımı (Raspberry Pi 3)")
    fig.tight_layout()
    out = Path(csv_path).with_suffix(".png")
    fig.savefig(out, dpi=130)
    print(f"Grafik kaydedildi: {out}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vita Porta kaynak izleyici (1C).")
    parser.add_argument("--duration", type=int, default=120, help="İzleme süresi (sn).")
    parser.add_argument("--interval", type=float, default=1.0, help="Örnekleme aralığı (sn).")
    parser.add_argument("--out", type=str, default="metrics.csv", help="CSV çıktı yolu.")
    parser.add_argument("--esp", type=str, default=None, metavar="IP", help="ESP32-CAM IP (heap+fps).")
    parser.add_argument("--plot", type=str, default=None, metavar="CSV", help="CSV'den grafik üret.")
    args = parser.parse_args(argv)

    if args.plot:
        plot(args.plot)
        return 0

    run(args.duration, args.interval, args.out, args.esp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
