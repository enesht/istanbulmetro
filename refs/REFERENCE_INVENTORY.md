# Referans envanteri — kategori matrisi

`state × category` dağılımı. Boş hücreler kaynakta o fotoğrafın **bulunmadığını** gösterir,
işlenmediğini değil. Modellemeye başlamadan önce bu matrise bakıp hangi ögenin
fotoğraf desteği olmadığını bilmek gerekiyor.

## Tamamlanmış istasyon fotoğrafları

| | platforms | entrances | ticket halls | escalators | stairs | ceilings | columns | walls | flooring | signage | lighting | tracks | tunnels | architectural details |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Ayrılık Çeşmesi** | 4 | 6 | 2 | · | · | · | · | · | · | 3 | · | 1 | · | 2 |
| **Kazlıçeşme** | 3 | · | · | · | · | · | · | · | · | 2 | · | 1 | · | 1 |
| **Sirkeci** | 2 | 3 | 2 | · | · | · | · | 5 | · | 2 | · | · | · | · |
| **Söğütlüçeşme** | 10 | 1 | 1 | · | · | 1 | · | · | 1 | 2 | · | 4 | · | 4 |
| **Yenikapı** | 3 | · | · | · | · | · | · | · | · | · | · | · | · | 1 |
| **Üsküdar** | 1 | 2 | · | · | · | · | · | · | · | 3 | · | · | · | · |
| **Tünel** | · | · | · | · | · | · | · | 1 | · | · | · | · | 2 | · |
| **İnşaat** | · | · | · | · | · | · | · | · | · | · | · | · | · | · |

## İnşaat dönemi fotoğrafları

| | platforms | entrances | ticket halls | escalators | stairs | ceilings | columns | walls | flooring | signage | lighting | tracks | tunnels | architectural details |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Ayrılık Çeşmesi** | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| **Kazlıçeşme** | 1 | · | · | · | · | · | · | · | · | · | · | · | · | · |
| **Sirkeci** | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| **Söğütlüçeşme** | 1 | · | 2 | · | · | · | · | · | · | 1 | · | · | · | · |
| **Yenikapı** | · | · | · | · | · | · | · | · | · | · | · | · | · | · |
| **Üsküdar** | · | 1 | · | · | · | · | · | · | · | · | · | · | · | · |
| **Tünel** | · | · | · | · | · | · | · | · | · | 1 | · | · | 5 | · |
| **İnşaat** | 2 | · | · | · | 1 | · | · | 2 | · | 2 | · | 2 | 10 | · |

`unclear` durumundakiler inşaat tablosunda sayıldı; klasörde ayrı `unclear/` altında duruyorlar.

## Klasör yapısı

```
refs/<hedef>/<state>/<category>/<dosya>.jpg
  state    : completed | construction | unclear
  category : platforms, entrances, ticket_halls, escalators, stairs, ceilings, columns, walls, flooring, signage, lighting, tracks, tunnels, architectural_details
```

`refs/_categorised.json` her fotoğraf için kategori, durum, konu ve modellemede
işe yarayıp yaramadığı bilgisini tutuyor. `refs/ATTRIBUTION.md` lisans künyesi.

## Boşluklar (ajanların raporladığı)

### Ayrılık Çeşmesi

