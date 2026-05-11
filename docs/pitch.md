# VITA PORTA — Yaşam Kapısı
### Acil Servis için Yapay Zekâ Triaj Asistanı

**Ekip:** Yusuf Şahin · Mert Mirzaoğlu · Mert Korkmaz  
**Etkinlik:** CODEX AI Hackathon 2026 · Tıp ve Sağlık Teknolojileri

---

## Vita Porta Nedir?

Acil servis girişine konumlanan, hemşireye triaj asistanlığı yapan bir yapay zekâ sistemi.

Kapıdan giren her hastayı **3 saniye içinde** gözleyerek; yürüyüş örüntüsü, ten rengi, solunum hareketi, vücut sıcaklığı ve yüz ifadesi gibi görsel ve termal sinyalleri **beş bağımsız yapay zekâ ajanı** aracılığıyla analiz eder. Hemşireye gerekçeli ve açıklanabilir bir triaj kategorisi önerisi sunar.

| Özellik | Açıklama |
|---|---|
| ⚡ Hızlı | 3 saniye içinde değerlendirme |
| 🔍 Şeffaf | Her karar gerekçesiyle birlikte |
| 🤝 Asistan | Hemşirenin yerine değil yanında |

---

## Çözdüğü Problem

**Acil servislerde triaj subjektif ve zaman baskısı altında.**

Hastaneye gelen kritik vakalar, yorgun bir hemşirenin saniyeler içinde verdiği gözlemsel değerlendirmeye dayanır. Literatürde **"undertriage"** olarak bilinen — kritik hastaların düşük öncelikli sınıflandırılması — olgusu zamana duyarlı durumlarda ciddi sonuçlar doğurur.

Mevcut çözümler ya pahalı kurumsal hastane sistemleri ya da hastanın kendi doldurduğu self-servis ekranlardır; ön kapıda gerçek zamanlı, görsel tabanlı bir asistan yoktur.

### Vita Porta'nın Yaklaşımı

Görsel ve termal sinyallerin beş bağımsız yapay zekâ ajanı ile birleştirilip ESI triaj protokolüne göre değerlendirildiği, hemşirenin dikkatini doğru hastaya yönlendiren bir destek katmanı.

---

## Nasıl Çalışır?

```
1. Hasta kapıdan girer
   └─ ESP32-CAM ve termal kamera, kapıya monte cihazlar hastayı algılar.

2. Beş ajan paralel analiz yapar
   └─ Yürüyüş, ten rengi, solunum, vücut sıcaklığı ve yüz ifadesi eşzamanlı işlenir.

3. Supervisor sentezler
   └─ ESI triaj protokolüne göre değerlendirme yapılır.

4. Hemşireye öneri iletilir
   └─ Türkçe, gerekçeli ve açıklanabilir bir triaj önerisi sunulur.
```

### Triaj Çıktısı

| Renk | Öncelik |
|---|---|
| 🔴 Kırmızı | Acil |
| 🟡 Sarı | Kısa süre içinde |
| 🟢 Yeşil | Düşük öncelik |

---

## Beş Ajan, Bir Karar Verici

Her ajan tek bir modaliteden sorumludur ve birbirinden bağımsız çalışır.

### 🚶 Yürüyüş Ajanı
**Teknoloji:** MediaPipe Pose
- İskelet noktaları analizi
- Simetri analizi
- Sallanma tespiti
- Adım örüntüsü

### 🎨 Ten Rengi Ajanı
**Teknoloji:** OpenCV (HSV/LAB)
- Renk uzayı analizi
- Solgunluk tespiti
- Anormallik sinyali
- Kalibre eşikler

### 🌬️ Solunum Ajanı
**Teknoloji:** Optical Flow
- Göğüs hareketi takibi
- Frame-fark analizi
- Solunum hızı ölçümü
- Düzenlilik değerlendirmesi

