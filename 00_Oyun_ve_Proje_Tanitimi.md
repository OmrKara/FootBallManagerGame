# Futbol Kulübü Yönetim Sistemi

**BİL372 Veritabanı Sistemleri · Ortak proje tanıtımı**

Oyuncu, dört takımlı bir ligde bir futbol kulübünün menajeridir. Kulübüne isim verir, ilk 11’i seçer, transfer bütçesini kullanır ve takımını altı hafta boyunca yönetir. Maçları oyun motoru oynatır. Menajerin kararlarının sonucu sahada skor ve oyuncu performansı, kulüp yönetiminde ise puan durumu, kadro ve bütçe olarak görünür.

Bu yerel, tek oyunculu oyunda her hesabın kendine ait bir kariyeri ve ayrı bir ligi vardır. İki kullanıcı aynı bilgisayarda hesap açabilir. Birinin transfer ettiği oyuncu, kazandığı maç veya ilerlettiği hafta yalnızca kendi ligini etkiler.

## Bir kariyerde neler yaşanır?

### Kulübü kurmak

İlk girişte kullanıcı yöneteceği kulübün adını seçer. Örneğin “Ankara Yıldızları” adını verebilir. Diğer üç kulübün adı bir özellik ve bir hayvan adı birleştirilerek üretilir. “Çevik Panterler” ve “Cesur Kartallar” olası rakiplerdir. Kulüp adı seçimi tek seferliktir.

Her kulüp 2.000.000 bütçeyle ve 12 futbolcuyla başlar. Böylece ligde 48 futbolcu vardır. Ad ve soyad havuzlarıyla üretilen oyuncuların hız, pas, şut, savunma, güç, dayanıklılık ve top sürme değerleri değişir. Oyuncunun yaşı, ana mevkisi, oynayabildiği diğer mevkiler ve piyasa değeri kadro kararlarında kullanılır.

### İlk 11’i seçmek

Menajer 4-3-3 veya 4-4-2 dizilişini seçer, sonra her yere bir futbolcu yerleştirir. Aynı futbolcu iki yeri dolduramaz. Ana mevki ve oynanan mevki farklı olabilir. Örneğin santrforda da oynayabilen bir ofansif orta saha, o roldeki uyumu ölçüsünde takıma katkı verir.

Her futbolcu %70 olasılıkla Ateş, Toprak, Hava veya Su elementlerinden birini taşır. Kalan oyuncular elementsizdir. Bu olasılık her futbolcu için ayrı uygulanır, dolayısıyla iki kariyerde elementli futbolcu sayısı farklı olabilir. İlk 11’de aynı elementi taşıyan oyuncu sayısı ilgili eşiğe ulaştığında takım bonus kazanır. Kadro ekranında menajerin görmek istediği sonuç, seçiminin takımın **savunma, orta saha ve hücum** gücünü nasıl değiştirdiğidir.

### Haftayı oynatmak ve sonucu okumak

Dört kulüp birbiriyle bir kez evinde, bir kez deplasmanda karşılaşır. Her hafta iki maç oynanır. Bir sezon altı hafta ve toplam 12 maçtır. Menajer “Haftayı oynat” dediğinde diğer iki kulübün maçı da tamamlanır. Ana ekranda son maç, sıradaki rakip ve güncel puan tablosu görünür. Galibiyet üç, beraberlik bir puan getirir.

Bir maç açıldığında iki takımın maçtaki dizilişleri, ilk 11’leri, oyuncu istatistikleri ve dakika sırasıyla gol ve asist olayları gösterilir. Örneğin menajer ikinci hafta kalecisini değiştirdiğinde ilk haftanın maç ekranında o gün kalede duran futbolcu görünmeye devam eder. Oynanmamış bir maçta boş skor, tamamlanmış bir maçta ise gerçek 0-0 gösterilebilmelidir.

### Transfer yapmak