- Peronun tamamını veya kanopi aks/modül sayısını gösteren boydan boya ya da havadan bir kare yok; peron uzunluğu belirlenemiyor.
- Peron kesiti (ray kotu - peron kotu farkı, peron genişliği, ada peron mu yan peron mu olduğu) hiçbir fotoğrafta net belgelenmemiş; ada peron çıkarımı dolaylı.
- Peron kotundan bilet holüne inen merdiven/yürüyen merdiven/asansör çekirdeklerinin peron üzerindeki konumu ve biçimi hiç görülmüyor.
- Marmaray ile M4 metro peronları arasındaki bağlantı koridorları, aktarma tünelleri ve bu koridorların kaplamaları fotoğraflanmamış.
- M4 metro peronunun kendisine ait tek bir kare yok (yalnızca M4 bilet holü var).
- Kanopi kolon kaidesi, kolon-konsol birleşim detayı ve saçak kenar profili yakın plan olarak belgelenmemiş.
- Peron bankları, çöp kutuları, kameralar, hoparlörler gibi mobilyaların tipi ve aralığı yakın plan yok; sadece uzaktan siluet olarak görünüyor.
- Peronda sefer bilgi ekranı (PIS), hoparlör direkleri ve peron levhalarının asılma yükseklikleri belgelenmemiş.
- Gece aydınlatması, armatür renk sıcaklığı ve kanopi altı ışık dağılımı hakkında hiç fotoğraf yok.
- İkinci/diğer giriş ağızları ve bunların konumları gösterilmemiş; sadece bir giriş çukuru tekrar tekrar fotoğraflanmış.
- Bilet gişesi, WC, personel mekânları, teknik odalar gibi yardımcı hacimler yok.
- Döşeme plağı, fayans ve taktil plaka ölçülerini doğrulayacak bilinen boyutlu bir referans (cetvel, standart kapı, imalat detayı) hiçbir karede bulunmuyor; bu yüzden metre cinsinden hiçbir ölçü verilmedi.
- Renk/malzeme kodları (fayans tonu, boya rengi, granit tipi) yalnızca fotoğraf pozlamasından tahmin edilebiliyor; farklı karelerde ışık nedeniyle tonlar değişiyor.
- 18 fotoğrafın yaklaşık üçte ikisi giriş meydanı ve dış görünümlere ait; iç mekânlar (peron altı holler, koridorlar) orantısız biçimde az temsil ediliyor.

### Kazlıçeşme

- Toplam 8 fotoğraf var ve bunların 1'i hat şeması panosu (modelleme için kullanılamaz), 1'i de inşaat halinde - yani kullanılabilir mimari kare sayısı pratikte 6. Bu, bir istasyonun tam modellenmesi için az; aşağıdaki boşluklar tahminle doldurulmamalı.
- Sokak kotundaki giriş yapısı / istasyon binası dış cephesi hiç yok. Girişin nerede ve hangi biçimde olduğu bilinmiyor.
- Bilet holü / gişe / turnike hattı iç mekânından tek kare yok. Peron altı alt geçidin mekânsal büyüklüğü, tavan yüksekliği ve kaplaması bilinmiyor.
- Peronu alt geçide bağlayan merdivenin yalnızca ağzı görülüyor; basamak sayısı, kot farkı, merdiven kovası ve iniş sahanlığı görünmüyor.
- Yürüyen merdiven olup olmadığı belirlenemiyor - hiçbir karede yok.
- Asansörün peron kotu dışındaki hiçbir parçası (alt kat kapısı, kabin içi, kule tabanı) görünmüyor.
- Peronun tam uzunluğu ve genişliği ile toplam hat sayısını gösteren bir üst/uzak açı (kuşbakışı veya köprüden çekim) yok; peron-hat yerleşim planı çıkarılamıyor.
- 2023 (T6) kanopisinin alttan görünümü, tavan kaplaması ve armatür düzeni yok - yalnızca karşı peronda uzaktan görülüyor.
- Kaz rölyefli panonun bulunduğu sundurmanın tamamı, panonun peron üzerindeki konumu ve arka yüzü görünmüyor; pano gece ve tek açıdan çekilmiş, gerçek renk tonu gündüz ışığında doğrulanamıyor. Panonun hâlâ yerinde olup olmadığı da (fotoğraf 2013 tarihli) bilinmiyor.
- Kolon kesit tipi (kutu mu, I profil mi), kolon-kiriş birleşim detayı ve kolon aralığı net ölçülemiyor; hiçbir karede dik açıdan kolon dizisi yok.
- Zemin karolarının gerçek modül boyutu (ör. 60x60 mu 80x80 mi) bilinen bir referans olmadığı için belirlenemiyor.
- Peron üstündeki yolcu bilgilendirme ekranı, hoparlör, kamera ve bilet validatör donanımlarının yakın plan detayı yok.
- Gece aydınlatma atmosferi yalnızca 2013 peronu için var; yeni bölümün gece görünümü yok.
- Tünel ağzı, hat makası veya istasyon yaklaşım geometrisini gösteren kare yok.

### Sirkeci

