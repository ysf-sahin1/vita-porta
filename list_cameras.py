import cv2

print("--- KAMERA TARAMASI BAŞLATILIYOR ---")
print("Sistemdeki kamera indeksleri test ediliyor (0'dan 5'e kadar)...\n")

for i in range(6):
    print(f"[*] Indeks {i} test ediliyor...")
    
    # 1. Varsayılan (MSMF) backend testi
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        if ret:
            print(f"    [Varsayılan Backend]: BAŞARILI - Görüntü akışı alınıyor. (Çözünürlük: {frame.shape[1]}x{frame.shape[0]})")
        else:
            print(f"    [Varsayılan Backend]: AÇILDI ancak kare okunamadı (Siyah ekran veya pasif sanal sürücü).")
    else:
        print(f"    [Varsayılan Backend]: Açılamadı.")

    # 2. DirectShow (DSHOW) backend testi
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if cap.isOpened():
        ret, frame = cap.read()
        cap.release()
        if ret:
            print(f"    [DirectShow (DSHOW)]: BAŞARILI - Görüntü akışı alınıyor. (Çözünürlük: {frame.shape[1]}x{frame.shape[0]})")
        else:
            print(f"    [DirectShow (DSHOW)]: AÇILDI ancak kare okunamadı.")
    else:
        print(f"    [DirectShow (DSHOW)]: Açılamadı.")
    print("-" * 50)

print("\nTARAMA TAMAMLANDI.")
print("Iriun Webcam uygulamasının telefonda aktif olduğundan emin olun.")
