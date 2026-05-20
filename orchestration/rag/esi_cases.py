"""Seed ESI case patterns for the RAG layer.

456 canonical ESI patterns covering red (137), yellow (108) and green (211)
categories. Signals limited to the three active visual agents:
yürüyüş (gait), termal (thermal) and yüz ifadesi (expression).
"""

from __future__ import annotations

ESI_SEED_CASES: list[dict[str, str]] = [
    # ────────────────────────────────────────────────────────── RED (137)
    {
        "id": "esi-red-cardiac-arrest-floor",
        "category": "red",
        "pattern": "Yürüyüş: Yere yığılmış, hareketsiz. Yüz: Tamamen yanıtsız, gözler kapalı. Termal: Hızla düşen genel vücut ısısı (<35°C). -> Kardiyak arrest veya derin şok şüphesi. ESI 1.",
    },
    {
        "id": "esi-red-airway-obstruction",
        "category": "red",
        "pattern": "Yürüyüş: Desteksiz ayakta duramıyor, sendeliyor. Yüz: Şiddetli korku ve panik ifadesi, ağız açık. Termal: 36.5°C. -> Akut hava yolu tıkanıklığı / Asfiksi. ESI 1.",
    },
    {
        "id": "esi-red-active-seizure-status",
        "category": "red",
        "pattern": "Yürüyüş: Yerde ritmik, istemsiz şiddetli kasılmalar (çırpınma). Yüz: Çenesi kilitli, tepkisiz. Termal: 38.5°C (Kas aktivitesine bağlı artış). -> Aktif Jeneralize Nöbet / Status Epileptikus. ESI 1.",
    },
    {
        "id": "esi-red-acute-stroke-hemiplegia",
        "category": "red",
        "pattern": "Yürüyüş: Tek bacak sürükleniyor, asimetrik yığılma. Yüz: Tek taraflı belirgin sarkma, şaşkın/boş bakış. Termal: 36.8°C. -> Akut İnme (Felç). ESI 1.",
    },
    {
        "id": "esi-red-stemi-collapse",
        "category": "red",
        "pattern": "Yürüyüş: İki büklüm, göğsünü tutarak yere çökme. Yüz: Maksimum ağrı grimesi, dişler sıkılı. Termal: Baş/boyun bölgesinde ani soğuma. -> Akut Koroner Sendrom / STEMI. ESI 1.",
    },
    {
        "id": "esi-red-severe-respiratory-failure",
        "category": "red",
        "pattern": "Yürüyüş: Öne eğik, elleri dizlerinde destekli (Tripod pozisyonu), adım atamıyor. Yüz: Aşırı endişeli, burun delikleri açılıp kapanıyor. Termal: 37.2°C. -> Şiddetli Solunum Yetmezliği. ESI 1.",
    },
    {
        "id": "esi-red-septic-shock-hyperthermia",
        "category": "red",
        "pattern": "Yürüyüş: Sedyede/Tekerlekli sandalyede tamamen pelte gibi. Yüz: Donuk, letarjik, göz kapakları yarı açık. Termal: 40.5°C (Aşırı yüksek ateş). -> Sepsis / Septik Şok. ESI 1.",
    },
    {
        "id": "esi-red-acute-psychosis-toxidrome",
        "category": "red",
        "pattern": "Yürüyüş: Ajite, odada koordinasyonsuz volta atma, nesnelere çarpma. Yüz: Agresif, halüsinatif odaklanma. Termal: 39.0°C. -> Akut Psikoz / Toksidrom (Amfetamin vb.). ESI 2.",
    },
    {
        "id": "esi-red-deep-hypothermia-coma",
        "category": "red",
        "pattern": "Yürüyüş: Sırtüstü hareketsiz yatar pozisyon. Yüz: Ağrıya dahi mimik vermiyor (GKS çok düşük). Termal: 34.0°C (Derin Hipotermi). -> Çevresel Hipotermi / Koma. ESI 1.",
    },
    {
        "id": "esi-red-aspiration-anaphylaxis-edema",
        "category": "red",
        "pattern": "Yürüyüş: Boynunu elleriyle sarmış, adımlar donuk. Yüz: Gözler dışarı fırlamış gibi, belirgin boğulma paniği. Termal: 36.5°C. -> Yabancı Cisim Aspirasyonu / Anafilaksi ödemi. ESI 1.",
    },
    {
        "id": "esi-red-major-pelvic-femur-trauma",
        "category": "red",
        "pattern": "Yürüyüş: Yığılmış, pelvik/bacak bölgesinde belirgin anatomik bozukluk. Yüz: Şoka bağlı donukluk, terleme çizgileri. Termal: Ekstremitelerde ciddi ısı kaybı. -> Majör Pelvis/Femur Travması (İç kanama). ESI 1.",
    },
    {
        "id": "esi-red-meningitis-subarachnoid",
        "category": "red",
        "pattern": "Yürüyüş: Başını elleri arasına almış, yere çökmüş. Yüz: Işığa karşı gözlerini tamamen kısmış, aşırı acı. Termal: 39.8°C. -> Akut Menenjit / Subaraknoid Kanama. ESI 2.",
    },
    {
        "id": "esi-red-hypoglycemic-coma",
        "category": "red",
        "pattern": "Yürüyüş: Koordinasyon tamamen kayıp, sarhoş gibi yalpalanma, düşme. Yüz: Gözler kaymış, konfüze. Termal: 35.5°C. -> Hipoglisemik Koma başlangıcı. ESI 1.",
    },
    {
        "id": "esi-red-aortic-dissection-rupture",
        "category": "red",
        "pattern": "Yürüyüş: Sırtını dik tutamıyor, karın bölgesine sarılmış kilitli postür. Yüz: Kesik kesik grimase, gözler fal taşı gibi. Termal: Karın bölgesinde geniş asimetrik ısı (iç kanama/rüptür bulgusu). -> Aort Diseksiyonu / Rüptür. ESI 1.",
    },
    {
        "id": "esi-red-neonatal-sepsis-lethargy",
        "category": "red",
        "pattern": "Yürüyüş: Yerde hareketsiz yatan çocuk/bebek. Yüz: Tamamen gevşemiş, emme/ağlama mimiği yok. Termal: 38.8°C veya 35.0°C. -> Yenidoğan Sepsisi / Letarji. ESI 1.",
    },
    {
        "id": "esi-red-cervical-trauma-severe",
        "category": "red",
        "pattern": "Yürüyüş: Boyun kas kaskatı, sağa sola dönemiyor. Yüz: Korkunç bir ağrı ifadesi, çene kitlenmiş. Termal: Yüzeyde normal. -> Ciddi Servikal (Boyun) Travması. ESI 1.",
    },
    {
        "id": "esi-red-pediatric-febrile-seizure",
        "category": "red",
        "pattern": "Yürüyüş: Bebek annenin kucağında pelte gibi, boyun düşmüş. Yüz: Sabit bir noktaya boş bakış (fiksasyon). Termal: 39.5°C. -> Pediatrik Febril Konvülsiyon / Sepsis. ESI 1.",
    },
    {
        "id": "esi-red-major-fracture-vagal-shock",
        "category": "red",
        "pattern": "Yürüyüş: Kolunu dirsekten kavramış, ekstremitede ciddi açılanma (kırık). Yüz: Rengi solmuş (termal kamerada yüzde ani soğuma), senkop öncesi boşluk. -> Açık/Majör Kırık kaynaklı Vagal Şok. ESI 2.",
    },
    {
        "id": "esi-red-anticholinergic-toxidrome",
        "category": "red",
        "pattern": "Yürüyüş: Ayakta zikzak çiziyor, kollarını anlamsızca havaya kaldırıyor. Yüz: İfadesiz, göz bebekleri kocaman açılmış. Termal: 40.0°C. -> İlaç Zehirlenmesi (Antikolinerjik Sendrom/Serotonin Sendromu). ESI 2.",
    },
    {
        "id": "esi-red-cardiac-syncope-arrhythmia",
        "category": "red",
        "pattern": "Yürüyüş: Adım atarken aniden donup kalma, ardından yere yığılma. Yüz: Gözler geriye dönmüş. Termal: Ani değişim yok. -> Kardiyak Senkop / Aritmi. ESI 1.",
    },
    {
        "id": "esi-red-ectopic-pregnancy-rupture",
        "category": "red",
        "pattern": "Yürüyüş: Karın bölgesini koruyarak cenin pozisyonunda yatma. Yüz: Çığlık atar gibi açık ağız ama sessiz. Termal: 36.5°C. -> Akut Ektopik Gebelik Rüptürü (İç kanama). ESI 1.",
    },
    {
        "id": "esi-red-malignant-hyperthermia",
        "category": "red",
        "pattern": "Yürüyüş: Hareketsiz, vücut tamamen kaskatı (rijidite). Yüz: Donuk, çene kilitli, diş gıcırdatma. Termal: 41.0°C. -> Malign Hipertermi / Nöroleptik Malign Sendrom. ESI 1.",
    },
    {
        "id": "esi-red-major-burn-extensive",
        "category": "red",
        "pattern": "Yürüyüş: Sedyede getirilmiş, ekstremitelerde yanık postürü (fleksiyonda kilitli). Yüz: Ağrı eşiği aşılmış, tepkisiz. Termal: Vücut yüzeyinin %50'sinde aşırı yüksek ısı paterni. -> Majör Yanık. ESI 1.",
    },
    {
        "id": "esi-red-tension-pneumothorax",
        "category": "red",
        "pattern": "Yürüyüş: Göğsüne darbe almış gibi nefes almaya çalışarak bükülme. Yüz: Ağız sonuna kadar açık, oksijen açlığı paniği. Termal: Yüz bölgesinde soğuma. -> Tansiyon Pnömotoraks. ESI 1.",
    },
    {
        "id": "esi-red-massive-gi-bleed",
        "category": "red",
        "pattern": "Yürüyüş: İki büklüm, sürekli öğürme hareketiyle kasılma. Yüz: Gözler sulanmış, aşırı distres. Termal: Yüzde ve karında homojen 37.0°C. -> Aktif Masif GİS Kanaması / Hematemez (Tahmin). ESI 1.",
    },
    {
        "id": "esi-red-intracranial-hemorrhage",
        "category": "red",
        "pattern": "Yürüyüş: Desteksiz yürüyemiyor, gövde tek tarafa eğik. Yüz: Şiddetli baş ağrısı mimiği, gözünü tek taraflı kapatma. Termal: 36.6°C. -> Akut Kafa İçi Kanaması. ESI 2.",
    },
    {
        "id": "esi-red-tetanus-opisthotonus",
        "category": "red",
        "pattern": "Yürüyüş: Boyun geride, sırt kavisli (opistotonus pozisyonu). Yüz: Kasılmış, dişler kilitli. Termal: 37.5°C. -> Tetanoz / Menenjit irritasyonu. ESI 1.",
    },
    {
        "id": "esi-red-myasthenic-crisis",
        "category": "red",
        "pattern": "Yürüyüş: Yavaş, kas gücü tamamen tükenmiş, adım atarken dizleri bükülüyor. Yüz: Tam bir çaresizlik ve pitoz (göz kapakları düşmüş). Termal: 36.5°C. -> Miyastenik Kriz / Nöromüsküler Solunum Yetmezliği. ESI 2.",
    },
    {
        "id": "esi-red-necrotizing-fasciitis",
        "category": "red",
        "pattern": "Yürüyüş: Hareketsiz yatış, kol veya bacakta belirgin asimetrik şişlik. Yüz: Ağrı uyarısına inleme mimiği. Termal: Şiş olan ekstremitede aşırı termal parlama (>39°C lokal). -> Nekrotizan Fasiit / Kompartman Sendromu. ESI 2.",
    },
    {
        "id": "esi-red-acute-epiglottitis",
        "category": "red",
        "pattern": "Yürüyüş: Boğazını tutarak debelenme, dik duramama. Yüz: Gözler yuvalarından fırlamış, ağızda yutkunma çabası. Termal: 38.5°C. -> Akut Epiglottit. ESI 1.",
    },
    {
        "id": "esi-red-massive-pe-opiate-od",
        "category": "red",
        "pattern": "Yürüyüş: Yerde hareketsiz. Yüz: Yarım açık gözler, pupiller sabit (görsel olarak donuk). Termal: Burun ve dudak çevresinde belirgin hipotermi. -> Masif Pulmoner Emboli / Opiyat Doz Aşımı. ESI 1.",
    },
    {
        "id": "esi-red-eclampsia-preictal",
        "category": "red",
        "pattern": "Yürüyüş: Gebeliği belirgin (karnı büyük) hasta, bacakları titreyerek yere çöküyor. Yüz: Gözlerde kayma, yüz kaslarında seğirme. Termal: 37.0°C. -> Eklampsi Nöbeti Öncesi/Anı. ESI 1.",
    },
    {
        "id": "esi-red-penetrating-thorax-trauma",
        "category": "red",
        "pattern": "Yürüyüş: Göğsüne sert bir obje saplanmış gibi koruyucu postür. Yüz: Şok tablosu, gözlerde odak kaybı. Termal: Göğüs bölgesinde sıvı yayılımına bağlı termal leke (kanama). -> Penetran Toraks Travması. ESI 1.",
    },
    {
        "id": "esi-red-pediatric-shock-dehydration",
        "category": "red",
        "pattern": "Yürüyüş: Sedyede getirilen bebek, postür kurbağa bacağı gibi gevşek. Yüz: Yüz kasları sarkık, tepkisiz. Termal: 35.8°C (Hipotermik). -> Pediatrik Şok / İleri Dehidratasyon Komplikasyonu. ESI 1.",
    },
    {
        "id": "esi-red-sympathomimetic-poisoning",
        "category": "red",
        "pattern": "Yürüyüş: Hızlı ve düzensiz ajite adımlar, etrafa vurma eylemi. Yüz: Aşırı gergin ve agresif ifade, terleme belirgin. Termal: 39.5°C. -> Sempatomimetik Zehirlenme (Kokain/Meth). ESI 2.",
    },
    {
        "id": "esi-red-hemorrhagic-stroke-massive",
        "category": "red",
        "pattern": "Yürüyüş: Yığılmış yatıyor, vücudun tek tarafı kaskatı, diğer tarafı gevşek. Yüz: Çarpılmış ifade. Termal: Baş bölgesinde lokal ısı artışı. -> Masif Hemorajik İnme. ESI 1.",
    },
    {
        "id": "esi-red-organophosphate-poisoning",
        "category": "red",
        "pattern": "Yürüyüş: İki büklüm, kramplar nedeniyle zıplar tarzda hareketler. Yüz: Ağız kenarında sürekli tükürük birikimi (yutkunamama mimiği), şaşkınlık. Termal: 36.5°C. -> Organofosfat Zehirlenmesi. ESI 2.",
    },
    {
        "id": "esi-red-deep-neck-infection-ludwig",
        "category": "red",
        "pattern": "Yürüyüş: Boyun bölgesinde devasa asimetrik şişlik (hava yolu basısı postürü), baş geride. Yüz: Ağzı zorlukla açıyor, panik. Termal: Boyun bölgesinde yüksek termal aktivite (>39°C). -> Derin Boyun Enfeksiyonu / Ludwig Anjini. ESI 2.",
    },
    {
        "id": "esi-red-acute-pe-ambulating",
        "category": "red",
        "pattern": "Yürüyüş: Eller göğüste, adım attıkça yüzünü buruşturarak duraksama. Yüz: Derin nefes alamama paniği, dudaklar büzük. Termal: Normal (36.8°C). -> Akut Pulmoner Emboli Şüphesi. ESI 2.",
    },
    {
        "id": "esi-red-toxic-coma-encephalitis",
        "category": "red",
        "pattern": "Yürüyüş: Yerde sürükleniyor. Yüz: Gözler kapalı, ancak ağrılı uyarana sadece yüzünü buruşturuyor (GKS 8 civarı). Termal: 38.5°C. -> Toksik Koma / Ensefalit. ESI 1.",
    },
    {
        "id": "esi-red-penetrating-abdominal-trauma",
        "category": "red",
        "pattern": "Yürüyüş: Karnına saplanmış bir obje ile destekli yürüme. Yüz: Gözler fal taşı gibi, şok evresi sessizliği. Termal: Batın bölgesinde geniş soğuma paterni (kanama/şok). -> Penetran Batın Travması. ESI 1.",
    },
    {
        "id": "esi-red-myxedema-coma",
        "category": "red",
        "pattern": "Yürüyüş: Yaşlı hasta, bir sandalyeye yığılmış, omuzlar tamamen düşük. Yüz: Mandibula (çene) sarkmış, gözler boşluğa bakıyor. Termal: 34.5°C. -> Miksödem Koması / Şiddetli Sepsis. ESI 1.",
    },
    {
        "id": "esi-red-intussusception-pediatric",
        "category": "red",
        "pattern": "Yürüyüş: Bebek, kucakta taşınıyor, ara ara tüm vücuduyla içe doğru katlanma (kramp). Yüz: Ağlama mimiği var ama çok zayıf/letarjik. Termal: 37.0°C. -> İntussusepsiyon (Geç dönem). ESI 2.",
    },
    {
        "id": "esi-red-open-skull-fracture-tbi",
        "category": "red",
        "pattern": "Yürüyüş: Sırt üstü hareketsiz, ekstremitelerde tuhaf dışa/içe dönüklük. Yüz: Kafa tası asimetrisi görseli, kanamaya bağlı termal iz, koma mimiği. -> Açık Kafatası Kırığı / Şiddetli TBI. ESI 1.",
    },
    {
        "id": "esi-red-ruptured-aaa",
        "category": "red",
        "pattern": "Yürüyüş: Elleriyle duvarlara tutunarak ilerleme çabası, aniden diz üstü çökme. Yüz: Sırta vuran ağrıyı simgeleyen başı geriye atma, diş sıkma. Termal: 36.5°C. -> Rüptüre AAA (Abdominal Aort Anevrizması). ESI 1.",
    },
    {
        "id": "esi-red-meningococcemia-pediatric",
        "category": "red",
        "pattern": "Yürüyüş: Çocuğun tüm vücudunda kırmızı/mor lekeler, kucakta gevşek postür. Yüz: Tamamen ifadesiz, gözler yarı açık. Termal: 40.0°C. -> Meningokoksemi. ESI 1.",
    },
    {
        "id": "esi-red-acute-heart-failure-edema",
        "category": "red",
        "pattern": "Yürüyüş: Sedyede yatarken bile kollarla göğsü destekleme çabası (ortopne pozisyonu). Yüz: Boğulma hissi, aşırı panik. Termal: Yüzde belirgin soğuma. -> Akut Kalp Yetmezliği / Akciğer Ödemi. ESI 1.",
    },
    {
        "id": "esi-red-femoral-artery-bleeding",
        "category": "red",
        "pattern": "Yürüyüş: Hareketsiz yatış, pelviste açık yara görseli. Yüz: Bilinç bulanık, mimik yok. Termal: Kasık bölgesinde masif ısı kaybı ve etrafa yayılan termal sıvı (kan) paterni. -> Femoral Arter Kanaması. ESI 1.",
    },
    {
        "id": "esi-red-electrocution-tetanus",
        "category": "red",
        "pattern": "Yürüyüş: Adım atarken vücut bir anda tahta gibi geriye kasılıyor. Yüz: Çığlık atacakmış gibi ama kilitli. Termal: 37.5°C. -> Elektrik Çarpması (Kardiyak/Nörolojik hasar) veya Tetanoz. ESI 1.",
    },
    {
        "id": "esi-red-gait-collapse",
        "category": "red",
        "pattern": "Sallantılı veya destekli yürüyüş + ayakta duramama hayati tehlike işaretidir. ESI Seviye 1-2 kapsamında acil müdahale gerekir.",
    },
    {
        "id": "esi-red-chest-pain",
        "category": "red",
        "pattern": "Göğüs ağrısı + terleme + dengesiz yürüyüş kombinasyonu kardiyak acil işaretidir. ESI Seviye 1-2 kapsamında acil müdahale gerekir.",
    },
    {
        "id": "esi-red-stroke",
        "category": "red",
        "pattern": "Yüz asimetrisi (sarkma, eğrilik) + denge kaybı + sürüklenerek yürüme akut inme belirtisidir. ESI Seviye 1 kapsamında acil nörolojik değerlendirme gerekir.",
    },
    {
        "id": "esi-red-anaphylaxis",
        "category": "red",
        "pattern": "Ani gelişen yüz/boyun ödemi + yüz ifadesinde belirgin distres + döküntü anafilaksi işaretidir. ESI Seviye 1, epinefrin uygulanmalı.",
    },
    {
        "id": "esi-red-trauma",
        "category": "red",
        "pattern": "Yüksek enerjili travma + yüz ifadesinde bilinç değişikliği/donukluk + yürüyememe veya desteksiz duramama. ESI Seviye 1-2 acil müdahale.",
    },
    {
        "id": "esi-red-sepsis",
        "category": "red",
        "pattern": "Yüksek ateş (>39°C) + yüz ifadesinde konfüzyon/donukluk + postürde çöküş eğilimi sepsis tablosunu düşündürür. ESI Seviye 1-2, acil değerlendirme.",
    },
    {
        "id": "esi-red-hyperthermia-collapse",
        "category": "red",
        "pattern": "Yüksek ateş (>39°C) + postur çöküşü + yüz ifadesinde ağrı/bilinç bulanıklığı sepsis veya ısı çarpması işareti olabilir. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-hypothermia",
        "category": "red",
        "pattern": "Hipotermi (<35°C) + düşük postür + yüz ifadesinde yanıtsızlık hipotermi şoku riskidir. Isınma protokolü ve acil değerlendirme gerekir.",
    },
    {
        "id": "esi-red-unresponsive",
        "category": "red",
        "pattern": "Bilince yanıtsız veya minimal yanıtlı hasta; yüz ifadesi donuk, postür çökmüş. Resüsitasyon protokolü. ESI Seviye 1.",
    },
    {
        "id": "esi-red-facial-asymmetry-fast",
        "category": "red",
        "pattern": "Yüz asimetrisi (FAST protokolü) + denge kaybı + yürüyüşte sürükleme akut inme protokolünü tetikler. ESI Seviye 1; görüntüleme acil.",
    },
    {
        "id": "esi-red-severe-pain-collapse",
        "category": "red",
        "pattern": "Yüz ifadesinde maksimum ağrı skoru + dizleri üzerine çöküş + yürüyememe durumu iç organ hasarı veya kardiyak acil işareti. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-heat-stroke",
        "category": "red",
        "pattern": "Vücut ısısı >40°C + bilinç bulanıklığı + koordinasyonsuz yürüyüş ısı çarpması tanısını destekler. ESI Seviye 1, aktif soğutma başlat.",
    },
    {
        "id": "esi-red-diabetic-emergency",
        "category": "red",
        "pattern": "Yüz ifadesinde konfüzyon + sallantılı denge + anormal terleme hipoglisemi veya hiperglisemik kriz düşündürür. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-seizure-postictal",
        "category": "red",
        "pattern": "Nöbet sonrası postiktal dönem: yüz gevşemiş, göz kapakları yarı kapalı, yürüyüş yok veya koordinasyonsuz. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-overdose",
        "category": "red",
        "pattern": "Aşırı ilaç alımı şüphesi: bilinç deprese, yüz ifadesi yanıtsız, ayakta duramıyor veya düşme riski. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-meningitis",
        "category": "red",
        "pattern": "Yüksek ateş (>39°C) + yüzde şiddetli ağrı grimesi + baş öne eğik gergin postür menenjit şüphesini güçlendirir. ESI Seviye 1-2, izolasyon.",
    },
    {
        "id": "esi-red-pulmonary-embolism",
        "category": "red",
        "pattern": "Ani başlayan göğüs ağrısı yüz ifadesine yansımış + yürüyüşte belirgin halsizlik pulmoner emboli riski taşır. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-aortic-dissection",
        "category": "red",
        "pattern": "Yırtılır nitelikte sırt/göğüs ağrısı yüzüne yansımış + yürüyüşte çökme eğilimi aort diseksiyonu açısından değerlendirilmeli. ESI Seviye 1.",
    },
    {
        "id": "esi-red-burn-major",
        "category": "red",
        "pattern": "Geniş yanık alanı + yüzde ağrı grimesi + postür bozukluğu majör yanık protokolü gerektirir. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-pediatric-fever",
        "category": "red",
        "pattern": "Çocuk hastada ateş >39°C + donuk yüz ifadesi + sarkık postür sepsis açısından acil değerlendirilmeli. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-spinal-injury",
        "category": "red",
        "pattern": "Yüksek enerjili düşme + yürüyememe + yüzde ağrı/korku ifadesi spinal yaralanma şüphesi; hareketsizleştir. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-crush-injury",
        "category": "red",
        "pattern": "Ezilme travması + yürüyüş yok + yüzde şiddetli ağrı ifadesi kompartman sendromu ve rabdomiyoliz riski. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-cardiac-arrest-pre",
        "category": "red",
        "pattern": "Göğsünü tutan hasta + bacaklarının tutmaması + gözlerin kapanmaya başlaması kardiyak arrest öncesi tablo. ESI Seviye 1.",
    },
    {
        "id": "esi-red-toxic-ingestion",
        "category": "red",
        "pattern": "Kimyasal maruziyet şüphesi + yüzde ağrı/distres + koordinasyon kaybı toksik maruziyet acili. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-high-fever-elderly",
        "category": "red",
        "pattern": "Yaşlı hastada ateş >38.5°C + yavaş ve desteksiz yürüyüş + yüz ifadesinde konfüzyon; atipik sepsis tablosu. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-drowning",
        "category": "red",
        "pattern": "Boğulma sonrası: düşük vücut ısısı + bilinç deprese + yüz ifadesi yanıtsız. Resüsitasyon ve ısınma protokolü. ESI Seviye 1.",
    },
    {
        "id": "esi-red-electrocution",
        "category": "red",
        "pattern": "Elektrik çarpması + yere düşmüş postür + yüzde yanık izi veya yanıtsızlık. ESI Seviye 1, kardiyak monitorizasyon.",
    },
    {
        "id": "esi-red-abdominal-rupture",
        "category": "red",
        "pattern": "Karın bölgesinde şiddetli ağrı yüze yansımış + öne eğilmiş postür + yürüyememe iç organ rüptürü düşündürür. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-acute-psychosis-danger",
        "category": "red",
        "pattern": "Akut psikoz: çok ajite yüz ifadesi + koordinasyonsuz hızlı hareket + kendine veya çevreye zarar riski. ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-penetrating-trauma",
        "category": "red",
        "pattern": "Delici alet yaralanması + yürüme güçlüğü + yüzde şok ifadesi penetran travma protokolü. ESI Seviye 1.",
    },
    {
        "id": "esi-red-anaphylaxis-angioedema-visible",
        "category": "red",
        "pattern": "Yüzde belirgin ödem ve şişlik (termal kamerada asimetrik ısı dağılımı) + dik duramayan postür + yüzde panik ve distress ifadesi. Anafilaksi/anjiyoödem; ESI Seviye 1, adrenalin acil.",
    },
    {
        "id": "esi-red-heat-stroke-hyperthermia-collapse",
        "category": "red",
        "pattern": "Termal kamerada tüm vücut yüzey sıcaklığı kritik yüksek (>40°C) + zemine çökmüş ya da tam destek gerektiren postür + yüzde yanıt azalmış donuk ifade. Isı çarpması; ESI Seviye 1, acil soğutma.",
    },
    {
        "id": "esi-red-severe-hypothermia-unresponsive",
        "category": "red",
        "pattern": "Termal kamerada vücut yüzey sıcaklığı <32°C + zemine yakın çökmüş veya desteksiz duramayan postür + yüzde tamamen ifadesiz donuk görünüm. Ağır hipotermi; ESI Seviye 1, ısınma protokolü acil.",
    },
    {
        "id": "esi-red-acute-dystonia-opisthotonus-visible",
        "category": "red",
        "pattern": "Belirgin anormal postür: gövde geriye kavislenmiş, boyun ekstansiyonda (termal görüntüde kas gruplarında ısı artışı) + yüzde aşırı kasılma ve ağrı ifadesi. Akut distoni/opistotonus; ESI Seviye 1-2.",
    },
    {
        "id": "esi-red-trauma-floor-unresponsive",
        "category": "red",
        "pattern": "Zemine düşmüş, kendi kendine hareket edemeyen postür + yüzde yanıtsız veya minimal yanıtlı ifade + termal kamerada alın bölgesinde ısı artışı (kafa travması). ESI Seviye 1, resüsitasyon odası.",
    },
    {
        "id": "esi-red-severe-agitation-toxic-posture",
        "category": "red",
        "pattern": "Aşırı ajite, kontrolsüz hareketler, düşme riski yüksek dengesiz postür + yüzde korku/panik/saldırgan ifade + termal kamerada yüksek yüzey sıcaklığı. Toksik ajitasyon; ESI Seviye 1-2, fiziksel kontrol gerekebilir.",
    },
    {
        "id": "esi-red-pediatric-febrile-collapse-thermal",
        "category": "red",
        "pattern": "Çocuk hasta: termal kamerada yüksek alın sıcaklığı (>39°C) + postür çöküşü (tutularak taşınıyor) + yüzde bilinç azalmış letarjik ifade. Febril kollaps; ESI Seviye 1-2, pediatri acil.",
    },
    {
        "id": "esi-red-complete-gait-failure-neurologic",
        "category": "red",
        "pattern": "Yürüyüş tamamen kayıp: zemine çökmüş, ayağa kalkamıyor + yüzde konfüzyon ve ağrı karışımı ifade + termal kamerada normal sıcaklık (nörolojik acil). ESI Seviye 1-2; görüntüleme acil.",
    },
    {
        "id": "esi-red-burn-extensive-thermal-visible",
        "category": "red",
        "pattern": "Termal kamerada geniş vücut yüzeyinde aşırı yüksek lokal ısı (yanık alanı) + desteksiz duramayan postür + yüzde aşırı ağrı ifadesi (grimase). Geniş yanık; ESI Seviye 1, yanık protokolü.",
    },
    {
        "id": "esi-red-acute-vertigo-fall-zemin",
        "category": "red",
        "pattern": "Ani denge kaybı: zemine çökmüş veya duvara yaslanmış sabit postür + yüzde aşırı distress, gözler kapalı veya yarı açık ifade + termal normal. Ağır akut vertigo/düşme; ESI Seviye 2.",
    },
    {
        "id": "esi-red-infant-choking",
        "category": "red",
        "pattern": "Yürüyüş: Ailesi tarafından kucakta koşarak getirilen, kollar ve bacaklar tamamen sarkık bebek. Yüz: Ağzı açık ama sessiz, gözler kaymış. Termal: Yüz çevresinde hızla düşen ısı (siyanoz/hipoksi bulgusu). -> Asfiksi / Yabancı Cisim Aspirasyonu. ESI 1.",
    },
    {
        "id": "esi-red-massive-hemoptysis-active",
        "category": "red",
        "pattern": "Yürüyüş: İki büklüm, sürekli öne doğru şiddetli öğürme/öksürme ile yığılma. Yüz: Ağızdan sürekli sıvı (kan) boşalıyor, panik ve boğulma mimiği. Termal: Yüzde panik terlemesine bağlı soğuma, ağız çevresinde taze kanın 37°C'lik sıcak yayılımı. -> Masif Hemoptizi. ESI 1.",
    },
    {
        "id": "esi-red-spinal-cord-transection",
        "category": "red",
        "pattern": "Yürüyüş: Travma tahtasında getiriliyor, boyundan aşağısı tamamen hareketsiz ve gevşek. Yüz: Gözler açık, korku dolu, sadece başını çevirebiliyor. Termal: Boyun seviyesinin altında (gövde ve bacaklarda) vazodilatasyona bağlı anormal homojen ısı artışı (Nörojenik Şok). -> Servikal Spinal Kord Hasarı. ESI 1.",
    },
    {
        "id": "esi-red-crushed-pelvis",
        "category": "red",
        "pattern": "Yürüyüş: Sedyede, pelvis bölgesi tamamen yassılaşmış/asimetrik. Yüz: Bilinç kapalı, acıya dahi tepkisiz. Termal: Karın altı ve bacaklarda devasa ısı kaybı (masif iç kanama). -> Ezilme Travması / Pelvis Kırığı. ESI 1.",
    },
    {
        "id": "esi-red-severe-asthma-exhaustion",
        "category": "red",
        "pattern": "Yürüyüş: Tekerlekli sandalyede öne yığılmış, göğüs kafesi aşırı inip kalkıyor ama adımlar tamamen durmuş. Yüz: Gözler yarı kapalı, dudaklar büzük (pursed-lip), tükenmişlik ifadesi. Termal: 36.5°C. -> Solunum Yetmezliği / Astım Tükenme Evresi. ESI 1.",
    },
    {
        "id": "esi-red-neck-laceration-arterial",
        "category": "red",
        "pattern": "Yürüyüş: Boynuna eliyle şiddetle bastırarak ve sendeleyerek koşma, aniden diz çökme. Yüz: Şok, göz bebekleri genişlemiş. Termal: Boyun ve göğse doğru yayılan yoğun, sıcak (37.5°C) sıvı döküntüsü paterni, elde ve kolda hızla soğuma. -> Arteriyel Boyun Kanaması. ESI 1.",
    },
    {
        "id": "esi-red-hypothermic-cardiac-arrest",
        "category": "red",
        "pattern": "Yürüyüş: Sedye ile taşınan tamamen kaskatı, donmuş postür. Yüz: Gözler ve çene yarı açık, kilitli. Termal: Gövde ve ekstremitelerde 30°C'nin altında derin soğuma. -> Derin Hipotermi / Arrest. ESI 1.",
    },
    {
        "id": "esi-red-eclampsia-active-seizure",
        "category": "red",
        "pattern": "Yürüyüş: Gebe karnı belirgin hasta sedyede, tüm vücutta ritmik ve şiddetli sıçrama (tonik-klonik). Yüz: Çene kilitli, ağız kenarında köpürme (sıvı çıkışı), gözler yukarı devrilmiş. Termal: 37.8°C (Kasılma ısısı). -> Eklampsi Nöbeti. ESI 1.",
    },
    {
        "id": "esi-red-tension-pneumo-traumatic",
        "category": "red",
        "pattern": "Yürüyüş: Göğsünün sağ tarafını tutarak tek taraflı büzülme, yığılma. Yüz: Ağız sonuna kadar açık (hava açlığı), boyun damarları (juguler) kamera açısında şişkin/belirgin. Termal: Normal. -> Travmatik Tansiyon Pnömotoraks. ESI 1.",
    },
    {
        "id": "esi-red-corrosive-ingestion",
        "category": "red",
        "pattern": "Yürüyüş: Boğazını ve midesini tutarak yerde debelenme, istemsiz kasılmalar. Yüz: Çığlık atma mimiği, ağız çevresinde kimyasal yanığa bağlı yapısal bozulma. Termal: Ağız ve boyun hattında anormal enflamasyon ısısı. -> Korozif/Kimyasal Madde İçimi. ESI 1.",
    },
    {
        "id": "esi-red-heat-stroke-coma",
        "category": "red",
        "pattern": "Yürüyüş: Taşıyarak getirilmiş, pelte gibi gevşek yatış, terleme hiç yok (kuru cilt görseli). Yüz: Tamamen donuk, yanıtsız. Termal: Tüm vücut yüzeyinde 41°C üzeri aşırı kırmızı/parlak termal imza. -> Sıcak Çarpması Koması. ESI 1.",
    },
    {
        "id": "esi-red-brainstem-herniation",
        "category": "red",
        "pattern": "Yürüyüş: Koma pozisyonu, kollar dışa bükülmüş, bacaklar kaskatı ekstansiyonda (Deserebre postür). Yüz: Tamamen tepkisiz, ağrı uyarısına yüz yanıtı yok, göz kapakları kilitli. Termal: Kafa bölgesinde lokalize ısı artışı. -> Beyin Herniasyonu. ESI 1.",
    },
    {
        "id": "esi-red-amputation-upper-limb",
        "category": "red",
        "pattern": "Yürüyüş: Sağ kol omuz altından yok, diğer eliyle kalan parçayı sıkarak yalpalanma. Yüz: Şok evresinin getirdiği hissiz, bembeyaz (görsel) ve donuk ifade. Termal: Amputasyon güdüğünden dışarı yayılan sıcak kan termali, vücut genelinde hızla gelişen hipotermi. -> Majör Amputasyon. ESI 1.",
    },
    {
        "id": "esi-red-facial-burn-airway",
        "category": "red",
        "pattern": "Yürüyüş: Panik halinde kollarını çırparak yürüme, dengesiz. Yüz: Yüzdeki deri tamamen yanmış/soyulmuş, dudaklar şiş, ağzı açık nefes alma çabası. Termal: Yüz bölgesinde aşırı yüksek yanık ısısı (>40°C lokal). -> Havayolu/Yüz Yanığı. ESI 1.",
    },
    {
        "id": "esi-red-flail-chest-trauma",
        "category": "red",
        "pattern": "Yürüyüş: Göğsüne aldığı darbe sonrası yerde diz üzeri çökme. Yüz: Her nefes alışta acıyla irkilme. Termal: Göğüs duvarının bir kısmında nefes alırken içeri göçme (paradoksal hareket) görseli. -> Yelken Göğüs (Flail Chest). ESI 1.",
    },
    {
        "id": "esi-red-cardiac-tamponade-visual",
        "category": "red",
        "pattern": "Yürüyüş: Sedyede üst gövde dik tutulmaya çalışılıyor, aşırı huzursuz çırpınışlar. Yüz: Boğulma paniği, aşırı terlemeye bağlı yüzde termal soğuma. Termal: Göğüs ortasında delici alet yarasına bağlı lokal kan ısısı. -> Kardiyak Tamponad Şüphesi. ESI 1.",
    },
    {
        "id": "esi-red-massive-stroke-hemiplegia",
        "category": "red",
        "pattern": "Yürüyüş: Vücudun sol tarafı tamamen felçli (kol içe bükük, bacak sürükleniyor), yere kapaklanma. Yüz: Sol yüz yarısı tamamen düşük, gözler sadece sağa bakacak şekilde kilitlenmiş (gaze deviasyonu). Termal: 36.8°C. -> Akut İskemik/Hemorajik İnme. ESI 1.",
    },
    {
        "id": "esi-red-sepsis-mottled-skin",
        "category": "red",
        "pattern": "Yürüyüş: Sedyede tamamen hareketsiz yatış. Yüz: Letarjik, gözaltları morarmış görünüm. Termal: Gövde 39.5°C ateşli iken, diz kapakları ve ellerde mermerleşmeye (mottling) bağlı anormal bölgesel soğumalar. -> Septik Şok (Bozuk perfüzyon). ESI 1.",
    },
    {
        "id": "esi-red-toxic-gas-inhalation",
        "category": "red",
        "pattern": "Yürüyüş: Dört ayak üzerinde emekleyerek gelme, sürekli öksürük ve kasılma. Yüz: Gözler ve burundan şiddetli sıvı akışı, boğulma mimiği. Termal: Yüzde ve gözlerde tahrişe bağlı yüzeyel ısı artışı. -> Toksik Gaz Maruziyeti. ESI 1.",
    },
    {
        "id": "esi-red-open-abdominal-evisceration",
        "category": "red",
        "pattern": "Yürüyüş: İki büklüm, elleriyle karnından dışarı sarkan iç organlarını tutarak yığılma. Yüz: Dehşet ve şok ifadesi, dişler kenetlenmiş. Termal: Karın bölgesinde vücut dışına çıkmış organların 37°C'lik termal imzası. -> Eviserasyon / Açık Batın Travması. ESI 1.",
    },
    {
        "id": "esi-red-cocaine-overdose-agitation",
        "category": "red",
        "pattern": "Yürüyüş: Güvenlik görevlileri eşliğinde, aşırı saldırgan, sürekli tekme/yumruk atma; durdurulması için birden fazla personel gerekiyor. Yüz: Diş gıcırdatma, aşırı terleme (yüz termal olarak sıcak), gözler tam açık ve anlamsız bakış. Termal: Kas aktivitesine bağlı 39.2°C genel ısı. -> Sempatomimetik Toksidrom / Deliryum. ESI 2.",
    },
    {
        "id": "esi-red-hanging-strangulation",
        "category": "red",
        "pattern": "Yürüyüş: Kucakta getirilmiş, boyunda belirgin ip izi/çöküklük görünümü, kollar sarkık. Yüz: Dil dışarıda ve şiş, çene gevşek, bilinçsiz ve tepkisiz. Termal: Baş ve boyun bölgesinde venöz konjesyona bağlı anormal ısı artışı. -> Ası / Strangülasyon. ESI 1.",
    },
    {
        "id": "esi-red-child-abuse-unresponsive",
        "category": "red",
        "pattern": "Yürüyüş: Kucakta getirilen küçük çocuk, tamamen pelte gibi. Yüz: Yüzünde çok sayıda asimetrik şişlik/ezik, gözler kapalı, ağrı uyarısına tepki yok. Termal: Vücudun farklı yerlerinde eski (soğuk) ve yeni (sıcak) travma izleri. -> Nörolojik Hasarlı Çocuk Travması. ESI 1.",
    },
    {
        "id": "esi-red-amniotic-fluid-embolism-collapse",
        "category": "red",
        "pattern": "Yürüyüş: Doğumhaneden yeni çıkmış/doğum yapan kadın, aniden sedyede çırpınarak geriye kasılma. Yüz: Saniyeler içinde ağzı açarak nefes alamama paniği ve ardından tam donukluk (arrest). Termal: Yüzde hızla soğuma. -> Amniyotik Sıvı Embolisi. ESI 1.",
    },
    {
        "id": "esi-red-bacterial-meningitis-petechiae",
        "category": "red",
        "pattern": "Yürüyüş: Sedyede bacaklarını karnına çekerek kıvrılmış yatış (fetal pozisyon). Yüz: Işığa karşı yüzünü tamamen yastığa gömme, inleme. Termal: 40.5°C çok yüksek ateş + yüzde/gövdede termal kamerada karanlık görünen (nekrotik) peteşiyal lekeler. -> Meningokoksemik Menenjit. ESI 1.",
    },
    {
        "id": "esi-red-aortic-rupture-syncope",
        "category": "red",
        "pattern": "Yürüyüş: Sırta vuran ağrı nedeniyle ayakta kaskatı dururken bir anda odun gibi sırtüstü devrilme. Yüz: Devrilirken gözlerin tamamen geriye kayması. Termal: Gövde merkezinde (batın/toraks) homojen olmayan ısı dalgalanması. -> Masif Rüptür/Kardiyak Arrest. ESI 1.",
    },
    {
        "id": "esi-red-hypoglycemia-combative",
        "category": "red",
        "pattern": "Yürüyüş: Sarhoş gibi sendeleme, etrafa anlamsız ve koordinasyonsuz vurma. Yüz: Aşırı terli (termal olarak yüzü soğuk görünüyor), boş bakan agresif gözler. Termal: 35.5°C (Hafif hipotermik ve terli). -> Şiddetli Hipoglisemi (Nöroglikopenik evre). ESI 2.",
    },
    {
        "id": "esi-red-burn-inhalation-soot",
        "category": "red",
        "pattern": "Yürüyüş: Yangından çıkarılmış, öksürerek ve dizleri üzerine çökerek ilerleme. Yüz: Burun ve ağız çevresinde yoğun siyah is (kurum), sesi kısık şekilde ağzı açık. Termal: 38.0°C. -> İnhalasyon Yanığı (Havayolu Ödemi Riski). ESI 1.",
    },
    {
        "id": "esi-red-snakebite-anaphylaxis",
        "category": "red",
        "pattern": "Yürüyüş: Bacağını sürükleyerek gelme, aniden yere kapaklanma. Yüz: Göz kapakları ve dudaklar devasa şekilde şişmiş, hırıltılı solunum mimiği. Termal: Isırılan bacakta aşırı ısı artışı, yüzde ise ödeme bağlı genişleme. -> Zehirli Isırık + Anafilaktik Şok. ESI 1.",
    },
    {
        "id": "esi-red-electrical-burn-cardiac",
        "category": "red",
        "pattern": "Yürüyüş: Yere fırlatılmış gibi kollar ve bacaklar asimetrik açılmış yatış. Yüz: Çene kilitli, dudak kenarında yanık izi. Termal: Elde (giriş) ve ayakta (çıkış) çok yüksek lokal termal noktalar, gövdede kalp durmasına bağlı soğuma eğilimi. -> Yüksek Voltaj Elektrik Çarpması. ESI 1.",
    },
    {
        "id": "esi-red-status-asthmaticus-silent",
        "category": "red",
        "pattern": "Yürüyüş: Dik oturmaya çalışıyor ama başı öne düşüyor, göğüs hareketleri neredeyse durmuş. Yüz: Gözler açık ama camsı bakış, kaslar tamamen gevşemiş. Termal: Yüzde belirgin vazokonstriksiyon (soğuk görünüm). -> Sessiz Akciğer (Sıfır solunum, pre-arrest). ESI 1.",
    },
    {
        "id": "esi-red-penetrating-eye-brain",
        "category": "red",
        "pattern": "Yürüyüş: Bir başkası tarafından kollarına girilmiş yürüyor, bacaklar pelte gibi. Yüz: Göz küresine saplanmış derin bir obje (bıçak/demir), diğer göz şoktan donuk. Termal: Göz çevresinde travmaya bağlı ısı değişimi. -> Penetran Kranial Travma. ESI 1.",
    },
    {
        "id": "esi-red-severe-croup-stridor",
        "category": "red",
        "pattern": "Yürüyüş: Çocuğun göğüs kafesi her nefeste içe çöküyor (retraksiyon görseli), huzursuz debelenme. Yüz: Havlayan köpek gibi öksürük mimiği, gözler korkuyla açılmış. Termal: 38.5°C. -> Şiddetli Krup / Havayolu Obstrüksiyonu. ESI 2.",
    },
    {
        "id": "esi-red-placental-abruption-rigid",
        "category": "red",
        "pattern": "Yürüyüş: Gebe kadın karnını sımsıkı tutarak iki büklüm bağırarak yürüme çabası. Yüz: Sürekli, kesintisiz bir acı grimesi (dalgalı değil, sabit). Termal: Karın bölgesi (uterus) çevresinde yoğun iskemi/kanama termal izi. -> Plasenta Dekolmanı. ESI 1.",
    },
    {
        "id": "esi-red-cyanide-poisoning-coma",
        "category": "red",
        "pattern": "Yürüyüş: Yangın veya endüstriyel kaza sonrası getirilen hareketsiz hasta, kendi başına hareket edemiyor. Yüz: Gözler yarı açık tepkisiz, hiçbir uyarana yanıt yok, çene gevşek. Termal: Tüm vücut yüzey sıcaklığı 38-39°C anormal ısınma (dokular oksijen kullanamadığı için). -> Siyanür/CO Zehirlenmesi. ESI 1.",
    },
    {
        "id": "esi-red-postpartum-hemorrhage-shock",
        "category": "red",
        "pattern": "Yürüyüş: Tekerlekli sandalyeden kayarak yere yığılma, ayakta tutunma yok. Yüz: Göz kapakları kendiliğinden kapanıyor, uyarıya yanıt yok. Termal: Bacak arası bölgesinden yere yayılan devasa sıcak sıvı (kan) paterni; ekstremitelerde hızla gelişen soğuma. -> Masif Postpartum Kanama. ESI 1.",
    },
    {
        "id": "esi-red-thyroid-storm-agitation",
        "category": "red",
        "pattern": "Yürüyüş: Sedyede duramıyor, sürekli kıvranma, ekstremitelerde belirgin titreme (tremor). Yüz: Gözler pırtlak (ekzoftalmi), aşırı terli, ajite. Termal: 41.5°C (Kritik hipertermi). -> Tiroid Fırtınası. ESI 1.",
    },
    {
        "id": "esi-red-open-pneumothorax-sucking",
        "category": "red",
        "pattern": "Yürüyüş: Göğsündeki açık yaraya elini bastırarak iki büklüm durma. Yüz: Nefes aldıkça acıdan inleme, panik. Termal: Göğüsteki açık yaradan her nefeste içeri giren soğuk hava ve dışarı çıkan sıcak havanın termal dalgalanması. -> Açık Pnömotoraks. ESI 1.",
    },
    {
        "id": "esi-red-drug-induced-dystonia-airway",
        "category": "red",
        "pattern": "Yürüyüş: Boyun tamamen arkaya veya yana bükülü kilitlenmiş (tortikolis), adımlar kontrolsüz. Yüz: Dil tamamen dışarı sarkmış ve şiş (hava yolunu tıkıyor), gözler yukarı dikili. Termal: 37°C. -> Şiddetli Akut Distoni (Hava yolu riski). ESI 1.",
    },
    {
        "id": "esi-red-massive-ascites-rupture",
        "category": "red",
        "pattern": "Yürüyüş: Karnı devasa şiş olan (siroz) hasta, karnını tutarak yere devriliyor. Yüz: Şiddetli karın ağrısı ve şok yüzü. Termal: Göbek deliği (umbilikus) çevresinde sızan/patlayan asit sıvısına bağlı termal yayılım. -> Umbilikal Herni Rüptürü / Spontan Bakteriyel Peritonit Şoku. ESI 2.",
    },
    {
        "id": "esi-red-tracheostomy-bleeding",
        "category": "red",
        "pattern": "Yürüyüş: Boynundaki deliği (trakeostomi) tutarak koşma, boğulma eylemi. Yüz: Kan yutmaya bağlı sürekli öğürme, şiddetli hipoksi paniği. Termal: Boyundaki kanülden fışkıran sıcak kan paterni. -> Trakeostomi Kanama/Tıkanması. ESI 1.",
    },
    {
        "id": "esi-red-high-altitude-pulmonary-edema",
        "category": "red",
        "pattern": "Yürüyüş: Kurtarma ekibiyle gelmiş, adımlar pelte gibi, ayakta duramıyor. Yüz: Ağız çevresinde pembe/köpüklü sıvı, nefes alırken aşırı çaba mimiği, gözler yarı kapalı. Termal: 35.0°C (Dağ ortamı hipotermi etkisi). -> HAPE (Yüksek İrtifa Akciğer Ödemi). ESI 1.",
    },
    {
        "id": "esi-red-neurogenic-shock-priapism",
        "category": "red",
        "pattern": "Yürüyüş: Boyun travmalı sedyede, gövde altı tamamen felçli ve hareketsiz. Yüz: Bilinç düzeyi azalmış, gözler ara ara kapanıyor (senkop eğilimi). Termal: Pelvik bölge ve bacaklarda nörojenik vazodilatasyona bağlı homojen ısı artışı (gövde altı sıcak, üst gövde normal). -> Nörojenik Şok. ESI 1.",
    },
    {
        "id": "esi-red-fulminant-hepatic-failure",
        "category": "red",
        "pattern": "Yürüyüş: Yarı koma halinde sürüklenerek getirilmiş, kendi gücüyle hareket yok. Yüz: Ağız açık, sızma halinde, uyarıya minimal yanıt; ağız ve burundan aktif kanama görünümü. Termal: 36.0°C. -> Karaciğer Koması / Hepatik Ensefalopati. ESI 2.",
    },
    {
        "id": "esi-red-lethal-arrhythmia-vt",
        "category": "red",
        "pattern": "Yürüyüş: Göğsünü ovalayarak yavaşça oturma, ardından aniden bilincini kaybedip sandalyeden kayma. Yüz: Gözler fal taşı gibi açık kalmış ancak boş bakıyor, yüz kasları titriyor. Termal: Normalden hızla soğumaya geçiş. -> Nabızsız VT/VF arresti başlangıcı. ESI 1.",
    },
    {
        "id": "esi-red-acute-mesenteric-ischemia",
        "category": "red",
        "pattern": "Yürüyüş: Yaşlı hasta, dizlerini göğsüne çekip yerde debeleniyor (muayeneyle uyumsuz şiddetli ağrı). Yüz: Çığlık atıyor, ter içinde. Termal: Batın bölgesinde organ iskemisine bağlı olağandışı soğuk termal odak. -> Akut Mezenter İskemisi. ESI 1.",
    },
    {
        "id": "esi-red-gas-gangrene-crepitus",
        "category": "red",
        "pattern": "Yürüyüş: Açık yaralı bacağı tamamen sürükleyerek yürüme, aşırı toksik görünüm. Yüz: Deliryum, anlamsız bakışlar. Termal: Bacakta gaz birikimine bağlı dalgalı (sıcak-soğuk alacalı) termal imza ve yara çevresinde çok yüksek ateş. -> Gazlı Gangren. ESI 1.",
    },
    {
        "id": "esi-red-malignant-hypertension-encephalopathy",
        "category": "red",
        "pattern": "Yürüyüş: Kusarak ve sendeliyerek yürüme, dengesini kuramama. Yüz: Gözünü sıkıca kapatmış, başını iki eliyle preslercesine sıkıştırma, şuur bulanıklığı. Termal: 37°C. -> Hipertansif Ensefalopati. ESI 2.",
    },
    # ─────────────────────────────────────────────────────── YELLOW (108)
    {
        "id": "esi-yellow-appendicitis-suspicion",
        "category": "yellow",
        "pattern": "Yürüyüş: Sağ alt karın bölgesini tutarak hafif iki büklüm, yavaş adımlar. Yüz: Her adımda hafif irkilme/ağrı grimesi. Termal: 37.8°C (Subfebril). -> Apandisit Şüphesi. ESI 3.",
    },
    {
        "id": "esi-yellow-pneumonia-systemic",
        "category": "yellow",
        "pattern": "Yürüyüş: Yavaş, ara sıra duraklayıp derin nefes alma ihtiyacı. Yüz: Yorgun, hafif bitkin. Termal: 38.5°C (Tüm vücut geneli). -> Pnömoni / Sistemik Enfeksiyon. ESI 3.",
    },
    {
        "id": "esi-yellow-acute-cholecystitis",
        "category": "yellow",
        "pattern": "Yürüyüş: Sağ üst batını (kaburga altı) tutarak temkinli yürüme. Yüz: Ara ara bulantı mimiği, orta şiddetli ağrı. Termal: 38.0°C. -> Akut Kolesistit (Safra Kesesi İltihabı). ESI 3.",
    },
    {
        "id": "esi-yellow-ureteral-colic",
        "category": "yellow",
        "pattern": "Yürüyüş: Bel bölgesini (böğür) arkadan tutarak yerinde duramama, volta atma. Yüz: Aralıklı olarak çok şiddetli, kıvrandırıcı ağrı ifadesi. Termal: 36.6°C. -> Böbrek Taşı (Üriner Kolik). ESI 3.",
    },
    {
        "id": "esi-yellow-deep-vein-thrombosis",
        "category": "yellow",
        "pattern": "Yürüyüş: Sol alt bacakta belirgin asimetrik kalınlaşma, o bacağa basarken topallama. Yüz: Endişeli, hafif ağrı. Termal: Sol bacak baldırında sağa göre +2°C lokal ısı artışı. -> Derin Ven Trombozu (DVT). ESI 3.",
    },
    {
        "id": "esi-yellow-central-vertigo-ataxia",
        "category": "yellow",
        "pattern": "Yürüyüş: Bağımsız ancak sarhoş gibi sallantılı, geniş tabanlı yürüme. Yüz: Gözlerini odaklamakta zorlanma, bulantı/baş dönmesi mimiği. Termal: 36.5°C. -> Santral Vertigo / Serebellar Ataksi. ESI 3.",
    },
    {
        "id": "esi-yellow-pediatric-gastroenteritis",
        "category": "yellow",
        "pattern": "Yürüyüş: Çocuk hasta, yürüyor ama annesinin bacağına sarılarak çöküyor. Yüz: Yorgun, halsiz, göz altları çökmüş (dehidrate görünüm). Termal: 38.9°C. -> Pediatrik Gastroenterit / Orta Dehidratasyon. ESI 3.",
    },
    {
        "id": "esi-yellow-shoulder-fracture-dislocation",
        "category": "yellow",
        "pattern": "Yürüyüş: Kolu gövdeye bitişik tutarak koruma, omuzu oynatmadan yürüme. Yüz: Kolda hareket olunca ani şiddetli acı mimiği. Termal: Omuz ekleminde lokal ısı farkı. -> Omuz Çıkığı / Kapalı Kırık. ESI 3.",
    },
    {
        "id": "esi-yellow-complex-migraine",
        "category": "yellow",
        "pattern": "Yürüyüş: Gövde dik ama adımlar çok yavaş, halsiz. Yüz: Elleriyle şakaklarını ovuşturma, ışıktan rahatsız olma (gözleri kısma). Termal: 36.8°C. -> Kompleks / Dirençli Migren. ESI 3.",
    },
    {
        "id": "esi-yellow-pid-ovarian-cyst",
        "category": "yellow",
        "pattern": "Yürüyüş: Alt karın bölgesini iki eliyle tutarak öne eğik ilerleme. Yüz: Sürekli, donuk bir ağrı ifadesi, solgunluk. Termal: 37.2°C. -> Pelvik İnflamatuar Hastalık (PID) / Over Kisti. ESI 3.",
    },
    {
        "id": "esi-yellow-complicated-cellulitis",
        "category": "yellow",
        "pattern": "Yürüyüş: Bacakta diz altı bölgede geniş alanda kızarıklık, hafif topallama. Yüz: Rahatsızlık ifadesi. Termal: Kızarık bölgede +3°C'lik ciddi fokal ısı artışı. -> Komplike Selülit. ESI 3.",
    },
    {
        "id": "esi-yellow-new-atrial-fibrillation",
        "category": "yellow",
        "pattern": "Yürüyüş: Dik yürüyor ancak göğsüne dokunarak sıkıntı belirtiyor. Yüz: Tedirgin ve gergin ifade, ara sıra derin nefes alma hareketi. Termal: 36.7°C. -> Yeni Başlangıçlı Atriyal Fibrilasyon (Stabil). ESI 3.",
    },
    {
        "id": "esi-yellow-geriatric-syncope",
        "category": "yellow",
        "pattern": "Yürüyüş: Yaşlı hasta, çok temkinli ve yavaş yürüme, bastonla zorlanma. Yüz: Herhangi bir akut ağrı yok ama genel düşkünlük. Termal: 35.8°C (Hafif hipotermik/Düşkün). -> Geriatrik Senkop Araştırması / Genel Durum Bozukluğu. ESI 3.",
    },
    {
        "id": "esi-yellow-septic-arthritis-gout",
        "category": "yellow",
        "pattern": "Yürüyüş: Diz eklemi aşırı şiş, hiç yük veremeden sekerek ilerleme. Yüz: Eklem hareketinde şiddetli grimase. Termal: Diz kapağında çok belirgin dairesel ısı artışı (>38.5°C lokal). -> Septik Artrit / Akut Gut Atağı. ESI 3.",
    },
    {
        "id": "esi-yellow-moderate-burn-tbsa",
        "category": "yellow",
        "pattern": "Yürüyüş: Gövdede veya kolda geniş yanık alanı, yürüyüş bağımsız ama yavaş. Yüz: Sürekli ağrı mimiği. Termal: Yanık alanında homojen olmayan termal parlama/soğuma karışımı. -> Orta Derece Yanık (%10-15 TBSA). ESI 3.",
    },
    {
        "id": "esi-yellow-peritonsillar-abscess",
        "category": "yellow",
        "pattern": "Yürüyüş: Elleriyle çenesinin altını (boynunu) tutarak yutkunmaktan kaçınan postür. Yüz: Ağzı hafif açık, yutkununca yüz ekşitme. Termal: 38.5°C. -> Peritonsiller Apse. ESI 3.",
    },
    {
        "id": "esi-yellow-bell-palsy",
        "category": "yellow",
        "pattern": "Yürüyüş: Tam bağımsız ancak yüzde asimetri var. Yüz: Sadece yüzün yarısında sarkma (alın dahil, göz kapağı kapanmıyor), panik yok, ağrı yok. Termal: 36.6°C. -> Bell Paralizisi (Yüz Felci, inme ekarte edilecek). ESI 3.",
    },
    {
        "id": "esi-yellow-acute-pancreatitis",
        "category": "yellow",
        "pattern": "Yürüyüş: Gövde öne eğik, sırttan öne kuşak tarzı yayılan ağrıyı koruyan duruş. Yüz: Bulantı mimiği, ara sıra durup kusma refleksi. Termal: 37.5°C. -> Akut Pankreatit. ESI 3.",
    },
    {
        "id": "esi-yellow-acute-diverticulitis",
        "category": "yellow",
        "pattern": "Yürüyüş: Yaşlı hasta, sol alt kadranı tutarak dikkatli adım atma. Yüz: Halsiz, ağrılı yüz. Termal: 38.2°C. -> Akut Divertikülit. ESI 3.",
    },
    {
        "id": "esi-yellow-complicated-animal-bite",
        "category": "yellow",
        "pattern": "Yürüyüş: Köpek ısırığı nedeniyle baldırını sarmış, sekerek yürüme. Yüz: Orta şiddetli ağrı ve endişe. Termal: Bacakta doku bütünlüğü bozulmuş bölgede termal değişiklik. -> Komplike Hayvan Isırığı. ESI 3.",
    },
    {
        "id": "esi-yellow-testicular-torsion",
        "category": "yellow",
        "pattern": "Yürüyüş: Kasığını/skrotum bölgesini koruyarak, bacakları açık (ördekvari) yürüme. Yüz: Şiddetli rahatsızlık ve utanma/ağrı karışımı. Termal: Pelvik bölgede lokal ısı artışı. -> Orşit / Testis Torsiyonu Şüphesi. ESI 3.",
    },
    {
        "id": "esi-yellow-atypical-chest-pleurisy",
        "category": "yellow",
        "pattern": "Yürüyüş: Göğüs duvarını tek eliyle destekleyip sığ nefes alarak yürüme. Yüz: Derin nefes aldığında anlık batma grimesi. Termal: 36.5°C. -> Atipik Göğüs Ağrısı / Plörezi. ESI 3.",
    },
    {
        "id": "esi-yellow-opioid-withdrawal",
        "category": "yellow",
        "pattern": "Yürüyüş: Eller titriyor, yerinde duramama, aşırı hareketlilik (ajitasyon). Yüz: Terleme, esneme, burnunu çekme, aşırı huzursuzluk. Termal: 37.2°C (Hafif yüksek). -> Opiyat Yoksunluk Sendromu. ESI 3.",
    },
    {
        "id": "esi-yellow-acute-pyelonephritis",
        "category": "yellow",
        "pattern": "Yürüyüş: Sırtına ve böğrüne vurarak ağrıyı dindirmeye çalışma. Yüz: Orta/şiddetli ağrı, terleme yok. Termal: 38.8°C. -> Akut Piyelonefrit (Böbrek İltihabı). ESI 3.",
    },
    {
        "id": "esi-yellow-urinary-retention",
        "category": "yellow",
        "pattern": "Yürüyüş: Alt karın ortasını (mesane hizası) iki eliyle tutarak kıvranma, adımlar kısa ve sık. Yüz: Şiddetli baskı ağrısı grimesi, sürekli rahatsızlık ifadesi. Termal: 36.8°C. -> Akut İdrar Retansiyonu (Glob Vesicale). ESI 3.",
    },
    {
        "id": "esi-yellow-displaced-arm-fracture",
        "category": "yellow",
        "pattern": "Yürüyüş: El bileğinde gözle görülür açılanma (deformite), diğer eliyle destekleyerek yürüme. Yüz: Hareket ettirmeme paniği, ağrı. Termal: Bilek çevresinde lokal ısı artışı. -> Deplase Kapalı Kol Kırığı. ESI 3.",
    },
    {
        "id": "esi-yellow-corneal-ulcer",
        "category": "yellow",
        "pattern": "Yürüyüş: Gözünü sıkıca kapatıp elleriyle örtmüş, yardımla yürüme. Yüz: Işığa karşı aşırı hassasiyet (fotofobi), göz kapağında spazm. Termal: Normal. -> Korneal Ülser / Derin Yabancı Cisim. ESI 3.",
    },
    {
        "id": "esi-yellow-dental-abscess-trismus",
        "category": "yellow",
        "pattern": "Yürüyüş: Çenesi belirgin asimetrik şiş, yürüme normal. Yüz: Ağzı açamama (trismus), yutkunurken acı çekme. Termal: Çene altı/boyun bölgesinde +2°C ısı artışı. -> Yaygın Dental Apse / Erken Selülit. ESI 3.",
    },
    {
        "id": "esi-yellow-stable-blunt-abdominal",
        "category": "yellow",
        "pattern": "Yürüyüş: Araç içi trafik kazası (düşük hız) sonrası dik yürüyor ama karın kasları gergin. Yüz: Karnına dokunulduğunda irkilme. Termal: 36.6°C. -> Stabil Künt Batın Travması. ESI 3.",
    },
    {
        "id": "esi-yellow-bacteremia-rigors",
        "category": "yellow",
        "pattern": "Yürüyüş: Titreme nöbetleri (rigor) geçirerek, battaniyeye sarılı yürüme. Yüz: Dişleri birbirine vuruyor, aşırı üşüme mimiği. Termal: 39.5°C. -> Akut Bakteriyemi / Sıtma atağı (Stabil vitaller varsayımıyla). ESI 3.",
    },
    {
        "id": "esi-yellow-herpes-zoster-ophthalmic",
        "category": "yellow",
        "pattern": "Yürüyüş: Yüzün bir yarısında kabarcıklı lezyonlar, yürüme bağımsız. Yüz: Lezyonlu bölgeye dokunmaktan kaçınan ağrı mimiği. Termal: Yüzün tek tarafında lokal inflamasyon ısısı. -> Herpes Zoster Oftalmikus (Zona). ESI 3.",
    },
    {
        "id": "esi-yellow-refractory-epistaxis",
        "category": "yellow",
        "pattern": "Yürüyüş: Sürekli burun kanaması, elinde kanlı peçeteyle bası yaparak yürüme. Yüz: Kan yutmaya bağlı hafif bulantı, panik. Termal: 36.5°C. -> Dirençli Epistaksis (Burun kanaması). ESI 3.",
    },
    {
        "id": "esi-yellow-systemic-rash-viral",
        "category": "yellow",
        "pattern": "Yürüyüş: Gövdesi dik, ancak tüm vücudunda yaygın döküntü görünüyor. Yüz: Yorgunluk, hafif eklem ağrısı mimiği. Termal: 38.5°C. -> Sistemik Döküntülü Hastalık / Viral Sendrom. ESI 3.",
    },
    {
        "id": "esi-yellow-threatened-abortion",
        "category": "yellow",
        "pattern": "Yürüyüş: Hamile kadın, bacak arasına havlu bastırarak temkinli adımlar. Yüz: Düşük tehdidi endişesi, hafif kramp mimiği. Termal: 36.8°C. -> Abortus İmminens (Düşük Tehdidi) / Stabil Kanama. ESI 3.",
    },
    {
        "id": "esi-yellow-electrolyte-imbalance",
        "category": "yellow",
        "pattern": "Yürüyüş: Kol/bacak kaslarında şiddetli seğirme ve kasılmalarla yürüme. Yüz: Kasılan bölgeye bakarak şaşkınlık ve acı. Termal: 36.5°C. -> Semptomatik Elektrolit Bozukluğu (Hipokalemi/Hipokalsemi). ESI 3.",
    },
    {
        "id": "esi-yellow-ear-barotrauma",
        "category": "yellow",
        "pattern": "Yürüyüş: Dalış sonrası kulağını tutarak dengesiz adımlar. Yüz: Şiddetli kulak ağrısı ve baş dönmesi grimesi. Termal: 36.6°C. -> Orta Kulak Barotravması. ESI 3.",
    },
    {
        "id": "esi-yellow-polyarticular-gout",
        "category": "yellow",
        "pattern": "Yürüyüş: İki veya üç ekleminde birden şişlik ve kızarıklık, zorlanarak yürüme. Yüz: Her adımda eklem ağrısı. Termal: Eklemlerde çoklu (poliartiküler) lokal ateş. -> Romatolojik Alevlenme / Poliartiküler Gut. ESI 3.",
    },
    {
        "id": "esi-yellow-post-ictal-first-seizure",
        "category": "yellow",
        "pattern": "Yürüyüş: Postiktal dönemden yeni çıkmış, yorgun ve ağır adımlar. Yüz: Hala hafif şaşkın, etrafı anlamaya çalışan bakışlar. Termal: 37.0°C. -> İlk Kez Geçirilen ve Durmuş Nöbet. ESI 3.",
    },
    {
        "id": "esi-yellow-foreign-body-ingestion-stable",
        "category": "yellow",
        "pattern": "Yürüyüş: Çocuğun elinde yuttuğu objenin aynısından var, yürümesi normal. Yüz: Salya akıntısı yok, rahat görünüm, aile panik. Termal: 36.5°C. -> Yabancı Cisim Yutma Şüphesi (Stabil). ESI 3.",
    },
    {
        "id": "esi-yellow-intractable-hiccups",
        "category": "yellow",
        "pattern": "Yürüyüş: Günlerdir süren hıçkırık nedeniyle bedeni sarsılarak yürüme. Yüz: Uykusuz, bitkin, sürekli hıçkırmaya bağlı rahatsızlık. Termal: 36.6°C. -> İnatçı Hıçkırık (İntractable Hiccups). ESI 3.",
    },
    {
        "id": "esi-yellow-pediatric-uti-biliary",
        "category": "yellow",
        "pattern": "Yürüyüş: Bebek aktif ağlıyor, ayaklarını karnına çekiyor. Yüz: Ağlama krizi. Termal: 38.3°C. -> Pediatrik İdrar Yolu Enfeksiyonu / Biliyer Kolik Şüphesi. ESI 3.",
    },
    {
        "id": "esi-yellow-cervical-radiculopathy",
        "category": "yellow",
        "pattern": "Yürüyüş: Başını tek bir pozisyonda sabit tutmaya çalışarak robotik yürüme. Yüz: Ense kökünde sertlik ve ağrı mimiği. Termal: 37.8°C. -> Servikal Radikülopati / Erken Menenjit Şüphesi. ESI 3.",
    },
    {
        "id": "esi-yellow-stable-gi-bleed-melena",
        "category": "yellow",
        "pattern": "Yürüyüş: Yaşlı hasta yavaş ve halsiz adımlarla yürüme. Yüz: Yorgun, bitkin ifade, gergin bakış. Termal: 36.2°C (hafif düşük). -> Stabil GİS Kanaması. ESI 3.",
    },
    {
        "id": "esi-yellow-sickle-cell-crisis",
        "category": "yellow",
        "pattern": "Yürüyüş: Bacaklardan gelen ağrıyla bastonla güç alarak yürüme, her adımda duraksamalar. Yüz: Şiddetlenmiş ağrı grimesi, kasılan yüz kasları. Termal: 37.5°C. -> Orak Hücreli Anemi Vazooklüzif Krizi. ESI 3.",
    },
    {
        "id": "esi-yellow-suicidal-ideation-no-harm",
        "category": "yellow",
        "pattern": "Yürüyüş: Tam bağımsız, odanın bir köşesinde sessizce durma eğilimi. Yüz: Sürekli yere bakma, ağlama atakları, donukluk (psikomotor retardasyon). Termal: 36.5°C. -> Aktif Suisidal Düşünce (Fiziksel hasar yok). ESI 3.",
    },
    {
        "id": "esi-yellow-hemophilia-hemarthrosis",
        "category": "yellow",
        "pattern": "Yürüyüş: Dizde travma olmaksızın devasa kanama şişliği (hemartroz), sekiyor. Yüz: Gerginlik hissine bağlı ağrı. Termal: Diz ekleminde sıvı birikimine bağlı termal parlama. -> Hemofili Eklem İçi Kanama. ESI 3.",
    },
    {
        "id": "esi-yellow-hip-prosthesis-dislocation",
        "category": "yellow",
        "pattern": "Yürüyüş: Kalça protezi öyküsü olan yaşlı, bacağını dışa dönük sürükleyerek yürüme. Yüz: Her adımda orta ağrı. Termal: Normal. -> Kalça Çıkığı / Kırığı (Stabil vitaller). ESI 3.",
    },
    {
        "id": "esi-yellow-orbital-preseptal-cellulitis",
        "category": "yellow",
        "pattern": "Yürüyüş: Göz kapağında büyük şişlik, o tarafı göremeyerek yürüme. Yüz: Göz kapağı kızarık ve kapalı, orbita çevresinde gerginlik. Termal: Göz çevresinde çok yüksek lokal ısı. -> Preseptal / Orbital Selülit. ESI 3.",
    },
    {
        "id": "esi-yellow-abnormal-uterine-bleeding",
        "category": "yellow",
        "pattern": "Yürüyüş: Postmenopozal kadın, yoğun kanama nedeniyle kıyafetine sarılı yürüme. Yüz: Endişeli, halsizlik mimiği. Termal: 36.7°C. -> Anormal Uterin Kanama (Stabil). ESI 3.",
    },
    {
        "id": "esi-yellow-gait-sway",
        "category": "yellow",
        "pattern": "Stabilite kaybı (sallantılı yürüyüş, asimetri) tek başına ESI Seviye 3 değerlendirmesi gerektirir; düşme riski ve nörolojik bulgular için yakın izlem.",
    },
    {
        "id": "esi-yellow-abdominal",
        "category": "yellow",
        "pattern": "Karın ağrısı + bulantı + hafif ateş gözlem gerektiren durumdur. ESI Seviye 3, apandisit ekarte edilmeli.",
    },
    {
        "id": "esi-yellow-headache",
        "category": "yellow",
        "pattern": "Yüzde şiddetli ağrı grimesi + gözleri kısan/kapatan ifade + yavaş dikkatli yürüyüş migren veya ciddi baş ağrısı tablosu. ESI Seviye 2-3.",
    },
    {
        "id": "esi-yellow-fracture",
        "category": "yellow",
        "pattern": "Ekstremitede şişlik + hareket kısıtlılığı + ağrı kırık şüphesi işaretidir. ESI Seviye 3, radyoloji değerlendirmesi gerekir.",
    },
    {
        "id": "esi-yellow-hypertension",
        "category": "yellow",
        "pattern": "Yüzde gergin/ağrılı ifade + yavaş ve temkinli yürüyüş + normal vücut ısısı hipertansif tablo ile uyumlu olabilir. ESI Seviye 2-3 yakın izlem.",
    },
    {
        "id": "esi-yellow-dysrhythmia",
        "category": "yellow",
        "pattern": "Yüzde tedirgin/gergin ifade + yürüyüşte hafif sallantı + normal vücut ısısı kardiyak aritmi şüphesiyle uyumlu olabilir. ESI Seviye 3, EKG öncelikli.",
    },
    {
        "id": "esi-yellow-moderate-fever",
        "category": "yellow",
        "pattern": "Orta düzeyde ateş (37.5–39°C) + yürüyüşte hafif yavaşlama + yüzde rahatsızlık ifadesi; vital bulgular stabil. ESI Seviye 3.",
    },
    {
        "id": "esi-yellow-elderly-gait",
        "category": "yellow",
        "pattern": "Yaşlı hastada yavaş ve temkinli yürüyüş + hafif yüz gerginliği; düşme öyküsü veya ilaç etkileşimi olasılığı. ESI Seviye 3.",
    },
    {
        "id": "esi-yellow-vertigo",
        "category": "yellow",
        "pattern": "Baş dönmesi + yürüyüşte yalpalama + yüzde bulantı ifadesi vestibüler patoloji veya santral vertigo. ESI Seviye 3.",
    },
    {
        "id": "esi-yellow-back-pain",
        "category": "yellow",
        "pattern": "Bel ağrısı + öne eğik yürüyüş + yüzde ağrı grimesi disk hernisi veya kas spazmı. ESI Seviye 3.",
    },
    {
        "id": "esi-yellow-mild-burn",
        "category": "yellow",
        "pattern": "Kısmi yanık alanı + ağrıya bağlı yüz buruşturma + normal yürüyüş ESI Seviye 3, yara bakımı ve analjezi.",
    },
    {
        "id": "esi-yellow-urinary",
        "category": "yellow",
        "pattern": "İdrar yolu enfeksiyonu şüphesi + hafif ateş (38°C civarı) + yüzde rahatsızlık ifadesi. ESI Seviye 3, idrar analizi.",
    },
    {
        "id": "esi-yellow-pediatric-fever",
        "category": "yellow",
        "pattern": "Çocuk hasta ateş 38–39°C + huzursuz yüz ifadesi + normal yürüyüş enfeksiyon odağı araştırılmalı. ESI Seviye 3.",
    },
    {
        "id": "esi-yellow-dehydration",
        "category": "yellow",
        "pattern": "Uzun süreli kusma/ishal + halsiz yüz ifadesi + yavaş yürüyüş dehidrasyon işareti. ESI Seviye 3, IV sıvı değerlendirmesi.",
    },
    {
        "id": "esi-yellow-chest-wall-pain",
        "category": "yellow",
        "pattern": "Göğüs duvarı ağrısı + yüzde orta düzey ağrı ifadesi + normal yürüyüş kas-iskelet kökenli olabilir; kardiyak ekarte edilmeli. ESI Seviye 3.",
    },
    {
        "id": "esi-yellow-syncope-recovered",
        "category": "yellow",
        "pattern": "Geçirilmiş senkop + şu an yürüyebiliyor ama sallantılı + yüzde tedirgin ve şaşkın ifade. ESI Seviye 2-3, kardiyak tetkik.",
    },
    {
        "id": "esi-yellow-kidney-stone",
        "category": "yellow",
        "pattern": "Böğür ağrısı + yüzde şiddetli ağrı grimesi + eğik yürüyüş üreter taşı düşündürür. ESI Seviye 3, görüntüleme.",
    },
    {
        "id": "esi-yellow-hip-pain",
        "category": "yellow",
        "pattern": "Kalça ağrısı + topallayan yürüyüş + yüzde orta ağrı ifadesi kalça kırığı veya bursit. ESI Seviye 3, radyoloji.",
    },
    {
        "id": "esi-yellow-dental-abscess",
        "category": "yellow",
        "pattern": "Yüz şişliği + yüzde ağrı nedeniyle çene gerginliği + normal yürüyüş dental apse veya selülit. ESI Seviye 3-4, ağız-diş cerrahisi.",
    },
    {
        "id": "esi-yellow-psychiatric-agitation",
        "category": "yellow",
        "pattern": "Orta düzey ajitasyon + yüzde gergin/öfkeli ifade + hızlı ama koordineli yürüyüş. ESI Seviye 2-3, psikiyatri değerlendirmesi.",
    },
    {
        "id": "esi-yellow-mild-hypothermia",
        "category": "yellow",
        "pattern": "Vücut ısısı 35–36°C arası + hafif titreme yüze yansımış + yavaş yürüyüş. ESI Seviye 3, ısınma ve izlem.",
    },
    {
        "id": "esi-yellow-post-fall",
        "category": "yellow",
        "pattern": "Düşme sonrası ayağa kalkabiliyor ancak yürüyüş ağrılı ve yavaş + yüzde ağrı ifadesi. ESI Seviye 3, kırık ekarte edilmeli.",
    },
    {
        "id": "esi-yellow-migraine",
        "category": "yellow",
        "pattern": "Migren atağı: ışığa/sese duyarlı yüz + yavaş dikkatli yürüyüş + bulantı ifadesi. ESI Seviye 3, analjezi ve karanlık oda.",
    },
    {
        "id": "esi-yellow-cellulitis",
        "category": "yellow",
        "pattern": "Ekstremite enfeksiyonu + ateş 38°C + hafif topallama + yüzde rahatsızlık. ESI Seviye 3, antibiyotik ve kan tahlili.",
    },
    {
        "id": "esi-yellow-shoulder-dislocation",
        "category": "yellow",
        "pattern": "Omuz dislokasyonu + tek kol tutulmuş yürüyüş + yüzde ağrı grimesi ESI Seviye 3, redüksiyon öncesi görüntüleme.",
    },
    {
        "id": "esi-yellow-gastrointestinal-bleed",
        "category": "yellow",
        "pattern": "GI kanama şüphesi + hafif halsizlik yüze yansımış + yavaş temkinli yürüyüş. ESI Seviye 2-3, acil endoskopi değerlendirmesi.",
    },
    {
        "id": "esi-yellow-alcohol-intoxication",
        "category": "yellow",
        "pattern": "Alkol entoksikasyonu: sallantılı yürüyüş + yüz gevşemiş ve koordinasyonsuz + vücut ısısı düşme eğilimi. ESI Seviye 3, gözlem.",
    },
    {
        "id": "esi-yellow-panic-attack",
        "category": "yellow",
        "pattern": "Panik atak: yüzde belirgin korku ve terleme ifadesi + hızlı ama stabil yürüyüş. ESI Seviye 3, psikiyatrik destek.",
    },
    {
        "id": "esi-yellow-antalgic-gait-hip-pain",
        "category": "yellow",
        "pattern": "Belirgin antaljik yürüyüş: sol veya sağ kalçaya yük bindirmeme, yavaş ve korumalı adımlar + yüzde orta düzey ağrı ifadesi + termal normal. ESI Seviye 3; kalça patolojisi değerlendirmesi.",
    },
    {
        "id": "esi-yellow-moderate-fever-lethargic-child",
        "category": "yellow",
        "pattern": "Çocuk hasta: termal kamerada orta ateş (38-39°C) + yavaş ve yorgun yürüyüş, ebeveyn desteğiyle + yüzde huzursuz ağlamaklı ifade. ESI Seviye 3; ateş kaynağı araştırılmalı.",
    },
    {
        "id": "esi-yellow-facial-pain-grimace-jaw",
        "category": "yellow",
        "pattern": "Yüzde belirgin ağrı grimacı, çene kaslarında gerilim görünümü + yürüyüş normal ancak yavaş + termal kamerada yüz bölgesinde hafif ısı artışı. ESI Seviye 3; ağrı kaynağı değerlendirmesi.",
    },
    {
        "id": "esi-yellow-elderly-unsteady-thermal-normal",
        "category": "yellow",
        "pattern": "Yaşlı hasta: belirgin denge bozukluğu, ayak sürüyerek yavaş yürüyüş + yüzde gergin ve endişeli ifade + termal normal. ESI Seviye 3; düşme riski yüksek, nörolojik ve ortopedik değerlendirme.",
    },
    {
        "id": "esi-yellow-limping-knee-effusion",
        "category": "yellow",
        "pattern": "Diz üzerine yük bindirememe, belirgin topallama, merdiven inememe + yüzde orta ağrı ifadesi + termal kamerada diz bölgesinde hafif ısı artışı (efüzyon). ESI Seviye 3; ortopedi.",
    },
    {
        "id": "esi-yellow-migraine-posture-guarded",
        "category": "yellow",
        "pattern": "Işıktan kaçınan postür, baş öne eğik korumalı yürüyüş + yüzde belirgin ağrı ifadesi, gözler kısılmış + termal kamerada alın bölgesi normale yakın. ESI Seviye 3; migren protokolü.",
    },
    {
        "id": "esi-yellow-back-pain-guarded-gait-new",
        "category": "yellow",
        "pattern": "Bel bölgesini koruyarak eğimli yürüyüş, her adımda yüz ifadesi geriliyor + yüzde orta-şiddetli ağrı grimacı + termal kamerada bel bölgesinde hafif lokal ısı artışı. ESI Seviye 3.",
    },
    {
        "id": "esi-yellow-wrist-fracture-arm-guarded",
        "category": "yellow",
        "pattern": "Yaralı kolu karşı elle destekleyerek yürüyen postür, kol hareketi yok + yüzde orta ağrı ifadesi + termal kamerada önkol/el bileği bölgesinde hafif ısı artışı. ESI Seviye 3; radyoloji.",
    },
    {
        "id": "esi-yellow-thermal-fever-adult-moderate",
        "category": "yellow",
        "pattern": "Erişkin: termal kamerada alın sıcaklığı 38-39°C + yavaş ve yorgun yürüyüş, duraksama + yüzde bitkin ve rahatsız ifade. ESI Seviye 3; ateş odağı araştırılmalı.",
    },
    {
        "id": "esi-yellow-shoulder-pain-limited-motion-gait",
        "category": "yellow",
        "pattern": "Yaralı omuzu kımıldatmadan yürüyen hasta, gövde rotasyonu sıfır + yüzde orta ağrı ifadesi, hareket ettirince belirginleşiyor + termal kamerada omuz bölgesinde hafif ısı artışı. ESI Seviye 3.",
    },
    {
        "id": "esi-yellow-patellar-dislocation",
        "category": "yellow",
        "pattern": "Yürüyüş: Tek bacak üzerinde sekerek gelme, diğer diz kapağı dışa doğru bariz kaymış (deforme). Yüz: Bacağı hareket ettirme korkusu, şiddetli lokal ağrı. Termal: Diz çevresinde inflamasyon ısısı. -> Patella Çıkığı. ESI 3.",
    },
    {
        "id": "esi-yellow-colles-fracture-deformity",
        "category": "yellow",
        "pattern": "Yürüyüş: Bileği çatal sırtı şeklinde bükülmüş, kolu göğsüne yaslayarak yürüme. Yüz: Hareket ettirildiğinde şiddetli acı. Termal: Kırık hattında fokal ısı artışı, parmak uçlarında normal ısı (dolaşım sağlam). -> Deplase El Bilek Kırığı. ESI 3.",
    },
    {
        "id": "esi-yellow-tia-resolved-weakness",
        "category": "yellow",
        "pattern": "Yürüyüş: Yaşlı hasta, tam bağımsız ve düzgün yürüyor. Yüz: Öncesinde yüzünün kaydığını ifade eden el jestleri yapıyor, şu an yüzü simetrik, nötr ifade. Termal: 36.6°C. -> Çözülmüş GİA (Geçici İskemik Atak). ESI 3.",
    },
    {
        "id": "esi-yellow-moderate-dehydration-peds",
        "category": "yellow",
        "pattern": "Yürüyüş: Çocuğun yürüyüşü çok ağır, annesinin eteğine tutunarak ayakta duruyor. Yüz: Gözleri çökmüş, ağlarken gözyaşı akmıyor (kuru ağlama). Termal: 38.0°C. -> Orta Derece Dehidratasyon. ESI 3.",
    },
    {
        "id": "esi-yellow-scrotal-epididymitis",
        "category": "yellow",
        "pattern": "Yürüyüş: Bacaklarını omuz genişliğinde açarak (paytak) dikkatli yürüme. Yüz: Testis bölgesindeki ağrı nedeniyle her adımda yüzünü ekşitme. Termal: Skrotum bölgesinde tek taraflı belirgin ısı artışı. -> Epididimit/Orşit. ESI 3.",
    },
    {
        "id": "esi-yellow-acute-gout-knee",
        "category": "yellow",
        "pattern": "Yürüyüş: Diz eklemi aşırı şişkin ve kırmızı, yere basmayı reddederek sekme. Yüz: Dize ufak bir temas anında (kıyafet değmesi bile) şiddetli irkilme. Termal: Diz kapağında çok yüksek yuvarlak ısı odağı. -> Akut Gut Atağı. ESI 3.",
    },
    {
        "id": "esi-yellow-foreign-body-esophagus",
        "category": "yellow",
        "pattern": "Yürüyüş: Düzgün yürüyor ancak göğüs kafesini işaret ediyor. Yüz: Sürekli yutkunma çabası, yutkununca ağrı mimiği (salya akmıyor). Termal: 36.8°C. -> Özofagusta Yabancı Cisim (Tam tıkanıklık yok). ESI 3.",
    },
    {
        "id": "esi-yellow-acute-asthma-talking",
        "category": "yellow",
        "pattern": "Yürüyüş: Hızlı yürüyor, göğüs kafesi inip kalkıyor. Yüz: Nefes darlığı çekiyor ancak tam cümleler kurabiliyor (ağız hareketi), yorgunluk. Termal: 36.9°C. -> Orta Şiddette Astım Atağı. ESI 3.",
    },
    {
        "id": "esi-yellow-complex-abscess-buttock",
        "category": "yellow",
        "pattern": "Yürüyüş: Kalça/Gluteal bölgedeki devasa apse nedeniyle bir bacağı dışa atarak aksama, oturamama. Yüz: Şiddetli lokal ağrı. Termal: Kalçada +3°C sıcak, geniş enflamasyon odağı. -> Gluteal/Perianal Apse. ESI 3.",
    },
    {
        "id": "esi-yellow-biliary-colic-postprandial",
        "category": "yellow",
        "pattern": "Yürüyüş: Karnının üst kısmını tutup kıvrılma, ayakta durabiliyor. Yüz: Yemek sonrası başlayan kıvrandırıcı epigastrik ağrı, terleme. Termal: 36.8°C. -> Biliyer Kolik (Safra Taşı ağrısı). ESI 3.",
    },
    {
        "id": "esi-yellow-syncope-postural",
        "category": "yellow",
        "pattern": "Yürüyüş: Ayağa kalkarken bayıldığını tarif ediyor, şu an yavaş ama düzgün yürüyor. Yüz: Solgunluk (geçmiş), şu an yorgun. Termal: 36.5°C. -> Senkop (Kardiyak/Nörolojik dışlama gerekir). ESI 3.",
    },
    {
        "id": "esi-yellow-spider-bite-systemic",
        "category": "yellow",
        "pattern": "Yürüyüş: Kolunu tutarak sağlam adımlarla giriyor, ancak kol kasılmış. Yüz: Isırık bölgesinde şiddetli ağrı, karın kaslarında kramp mimiği (Karadul zehri). Termal: Isırık yerinde hedef tahtası şeklinde ısı değişimi. -> Toksik Örümcek Isırığı. ESI 3.",
    },
    {
        "id": "esi-yellow-unexplained-gross-hematuria",
        "category": "yellow",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Elinde kırmızı/kanlı idrar kabı taşıyarak endişeli ifade, ağrı mimiği yok. Termal: 36.8°C. -> Ağrısız Makroskopik Hematüri (BT/Sistoskopi vb. gerekir). ESI 3.",
    },
    {
        "id": "esi-yellow-fractured-clavicle",
        "category": "yellow",
        "pattern": "Yürüyüş: Omuz asimetrik, düşen omzunu dirsekten kaldırarak koruma pozisyonu. Yüz: Köprücük kemiğinde lokalize şiddetli ağrı grimesi. Termal: Klavikula üzerinde ısı artışı ve şişlik. -> Klavikula Kırığı. ESI 3.",
    },
    {
        "id": "esi-yellow-severe-sciatica",
        "category": "yellow",
        "pattern": "Yürüyüş: Kalçadan topuğa elektrik çarpar gibi sızıyla bacağını sürükleyerek (antalgik) yürüme. Yüz: Hareketle aniden beliren keskin ağrı mimiği. Termal: 36.6°C. -> Şiddetli Siyatik / Disk Hernisi. ESI 3.",
    },
    {
        "id": "esi-yellow-hyperglycemia-symptomatic",
        "category": "yellow",
        "pattern": "Yürüyüş: Çok halsiz, yavaş, sürekli su içme isteği belirten el hareketleri. Yüz: Ağız kuruluğu mimiği, letarji. Termal: 36.8°C. -> Semptomatik Hiperglisemi (DKA dışlanmalı). ESI 3.",
    },
    {
        "id": "esi-yellow-suspected-bone-infection",
        "category": "yellow",
        "pattern": "Yürüyüş: Bacakta eski yara izi üzeri kızarık, topallıyor. Yüz: Derin, sızlayıcı kronik ağrı grimesi. Termal: Kemik hattı boyunca uzun ve sıcak (+2°C) termal iz. -> Osteomiyelit Şüphesi. ESI 3.",
    },
    {
        "id": "esi-yellow-foreign-body-ear-child",
        "category": "yellow",
        "pattern": "Yürüyüş: Çocuğun yürüyüşü normal. Yüz: Kulağında bir şey (böcek vb.) olduğu için sürekli çığlık atıp kulağını tokatlama. Termal: 36.8°C. -> Kulakta Canlı Yabancı Cisim. ESI 3 (Sedasyon/Müdahale gerektirebilir).",
    },
    {
        "id": "esi-yellow-deep-laceration-hand",
        "category": "yellow",
        "pattern": "Yürüyüş: Elini havaya kaldırıp kanlı havluyla sıkarak yürüme. Yüz: Parmağını hareket ettiremediğini (tendon koptu) gösteren panik. Termal: Elde soğuma yok, sadece kesi hattında termal boşluk. -> Tendon Kesisi Şüphesi. ESI 3.",
    },
    {
        "id": "esi-yellow-toxic-exposure-skin",
        "category": "yellow",
        "pattern": "Yürüyüş: Kimyasal dökülen kolunu vücudundan uzak tutarak panikle yürüme. Yüz: Kimyasal yanığa bağlı şiddetli ağrı grimesi. Termal: Kolda yüzeyel kimyasal reaksiyona bağlı anormal ısı dalgalanması. -> Geniş Kimyasal Yanık. ESI 3.",
    },
    {
        "id": "esi-yellow-preeclampsia-mild",
        "category": "yellow",
        "pattern": "Yürüyüş: Gebe kadın, bacaklarda aşırı ödem (şişlik) nedeniyle ağır yürüme. Yüz: Baş ağrısı ve görme bulanıklığını ifade eden göz kısma eylemi. Termal: 36.7°C. -> Preeklampsi Şüphesi. ESI 3.",
    },
    # ──────────────────────────────────────────────────────── GREEN (211)
    {
        "id": "esi-green-simple-laceration-suture",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız, normal hızda. Yüz: Rahat, parmağındaki küçük kesiğe bakıyor. Termal: 36.5°C. -> Basit Yüzeysel Kesi (Sadece dikiş). ESI 4.",
    },
    {
        "id": "esi-green-simple-ankle-sprain",
        "category": "green",
        "pattern": "Yürüyüş: Ayak bileğini burkmuş, hafif topallıyor ama tam yük verebiliyor. Yüz: Sadece üzerine basarken hafif rahatsızlık. Termal: Ayak bileğinde hafif lokal ısı. -> Basit Bilek Burkulması. ESI 4.",
    },
    {
        "id": "esi-green-uncomplicated-pharyngitis",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Boğazını gösterip yutkunma hareketi, hafif halsiz. Termal: 37.2°C. -> Komplike Olmayan Farenjit / ÜSYE. ESI 5.",
    },
    {
        "id": "esi-green-rhinitis-common-cold",
        "category": "green",
        "pattern": "Yürüyüş: Sağlam, düz adımlar. Yüz: Ara sıra kağıt mendille burnunu siliyor, rahat. Termal: 36.7°C. -> Rinit / Basit Soğuk Algınlığı. ESI 5.",
    },
    {
        "id": "esi-green-routine-prescription",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız, bekleme salonunda rahatça oturuyor. Yüz: Tamamen nötr, şikayeti yokmuş gibi. Termal: 36.6°C. -> Rutin İlaç Yazdırma / Rapor Talebi. ESI 5.",
    },
    {
        "id": "esi-green-impetigo",
        "category": "green",
        "pattern": "Yürüyüş: Sağlam adımlar. Yüz: Çocuğun yüzünde dudağında bal rengi kabuklanmalar, gülümsüyor. Termal: 36.8°C. -> İmpetigo. ESI 5.",
    },
    {
        "id": "esi-green-simple-sunburn",
        "category": "green",
        "pattern": "Yürüyüş: Hafif yavaş ama desteksiz. Yüz: Sırttaki 1. derece güneş yanığına elbise değdikçe hafif yüz ekşitme. Termal: Sırtta geniş alanda yüzeysel sıcaklık (+1°C). -> Basit Güneş Yanığı. ESI 5.",
    },
    {
        "id": "esi-green-local-insect-sting",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Kolunu kaşıyor, arı sokan bölgeye bakıyor, nefes darlığı mimiği yok. Termal: Kolda madeni para büyüklüğünde lokal ısı. -> Lokal Böcek/Arı Sokması. ESI 5.",
    },
    {
        "id": "esi-green-simple-dental-pain",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Yanağını eliyle dışarıdan tutuyor, hafif ağrı ifadesi. Termal: Yüzde şişlik yok, ısı artışı yok. -> Basit Diş Ağrısı (Apse yok). ESI 5.",
    },
    {
        "id": "esi-green-minor-abrasion-pediatric",
        "category": "green",
        "pattern": "Yürüyüş: Dizde basit bir sıyrık, normal yürüyor. Yüz: Ağlamayan, etrafa bakan çocuk. Termal: 36.6°C. -> Minör Abrazyon (Sıyrık). ESI 5.",
    },
    {
        "id": "esi-green-tension-headache",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Kafasının yan/arka tarafını tutarak rutin stres baş ağrısı mimiği yapıyor. Termal: 36.5°C. -> Gerilim Tipi Baş Ağrısı. ESI 5.",
    },
    {
        "id": "esi-green-ring-removal",
        "category": "green",
        "pattern": "Yürüyüş: Parmağına sıkışan yüzüğü göstererek sakince yürüme. Yüz: Ağrı yok, sadece yüzüğü çıkarma çabası. Termal: Parmakta ısı veya soğuma yok (dolaşım bozulmamış). -> Yüzük Çıkarma (Mekanik). ESI 5.",
    },
    {
        "id": "esi-green-simple-back-pain-mechanical",
        "category": "green",
        "pattern": "Yürüyüş: Belini tutarak yavaşça oturup kalkma. Yüz: Ağır kaldırırken kasılma mimiği, radikal ağrı yok. Termal: 36.7°C. -> Basit Mekanik Bel Ağrısı (Kas spazmı). ESI 5.",
    },
    {
        "id": "esi-green-pregnancy-test-visit",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız, karın ağrısı yok. Yüz: Rahat ifade. Termal: 36.5°C. -> Gebelik Testi / Adet Gecikmesi Başvurusu. ESI 4.",
    },
    {
        "id": "esi-green-contact-dermatitis-urticaria",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız, kollarında ve göğsünde kabartılar var. Yüz: Sürekli kollarını kaşıyor, rahatsız. Termal: 36.8°C. -> Basit Kontakt Dermatit / Ürtiker (Nefes darlığı yok). ESI 5.",
    },
    {
        "id": "esi-green-toe-minor-trauma",
        "category": "green",
        "pattern": "Yürüyüş: Ayak baş parmağını sehpaya çarpmış, sekerek giriyor ama tam basabiliyor. Yüz: Anlık acı ifadesi. Termal: Parmakta minimal ısı artışı. -> Ayak Parmağı Minör Travma. ESI 4.",
    },
    {
        "id": "esi-green-routine-suture-removal",
        "category": "green",
        "pattern": "Yürüyüş: Dikiş bölgesini göstererek rahat adımlar. Yüz: Tamamen nötr. Termal: 36.6°C. -> Rutin Dikiş Alımı / Yara Kontrolü. ESI 5.",
    },
    {
        "id": "esi-green-superficial-cornea-fb",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Gözünü sık sık kırpıştırıyor, eliyle göz çevresini ovuşturuyor. Termal: 36.7°C. -> Yüzeyel Kornea Yabancı Cisim / Toz Kaçması. ESI 4.",
    },
    {
        "id": "esi-green-external-ear-otitis",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Kulak yoluna parmağını sokup kaşıma hareketi. Termal: 36.5°C. -> Dış Kulak Yolu Enfeksiyonu (Yüzücü Kulağı). ESI 5.",
    },
    {
        "id": "esi-green-simple-dysmenorrhea",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Karın alt bölgesini tutup dismenore (adet sancısı) grimesi. Termal: 36.6°C. -> Basit Dismenore (Adet Sancısı). ESI 5.",
    },
    {
        "id": "esi-green-uncomplicated-cystitis",
        "category": "green",
        "pattern": "Yürüyüş: Sürekli tuvalete gitme ihtiyacıyla hızlı adımlar. Yüz: İdrar yaparken yanma hissini anlatan mimik. Termal: 36.8°C. -> Komplike Olmayan Sistit (İYE). ESI 4.",
    },
    {
        "id": "esi-green-superficial-splinter",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız, işaret parmağını gösteriyor. Yüz: Yüzeysel batan kıymığa bakarak hafif yüz buruşturma. Termal: Normal. -> Yüzeysel Kıymık Batması. ESI 5.",
    },
    {
        "id": "esi-green-allergic-rhinitis",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Bahar alerjisi nedeniyle sürekli hapşırma, burun silme. Termal: 36.7°C. -> Alerjik Rinit. ESI 5.",
    },
    {
        "id": "esi-green-osteoarthritis-chronic",
        "category": "green",
        "pattern": "Yürüyüş: Uzun süreli kireçlenme öyküsü, kronik alışıldık yavaş yürüyüş. Yüz: Yeni bir travma yok, standart yaşlılık ağrısı yüzü. Termal: Dizlerde kronik hafif ısı artışı. -> Osteoartrit (Kireçlenme) Ağrısı. ESI 5.",
    },
    {
        "id": "esi-green-epistaxis-stopped-child",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız çocuk. Yüz: Burnunda kanama durmuş, etrafta koşuşturuyor, şikayetçi değil. Termal: 36.6°C. -> Evde Durmuş Epistaksis (Kontrol). ESI 5.",
    },
    {
        "id": "esi-green-tick-bite",
        "category": "green",
        "pattern": "Yürüyüş: Sağlam yürüyor, bacağındaki keneyi gösteriyor. Yüz: Tiksinme/Endişe mimiği, ağrı yok. Termal: 36.5°C. -> Kene Isırığı (Kene hala yapışık). ESI 5.",
    },
    {
        "id": "esi-green-oral-candidiasis-aphthous",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Ağız içinde aft veya pamukçuk nedeniyle diliyle yanak içini yoklama. Termal: 36.8°C. -> Oral Kandidiyazis / Aft. ESI 5.",
    },
    {
        "id": "esi-green-subconjunctival-hemorrhage",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız, sağlıklı. Yüz: Gözün beyaz kısmında öksürüğe bağlı kızarıklık, ama görme/ağrı mimiği yok. Termal: Normal. -> Subkonjonktival Kanama. ESI 5.",
    },
    {
        "id": "esi-green-pinworm-pediatric",
        "category": "green",
        "pattern": "Yürüyüş: Çocuğun yürüyüşü normal, poposunu kaşıyor. Yüz: Ateşsiz, rahat ama uykusuz. Termal: 36.5°C. -> Oksiür (Kıl kurdu) Şüphesi. ESI 5.",
    },
    {
        "id": "esi-green-folliculitis-ingrown-hair",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Boynunda tıraş sonrası kıl dönmesini gösteren hafif rahatsızlık. Termal: Normal. -> Follikülit / Kıl Dönmesi. ESI 5.",
    },
    {
        "id": "esi-green-old-contusion-ecchymosis",
        "category": "green",
        "pattern": "Yürüyüş: Sağlam adımlar. Yüz: 1 hafta önceki çarpmanın morluğunu (ekimoz) gösteriyor, ağrı yok. Termal: Moraran bölgede ısı artışı yok, soğuk. -> Eski Kontüzyon / İyileşen Ekimoz. ESI 5.",
    },
    {
        "id": "esi-green-plantar-callus",
        "category": "green",
        "pattern": "Yürüyüş: Ayak tabanına basarken hafif sakınarak yürüme. Yüz: Nasır (kallus) üzerine bastıkça batan bir acı mimiği. Termal: Normal. -> Ayak Tabanında Nasır. ESI 5.",
    },
    {
        "id": "esi-green-verruca-wart",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Parmaktaki et benini / siğili göstererek nötr ifade. Termal: Normal. -> Verruka (Siğil). ESI 5.",
    },
    {
        "id": "esi-green-lost-inhaler-prescription",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız, seyahatte astım ilacını unuttuğunu söylüyor. Yüz: Şu an nefes darlığı çekmiyor, çok rahat. Termal: 36.6°C. -> Kayıp İlaç Yazdırma. ESI 5.",
    },
    {
        "id": "esi-green-simple-constipation",
        "category": "green",
        "pattern": "Yürüyüş: Yavaş adımlar, karnını hafif ovuşturuyor. Yüz: Günlük 3-4 gün süren kabızlık rahatsızlığı. Termal: 36.5°C. -> Kronik/Basit Konstipasyon. ESI 5.",
    },
    {
        "id": "esi-green-reactive-lymphadenopathy",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız, normal hızda. Yüz: Boynundaki ağrısız beze (lenf nodu) bölgesini gösteren meraklı ifade. Termal: 36.8°C. -> Reaktif Lenfadenopati. ESI 5.",
    },
    {
        "id": "esi-green-resolved-urticaria",
        "category": "green",
        "pattern": "Yürüyüş: Sağlam adımlar. Yüz: Evde kurdeşen dökmüş, alerji hapı içip gelmiş, şu an kaşıntısı bitmiş, yüzü rahat. Termal: 36.6°C. -> Çözülmüş Ürtiker Atağı. ESI 5.",
    },
    {
        "id": "esi-green-muscle-cramp-post-sport",
        "category": "green",
        "pattern": "Yürüyüş: Spor sonrası bacağına masaj yaparak hafif sekiyor. Yüz: Anlık giren kas krampının geride bıraktığı sızı ifadesi. Termal: Baldırda hafif ısı artışı. -> Kas Krampı / Laktik Asit birikimi. ESI 5.",
    },
    {
        "id": "esi-green-skin-rash-no-systemic",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Gövdesindeki döküntüye (Pitiryazis Rosea) bakıyor, kaşıntı/ağrı mimiği yok. Termal: 36.5°C. -> Dermatolojik Döküntü (Sistemik bulgusuz). ESI 5.",
    },
    {
        "id": "esi-green-uncomplicated-hemorrhoid",
        "category": "green",
        "pattern": "Yürüyüş: Dışkılama sonrası makatta hafif yanma nedeniyle otururken sakınma. Yüz: Utanma ve hafif rahatsızlık mimiği. Termal: 36.6°C. -> Komplike Olmayan Hemoroid (Basur). ESI 5.",
    },
    {
        "id": "esi-green-seborrheic-dermatitis",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Kepeklenen saç derisini şiddetle kaşıyor, omuzlarında beyaz pullar. Termal: 36.5°C. -> Seboreik Dermatit. ESI 5.",
    },
    {
        "id": "esi-green-mild-gastroenteritis",
        "category": "green",
        "pattern": "Yürüyüş: Yetişkin hasta, bir kez ishal olmuş, sağlam yürüyor. Yüz: Sadece hafif mide gurultusu rahatsızlığı, dehidrate değil. Termal: 36.7°C. -> Hafif Gastroenterit. ESI 5.",
    },
    {
        "id": "esi-green-tetanus-prophylaxis",
        "category": "green",
        "pattern": "Yürüyüş: Paslı çivi deriyi yüzeysel çizmiş, sağlam yürüyor. Yüz: Tetanoz iğnesi sırası bekleyen rahat ifade. Termal: Normal. -> Tetanoz Profilaksisi Aşısı. ESI 4 (Aşı nedeniyle 1 kaynak) veya 5.",
    },
    {
        "id": "esi-green-vaginal-candidiasis",
        "category": "green",
        "pattern": "Yürüyüş: Vajinal kaşıntı hissini bastırmak için adımlarını kısa ve sık atıyor. Yüz: Karın ağrısı yok, sadece lokal rahatsızlık grimesi. Termal: 36.8°C. -> Vajinal Kandidiyazis (Mantar). ESI 5.",
    },
    {
        "id": "esi-green-diaper-rash",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Bebekte ağlama yok, sadece bez bölgesinde pişik (kızarıklık) gösteriliyor. Termal: Bez bölgesinde yüzeyel pişik ısısı. -> Bebek Bezi Dermatiti. ESI 5.",
    },
    {
        "id": "esi-green-ingrown-toenail",
        "category": "green",
        "pattern": "Yürüyüş: Tırnak batması nedeniyle ayakkabısının arkasına basarak (terlik gibi) yürüme. Yüz: Parmağa dokunuldukça hafif sızı. Termal: Ayak baş parmağında 1 cm'lik ısı artışı. -> Batık Tırnak (Minör enfeksiyon). ESI 4.",
    },
    {
        "id": "esi-green-friction-blister",
        "category": "green",
        "pattern": "Yürüyüş: Yeni ayakkabı vurması nedeniyle topukta su toplaması, sekiyor. Yüz: Sızı grimesi. Termal: Topukta lokal ısı. -> Ayak Kabarcığı (Friction blister). ESI 5.",
    },
    {
        "id": "esi-green-resolved-anxiety-hyperventilation",
        "category": "green",
        "pattern": "Yürüyüş: Panik atak sonrası sakinleşmiş, odada tamamen rahat oturuyor/yürüyor. Yüz: Nefes darlığı veya korku mimiği kalmamış, yorgun ama stabil. Termal: 36.5°C. -> Çözülmüş Hiperventilasyon / Anksiyete. ESI 5.",
    },
    {
        "id": "esi-green-eye-injury",
        "category": "green",
        "pattern": "Göz ağrısı + gözü oğuşturma/kapatma refleksi yüzde + normal yürüyüş kornea hasarı veya yabancı cisim. ESI Seviye 4.",
    },
    {
        "id": "esi-green-mild-pain",
        "category": "green",
        "pattern": "Orta düzeyde ağrı yüz ifadesine yansımış (kaş çatma, grimase) + normal yürüyüş. ESI Seviye 4-5; ağrı değerlendirmesi ve takip.",
    },
    {
        "id": "esi-green-allergic-reaction",
        "category": "green",
        "pattern": "Lokal alerjik reaksiyon + yüzde kaşıma/rahatsızlık + normal yürüyüş sistemik belirti yok. ESI Seviye 4, antihistamin.",
    },
    {
        "id": "esi-green-stable",
        "category": "green",
        "pattern": "Dik ve simetrik yürüyüş, normal vücut ısısı ve rahat yüz ifadesi ESI Seviye 4-5 kapsamındadır; rutin akışta değerlendirilir.",
    },
    {
        "id": "esi-green-minor-laceration",
        "category": "green",
        "pattern": "Küçük yüzeysel kesi + aktif kanama yok + vital bulgular normal. ESI Seviye 4-5, yara bakımı ve pansuman yeterli.",
    },
    {
        "id": "esi-green-sprain",
        "category": "green",
        "pattern": "Ayak bileği burkması + hafif şişlik + yük verebiliyor + vital normal. ESI Seviye 5, Ottawa kuralları negatif.",
    },
    {
        "id": "esi-green-cold-symptoms",
        "category": "green",
        "pattern": "Hafif soğuk algınlığı belirtileri + normal yürüyüş + yüzde minimal rahatsızlık + ateş yok. ESI Seviye 5, semptomatik tedavi.",
    },
    {
        "id": "esi-green-routine-checkup",
        "category": "green",
        "pattern": "Rutin kontrol: tam bağımsız yürüyüş, rahat yüz ifadesi, normal vücut ısısı. ESI Seviye 5.",
    },
    {
        "id": "esi-green-minor-contusion",
        "category": "green",
        "pattern": "Küçük çürük veya ezik + ağrı yok veya minimal + normal yürüyüş ESI Seviye 5, buz ve istirahat yeterli.",
    },
    {
        "id": "esi-green-insect-bite",
        "category": "green",
        "pattern": "Böcek ısırığı + lokal kızarıklık + sistemik belirti yok + normal yürüyüş ve yüz ifadesi. ESI Seviye 5.",
    },
    {
        "id": "esi-green-medication-refill",
        "category": "green",
        "pattern": "Kronik ilaç yenilemesi için başvuru + tam bağımsız yürüyüş + rahat yüz + normal ısı. ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-headache",
        "category": "green",
        "pattern": "Hafif baş ağrısı + yüzde minimal rahatsızlık + normal dik yürüyüş + ateş yok. ESI Seviye 4-5, analjezi.",
    },
    {
        "id": "esi-green-minor-eye-irritation",
        "category": "green",
        "pattern": "Göz kızarıklığı + hafif kaşıma hareketi yüzde + normal yürüyüş + ateş yok. ESI Seviye 5, göz damlası.",
    },
    {
        "id": "esi-green-sore-throat",
        "category": "green",
        "pattern": "Boğaz ağrısı + yüzde hafif rahatsızlık ifadesi + normal yürüyüş + ateş 37.5°C altı. ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-ear-pain",
        "category": "green",
        "pattern": "Kulak ağrısı + kulağını tutan jest + bağımsız yürüyüş + ateş yok otit şüphesi. ESI Seviye 4-5, KBB değerlendirmesi.",
    },
    {
        "id": "esi-green-mild-nausea",
        "category": "green",
        "pattern": "Hafif bulantı + yüzde iştahsız ifade + normal yürüyüş + ateş yok gastroenterit veya beslenme bozukluğu. ESI Seviye 5.",
    },
    {
        "id": "esi-green-wrist-pain",
        "category": "green",
        "pattern": "Bilek ağrısı + elde hafif koruyucu pozisyon + normal yürüyüş tendinit veya hafif burkma. ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-lower-back-mild",
        "category": "green",
        "pattern": "Hafif bel ağrısı + yürüyüş normal ama hafif gergin + yüzde minimal rahatsızlık. ESI Seviye 4-5, istirahat.",
    },
    {
        "id": "esi-green-skin-rash-mild",
        "category": "green",
        "pattern": "Lokalize döküntü + kaşıntı + sistemik belirti yok + normal yürüyüş alerjik kontakt dermatit. ESI Seviye 5, topikal tedavi.",
    },
    {
        "id": "esi-green-vaccination",
        "category": "green",
        "pattern": "Aşı uygulaması + tam bağımsız yürüyüş + rahat yüz ifadesi + normal vücut ısısı. ESI Seviye 5.",
    },
    {
        "id": "esi-green-blood-pressure-check",
        "category": "green",
        "pattern": "Tansiyon kontrolü + semptom yok + normal yürüyüş + rahat yüz ifadesi. ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-diarrhea",
        "category": "green",
        "pattern": "Hafif ishal + yüzde minimal rahatsızlık + normal yürüyüş + ateş yok + dehidrasyon bulgusu yok. ESI Seviye 5.",
    },
    {
        "id": "esi-green-neck-stiffness-mild",
        "category": "green",
        "pattern": "Hafif boyun tutukluğu (kas gerilmesi) + yavaş ama bağımsız yürüyüş + ateş yok + rahat yüz. ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-finger-injury",
        "category": "green",
        "pattern": "Parmak yaralanması + parmağını koruyan jest + normal yürüyüş + ateş yok. ESI Seviye 4-5, radyoloji.",
    },
    {
        "id": "esi-green-cough-mild",
        "category": "green",
        "pattern": "Hafif öksürük + yüzde minimal rahatsızlık + normal yürüyüş + ateş yok veya 37.5°C altı. ESI Seviye 5.",
    },
    {
        "id": "esi-green-abdominal-mild",
        "category": "green",
        "pattern": "Hafif karın ağrısı + yüzde orta rahatsızlık + bağımsız normal yürüyüş + ateş yok. ESI Seviye 4-5, gözlem.",
    },
    {
        "id": "esi-green-pediatric-stable",
        "category": "green",
        "pattern": "Çocuk hasta tam bağımsız hareket + aktif yüz ifadesi + normal ısı vital sinyaller normal sınırda. ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-sport-injury-minor",
        "category": "green",
        "pattern": "Spor yaralanması + hafif topallama + ağrı yüze hafif yansımış + ateş yok. ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-knee-pain-mild",
        "category": "green",
        "pattern": "Hafif diz ağrısı + yük verebiliyor + yüzde minimal rahatsızlık + normal ısı. ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-shoulder-mild",
        "category": "green",
        "pattern": "Hafif omuz ağrısı + kolu hafif koruyan yürüyüş + yüzde minimal rahatsızlık + normal ısı. ESI Seviye 5.",
    },
    {
        "id": "esi-green-anxiety-mild",
        "category": "green",
        "pattern": "Hafif anksiyete + yüzde gergin ama kontrollü ifade + normal yürüyüş + normal ısı. ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-foreign-body-skin",
        "category": "green",
        "pattern": "Deri altı yabancı cisim (diken vs.) + lokal ağrı jesti + normal yürüyüş + ateş yok. ESI Seviye 5.",
    },
    {
        "id": "esi-green-ingrown-nail",
        "category": "green",
        "pattern": "Batık tırnak + hafif topallama + yüzde minimal rahatsızlık + ateş yok. ESI Seviye 4, küçük cerrahi.",
    },
    {
        "id": "esi-green-urticaria-mild",
        "category": "green",
        "pattern": "Yaygın ürtiker + kaşıma jesti + normal yürüyüş + ateş yok + yüzde hafif rahatsızlık. ESI Seviye 4-5, antihistamin.",
    },
    {
        "id": "esi-green-chronic-stable",
        "category": "green",
        "pattern": "Bilinen kronik hastalık kontrolü + tam bağımsız yürüyüş + rahat yüz ifadesi + normal ısı. ESI Seviye 5.",
    },
    {
        "id": "esi-green-wound-check",
        "category": "green",
        "pattern": "Yara kontrolü + iyileşme süreci normal + bağımsız yürüyüş + ateş yok + rahat yüz. ESI Seviye 5.",
    },
    {
        "id": "esi-green-elbow-pain-mild",
        "category": "green",
        "pattern": "Hafif dirsek ağrısı + kolu hafif sallayan yürüyüş + yüzde minimal rahatsızlık + ateş yok. ESI Seviye 5.",
    },
    {
        "id": "esi-green-prescription-request",
        "category": "green",
        "pattern": "Reçete talebi + tam bağımsız yürüyüş + rahat yüz ifadesi + normal vücut ısısı. ESI Seviye 5.",
    },
    {
        "id": "esi-green-lab-result",
        "category": "green",
        "pattern": "Tahlil sonucu için başvuru + tam sağlıklı yürüyüş + rahat yüz + normal ısı. ESI Seviye 5.",
    },
    {
        "id": "esi-green-foot-blister",
        "category": "green",
        "pattern": "Ayak kabarcığı + hafif topallama + yüzde minimal rahatsızlık + ateş yok. ESI Seviye 5, yara bakımı.",
    },
    {
        "id": "esi-green-splinter",
        "category": "green",
        "pattern": "Kıymık + bölgesel ağrı jesti + normal yürüyüş + ateş yok + rahat yüz. ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-sunburn",
        "category": "green",
        "pattern": "Hafif güneş yanığı + yüzde minimal rahatsızlık + normal yürüyüş + ateş yok veya 37.5°C altı. ESI Seviye 5.",
    },
    {
        "id": "esi-green-dressing-change",
        "category": "green",
        "pattern": "Pansuman değişimi + yara iyileşiyor + bağımsız yürüyüş + ateş yok + rahat yüz ifadesi. ESI Seviye 5.",
    },
    {
        "id": "esi-green-toe-injury",
        "category": "green",
        "pattern": "Parmak yaralanması + hafif topallama + yüzde orta ağrı ifadesi + ateş yok. ESI Seviye 4, radyoloji.",
    },
    {
        "id": "esi-green-mild-nausea-no-distress",
        "category": "green",
        "pattern": "Bağımsız ve stabil yürüyüş + yüzde hafif rahatsız ama sakin ifade + termal normal. Bulantı şikayeti; vital sinyaller normal. ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-mild-diarrhea-stable",
        "category": "green",
        "pattern": "Normal yürüyüş, dik postür + yüzde rahat ifade + termal normal. Hafif ishal şikayeti, dehidratasyon bulgusu yok. ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-conjunctivitis-viral",
        "category": "green",
        "pattern": "Bağımsız yürüyüş, dik postür + yüzde göz ovma hareketi dışında rahat ifade + termal normal. Viral konjonktivit; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-nail-injury-minor",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde hafif rahatsızlık ifadesi + termal normal. Tırnak yaralanması (parsiyel avülsiyon); ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-finger-burn-minor",
        "category": "green",
        "pattern": "Bağımsız yürüyüş + yüzde hafif ağrı ifadesi, genel görünüm sakin + termal kamerada parmak ucunda küçük lokal ısı artışı. 1. derece parmak yanığı; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-ear-wax-removal",
        "category": "green",
        "pattern": "Normal yürüyüş, dik ve simetrik postür + yüzde rahat ve sakin ifade + termal normal. Kulak tıkacı çıkartma; ESI Seviye 5.",
    },
    {
        "id": "esi-green-knee-bruise-minor",
        "category": "green",
        "pattern": "Hafif yavaşlamış ama bağımsız yürüyüş + yüzde rahat ifade + termal kamerada diz bölgesinde minimal ısı artışı. Küçük diz kontüzyonu; ESI Seviye 5.",
    },
    {
        "id": "esi-green-chronic-shoulder-pain-stable",
        "category": "green",
        "pattern": "Normal yürüyüş, hafif kol koruma postu + yüzde sakin, kronik ağrıya alışık ifade + termal normal. Kronik omuz ağrısı kontrolü; ESI Seviye 5.",
    },
    {
        "id": "esi-green-flu-symptoms-mild",
        "category": "green",
        "pattern": "Bağımsız yürüyüş + yüzde hafif bitkin ama stabil ifade + termal kamerada alın sıcaklığı sınırda (37.5°C). Hafif grip belirtileri; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-mild-allergic-reaction-resolved",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde rahat ifade + termal normal. Hafif allerjik reaksiyon, poliklinik tedavisiyle geçmiş; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-wrist-sprain-minor",
        "category": "green",
        "pattern": "Normal yürüyüş, bileği hafif destekleyen postür + yüzde sakin ifade + termal kamerada el bileğinde minimal ısı artışı. Hafif bilek burkulması; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-minor-facial-bruise",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade, minimal hassasiyet + termal kamerada yüzde hafif lokal ısı artışı. Küçük yüz kontüzyonu; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-sinus-congestion-stable",
        "category": "green",
        "pattern": "Bağımsız yürüyüş + yüzde hafif rahatsızlık, burun çekme + termal normal. Sinüzit/konjesyon; vital sinyaller stabil. ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-minor-lip-laceration",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade + termal kamerada dudak bölgesinde minimal ısı artışı. Küçük dudak laserasyonu; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-herpes-labialis-cold-sore",
        "category": "green",
        "pattern": "Normal yürüyüş, dik postür + yüzde rahat genel ifade + termal kamerada dudak çevresinde çok lokal minimal ısı artışı. Herpes labialis; ESI Seviye 5.",
    },
    {
        "id": "esi-green-sebaceous-cyst-check",
        "category": "green",
        "pattern": "Bağımsız ve stabil yürüyüş + yüzde rahat ifade + termal normal. Sebase kist kontrolü; acil özellik yok. ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-chemical-splash-rinsed",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde hafif kızarık göz, sakin genel ifade + termal kamerada göz çevresinde çok hafif ısı artışı. Hafif kimyasal sıçrama, yıkandı; ESI Seviye 4.",
    },
    {
        "id": "esi-green-mild-vertigo-resolved",
        "category": "green",
        "pattern": "Normale dönmüş yürüyüş, hafif yavaş ama stabil + yüzde rahat ifade + termal normal. Geçici hafif baş dönmesi, çözüldü; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-finger-sprain",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür, parmak sarılı + yüzde sakin ifade + termal kamerada parmakta minimal ısı artışı. Parmak burkulması; ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-gas-abdominal-pain",
        "category": "green",
        "pattern": "Bağımsız yürüyüş + yüzde hafif rahatsızlık ifadesi + termal normal. Hafif gaz ağrısı; akut batın bulgusu yok, vital stabil. ESI Seviye 5.",
    },
    {
        "id": "esi-green-minor-scalp-laceration",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade + termal kamerada saçlı deride lokal ısı artışı. Küçük saçlı deri laserasyonu; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-elbow-minor-trauma",
        "category": "green",
        "pattern": "Normal yürüyüş, dirsek hafif bükülü korumalı postür + yüzde sakin ifade + termal kamerada dirsekte hafif ısı artışı. Hafif dirsek travması; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-nasal-fracture-no-displacement",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde hafif ağrılı ifade, burnunu tutuyor + termal kamerada burun çevresinde hafif ısı artışı. Deplase olmayan burun kırığı; ESI Seviye 4.",
    },
    {
        "id": "esi-green-mild-tonsillitis",
        "category": "green",
        "pattern": "Bağımsız yürüyüş + yüzde hafif rahatsızlık, yutkunma güçlüğü mimikleri + termal kamerada alın normal-sınır. Hafif tonsillit; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-minor-finger-fracture",
        "category": "green",
        "pattern": "Normal yürüyüş, parmak atellendi + yüzde sakin ifade + termal kamerada parmakta minimal ısı artışı. Küçük parmak kırığı (atel); ESI Seviye 4.",
    },
    {
        "id": "esi-green-mild-reflux-complaint",
        "category": "green",
        "pattern": "Bağımsız ve stabil yürüyüş + yüzde hafif rahatsızlık ifadesi + termal normal. Hafif gastroözofageal reflü şikayeti; ESI Seviye 5.",
    },
    {
        "id": "esi-green-cat-scratch-minor",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade + termal kamerada tırmık izinde minimal ısı artışı. Kedi tırmığı, yüzeyel; ESI Seviye 5.",
    },
    {
        "id": "esi-green-old-ankle-chronic-pain",
        "category": "green",
        "pattern": "Hafif topallayan ama bağımsız yürüyüş + yüzde sakin, kronik ağrıya alışık ifade + termal normal. Eski ayak bileği ağrısı kontrolü; ESI Seviye 5.",
    },
    {
        "id": "esi-green-postop-wound-check",
        "category": "green",
        "pattern": "Normal veya hafif kısıtlı yürüyüş + yüzde rahat ifade + termal kamerada ameliyat bölgesinde minimal ısı değişimi. Postoperatif yara kontrolü; ESI Seviye 5.",
    },
    {
        "id": "esi-green-child-mild-fever-no-distress",
        "category": "green",
        "pattern": "Çocuk: bağımsız hareket, oyun oynuyor + yüzde rahat ifade + termal kamerada hafif alın sıcaklığı artışı (37.5-38°C). ESI Seviye 4-5; poliklinik takibi yeterli.",
    },
    {
        "id": "esi-green-mild-dehydration-drinking",
        "category": "green",
        "pattern": "Bağımsız yürüyüş, dik postür + yüzde hafif bitkin ama stabil ifade + termal normal. Hafif dehidrasyon, oral alım yapıyor; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-sport-bruise-minor",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde sakin ifade + termal kamerada kontüzyon bölgesinde minimal ısı artışı. Spor kaynaklı küçük kontüzyon; ESI Seviye 5.",
    },
    {
        "id": "esi-green-eyebrow-laceration-minor",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin genel ifade, kaş yaralanması lokal + termal kamerada kaş çevresinde hafif ısı artışı. Kaş laserasyonu; ESI Seviye 4.",
    },
    {
        "id": "esi-green-mild-neck-muscle-stiffness",
        "category": "green",
        "pattern": "Normal yürüyüş, baş dönüşü kısıtlı postür + yüzde hafif rahatsızlık + termal kamerada boyun kaslarında minimal ısı artışı. Kas kökenli boyun tutukluğu; ESI Seviye 5.",
    },
    {
        "id": "esi-green-plantar-fasciitis-chronic",
        "category": "green",
        "pattern": "Hafif topallayan bağımsız yürüyüş, sabah adımı ağır + yüzde sakin kronik ifade + termal normal. Plantar fasiit; ESI Seviye 5.",
    },
    {
        "id": "esi-green-fingernail-subungual-hematoma",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde hafif rahatsız ifade + termal kamerada parmak ucunda lokal ısı artışı. Tırnak altı hematomu; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-mild-eczema-flare",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade + termal kamerada egzama bölgesinde lokal hafif ısı artışı. Hafif egzama alevlenmesi; ESI Seviye 5.",
    },
    {
        "id": "esi-green-eyelid-minor-trauma",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde sakin ifade, gözkapağında şişlik lokal + termal kamerada gözkapağında minimal ısı artışı. Hafif göz kapağı travması; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-foot-pain-chronic-mild",
        "category": "green",
        "pattern": "Bağımsız yürüyüş, hafif yavaş adım + yüzde sakin kronik ifade + termal normal. Kronik hafif ayak ağrısı; ESI Seviye 5.",
    },
    {
        "id": "esi-green-small-abscess-minor",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade + termal kamerada abse bölgesinde lokal ısı artışı. Küçük yüzeyel abse; ESI Seviye 4.",
    },
    {
        "id": "esi-green-tinea-fungal-skin",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde rahat ifade + termal normal. Yüzeyel mantar enfeksiyonu (tinea); ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-conjunctivitis-allergic",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde göz ovma, hafif rahatsız ifade + termal normal. Allerjik konjonktivit; ESI Seviye 5.",
    },
    {
        "id": "esi-green-elbow-abrasion-minor",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade + termal kamerada dirsek abrazyonunda minimal ısı artışı. Küçük dirsek abrazyonu; ESI Seviye 5.",
    },
    {
        "id": "esi-green-chest-wall-musculoskeletal",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde hafif ağrılı ifade (hareketle) + termal normal. Kas-iskelet kaynaklı göğüs duvarı ağrısı, vital stabil; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-tmj-mild-pain",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde hafif yüz gerginliği, çene kasları gergin + termal kamerada çene ekleminde lokal minimal ısı artışı. Hafif TME ağrısı; ESI Seviye 5.",
    },
    {
        "id": "esi-green-superficial-phlebitis",
        "category": "green",
        "pattern": "Normal yürüyüş, bacakta lokal hassasiyet + yüzde sakin ifade + termal kamerada bacak veninde lineer ısı artışı. Yüzeyel flebit; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-minor-nosebleed-resolved-adult",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade + termal normal. Evde durmuş burun kanaması; ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-fatigue-checkup",
        "category": "green",
        "pattern": "Bağımsız yürüyüş, hafif yavaş adım + yüzde yorgun ama stabil ifade + termal normal. Hafif yorgunluk şikayeti, akut patoloji yok; ESI Seviye 5.",
    },
    {
        "id": "esi-green-ear-pain-resolved",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde rahat ifade + termal normal. Geçmiş kulak ağrısı kontrolü; ESI Seviye 5.",
    },
    {
        "id": "esi-green-hip-bruise-walking-fine",
        "category": "green",
        "pattern": "Normal yürüyüş, hafif yavaş + yüzde sakin ifade + termal kamerada kalça bölgesinde minimal ısı artışı. Düşme sonrası hafif kalça kontüzyonu, yürüyüş normal; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-wrist-tendinitis-mild",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde sakin ifade + termal kamerada el bileği tendon hattında minimal ısı artışı. Hafif bilek tendiniti; ESI Seviye 5.",
    },
    {
        "id": "esi-green-achilles-mild-pain",
        "category": "green",
        "pattern": "Hafif topallayan bağımsız yürüyüş + yüzde sakin kronik ifade + termal kamerada Aşil tendon bölgesinde minimal ısı artışı. Hafif Aşil tendon ağrısı; ESI Seviye 5.",
    },
    {
        "id": "esi-green-eye-strain-mild",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde hafif göz kısma, gözler ovuluyor + termal normal. Göz yorgunluğu; ESI Seviye 5.",
    },
    {
        "id": "esi-green-minor-knee-contusion",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde sakin ifade + termal kamerada diz üzerinde minimal lokal ısı artışı. Küçük diz kontüzyonu; ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-hand-eczema",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade + termal kamerada elde lokal minimal ısı artışı. Hafif el egzaması; ESI Seviye 5.",
    },
    {
        "id": "esi-green-routine-blood-pressure-check",
        "category": "green",
        "pattern": "Normal yürüyüş, dik ve simetrik postür + yüzde tamamen rahat ifade + termal normal. Rutin kontrol; ESI Seviye 5.",
    },
    {
        "id": "esi-green-minor-shoulder-blade-pain",
        "category": "green",
        "pattern": "Normal yürüyüş, hafif omuz düşük postür + yüzde sakin ifade + termal kamerada kürek kemiği bölgesinde çok hafif ısı artışı. Hafif sırt ağrısı; ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-rosacea-flare",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde yüzeyel kızarıklık görünümü, genel ifade sakin + termal kamerada yüzde hafif ısı artışı. Rosacea alevlenmesi; ESI Seviye 5.",
    },
    {
        "id": "esi-green-pediatric-minor-cut-hand",
        "category": "green",
        "pattern": "Çocuk: bağımsız yürüyüş, aktif hareket + yüzde hafif ağlamaklı ifade, sakinleşiyor + termal normal. Parmak küçük kesisi; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-routine-vaccination-visit",
        "category": "green",
        "pattern": "Normal yürüyüş, dik postür + yüzde rahat sakin ifade + termal normal. Rutin aşı uygulaması; ESI Seviye 5.",
    },
    {
        "id": "esi-green-insomnia-complaint",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde yorgun ama sakin ifade + termal normal. Uyku sorunu şikayeti; akut patoloji yok, ESI Seviye 5.",
    },
    {
        "id": "esi-green-minor-dog-bite-stable",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde hafif endişeli ama sakin ifade + termal kamerada ısırık bölgesinde minimal ısı artışı. Küçük köpek ısırığı, yüzeyel; ESI Seviye 4.",
    },
    {
        "id": "esi-green-mild-acne-treatment",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade + termal kamerada yüzde çok hafif dağınık ısı artışı. Akne tedavisi başvurusu; ESI Seviye 5.",
    },
    {
        "id": "esi-green-pregnancy-first-trimester-stable",
        "category": "green",
        "pattern": "Normal yürüyüş, dik postür + yüzde rahat ifade + termal normal. İlk trimester rutin gebelik başvurusu, bulgu yok; ESI Seviye 5.",
    },
    {
        "id": "esi-green-minor-lip-burn-hot-liquid",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde hafif rahatsızlık, dudakta ağrı mimikleri + termal kamerada dudak çevresinde minimal ısı artışı. Sıcak içecek dudak yanığı; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-chronic-knee-pain-routine",
        "category": "green",
        "pattern": "Bağımsız yürüyüş, hafif topallayan + yüzde sakin kronik ifade + termal kamerada diz bölgesinde çok hafif ısı artışı. Kronik diz ağrısı rutin kontrolü; ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-psoriasis-flare",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade + termal kamerada psoriasis plaklarında lokal ısı artışı. Hafif psoriasis alevlenmesi; ESI Seviye 5.",
    },
    {
        "id": "esi-green-minor-head-bump-alert",
        "category": "green",
        "pattern": "Normal yürüyüş, tam bilinçli + yüzde hafif endişeli ama sakin ifade + termal normal. Küçük kafa çarpması, bilinç kaybı yok; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-pediatric-otitis-media-stable",
        "category": "green",
        "pattern": "Çocuk: bağımsız yürüyüş + yüzde hafif huzursuz ama aktif ifade + termal kamerada kulak bölgesinde çok hafif ısı artışı. Orta kulak iltihabı şüphesi; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-mild-urticaria-localized",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde hafif kaşıntı ifadesi + termal kamerada ürtiker bölgesinde lokal ısı artışı. Lokalize ürtiker; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-minor-ankle-recheck",
        "category": "green",
        "pattern": "Normale dönmüş yürüyüş + yüzde rahat ifade + termal normal. İyileşmekte olan ayak bileği burkulması kontrolü; ESI Seviye 5.",
    },
    {
        "id": "esi-green-superficial-wound-infection-mild",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade + termal kamerada yara bölgesinde lokal ısı artışı. Yüzeyel yara yeri enfeksiyonu, sistemik belirti yok; ESI Seviye 4.",
    },
    {
        "id": "esi-green-medication-side-effect-query",
        "category": "green",
        "pattern": "Normal yürüyüş, dik postür + yüzde sakin ve endişeli ifade + termal normal. İlaç yan etkisi sorgulama; vital stabil. ESI Seviye 5.",
    },
    {
        "id": "esi-green-chronic-back-pain-follow-up",
        "category": "green",
        "pattern": "Hafif korumalı ama bağımsız yürüyüş + yüzde sakin kronik ifade + termal normal. Kronik bel ağrısı takip kontrolü; ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-elbow-tendinitis",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde sakin ifade + termal kamerada dirsek lateral/medial epikondil bölgesinde minimal ısı artışı. Hafif dirsek tendiniti; ESI Seviye 5.",
    },
    {
        "id": "esi-green-minor-toe-blister",
        "category": "green",
        "pattern": "Normal yürüyüş, hafif yavaş + yüzde rahat ifade + termal kamerada parmak ucunda minimal ısı artışı. Ayak parmağı sürtünme kabarcığı; ESI Seviye 5.",
    },
    {
        "id": "esi-green-pediatric-fall-alert-walking",
        "category": "green",
        "pattern": "Çocuk: düşme sonrası bağımsız yürüyor, denge normal + yüzde ağlamaklı ama sakinleşiyor + termal normal. Küçük çocuk düşmesi, bilinç tam; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-mild-thumb-sprain",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde sakin ifade + termal kamerada başparmakta minimal ısı artışı. Hafif başparmak burkulması; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-routine-cast-check",
        "category": "green",
        "pattern": "Alçılı uzuvla bağımsız yürüyüş + yüzde rahat ifade + termal normal. Rutin alçı kontrolü; ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-groin-strain",
        "category": "green",
        "pattern": "Hafif korumalı ama bağımsız yürüyüş + yüzde sakin ifade + termal kamerada kasık bölgesinde minimal ısı artışı. Hafif kasık zorlanması; ESI Seviye 5.",
    },
    {
        "id": "esi-green-simple-keloid-check",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde rahat ifade + termal normal. Keloid oluşumu kontrolü; acil özellik yok. ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-sunstroke-recovered",
        "category": "green",
        "pattern": "Bağımsız yürüyüş, hafif yavaş + yüzde hafif yorgun ama stabil ifade + termal kamerada alın sıcaklığı normale dönmüş. Hafif güneş çarpması, iyileşmiş; ESI Seviye 4-5.",
    },
    {
        "id": "esi-green-insect-bite-local-reaction",
        "category": "green",
        "pattern": "Normal yürüyüş ve postür + yüzde sakin ifade + termal kamerada böcek ısırığı bölgesinde lokal ısı artışı. Lokal böcek ısırığı reaksiyonu; ESI Seviye 5.",
    },
    {
        "id": "esi-green-pediatric-diaper-rash-severe",
        "category": "green",
        "pattern": "Bebek/küçük çocuk: ebeveynle taşınıyor, normal aktivite + yüzde hafif ağlama + termal kamerada bez bölgesinde lokal ısı artışı. Bez döküntüsü; ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-calf-cramp",
        "category": "green",
        "pattern": "Bağımsız yürüyüş, hafif gergin bacak adımı + yüzde sakin ifade + termal kamerada baldırda hafif ısı artışı. Baldır krampı, geçiyor; ESI Seviye 5.",
    },
    {
        "id": "esi-green-simple-rash-child-stable",
        "category": "green",
        "pattern": "Çocuk: bağımsız hareket, oyun oynuyor + yüzde rahat ifade + termal normal. Basit döküntü, sistem bulgusu yok; ESI Seviye 5.",
    },
    {
        "id": "esi-green-mild-anxiety-calm-presentation",
        "category": "green",
        "pattern": "Normal yürüyüş + yüzde gergin ama kontrollü ifade + termal normal. Hafif anksiyete başvurusu, vital stabil, fiziksel bulgu yok; ESI Seviye 5.",
    },
    {
        "id": "esi-green-lost-prescription-stable",
        "category": "green",
        "pattern": "Normal yürüyüş, dik postür + yüzde tamamen rahat ifade + termal normal. Kayıp/biten ilaç reçetesi; ESI Seviye 5.",
    },
    {
        "id": "esi-green-superficial-cat-scratch",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Elindeki yüzeysel kedi tırmığına bakıyor, rahat. Termal: Normal. -> Yüzeysel Kedi Tırmığı. ESI 5.",
    },
    {
        "id": "esi-green-minor-toe-stub",
        "category": "green",
        "pattern": "Yürüyüş: Ayak serçe parmağını çarpmış, ayakkabısını çıkarmış, sekerek yürüme. Yüz: Anlık acı sonrası rahatlama. Termal: Parmak ucunda hafif lokal ısı. -> Ayak Parmağı Çarpması (X-ray için). ESI 4.",
    },
    {
        "id": "esi-green-medication-refill-routine",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız, normal tempo. Yüz: Bekleme salonunda sıkılmış ama sağlıklı ifade. Termal: 36.6°C. -> Rutin İlaç Yazdırma. ESI 5.",
    },
    {
        "id": "esi-green-sunburn-shoulders",
        "category": "green",
        "pattern": "Yürüyüş: Dik duruyor, omuzlarını oynatmaktan kaçınıyor. Yüz: Omuzlara dokunulunca hafif sızlama grimesi. Termal: Omuzlarda geniş alanda yüzeysel (+1°C) sıcaklık. -> 1. Derece Güneş Yanığı. ESI 5.",
    },
    {
        "id": "esi-green-mild-viral-sore-throat",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Yutkunurken boğazını tutma, hafif ses kısıklığı (mimik olarak ağzı az açma). Termal: 37.1°C. -> Farenjit (Viral). ESI 5.",
    },
    {
        "id": "esi-green-splinter-finger",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Parmağına batan küçük kıymığı çıkarmaya çalışma mimiği. Termal: Normal. -> Yüzeysel Kıymık (Kesiği yok). ESI 5.",
    },
    {
        "id": "esi-green-poison-ivy-rash",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Bacaklarındaki döküntüleri sürekli kaşıyor, kızarık. Termal: 36.8°C. -> Zehirli Sarmaşık / Kontakt Dermatit. ESI 5.",
    },
    {
        "id": "esi-green-mild-earache-otitis-externa",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Kulak kepçesine dokununca sızlama mimiği. Termal: 36.7°C. -> Dış Kulak Yolu Enfeksiyonu. ESI 5.",
    },
    {
        "id": "esi-green-trigger-finger",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Kilitlenen parmağını (tetik parmak) diğer eliyle açarken çıkan klik sesine bağlı hafif sızı mimiği. Termal: Normal. -> Tetik Parmak (Kronik). ESI 5.",
    },
    {
        "id": "esi-green-old-contusion",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Bacağındaki sararmış/yeşermiş eski morluğu (ekimoz) gösteriyor, ağrı yok. Termal: Lokal ısı artışı yok. -> Eski Çürük/Kontüzyon. ESI 5.",
    },
    {
        "id": "esi-green-dandruff-itch",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Saçlı deriyi sürekli ve şiddetle kaşıma. Termal: 36.6°C. -> Seboreik Dermatit. ESI 5.",
    },
    {
        "id": "esi-green-mild-rhinitis",
        "category": "green",
        "pattern": "Yürüyüş: Sağlam yürüme. Yüz: Sürekli burun çekme, mendille hapşırma, kırmızı burun ucu. Termal: 36.8°C. -> Soğuk Algınlığı / Rinit. ESI 5.",
    },
    {
        "id": "esi-green-insect-bite-mosquito",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Kolundaki sinek/böcek ısırığını sürekli kaşıma. Termal: Lokal minik kızarıklık ısısı. -> Basit Böcek Isırığı. ESI 5.",
    },
    {
        "id": "esi-green-chronic-knee-osteoarthritis",
        "category": "green",
        "pattern": "Yürüyüş: Yaşlı hasta, dizleri hafif bükük, alışıldık kronik yavaş yürüme. Yüz: Yeni bir ağrı yok, sadece yaşlılık/eklem sızısı yüzü. Termal: Dizlerde hafif kronik ısı. -> Osteoartrit. ESI 5.",
    },
    {
        "id": "esi-green-superficial-burn-finger",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Sıcak tencereye değen parmağını üfleme/soğutma çabası, bül yok. Termal: Parmakta çok küçük 1. derece yanık ısısı. -> Minör Yanık. ESI 5.",
    },
    {
        "id": "esi-green-mild-back-muscle-spasm",
        "category": "green",
        "pattern": "Yürüyüş: Belini tutarak dikkatli oturup kalkma. Yüz: Yanlış hareket sonrası sırtta giren anlık kas spazmı grimesi, nörolojik kayıp yok. Termal: 36.7°C. -> Basit Kas Spazmı. ESI 5.",
    },
    {
        "id": "esi-green-ingrown-hair-neck",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Boynundaki kıl dönmesi sivilcesini sıkmaya/kaşımaya çalışma. Termal: Normal. -> Basit Follikülit. ESI 5.",
    },
    {
        "id": "esi-green-pityriasis-rosea-rash",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Gövdesindeki kızarıklıklara bakıp şaşkın, kaşıntı/ağrı mimiği yok. Termal: 36.5°C. -> Sistemik Olmayan Döküntü. ESI 5.",
    },
    {
        "id": "esi-green-resolved-hives",
        "category": "green",
        "pattern": "Yürüyüş: Bağımsız yürüme. Yüz: Evde kurdeşen çıkardığını tarif ediyor, şu an cildi normal, rahatlamış. Termal: Normal. -> Çözülmüş Ürtiker. ESI 5.",
    },
    {
        "id": "esi-green-work-excuse-note",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız, normal hızda. Yüz: Dinç görünüyor, iş yeri için rapor talebi. Termal: 36.6°C. -> Rapor Talebi. ESI 5.",
    },
    {
        "id": "esi-green-pinworm-itching",
        "category": "green",
        "pattern": "Yürüyüş: Çocuğun yürümesi normal. Yüz: Ateşsiz, enerjik, poposunu kaşıyor. Termal: 36.6°C. -> Kıl Kurdu Şüphesi. ESI 5.",
    },
    {
        "id": "esi-green-mild-hemorrhoid-flare",
        "category": "green",
        "pattern": "Yürüyüş: Dışkılama sonrası makatta yanma nedeniyle sandalyenin ucuna oturma. Yüz: Utanma ve lokal sızı mimiği. Termal: 36.6°C. -> Komplike Olmayan Hemoroid. ESI 5.",
    },
    {
        "id": "esi-green-superficial-thorns",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Elindeki diken batan yeri gösterip çıkarma ricası. Termal: Normal. -> Yüzeyel Diken Batması. ESI 5.",
    },
    {
        "id": "esi-green-post-exercise-muscle-soreness",
        "category": "green",
        "pattern": "Yürüyüş: Ağır spor sonrası bacakları et kesmiş (DOMS) şekilde kaskatı yürüme. Yüz: Kas ağrısına bağlı gülümseyerek sızlanma. Termal: Kaslarda yaygın hafif ısı. -> Gecikmiş Kas Ağrısı (DOMS). ESI 5.",
    },
    {
        "id": "esi-green-simple-cystitis-female",
        "category": "green",
        "pattern": "Yürüyüş: Hızlıca tuvalete gitme ihtiyacı. Yüz: İdrar yaparken yanma hissi nedeniyle rahatsızlık, ateş mimiği yok. Termal: 36.8°C. -> Komplike Olmayan Sistit (Kadın). ESI 4 (Sadece idrar tahlili).",
    },
    {
        "id": "esi-green-pregnancy-test-asymptomatic",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Adet gecikmesi nedeniyle gebelik testi isteği, karın ağrısı veya kanama mimiği yok. Termal: 36.7°C. -> Gebelik Testi Talebi. ESI 4 (Sadece kan/idrar testi).",
    },
    {
        "id": "esi-green-mild-canker-sore",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Diliyle ağız içindeki aftı (yarayı) yoklama, yemek yerken acıdığını ifade. Termal: 36.7°C. -> Aftöz Ülser. ESI 5.",
    },
    {
        "id": "esi-green-chapped-lips-severe",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Soğuktan çatlamış ve hafif kanamış dudaklarını gösteriyor, yalama mimiği. Termal: Dudak çevresi soğuk. -> Şiddetli Dudak Çatlağı. ESI 5.",
    },
    {
        "id": "esi-green-tick-attachment-no-symptoms",
        "category": "green",
        "pattern": "Yürüyüş: Sağlam yürüme. Yüz: Kolunda/bacağında yapışık duran keneyi gösterip çıkarma isteği, sistemik bulgu yok. Termal: 36.5°C. -> Kene Isırığı (Çıkarma). ESI 5.",
    },
    {
        "id": "esi-green-superficial-abrasion-knee",
        "category": "green",
        "pattern": "Yürüyüş: Halı saha/asfalt yanığı olan dizini bükmeden yürümeye çalışma. Yüz: Yara yanması grimesi, kanama yok. Termal: Dizde yüzeyel sürtünme ısısı. -> Yüzeyel Abrazyon. ESI 5.",
    },
    {
        "id": "esi-green-ear-wax-impaction",
        "category": "green",
        "pattern": "Yürüyüş: Tam bağımsız. Yüz: Kulağının tıkandığını/duymadığını işaret etme, ağrı veya akıntı yok. Termal: Normal. -> Buşon (Kulak Kiri). ESI 5.",
    },
]