- Toplam yalnizca 14 fotograf var ve bunlarin 5'i sadece karo pano/tabela detayi; istasyonun mekansal kapsamasi oldukca eksik.
- Hic INSAAT asamasi fotografi yok - yapim sureci, tasiyici sistem, kalip/iskele hakkinda hicbir gorsel kanit bulunmuyor.
- Peronun ustune dogru (tavana) bakan net bir fotograf yok; peron tavan sisteminin modul olculeri ve tonozun egrilik yaricapi cikarilamiyor.
- Iki peronun birbirine gore konumu belirsiz: ada peron mu, iki ayri yan peron mu, aralarinda ust gecit mi alt gecit mi var - dogrulanamadi.
- Peron uclari, peron toplam uzunlugu ve tunel agzina baglanti noktalari hicbir fotografta yok.
- Yurüyen merdivenlerin tam boy gorunumu yok; sadece giris holunden uzaktan ve turnike holunde korkuluk parcasi goruluyor. Egim, basamak sayisi, kova genisligi bilinmiyor.
- Merdiven detayi (basamak yuksekligi/genisligi orani, sahanlik, korkuluk profili) olculebilir sekilde belgelenmemis.
- Asansorler, asansor kuleleri ve engelli erisim guzergahi hic goruntulenmemis (varligi sadece tabeladan biliniyor).
- Turnike kati ile peron arasindaki baglanti koridorlari ve ara kat (mezanin) tamamen eksik.
- Gise/bilet bufesi, personel odalari, teknik hacimler, tuvaletler gorunmuyor.
- Peronda duran bir tren fotografi yok; arac ile peron kotu/boslugu iliskisi olculemiyor.
- Sirkeci Gar tarafindaki (kuzey/Eminonu) ana giris yapisinin dis cephesi yok; yalnizca Cagaloglu girisi belgelenmis.
- Tunel kesiti, tunel ici kaplama ve havalandirma yapilari yok.
- Hicbir fotografta bilinen olculu referans nesne (olculu kapi, cetvel, plan) yok; bu nedenle metre cinsinden mutlak olcu uretilemez - tum olculer insan boyu ve karo/panel moduluyle oransal verilmistir.
- Fotograflar 2013-2022 araligindan; 2023 sonrasi olasi yenileme/tabela degisiklikleri kapsanmiyor.
- Zemin, duvar ve tavan karolarinin gercek birim olculeri (orn. 30x30 mi 60x60 mi) hicbir karede guvenilir sekilde cikarilamiyor.
- Karo panolarin istasyon icindeki tam konumlari (hangi kat, hangi duvar, hangi koridor) belirsiz; 5311/5312/6322/6323 numarali detay cekimlerinde cevresel baglam yok.

### Söğütlüçeşme