Menajer pazarda diğer kulüplerin oyuncularını mevki, element ve fiyat aralığına göre inceler. Teklif verdiğinde oyuncu satıcının kadrosunda kalır. Bekleyen bir teklifi geri çekebilir veya değerlendirmeye gönderebilir. Satıcı, ilk 11’indeki oyuncu için gelen teklifi ve piyasa değerinin altındaki teklifi reddeder. Bedel uygunsa, oyuncu satılabiliyorsa ve alıcının bütçesi yetiyorsa transfer tamamlanır.

Örneğin başlangıç bütçesi 2.000.000 olan kulüp, rakibin yedek kalecisini 400.000’e aldığında bütçesi 1.600.000’e iner. Satıcı 400.000 kazanır ve oyuncu alıcının kadro listesinde görünür. Onu ilk 11’e almak menajerin ayrı bir kararıdır. Bu örnek üç ekranı birbirine bağlar: transfer geçmişinde anlaşma, finansta gider, kadroda yeni kaleci görünür. Finansın kapsamı transfer gelir ve giderleridir.

### Sezonu bitirmek ve devam etmek

Son hafta oynandığında puan tablosu kesinleşir. Oyuncular bir yaş büyür. Sezon boyunca oynanan maçlar, gol ve asist katkısı, yaş ve mevki oyuncu gelişimine etki eder. Genç oyuncularda düzenli forma giymek önemlidir. 35 yaş ve üzerinde temel eğilim düşüştür. Ara yaş grubunda küçük bir rastgele değişim vardır. Oyuncunun güncel özellikleri saklanır.

Menajer yeni sezonu başlattığında kulüpler, güncel oyuncular ve bütçeler taşınır. Yeni fikstür birinci haftadan açılır, puanlar sıfırlanır. Geçmiş sezonun maçları ve puan tablosu arşivde kalır. Bu nedenle bir maça bağlantı verirken hem sezonu hem maç numarasını bilmek gerekir.

## Arayüzde menajer ne görmeli?

| Ekran | Menajerin sorusu | Beklenen davranış |
|---|---|---|
| Giriş ve kulüp kurulumu | “Kendi kariyerime nasıl girerim?” | Kayıt ve girişten sonra ilk kullanımda ad seçimi açılır. Sonraki girişte mevcut kulübe dönülür. |
| Ana sayfa | “Hangi haftadayım, sıradaki rakibim kim?” | Kulüp, sezon, hafta, bütçe, son ve sıradaki maç ile puan tablosu birlikte görünür. Sezon sonunda yeni sezon eylemi açılır. |
| Kadro ve taktik | “Bu 11’i sahaya sürersem takımımın gücü ne olur?” | Diziliş, slotlar, oyuncular, mevki uyumu ve elementler okunabilir olmalı. Kayıttan sonra güncel üç takım gücü gösterilir. |
| Fikstür ve maç detayı | “Kim kiminle oynadı, golü kim attı?” | Hafta, rakip, saha veya sonuçla filtreleme yapılır. Maça tıklayınca o günün kadroları, skor, gol/asist dakikaları ve oyuncu performansları açılır. |
| İstatistikler ve arşiv | “Hangi oyuncu veya diziliş iyi performans gösterdi?” | Gol, asist ve maç puanı sıralamaları gösterilir. Güncel diziliş sonuçları incelenir. Arşivden seçilen sezonun maçları ve puan tablosu açılır. |
| Transfer ve finans | “Kimi alabilirim, teklifim ve bütçem ne durumda?” | Pazar, teklifler, sonuç gerekçesi, transfer geçmişi ve bütçe birbirini tamamlar. Kabul edilen transferden sonra ilgili listeler yenilenir. |

Ekranlar isimleri gösterir, işlemlerde backend’in verdiği kimlikleri kullanır. İki tarayıcı sekmesinde aynı hafta açıksa ilk sekmede oynanan haftayı ikinci sekmeden yeniden oynatmak mümkün olmamalıdır. İkinci sekme güncel haftayı okuyup menajere göstermelidir.

## Oyun verisi hangi tablolarda yaşar?