### 🌡️ Vücut Sıcaklığı Ajanı *(Yeni)*
**Teknoloji:** Termal Kamera + Termal Görüntü İşleme (ör. MLX90640 / FLIR Lepton)
- Temas gerektirmeden anlık vücut sıcaklığı ölçümü
- Ateş ve hipotermi tespiti
- Bölgesel sıcaklık dağılımı analizi
- Enfeksiyon ve inflamasyon sinyal tespiti

### 😣 Yüz İfadesi Ajanı *(Yeni)*
**Teknoloji:** MediaPipe Face Mesh + Derin Öğrenme Tabanlı Mimik Analizi
- Ağrı ifadesi tespiti
- Bilinç düzeyi değerlendirmesi (yanıt verirlik, göz hareketi)
- Distres ve anksiyete sinyalleri
- Yüz simetrisi ve kas aktivasyon örüntüleri (ör. felç şüphesi için FAST protokolü uyumu)

---

↓

### 🧠 Supervisor LLM
Beş ajanın çıktısını ve güven skorlarını ESI triaj protokolüyle birleştirip gerekçeli, Türkçe karar üretir.

---

## Neden Çoklu Ajan?

**Çünkü tek bir sinyal yetmez.**

Yürüyüşü düzgün ama cildi solgun ve vücut sıcaklığı yüksek bir hasta — ya da dik duran, solunumu normal ama yüzünde şiddetli ağrı ifadesi olan biri. Bu kombinasyonlar geleneksel kural tabanlı yazılımla çözülemez.

Beş modaliteyi bağımsız değerlendiren ve her ajanın kendi belirsizliğini ifade edebildiği bir orchestration katmanı bu noktada zorunluluk haline gelir.

| Avantaj | Açıklama |
|---|---|
| 🔀 Çoklu modalite | Görsel, hareket ve termal veriler eş zamanlı değerlendirilir |
| ⚖️ Belirsizlik yönetimi | Her ajan kendi güven skorunu supervisor'a bildirir |
| 🔎 Açıklanabilirlik | Karar gerekçesi şeffaftır; hangi ajan neyi gördü görülür |
| 🗣️ Doğal dil çıktısı | Hemşireye Türkçe, akışa uygun özet sunulur |

---

## Teknoloji Yığını

### Donanım
- ESP32-CAM
- Termal Kamera (ör. MLX90640 / FLIR Lepton)
- WS2812 LED halka
- Wi-Fi gateway

### Yapay Zekâ
- LangGraph (multi-agent orchestration)
- MediaPipe Pose & Face Mesh
- OpenCV (HSV/LAB)
- Optical Flow
- Termal görüntü işleme modülü
- LLM API + RAG
- ChromaDB (vektör veritabanı)

### Yazılım
- FastAPI (backend)
- Next.js + Tailwind CSS
- Server-Sent Events
- MQTT (edge → gateway)

> **Model esnekliği:** MVP'de hazır LLM API tüketiyoruz; pilot aşamada lokal açık kaynak modellere veya kendi fine-tune ettiğimiz modellere geçiş mimari düzeyde mümkündür.

---

## Etik Çerçeve

> **Vita Porta tanı koymaz.**

Sistem, hemşirenin yerine geçmez. Sadece dikkati doğru yere yönlendiren bir karar destek asistanıdır. Son söz her zaman triaj hemşiresine aittir.

| İlke | Açıklama |
|---|---|
| 🔍 Şeffaflık | Her karar, hangi ajanın hangi sinyali ürettiği şekilde gerekçelendirilir |
| 👩‍⚕️ İnsan Odaklılık | Hemşire her zaman sistemin önerisini geçersiz kılabilir |
| 🔒 Veri Güvenliği | Hasta verisi yerel ağda işlenir; ham görüntü harici sunucuya iletilmez |
| 📋 Klinik Yol Haritası | CE Sınıf I tıbbi cihaz ve etik kurul onayı süreçleri planlıdır |

---

*Yaşam kapısının bekçisi.*  
**Vita Porta** · Yusuf Şahin · Mert Mirzaoğlu · Mert Korkmaz · CODEX AI Hackathon 2026
