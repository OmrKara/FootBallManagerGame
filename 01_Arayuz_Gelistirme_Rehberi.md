# BİL372 · Futbol Kulübü Yönetim Sistemi
## Arayüz geliştirme rehberi

**Görevin** kullanıcının bir kulüp yönetebileceği yerel web arayüzünü HTML, CSS ve JavaScript ile geliştirmek. Backend hazır. Tarayıcı FastAPI’ye JSON gönderir ve gelen sonucu gösterir. PostgreSQL bağlantısını, maç motorunu, oyuncu gelişimini ve bütçe hesabını backend yönetir. İlk ekranları geliştirmek için bellek modu yeterlidir.

### 1. Oyuncunun izleyeceği yol

Kullanıcı kayıt olur, giriş yapar ve kendisine ait tek kariyeri açar. İlk girişte kendi kulübünün adını seçer. Diğer üç kulübün adı bir özellik ve bir hayvan adından üretilir. Başlangıçta dört kulübün her birinde 12 futbolcu vardır. Futbolcuların ad ve soyadları havuzdan, yedi yetenek puanı rastgele gelir. Her oyuncunun element taşıma olasılığı %70’tir. Elementsiz oyuncuyu “—” ile göster. Element sayıları, seçilen mevki ve mevki uyumu takımın savunma, orta saha ve hücum gücünü etkiler.

Kullanıcı ilk 11’i seçer, haftayı oynatır, skorları ve gol/asist olaylarını görür. Dört takımlı çift devreli lig altı hafta ve 12 maç sürer. Kullanıcı transfer teklifi verebilir. Kabul edilen transfer iki kulübün bütçesini ve oyuncunun kulübünü değiştirir. Finans ekranı transferleri gösterir. Son haftada oyuncuların yaşı ve mevkiye bağlı özelliği güncellenir. Yeni sezonda aynı kadro ve bütçeyle devam edilir, fikstür ve puan tablosu yeniden başlar. Eski sezonun maçları arşivden okunur.

### 2. İlk çalıştırma

Backend paketini bir klasöre çıkar. VS Code’da içinde `backend` ve `requirements.txt` bulunan klasörü aç. Windows PowerShell’de sırayla çalıştır:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:BIL372_USER_STORE = "memory"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Tarayıcıda http://127.0.0.1:8000/docs aç. Önce kayıt ve giriş işlemlerini dene. Güncel istek şeması http://127.0.0.1:8000/openapi.json adresindedir. Orada /career/club ile /career/season uçlarını görmelisin. Eksikse çalışan backend sürümünü proje sahibiyle kontrol et. Bellek modunda sunucuyu kapatmak veya otomatik yeniden yükleme, örnek hesap ve kariyer durumunu sıfırlar. İki ayrı tarayıcı kullanıcısı için iki ayrı giriş yap.

**Tarayıcı bağlantısı.** En basit seçenek sayfaları FastAPI ile aynı kökenden sunup aşağıdaki örnekteki göreli adresleri kullanmak. Statik dosyalar henüz bağlanmadıysa önce /docs ile dene. VS Code Live Server gibi ayrı bir sunucu kullanıyorsan gerçek API adresini belirt ve backend sorumlusuyla o sayfanın tam kökeni için CORS ayarla. Örneğin http://127.0.0.1:5500 için Authorization ve Content-Type başlıkları ile GET, POST, PUT istekleri kabul edilmeli. Adres çubuğundaki hostname ve port önemlidir.

### 3. Oturum ve ilk ekran

| İşlem | Gönder | Yanıttan kullan |
|---|---|---|
| POST /auth/register | JSON ile username, password | user_id, username. Başarıdan sonra giriş yap. |
| POST /auth/login | Aynı iki alan | access_token ve user. Sonraki kişisel çağrılarda token kullan. |
| GET /auth/me | Bearer başlığı | Oturum sahibinin user_id ve username alanları. |
| POST /auth/logout | Bearer başlığı, gövde yok | Başarılı çıkışta istemcideki tokenı sil. Eski tokenla /auth/me artık 401 verir. |
| GET /career/club | Bearer | club_id, name, clubs dizisi. name null ise kulüp adı ekranını aç. |
| PUT /career/club | Örneğin {"name":"Ankara Yıldızları"} | Güncellenen kulüp profili. Ad 1–60 karakter, boş olamaz. Başka kulübün adı seçilemez. Seçilmiş adı başka bir adla değiştirmek 409 verir. |

**Her kişisel istek** `Authorization: Bearer <access_token>` başlığı taşır. Kariyer kimliği oturumdan belirlenir. Başlangıçtaki 10 numaralı kulüp farklı kariyerlerde de bulunabilir. Seçilen kulübün kimliği için sunucunun döndürdüğü club_id değerini kullan. /demo/season ortak deneme alanıdır; kullanıcı hesabının ilerlemesini kişisel /career uçlarından oku.

Aynı kökenden servis edilen sayfa için çalışan çağrı örneği. Oturum açma formu kullanıcı adı ve parolayı login fonksiyonuna verir. Token bu örnekte sekmenin belleğindedir.