- Yürüyen merdiven hiç yok. Pakette tek bir eskalatör fotoğrafı bulunmuyor; oysa YHT binası ile Marmaray peron kotu arasında eskalatör olması çok muhtemel. Modellemede bu tamamen tahmine kalır.
- Sabit merdiven ve peronlar arası alt/üst geçit yok. Kotlar arası geçişin nerede ve nasıl olduğu (merdiven kovası genişliği, korkuluk tipi, basamak kaplaması) hiçbir kareden çıkarılamıyor.
- Marmaray bilet holünün İÇİ yok. Elde sadece kepenkleri kapalı, üstelik baş aşağı kaydedilmiş bir dış kare var; gişe bankoları, bilet otomatları, turnike hattı ve holün tavan/zemin kaplaması görülmüyor.
- Yeni istasyonun sokak kotundaki GİRİŞLERİ ve DIŞ CEPHESİ yok. Giriş saçağı, cephe malzemesi, bina kütlesi, meydanla ilişkisi bilinmiyor; elde yalnızca 2011 tarihli, bugün var olmayan eski istasyonun sokak kotu fotoğrafı var.
- Bütünsel bir plan/kesit/hava fotoğrafı yok. Peron sayısı, peron uzunlukları, YHT peronları ile Marmaray peronlarının birbirine göre konumu ve kot farkı ölçülemiyor; yalnızca '1' ve '2' numaralı peron girişleri dolaylı bilgi veriyor.
- Marmaray peron kotunun 2019 sonrası hâli yok. Tek Marmaray peron mekânı karesi 2019 tarihli; bugünkü tabela, ekran ve mobilya düzeni farklı olabilir.
- Marmaray peronunda tavan, kolon ve döşeme detayı yakın plan hiç yok — hepsi tek bir geniş açı karesinden, uzaktan okunuyor.
- YHT holünün geniş açı / bütün mekân karesi yok. İki giriş fotoğrafı da dar açılı; holün toplam genişliği, yüksekliği, turnike hattının uzunluğu ve mekânın genel kurgusu çıkarılamıyor.
- Tuvalet, bekleme salonu, ticari birimler, bagaj alanı, personel alanları gibi iç mekânlar hiç yok.
- Marmaray kotunda tabela tipografisinin yakın planı yok; Marmaray hat logosu, istasyon adı levhası, hat şeması ve renk kodu okunamıyor.
- Döşeme karolarının gerçek modül ölçüsü bilinmiyor. Hiçbir karede bilinen boyutta bir referans nesne (ölçek çubuğu, standart kapı, insan + karo aynı düzlemde) yok; bu yüzden metre cinsinden hiçbir karo/plaka boyutu verilemedi.
- Kolon kesiti ve profil ölçüleri yok. Kolonlar hep uzaktan ve tek yönden görülüyor; kesit biçimi (kutu mu, boru mu) ve boyut oranları kesinleştirilemiyor.
- Fotoğraf dağılımı dengesiz: 28 fotoğrafın 7'si neredeyse aynı kompozisyonlu bir seri (HT80113 yaklaşıyor), 4'ü sergi lokomotifi, 2'si sadece araç üzeri ekran/tren. Gerçekten farklı mimari bilgi taşıyan kare sayısı ~10 civarında.
- Veri hatası: 'Marmaray Söğütlüçeşme istasyonu 2 - İstanbul.jpg' dosyasının _meta.json açıklaması 'Marmaray Ayrılık Çeşmesi istasyonu' diyor, oysa fotoğraf net biçimde SÖĞÜTLÜÇEŞME isim tabelasını gösteriyor.
- Veri hatası: 'Söğütlüçeşme railway station.jpg' dosyası 180° DÖNDÜRÜLMÜŞ (baş aşağı) kaydedilmiş; kullanılmadan önce düzeltilmeli.
- Eski (yıkılmış) istasyon ile yeni istasyon fotoğrafları aynı klasörde karışık: 2009–2012 tarihli 6 kare bugün var olmayan yapıyı gösteriyor. Bunların güncel referans sanılması en büyük modelleme riski.

### Yenikapı

- Istasyon girisi / yeruzeyi giris yapisi hic yok (entrances kategorisinde tek fotograf bile yok).
- Bilet / turnike holu, gise ve bilet otomati alani hic yok.
- Yuruyen merdiven, sabit merdiven ve asansor hic yok; peron ile ust katlar arasindaki dusey sirkulasyon bilinmiyor.
- Kat plani / genel kesit yok: istasyonun kac katli oldugu, peron derinligi, mezanin olup olmadigi bilinmiyor ('B1' yalniz dosya adinda geciyor, fotograftan dogrulanamiyor).
- Karsi yol ve karsi peron hic goruntulenmemis; peronun ada mi yan peron mu oldugu, ikinci yolun duvarinda da mural olup olmadigi bilinmiyor.
- Peronun diger yarisi ve peron uclari (acil cikis, tunel agzi detayi, peron sonu kapilari) yok.
- Tavan lamel sisteminin yakin cekimi yok: lamel kesiti, genisligi, aski detayi ve armatur gomme detayi okunamiyor.
- Zemin karosunun yakin cekimi yok: karo boyutu, derz genisligi ve desen eki olcumlenemiyor.
- Duvar karosu yakin cekimi yok: karo modul olcusu, yuzey dokusu ve kose/bitis profilleri bilinmiyor.
- Mural'in duz karsidan, tam cerceveli ve yuksek cozunurluklu cekimi yok; eserin gercek en/boy orani ve karo modul duzeni kismen tahmine kaliyor. Eserin sanatcisi/adi da metadata'da yok.
- Peron kenari grafik bandinin tam metni, desen tekrari ve bant genislikleri yakin cekimde yok; '5 VAGONLU' disindaki vagon sayisi isaretleri gorulmuyor.
- Peron donatisi (bank, cop kutusu, PA hoparlor, CCTV, harita/plan panosu, yangin dolabi) hic goruntulenmemis.
- Yonlendirme tabela ailesinin tam seti yok; sarkan levhalarin uzaktan okunan tek bir ornegi disinda tipografi, olcu ve renk kodu bilinmiyor.
- Herhangi bir insaat donemi fotografi yok - yapim sistemi (ac-kapa kutu, kazik perde, celik destek) hakkinda gorsel kanit yok.
- Olcek referansi veren hicbir fotograf yok (metre, kapi, standart bir eleman yaninda cekim); bu nedenle metre cinsinden hicbir boyut verilemedi.
- Toplam fotograf sayisi yalnizca 4 ve bunlarin 3'u ayni peron-mural bolgesine bakiyor; istasyonun buyuk bolumu gorsel olarak kapsanmamistir.

