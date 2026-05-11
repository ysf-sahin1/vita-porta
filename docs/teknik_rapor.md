# Vita Porta — Detaylı Teknik Rapor
### Acil Servis Triajı için Multi-Agent Yapay Zekâ Asistanı

**Ekip:** Yusuf Şahin · Mert Mirzaoğlu · Mert Korkmaz  
**Etkinlik:** CODEX AI Hackathon 2026

---

## 1. Özet

Vita Porta, acil servis girişine konumlandırılan, kapıdan giren hastayı görsel, hareket ve termal tabanlı **çoklu modaliteyle 3 saniye içinde** değerlendiren bir karar destek asistanıdır.

Sistem, bağımsız çalışan **beş yapay zekâ ajanının** çıktısını ESI (Emergency Severity Index) triaj protokolüne dayalı bir supervisor ajanla birleştirerek hemşireye gerekçeli ve açıklanabilir bir triaj kategorisi önerisi sunar.

> **Vurgu önemlidir:** Sistem tanı koymaz; hemşirenin dikkatini doğru hastaya yönlendiren bir destek katmanıdır.

---

## 2. Problem Tanımı

Türkiye'de yıllık yaklaşık **130 milyon acil servis başvurusu** gerçekleşmekte; triaj kararı büyük ölçüde yorgun bir hemşirenin saniyeler içinde verdiği subjektif bir değerlendirmeye dayanmaktadır.

Literatürde **undertriage** olarak bilinen — kritik hastaların düşük öncelikli olarak sınıflandırılması — olgusu, zamana duyarlı durumlarda morbiditeyi ve mortaliteyi artırmaktadır.

Mevcut çözümler ya pahalı kurumsal hastane bilgi sistemleri ya da hastanın self-servis doldurduğu sorgu ekranlarıdır; ikisi de ön kapıda gerçek zamanlı ön değerlendirme problemini çözmemektedir.

---

## 3. Sistem Mimarisi

Sistemin omurgası **LangGraph** üzerine kurulmuş bir multi-agent orchestration katmanıdır. Her ajan tek bir modaliteden sorumlu olup birbirinden bağımsız çalışır; böylece bir ajanın belirsizliği diğerlerini etkilemez. Supervisor ajan, alt ajanların çıktılarını ve güven skorlarını birleştirerek nihai kararı oluşturur ve bu kararı ESI protokolüyle harmanlar.

### 3.1 Veri Akışı

```
ESP32-CAM + Termal Kamera (edge)
        │
        │ MQTT (Wi-Fi)
        ▼
  Python Gateway (yerel)
        │
        │ Paralel dağıtım
   ┌────┴─────────────────────────────────┐
   ▼        ▼         ▼        ▼         ▼
Yürüyüş  Ten Rengi  Solunum  Sıcaklık  Yüz İfadesi
 Ajanı    Ajanı     Ajanı    Ajanı     Ajanı
   └────┬─────────────────────────────────┘
        │ Yapılandırılmış JSON + güven skoru
        ▼
   Supervisor LLM (ESI protokolü + RAG)
        │
        │ Server-Sent Events (FastAPI)
        ▼
  Hemşire Dashboard (Next.js)
```

### 3.2 Ajan Katmanı

| Ajan | Modalite | Kullanılan Teknoloji |
|---|---|---|
| Yürüyüş Ajanı | Hareket / poz | MediaPipe Pose; iskelet noktaları, simetri, sallanma |
| Ten Rengi Ajanı | Renk analizi | OpenCV; HSV/LAB renk uzaylarında kalibre eşikleme |
| Solunum Ajanı | Göğüs hareketi | Optical flow ve frame-fark; solunum hızı ve düzeni |
| **Vücut Sıcaklığı Ajanı** *(Yeni)* | Termal görüntü | Termal kamera (MLX90640 / FLIR Lepton); temas gerektirmez |
| **Yüz İfadesi Ajanı** *(Yeni)* | Mimik & ifade analizi | MediaPipe Face Mesh + derin öğrenme tabanlı mimik sınıflandırma |
| Supervisor | Karar sentezi | LLM API + ESI prompt + ChromaDB RAG; Türkçe çıktı |

Her ajan kendi **güven skorunu (0–1)** supervisor'a iletir. Bir ajanın güveni belirli bir eşiğin altındaysa, supervisor bu sinyali ağırlıklandırmada düşürür ve nihai kararda "veri yetersiz" şeffaf bildiriminde bulunabilir.

---

## 4. Yeni Ajanların Teknik Detayları

### 4.1 Vücut Sıcaklığı Ajanı

