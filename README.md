# Futbol Kulübü Yönetim Oyunu

BİL372 Veritabanı Sistemleri dersi için geliştirilen bu proje, kullanıcının kendi futbol kulübünü yönettiği tek oyunculu bir menajerlik oyunudur. Projenin amacı; hesap, kariyer, kulüp, oyuncu, maç, fikstür ve transfer verilerini ilişkisel bir veritabanında modellemek ve bu veriler üzerinde çalışan bir oyunu web arayüzüyle oynanabilir hale getirmektir.

Uygulama yerel bilgisayarda çalışır. Arayüz FastAPI sunucusundan yayınlanır; oyun kuralları ve maç simülasyonu sunucuda yürütülür. Başlangıçta veriler bellekte tutulabilir, PostgreSQL kurulumu tamamlandığında kalıcı kayıt moduna geçilebilir.

## Geliştiriciler

- Ömer Kara
- Kubilay Filiz
- Mohammad El Ledib

## Oyun nasıl oynanır?

1. Hesap oluşturup giriş yap. İlk girişte kulübüne bir isim ver.
2. Kulübün 2.000.000 başlangıç bütçesi ve 12 oyunculu kadrosuyla lige katılır. Lig, senin kulübünle birlikte üç rakipten oluşur.
3. **Kadro ve taktik** ekranında 4-3-3 veya 4-4-2 dizilişini seç. Oyuncuları pozisyonlara yerleştirip takımının savunma, orta saha ve hücum gücünü incele. İlk 11’de aynı oyuncuyu iki kez kullanamazsın.
4. **Genel bakış** ekranından haftayı oynat. Sunucu, o haftadaki iki karşılaşmayı simüle eder; skorları, gol ve asist olaylarını, oyuncu performanslarını ve puan tablosunu kaydeder.
5. **Fikstür ve maçlar** ekranından maç raporlarını aç. Sahaya çıkan ilk 11’leri, dizilişleri ve maç olaylarını incele.
6. **Transfer pazarı** ekranında rakip kulüplerin oyuncularını filtrele ve teklif ver. Teklifin sonucunu değerlendirdiğinde kabul edilen transfer bütçeni ve kadronu günceller. **Finans** ekranında gelir ve giderleri gör.
7. Altı hafta sonunda sezon tamamlanır. **İstatistikler** ekranında oyuncu ve diziliş performansını incele, yeni sezonu başlat ve önceki sezonun sonuçlarına **Sezon arşivi** ekranından dön.

Lig çift devrelidir: her takım diğer takımlarla bir kez evinde, bir kez deplasmanda karşılaşır. Sezon altı hafta ve toplam 12 maç sürer. Galibiyet üç, beraberlik bir puan getirir. Oyuncuların element uyumu takım gücüne bonus sağlayabilir.

## Özellikler

- Hesap oluşturma, giriş ve çıkış
- Hesap başına ayrı kariyer ve lig
- Kulüp adı, oyuncu kadrosu ve piyasa değerleri
- 4-3-3 / 4-4-2 dizilişleri, ilk 11 seçimi ve mevki uyumu
- Takım gücü ve element bonusu hesabı
- Haftalık fikstür, maç simülasyonu, gol/asist ve oyuncu istatistikleri
- Puan durumu, oyuncu sıralamaları ve diziliş performansı
- Transfer pazarı, teklif değerlendirme, transfer geçmişi ve finans
- Sezon sonu oyuncu gelişimi, yeni sezon ve sezon arşivi
- Bellek modu ve PostgreSQL üzerinden kalıcı kayıt desteği

## Çalıştırma

Gereksinimler: Python 3.10 veya üstü ve PowerShell.

Proje klasöründe bağımlılıkları kur:

~~~powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

Demo sunucusunu başlat:

~~~powershell
.\run_demo.ps1
~~~

Arayüz: http://127.0.0.1:8765

API belgeleri: http://127.0.0.1:8765/docs

Betik sunucuyu bellek modunda başlatır. Elle başlatmak istersen:

~~~powershell
$env:BIL372_USER_STORE = "memory"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
~~~

Bellek modunda hesaplar, maçlar ve kariyer ilerlemesi sunucu çalıştığı sürece tutulur; sunucu yeniden başlatılınca sıfırlanır.

### PostgreSQL modu

Kalıcı kayıt için önce 02_PostgreSQL_Gelistirme_Rehberi.md içindeki veritabanı, rol, ODBC sürücüsü ve .env kurulum adımlarını tamamla. Ardından PowerShell’de:

~~~powershell
$env:BIL372_USER_STORE = "postgres"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
~~~

run_demo.ps1 bellek modunu seçtiği için PostgreSQL’de çalıştırırken yukarıdaki komutu kullan. .env dosyası Git tarafından yok sayılır; yerel veritabanı parolalarını GitHub’a ekleme.

## Proje yapısı

~~~text
backend/       FastAPI uçları, oyun kuralları, maç motoru ve PostgreSQL katmanı
web/           Tarayıcı arayüzü (HTML, CSS, JavaScript)
docs/          SQL kayıt örnekleri ve OpenAPI tanımı
test_*.py      Backend oyun mantığı ve veri katmanı için testler
requirements.txt
run_demo.ps1
00_*.md        Oyun ve proje tanıtımı
01_*.md        Arayüz geliştirme rehberi
02_*.md        PostgreSQL ve ders teslimi rehberi
~~~

Arayüz JSON isteklerini aynı FastAPI sunucusuna gönderir ve kişisel uçlarda Bearer token kullanır. Backend bellek modunda kariyeri süreç belleğinde saklar; PostgreSQL modunda kariyer, kulüp, oyuncu, sezon, fikstür, maç ve transfer verileri ilişkisel tablolara yazılır.

## Ders kapsamı

Bu depoda oynanabilir web demosu, backend ve veritabanı tasarım rehberleri bulunur. Büyük sentetik veri yükleme, beş analitik sorgunun gerçek PostgreSQL üzerinde ölçülmesi ve indeks öncesi/sonrası planların raporlanması gibi ders teslim adımları 02_PostgreSQL_Gelistirme_Rehberi.md içinde ayrıca açıklanmıştır.