| Oyun bilgisi | PostgreSQL tabloları | Aralarındaki ilişki |
|---|---|---|
| Hesap ve kişisel dünya | `user_account`, `career` | Bir hesabın en fazla bir kariyeri vardır. Kariyerin kimliği hesabın kimliğidir. |
| Kulüp ve oyuncu | `club`, `player`, `player_position` | Bir kariyerde birden çok kulüp, bir kulüpte birden çok oyuncu vardır. Bir oyuncunun farklı mevkilerdeki uyumları ayrı satırlardır. |
| Sahaya çıkacak takım | `lineup_selection`, `career_bonus_rule` | Her kulübün seçili slotları oyunculara bağlanır. Kariyerin element eşikleri ilk 11’e uygulanır ve takım gücü hesaplanır. |
| Sezon ve program | `season`, `fixture` | Bir kariyer birden çok sezon yaşayabilir. Her fikstür kaydı bir sezona ve ev sahibi/deplasman rollerindeki iki kulübe bağlıdır. |
| Oynanmış maç | `match_result`, `match_lineup`, `match_event`, `match_player_stat` | Bir fikstürün oynanınca bir sonucu olur. O sonuca maçtaki ilk 11’ler, sıralı olaylar ve oyuncu başına maç istatistikleri bağlanır. |
| Teklif ve anlaşma | `transfer_offer`, `transfer` | Teklif hangi oyuncu için hangi alıcı ve satıcının hangi bedelde görüştüğünü saklar. Kabul edilen teklif bir gerçekleşmiş transfere bağlanır. |

**Kariyer ve sezon kimlikleri neden önemlidir?** İki ayrı kullanıcının liginde 10 numaralı kulüp bulunabilir. Aynı kariyerde ilk sezonun 1 numaralı maçı ile ikinci sezonun 1 numaralı maçı farklı karşılaşmalardır. Dolayısıyla bir kulüp kariyeriyle, bir maç ise kariyeri ve sezonuyla birlikte tanımlanır.

**Geçmiş nasıl korunur?** Bugünkü kadro seçimi ile geçen haftanın maç kadrosu ayrı tutulur. Bir futbolcu transfer olduğunda eski golleri maçta oynadığı kulüpte kalır. Arşivlenen maçın kulübünü belirlerken o maçtaki tarafı ve fikstür kaydı esas alınır. Puan tablosu maç sonuçlarından, transfer geliri ve gideri gerçekleşmiş transferlerden hesaplanır.

## Üç kişinin yaptığı iş nerede birleşir?

Arayüz HTML, CSS ve JavaScript ile kullanıcının seçimini alır. FastAPI backend’i oturumu ve oyun kurallarını denetler, JSON yanıtını üretir. Kalıcı modda backend PostgreSQL’e pyodbc üzerinden bağlanır. Örneğin “Teklifi değerlendir” tıklamasında arayüz teklif numarasını gönderir. Backend kabul koşullarını denetler. PostgreSQL’de teklif durumu, oyuncunun kulübü, iki bakiye ve transfer geçmişi tek transaction içinde kaydedilir. İşlem yarıda kalırsa tamamı geri alınır. Arayüz sonucu okuduğunda kadro ve bütçe aynı anlaşmayı göstermelidir.

Arayüz geliştirme sırasında bellek modu kullanılabilir. Kullanıcının bilgisayarında geçen 130 test, oyun mantığını ve katmanlar arasındaki sözleşmeleri kapsar. Ekip birlikte gerçek PostgreSQL bağlantısında kayıt, maç, transfer, yeniden giriş ve sezon arşivi akışlarını doğrulayacaktır.

**Okuma sırası:** Bu ortak tanıtımın ardından arayüz sorumlusu `01_Arayuz_Gelistirme_Rehberi.md` ile ekran ve API ayrıntılarına, veritabanı sorumlusu `02_PostgreSQL_Gelistirme_Rehberi.md` ile fiziksel şema, roller, toplu yükleme ve analitik sorgulara geçebilir.