```javascript
let token = "";
async function api(path, method = "GET", data) {
  const headers = {};
  if (token) headers.Authorization = "Bearer " + token;
  if (data !== undefined) headers["Content-Type"] = "application/json";
  const response = await fetch(path, {
    method, headers,
    body: data === undefined ? undefined : JSON.stringify(data)
  });
  const result = await response.json();
  if (!response.ok) {
    const detail = result.detail;
    const message = typeof detail === "string" ? detail :
      detail?.message ?? JSON.stringify(detail ?? result);
    throw Object.assign(new Error(message), {status: response.status, detail});
  }
  return result;
}
async function login(username, password) {
  const result = await api("/auth/login", "POST", {username, password});
  token = result.access_token;
  return api("/career/club");
}
```

### 4. Ekran ve çağrı sözlüğü

**Aşağıdaki tablolarda S = /career/season.** Örneğin GET S/fixtures, GET /career/season/fixtures demektir. GET çağrılarında filtreler URL sorgu parametresidir. Birden çok filtreyi JavaScript URLSearchParams ile birleştir. Kullanılmayan anahtarı sorguya ekleme. Liste uçlarında boş dizi normal bir sonuçtur.

| Ekran | Yöntem ve yol | İstek ve gösterilecek sonuç |
|---|---|---|
| Ana sayfa | GET S | club_id, budget, season_no, next_week, last_week, finished, standings, last_match, next_match. İlk hafta last_match, son maçtan sonra next_match boş olabilir. Puan tablosundaki played, won, drawn, lost, goals_for, goals_against, goal_difference, points alanlarını göster. |
| Diziliş seçimi | GET S/formations | Her diziliş için name ve slots dizisi. 4-3-3 ve 4-4-2 slotlarını sunucunun sırasıyla çiz. CB gibi mevkiler birden fazla olabilir. Seçim anahtarı slot_id’dir. |
| Kadro | GET S/lineup | club_id, season_no, next_week, finished, formation, players, formation_slots, selections, power. İsimler first_name ve last_name, mevki primary_position, uygunluk compatibility. power.final_power içindeki DEF, MID, ATT değerlerini göster. |
| Kadro kaydı | PUT S/lineup | expected_season, expected_week, selections ve isteğe bağlı formation. Her seçimde slot_id ve player_id bulunur. 11 farklı oyuncuyu 11 geçerli slota yerleştir. Başarı yanıtı seçimleri ve yeni gücü döndürür. |
| Haftayı oynat | POST S/advance | expected_season ve expected_week. Sonuçta played_week, matches, standings, finished, next_week bulunur. Oynanan haftanın tüm maçlarını göster, ardından ana sayfayı yeniden oku. |
| Fikstür | GET S/fixtures | İsteğe bağlı week_no, season_no, opponent_id, venue=home/away, result=win/draw/loss. Kulüp filtresi yoksa tüm lig gelir. Rakip, saha ve sonuç filtreleri yönetilen kulüp açısından çalışır. |
| Maç detayı | GET S/matches/{match_id} | İsteğe bağlı season_no ve event_type=GOAL/ASSIST. Skor, lineups.home/away, formations, events, player_stats. Planlanan maçta skor ve kadrolar null, olaylar ve istatistikler boş dizidir. Olay türü filtresi yalnız olay listesini süzer. |
| Oyuncu sıralaması | GET S/player-stats | sort_by=goals/assists/rating, club_id, min_matches (en az 1), position, element, season_no. matches_played, minutes_played, goals, assists; rating sıralamasında ayrıca rated_matches, avg_rating, last_5_rating. Kulüp ve mevki maç anına göre değerlendirilir. |
| Diziliş performansı | GET S/formation-stats | İsteğe bağlı club_id. Güncel sezonda diziliş başına played, won, drawn, lost, goals_for, goals_against, win_pct. |
| Transfer pazarı | GET S/transfer-market | position, element, min_value, max_value. Fiyat sınırları dahil. İkincil mevkiler de aranır. Diğer kulüplerden oyuncuların kimliği, adı, kulübü, özellikleri, compatibility ve market_value gelir. Elementsiz için element=none. |
| Teklif oluştur | POST S/transfer-offers | player_id, amount, expected_season, expected_week. Tutar pozitif tam sayıdır. Başarı 201 ve PENDING teklif. |
| Tekliflerim | GET S/transfer-offers | Teklif dizisi, en yeni önce. offer_id, player_id, buyer_club_id, seller_club_id, amount, status. reason ve resolved_week mevcutsa göster. |
| Teklifi geri çek | POST S/transfer-offers/{offer_id}/cancel | Gövde yok. Bekleyen teklifi CANCELLED yapar. |
| Teklifi değerlendir | POST S/transfer-offers/{offer_id}/resolve | Gövde yok. Sonucu status ile oku. REJECTED ve gerekçesi de başarılı HTTP yanıtı olabilir. |
| Transfer geçmişi | GET S/transfers | club_id, budget, transfers. Her harekette offer_id, player_id, from_club_id, to_club_id, fee, season_no, week_no. |
| Finans | GET S/finance | budget, transfer_income, transfer_expense, net_transfer, movements. Alıcıda TRANSFER_OUT eksi tutar, satıcıda TRANSFER_IN artı tutar. |
| Yeni sezon | POST S/new-season | {"expected_season":1} örneğindeki sayıyı canlı durumdan al. Mevcut sezon bitince açılır. Yeni season_no, next_week, finished, standings döner. |
| Sezon arşivi | GET S/history/{season_no} | Açılan yeni sezondan önceki tamamlanmış sezonun season_no, matches ve standings verileri. Arşiv maç detayına giderken hem sezonu hem maç numarasını taşı. |