**Donanım:** MLX90640 veya FLIR Lepton serisi termal kamera; kapı çerçevesine ESP32-CAM ile birlikte monte edilir.

**İşleme Adımları:**
1. Termal frame alınır ve ısı haritasına dönüştürülür.
2. Yüz ve alın bölgesi, pose/yüz verisiyle örtüşerek izole edilir.
3. Bölgesel sıcaklık istatistikleri (ortalama, maksimum) hesaplanır.
4. Kalibre eşiklerle ateş (> 37.5 °C) veya hipotermi (< 35.5 °C) sinyali üretilir.
5. Güven skoru; görüntü kalitesi ve bölge tespiti netliğine göre belirlenir.

**Klinik Önemi:** Ateş pek çok acil tablonun (sepsis, menenjit, hipertermi) erken göstergesidir. Ten rengi ajanıyla birlikte değerlendirildiğinde ek bir doğrulama katmanı sağlar.

### 4.2 Yüz İfadesi Ajanı

**Teknoloji:** MediaPipe Face Mesh (468 yüz noktası) + özel eğitimli mimik sınıflandırıcı.

**İşleme Adımları:**
1. MediaPipe Face Mesh ile 468 yüz landmark noktası çıkarılır.
2. Kaş, göz, ağız ve çene bölgelerinden Action Unit (AU) benzeri özellikler türetilir.
3. Ağrı, distres ve bilinç kaybı örüntüleri için sınıflandırıcı çalıştırılır.
4. Yüz simetrisi analizi yapılır (asimetri → felç şüphesi için FAST protokolüne girdi).
5. Göz açıklığı ve odak takibi ile bilinç düzeyi kaba olarak değerlendirilir.

**Tespit Edilen Sinyaller:**
- Ağrı ifadesi (kaş çatma, göz kısma, ağız bükme)
- Bilinç bulanıklığı (göz yüzeyselliği, yavaş göz hareketi)
- Anksiyete / panik (genişlemiş göz, gerilmiş yüz kasları)
- Yüz simetrisi bozukluğu (felç, TIA şüphesi)

---

## 5. AI Model Stratejisi

### 5.1 Pre-trained Modeller

MVP aşamasında MediaPipe Pose, MediaPipe Face Mesh ve OpenCV tabanlı görsel modüller doğrudan kullanılmaktadır. Termal işleme modülü kalibre eşik tabanlı kural mantığıyla çalışır. Hesaplama yükü gateway tarafında yönetilir; edge cihazlar yalnızca veri toplama görevi üstlenir.

### 5.2 LLM Tüketim Stratejisi

Supervisor ajan, MVP aşamasında hazır bir LLM API'si üzerinden tüketilmektedir. Pilot ve ölçeklenme aşamalarında lokal deployment için açık kaynak alternatifler (Llama, Mistral aileleri) değerlendirilecek; ihtiyaç halinde ESI protokolüne özel fine-tune edilmiş model eğitilebilecektir. Karar mekanizması **model-agnostiktir**; supervisor arayüzü değişmeden farklı LLM backend'leri arasında geçiş mümkündür.

### 5.3 RAG Katmanı

ChromaDB üzerinde küçük ölçekli bir vektör deposu kullanılmaktadır. ESI protokolünün kategori bazlı vaka örüntüleri ve hastanenin (pilot aşamasında) kendi anonim triaj kayıtları indekslenir. Supervisor, karar üretirken benzer geçmiş vakaları referans alarak kararını hastaneye özel akışa adapte eder. Bu yaklaşım, modeli yeniden eğitmeden domain adaptasyonu sağlar.

---

## 6. Dataset Stratejisi

Hackathon süresi (12 gün) içinde anlamlı, etik açıdan onaylı bir tıbbi dataset oluşturmak gerçekçi değildir. Bu nedenle MVP'de pre-trained modeller ve prompt engineering'e odaklanılmıştır.

| Faz | Veri Kaynağı | Etik Süreç |
|---|---|---|
| MVP | Sentetik / kontrollü demo verisi | Gerekli değil |
| Pilot | Pilot hastane, anonim kayıtlar | Yerel etik kurul + KVKK aydınlatma |
| Klinik Validasyon | Çok merkezli, protokollü | IRB onayı + bilimsel yayın |

---

## 7. Donanım Mimarisi

MVP donanımı düşük maliyetli, üretilebilir bileşenlerden oluşur:

| Bileşen | Görev | Tahmini Maliyet |
|---|---|---|
| ESP32-CAM | Görüntü akışı, edge işleme | ~250 ₺ |
| Termal Kamera (MLX90640) | Temas gerektirmez sıcaklık ölçümü | ~600 ₺ |
| WS2812 LED Halka | Triaj durumu görsel göstergesi | ~100 ₺ |
| Wi-Fi Gateway (laptop) | Multi-agent orchestration | Mevcut |
| Muhafaza & Montaj | Kapı çerçevesi montajı | ~150 ₺ |

Pilot aşamasında endüstriyel bir muhafaza, IP67 sertifikalı kamera ve ARM tabanlı kompakt edge bilgisayar (Jetson Nano benzeri) kullanılması planlanmaktadır.

---

## 8. Yazılım Yığını

| Katman | Teknoloji |
|---|---|
| Edge firmware | ESP32 + Arduino/MicroPython, I2S kamera akışı |
| Gateway | Python 3.11, asyncio, MQTT broker (Mosquitto) |
| Orchestration | LangGraph (multi-agent), Pydantic schema |
| Görsel modüller | MediaPipe Pose & Face Mesh, OpenCV, NumPy |
| Termal modül | Termal görüntü işleme, kalibre eşik katmanı |
| LLM erişimi | REST API, async client, prompt template kütüphanesi |
| RAG | ChromaDB, sentence-transformers (embedding) |
| Backend API | FastAPI, Server-Sent Events |
| Frontend | Next.js 14, Tailwind CSS, shadcn/ui, Recharts |
| DevOps | Docker, Git, GitHub Actions (CI) |

---

## 9. Açıklanabilirlik ve Etik

Tıbbi karar destek sistemlerinde "kara kutu" davranışı kabul edilemez. Vita Porta'nın her triaj önerisi, hangi ajanın hangi sinyali ürettiği ve supervisor'ın bunları nasıl ağırlıklandırdığı dahil olmak üzere tamamen şeffaf biçimde sunulur.

Hemşire dashboard'unda:
- Her ajan kendi gözleminin metinsel özetini sunar.
- Supervisor kararını gerekçelendiren bir cümle üretir.
- Güven skoru görsel olarak gösterilir.
- Hemşire her zaman öneriyi **geçersiz kılabilir**; sistem onun aracıdır, otoritesi değil.

Sistem hiçbir zaman tanı cümlesi kurmaz; çıktı yalnızca triaj kategorisi (yeşil / sarı / kırmızı) ve gerekçedir. Klinik kullanımdan önce **CE Sınıf I tıbbi cihaz** statüsü ve ilgili etik kurul onayları hedeflenmektedir.

---

## 10. Bilinen Kısıtlar ve Riskler

| Risk | Azaltma Stratejisi |
|---|---|
| Kalabalıkta yanlış tetikleme | Kapı çerçevesi tek-hasta optik tasarımı; pose tracking ile özne izolasyonu |
| Düşük ışıkta renk analizi | Standart kapı altı ışıklandırması; kalibrasyon protokolü |
| Termal kamerada çevre sıcaklığı etkisi | Ortam sıcaklığı referans kalibrasyonu; delta-T tabanlı ölçüm |
| Yüz ifadesi çeşitliliği (kültürel fark) | Çeşitli demografik veriyle pilot validasyonu; düşük güvende "veri yetersiz" bildirimi |
| Yanlış pozitif (overtriage) | Supervisor güven eşikleri; hemşire her zaman nihai karar mercii |
| LLM API kesintisi | Kural tabanlı yedek karar mantığı; lokal model fallback |
| KVKK uyumluluğu | Veri yerel ağda işlenir; harici sunucuya ham görüntü gönderilmez |

---

## 11. Sonuç

Vita Porta, mevcut LLM ve görsel AI teknolojilerini ESI gibi yerleşik klinik protokollerle birleştirerek acil servis girişinde uygulanabilir, açıklanabilir ve düşük maliyetli bir karar destek katmanı sunar.

Beş modaliteli ajan mimarisi — yürüyüş, ten rengi, solunum, vücut sıcaklığı ve yüz ifadesi — tekil sinyal tabanlı sistemlerin kaçıracağı klinik kombinasyonları yakalamayı mümkün kılar. Sistem teknolojik açıdan mevcut araçlarla ulaşılabilir, operasyonel açıdan hemşire iş akışına entegre edilebilir ve etik açıdan "asistan" rolünden ayrılmayacak şekilde tasarlanmıştır.

CODEX AI Hackathon 2026 kapsamında üretilen PoC, bu vizyonun ilk somut adımıdır.

---

*Yaşam kapısının bekçisi.*  
**Vita Porta** · Yusuf Şahin · Mert Mirzaoğlu · Mert Korkmaz · CODEX AI Hackathon 2026