### Üsküdar

- Toplam 7 fotoğraf var ve bunların 3'ü yalnızca tabela/levha; istasyon mekanına ait tek iç fotoğraf 'Üsküdar Tren İstasyonu.jpg'. Bu sayı bir istasyonun 3B modellenmesi için açıkça yetersiz.
- Bilet holü / konkors mekanının hiçbir fotoğrafı yok (yalnızca kabartma kroki var): turnike sıraları, gişe bankosu, biletmatikler, konkors tavanı ve zemin deseni bilinmiyor.
- Yürüyen merdiven ve asansörlerin gerçek görünümü yok: korkuluk rengi, kılıf malzemesi, boşluk genişliği, kaç kademeli oldukları bilinmiyor.
- Peronun karşı tarafı ve ikinci ray kenarı kadraja girmiyor; peronun ada mı yan peron mu olduğu, genişliği ve toplam uzunluğu doğrulanamıyor.
- Ray yatağı, tünel kesiti, tünel ağzı, katener/elektrifikasyon düzeni ve sinyalizasyon ögeleri hiç görünmüyor.
- Peron sonu / merdiven inişi, peron-konkors bağlantı boşlukları ve şaft/galeri kesiti fotoğraflanmamış.
- Tavan ızgarasının ve karo kaplamanın yakın plan dokusu yok; karo boyutu, yüzey parlaklığı ve derz kalınlığı ancak uzaktan tahmin ediliyor.
- Zemin plakalarının modül boyutu ve ek yeri düzeni, peron kenarı taktil şeridinin net genişliği ölçülemiyor.
- Girişlerin iç mekanı (giriş holü, kapı grupları, saçak altı tavan detayı) fotoğraflanmamış; sadece dışarıdan genel görünüm var.
- M5 Üsküdar-Ümraniye-Çekmeköy metrosu ve vapur iskelesi ile aktarma koridorlarının hiçbir fotoğrafı yok.
- Gece/karanlık aydınlatma görünümü, armatür renk sıcaklığı ve parlaklık dağılımı hakkında veri yok.
- Hiçbir fotoğrafta bilinen ölçü referansı (insan boyu dışında) yok; metre cinsinden gerçek boyutlar için mimari proje/plan gerekir.
- İstasyonda tren bulunan hiçbir kare yok; araç gabarisi ile peron kotu ilişkisi doğrulanamıyor.

### Tünel

- Bu klasor SADECE tunel icini kapsiyor (9 fotograf): peron, giris, bilet holu, yuruyen merdiven, merdiven kategorilerinde hicbir gorsel yok. Istasyon modellemesi icin bu klasor tek basina yetersiz.
- Dairesel tunel capi veya kutu kesit genisligi/yuksekligi icin bilinen bir olcek referansi (cetvel, kapi, standart isaret) yok; metrik olculer fotograftan cikarilamaz.
- Prekast segment halkasinin yakin plani yok: halka genisligi, segment sayisi, derz contasi, cıvata cebi detayi olculemedi.
- Dairesel kesit ile batirma tup kesiti arasindaki GECIS noktasi (portal / adaptasyon yapisi) hicbir fotografta yok - modelde bu birlesim tahmin edilmek zorunda kalir.
- Tuneller arasi baglanti galerileri, acil cikis kapilari, yangin dolabi nisleri ve tahliye isaretlemeleri gorunmuyor.
- Tamamlanmis durumdaki aydinlatma armaturunun yakin plani yok: armatür boyu, montaj yuksekligi, aralik, govde tipi belirlenemiyor.
- Yuruyus/tahliye yolunda korkuluk veya el tutamagi olup olmadigi kesinlesmiyor - mevcut acilarda gorunmuyor, ama kadraj disi kalmis olabilir.
- Tunel tabani drenaj kanalinin kesiti, izgara kapagi veya pompa istasyonu detayi yok.
- Katener kontak teli yuksekligi, askı araligi ve konsol tipi olculemiyor; sadece varligi dogrulanabiliyor.
- Havalandirma bacasi, jet fan veya duman tahliye ekipmani hicbir fotografta yok.
- Tunel icindeki hiz/kilometre tabelalari, hat kodlari ve kilometre taslari icin okunabilir ornek yok (sadece bir sinyal direginde KBS4701 kodu var).
- Sirkeci cini panosunun cevresi gorunmuyor: panonun duvardaki konumu, cercevesi, zeminden yuksekligi ve etrafindaki duvar kaplamasi bilinmiyor.
- Fotograflarin cogu 2012 insaat donemine ait (6 adet); isletmedeki tamamlanmis tunel icin sadece 2 fotograf var (2024). Kalici detaylarin cogu bu iki kareye dayaniyor.