### 5. İki akışı uçtan uca bağlama

**Kadro → maç.** İlk isteğin döndürdüğü sezon ve hafta, kullanıcının gördüğü ekranın sürümüdür. Gönderirken bu değerleri koru. Kullanıcı formdayken başka sekme haftayı oynatmışsa 409 alıp ekranı yenile. Hafta oynatma düğmesini istek sürerken devre dışı bırak.

```javascript
const S = "/career/season";
const kadro = await api(S + "/lineup");
const surum = {expected_week: kadro.next_week, expected_season: kadro.season_no};
// Form, seçilen slotların player_id değerlerini değiştirir.
await api(S + "/lineup", "PUT", {
  ...surum, formation: kadro.formation, selections: kadro.selections
});
const hafta = await api(S + "/advance", "POST", surum);
const mac = hafta.matches[0];
const detay = await api(S + "/matches/" + mac.match_id +
  "?season_no=" + kadro.season_no);
```

**Pazar → teklif → finans.** Pazardan oyuncu seç. Ana sayfadan okuduğun sezon ve hafta ile teklifi gönder. Örneğin başlangıç dünyasındaki 2011 numaralı yedek için 400000 tutarlı teklif kabul edilirse 2000000 bütçe 1600000 olur. Oyuncu ilk 11’deyse veya bedel piyasa değerinin altındaysa satıcı reddeder. Bütçe yetersizse bekleyen teklif korunur. Sabit numaraları yalnız örnek kabul et. Kabulden sonra kadro, pazar, teklifler ve finansı yeniden oku.

### 6. Hata ve boş ekran davranışı

| Durum | Arayüzün davranışı |
|---|---|
| 401 | Kişisel ekranı kapat, oturumu temizle, tekrar giriş göster. |
| 404 | İlgili maç, oyuncu, teklif, sezon veya kulüp bulunamadı. Seçimi temizle ve geçerli listeye dön. |
| 409 | Bayat hafta, tamamlanmış sezon, ikinci bekleyen teklif, yetersiz bütçe veya ad çakışması gibi iş kuralı. detail alanını göster, ilgili veriyi yeniden getir. Yazma isteğini otomatik tekrarlama. |
| 422 | Eksik/uygunsuz alan, geçersiz diziliş veya fiyat aralığı. detail metin, nesne veya hata listesi olabilir. Formdaki değerleri koru. |
| Bağlantı kesilmesi | Özellikle transfer, hafta ve sezon geçişinde önce güncel durumu tekrar oku. İşlem sunucuda tamamlanmış olabilir. |
| Oynanmamış maç / boş sıralama | Skoru “Oynanmadı” olarak, sonuç listesini “Henüz maç oynanmadı” olarak göster. Gerçek 0-0 ayrı durumdur. |

### 7. Teslim öncesi kabul denemesi

1. A ve B adlı iki ayrı hesapla giriş yap. A kulübüne isim verip bir hafta oynat. B hâlâ ilk haftada ve başlangıç bütçesinde kalmalı.
2. Kadroda yedek kaleciyi seç ve kaydet. Haftayı oynatıp maç kadrosunda doğru 11 oyuncuyu ve yedek kalecinin maç istatistiğini gör. Sonraki hafta kadroyu değiştirince eski maçın 11’i korunmalı.
3. Gol ve asist filtreleri, maç ekranındaki olaya ait oyuncuyu göstermeli. Örneğin Türkçe karakter içeren isimler puan tablosu, kadro ve maç ekranında doğru görünmeli.
4. Bir teklifi iptal et, sonra yeni teklif oluşturup kabul sonucunu incele. Transfer yalnız bir defa gider yazmalı. Başarılı ve reddedilmiş teklif görünümlerini kontrol et.
5. Altıncı haftadan sonra “Yeni sezon” eylemi açılmalı. İkinci sezon ilk hafta ve sıfır puanla açılmalı; arşivde ilk sezonun 12 maçı bulunmalı.
6. Çıkış yaptıktan sonra /auth/me eski tokenı reddetmeli. Son teslimde çalıştırma talimatı, ekran kaynakları ve bu akışların kısa demo adımları backend sorumlusuna verilir.

**Elindeki dosyalar.** Bu rehber, güncel backend kaynakları, testler, requirements.txt ve canlı sunucudan alınmış docs/openapi.json. test_sql_api_modes.py kadrodan yeni sezona uzanan örnek akışı gösterir. Kesin rota ve gövde modellerini backend/season_api.py ile backend/club_profile.py üzerinden karşılaştır. Eski demo-api.json kişisel kariyer uçlarının tamamını içermeyebilir.