### İnşaat

- Klasörde TAMAMLANMIŞ istasyon gösteren tek bir fotoğraf bile yok; 19 karenin tamamı 2007-2013 inşaat dönemi. Nihai mimari bitişler tamamen eksik.
- İstasyon iç mekânını gösteren yalnızca 4 kare var (MarmarayUskudarStationunderconstruction, Marmarayunderconstruction, Marmaraystation, Marmaraystairs) ve hepsi aynı gün/aynı istasyon (3 Mayıs 2012, Üsküdar) çekilmiş; diğer istasyonların iç mekânı hiç yok.
- Nihai duvar kaplaması malzemesi, rengi ve derz düzeni bilinmiyor (ham beton dışında hiçbir yüzey görülmüyor).
- Nihai zemin kaplaması ve desen düzeni (karo ölçüsü, renk, hissedilebilir yüzey şeritleri) hiç görünmüyor.
- Yolcu peronu, peron kenarı profili, sarı güvenlik şeridi ve peron genişliği/uzunluğu hiçbir karede yok.
- Yürüyen merdiven, asansör ve bunların kovaları/korkulukları yok.
- Bilet holü, gişe, turnike hattı, bilet otomatı gibi konkors elemanları yok.
- Sokak seviyesindeki istasyon girişi, giriş saçağı/kütlesi, merdiven ağzı ve çevre peyzajı yok.
- Kalıcı istasyon tabela ve yönlendirme sistemi (tipografi, renk kodu, askı tipi, istasyon adı levhası) yok.
- Kalıcı aydınlatma armatürlerinin nihai biçimi belirsiz; fotoğraflardaki düşey lineer armatürlerin şantiye aydınlatması olma ihtimali dışlanamıyor.
- Tavan nihai bitişi (asma tavan var mı, panel tipi, havalandırma menfez düzeni) bilinmiyor; yalnızca ham beton kiriş-plak görülüyor.
- Oturma birimi, çöp kutusu, korkuluk, ekran, anons hoparlörü gibi kalıcı mobilya/ekipman yok.
- Hiçbir karede tren ya da tren-peron ilişkisi yok; araç gabarisi ve kapı hizası çıkarılamıyor.
- Plan, kesit veya ölçekli çizim yok; bu nedenle metre cinsinden hiçbir boyut doğrulanamıyor. Verilen ölçülerin tamamı insan boyu / ray açıklığı gibi göreli referanslara dayanan orandır.
- Tünel kesitinin segman sayısı, halka genişliği ve iç çapı güvenilir biçimde sayılamıyor (kameraya yakın segmanlar kadrajı taşıyor, uzaktakiler çözünürlük altında).
- Üsküdar dışındaki istasyonların (Sirkeci, Yenikapı, Ayrılık Çeşmesi) mimari karakteri hakkında hiçbir veri yok; Yenikapı ve Söğütlüçeşme yalnızca kazı aşamasında ve dışarıdan görülüyor.
- 3 kare (Building the first intercontinetal subway, Ray-Tüp, Istanbul Bosphorus) modelleme için kullanılamaz nitelikte; etkin referans sayısı 16'ya düşüyor.
