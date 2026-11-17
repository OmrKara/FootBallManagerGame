(() => {
  'use strict';

  const SEASON = '/career/season';
  const $ = (selector, root) => (root || document).querySelector(selector);
  const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));
  const state = {
    token: sessionStorage.getItem('bil372_token') || '',
    user: null,
    club: null,
    season: null,
    lineup: null,
    formations: [],
    view: 'home',
    fixtureWeek: '',
    fixtureSeason: null,
    archiveSeason: null,
    lastAdvance: null,
    authMode: 'login',
    toastTimer: null
  };

  const POSITION_NAMES = {
    GK: 'Kaleci', RB: 'Sağ bek', CB: 'Stoper', LB: 'Sol bek',
    CM: 'Merkez orta saha', CAM: 'Ofansif orta saha', RM: 'Sağ orta saha',
    LM: 'Sol orta saha', RW: 'Sağ kanat', LW: 'Sol kanat', ST: 'Forvet'
  };
  const ELEMENT_NAMES = {Fire: 'Ateş', Earth: 'Toprak', Air: 'Hava', Water: 'Su', none: 'Elementsiz'};
  const ATTRIBUTE_NAMES = {
    defending: 'Savunma', strength: 'Güç', stamina: 'Dayanıklılık',
    passing: 'Pas', dribbling: 'Top sürme', shooting: 'Şut', pace: 'Hız'
  };
  const MONEY = new Intl.NumberFormat('tr-TR', {style: 'currency', currency: 'TRY', maximumFractionDigits: 0});

  async function api(path, method, data) {
    const headers = {};
    if (state.token) headers.Authorization = 'Bearer ' + state.token;
    if (data !== undefined) headers['Content-Type'] = 'application/json';
    const response = await fetch(path, {
      method: method || 'GET',
      headers,
      body: data === undefined ? undefined : JSON.stringify(data)
    });
    const text = await response.text();
    let result = null;
    if (text) {
      try { result = JSON.parse(text); } catch (_) { result = text; }
    }
    if (!response.ok) {
      const detail = result && result.detail;
      const message = typeof detail === 'string' ? detail :
        (detail && detail.message) || (detail ? JSON.stringify(detail) : response.statusText);
      const error = new Error(message || 'İstek tamamlanamadı.');
      error.status = response.status;
      error.detail = detail;
      throw error;
    }
    return result;
  }

  function esc(value) {
    return String(value === null || value === undefined ? '' : value)
      .replace(/[&<>"']/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[char]));
  }
  function money(value) { return MONEY.format(Number(value) || 0); }
  function posName(position) { return POSITION_NAMES[position] || position || '—'; }
  function elementName(element) { return ELEMENT_NAMES[element || 'none'] || element || '—'; }
  function elementTag(element) {
    const key = element || 'none';
    return '<span class="tag element-' + esc(key) + '">' + esc(elementName(element)) + '</span>';
  }
  function clubName(id) {
    const club = (state.club && state.club.clubs || []).find(row => Number(row.club_id) === Number(id));
    return (club && club.name) || ('Kulüp ' + id);
  }
  function playerName(player) {
    return player.player_name || [player.first_name, player.last_name].filter(Boolean).join(' ') || ('Oyuncu ' + player.player_id);
  }
  function notify(message, error) {
    const toast = $('#toast');
    toast.textContent = message;
    toast.classList.toggle('error', !!error);
    toast.classList.add('show');
    clearTimeout(state.toastTimer);
    state.toastTimer = setTimeout(() => toast.classList.remove('show'), 3600);
  }
  function showAuth() {
    $('#auth-view').classList.remove('hidden');
    $('#setup-view').classList.add('hidden');
    $('#app-view').classList.add('hidden');
    renderAuthMode();
  }
  function renderAuthMode() {
    $$('.auth-tab').forEach(button => button.classList.toggle('active', button.dataset.authMode === state.authMode));
    $('#auth-submit').textContent = state.authMode === 'login' ? 'Giriş yap' : 'Hesap oluştur';
  }
  function showSetup() {
    $('#auth-view').classList.add('hidden');
    $('#setup-view').classList.remove('hidden');
    $('#app-view').classList.add('hidden');
  }
  function updateTop() {
    if (!state.user || !state.club || !state.season) return;
    $('#top-club').textContent = state.club.name || 'Kulübüm';
    $('#top-season').textContent = 'Sezon ' + state.season.season_no +
      (state.season.finished ? ' · tamamlandı' : ' · Hafta ' + state.season.next_week);
    $('#top-budget').textContent = money(state.season.budget);
    $('#top-user').textContent = state.user.username;
  }
  async function loadBase() {
    const values = await Promise.all([api('/career/club'), api(SEASON)]);
    state.club = values[0];
    state.season = values[1];
    updateTop();
  }
  async function enterApp() {
    try {
      state.user = await api('/auth/me');
      await loadBase();
      $('#auth-view').classList.add('hidden');
      $('#app-view').classList.remove('hidden');
      if (!state.club.name) {
        showSetup();
        return;
      }
      state.view = 'home';
      renderNav();
      await renderPage();
    } catch (error) {
      state.token = '';
      sessionStorage.removeItem('bil372_token');
      showAuth();
      if (error.status !== 401) notify(error.message, true);
    }
  }
  function renderNav() {
    $$('.nav-item').forEach(button => button.classList.toggle('active', button.dataset.view === state.view));
  }
  async function renderPage() {
    renderNav();
    const page = $('#page');
    page.innerHTML = '<div class="loading">Menajer masası hazırlanıyor…</div>';
    try {
      if (state.view === 'home') await renderHome();
      else if (state.view === 'lineup') await renderLineup();
      else if (state.view === 'matches') await renderMatches();
      else if (state.view === 'transfers') await renderTransfers();
      else if (state.view === 'stats') await renderStats();
      else if (state.view === 'finance') await renderFinance();
      else if (state.view === 'history') await renderHistory();
    } catch (error) {
      if (error.status === 401) {
        state.token = '';
        sessionStorage.removeItem('bil372_token');
        showAuth();
      } else {
        page.innerHTML = '<div class="notice error">' + esc(error.message) +
          '</div><button class="button secondary" data-action="refresh">Yeniden dene</button>';
      }
    }
  }
  function pageHeading(title, description, action) {
    return '<div class="page-heading"><div><h1>' + title + '</h1><p>' + description +
      '</p></div>' + (action || '') + '</div>';
  }
  function panelHeading(title, note) {
    return '<div class="panel-head"><h2>' + title + '</h2>' +
      (note ? '<span class="subhead">' + note + '</span>' : '') + '</div>';
  }
  function matchRow(match, seasonNo) {
    const score = match.status === 'played'
      ? '<span class="match-score">' + match.home_goals + ' : ' + match.away_goals + '</span>'
      : '<span class="result-pill scheduled">Oynanmadı</span>';
    return '<div class="match-row clickable" data-action="match-detail" data-match-id="' + match.match_id +
      '" data-season-no="' + (seasonNo || state.season.season_no) + '"><span class="match-week">' +
      match.week_no + '. hafta</span><span class="match-pair">' + esc(match.home_club_name || clubName(match.home_club_id)) +
      '<span>—</span>' + esc(match.away_club_name || clubName(match.away_club_id)) +
      '</span>' + score + '</div>';
  }
  function standingsTable(rows) {
    if (!rows || !rows.length) return '<div class="empty-state">Puan durumu henüz oluşmadı. İlk haftayı oynat.</div>';
    return '<div class="table-wrap"><table class="standings"><thead><tr><th>#</th><th>Kulüp</th><th>O</th><th>G</th><th>B</th><th>M</th><th>AV</th><th>P</th></tr></thead><tbody>' +
      rows.map((row, index) => '<tr class="' + (Number(row.club_id) === Number(state.season.club_id) ? 'my-club' : '') +
        '"><td class="rank">' + (index + 1) + '</td><td class="club-cell">' + esc(row.club_name || clubName(row.club_id)) +
        '</td><td>' + row.played + '</td><td>' + row.won + '</td><td>' + row.drawn + '</td><td>' + row.lost +
        '</td><td>' + (row.goal_difference > 0 ? '+' : '') + row.goal_difference + '</td><td>' + row.points +
        '</td></tr>').join('') + '</tbody></table></div>';
  }
  async function renderHome() {
    await loadBase();
    const s = state.season;
    const played = s.finished ? s.last_week : s.next_week - 1;
    const next = s.next_match;
    const feature = next
      ? '<div class="fixture-feature"><div class="feature-kicker">SIRADAKİ MAÇ · ' + next.week_no + '. HAFTA</div><div class="feature-teams"><div class="feature-team">' +
        esc(next.home_club_name) + '</div><span class="versus">VS</span><div class="feature-team">' +
        esc(next.away_club_name) + '</div></div><div class="feature-meta"><span>' +
        (Number(next.home_club_id) === Number(s.club_id) ? 'Ev sahibi' : 'Deplasman') +
        '</span><strong>HAFTA ' + next.week_no + '</strong></div><div class="feature-actions"><button class="button primary" data-action="advance">Haftayı oynat <span>→</span></button></div></div>'
      : '<div class="fixture-feature"><div class="feature-kicker">SEZON TAMAMLANDI</div><div class="feature-teams"><div class="feature-team">Altı haftalık lig sona erdi.</div></div><div class="feature-meta"><span>Puan tablosu kesinleşti</span><strong>🏆</strong></div><div class="feature-actions"><button class="button primary" data-action="new-season">Yeni sezonu başlat <span>→</span></button></div></div>';
    let advance = '';
    if (state.lastAdvance && state.lastAdvance.season_no === s.season_no) {
      advance = '<div class="panel"><div class="panel-head"><h2>' + state.lastAdvance.played_week +
        '. hafta sonuçları</h2><span class="subhead">Bu hafta iki maç oynandı</span></div><div class="match-list">' +
        state.lastAdvance.matches.map(match => matchRow({
          ...match, status: 'played', home_club_name: clubName(match.home_club_id),
          away_club_name: clubName(match.away_club_id)
        }, s.season_no)).join('') + '</div></div>';
    }
    const recent = s.last_match
      ? '<div class="match-row clickable" data-action="match-detail" data-match-id="' + s.last_match.match_id +
        '" data-season-no="' + s.season_no + '"><span class="match-week">' + s.last_match.week_no +
        '. hafta</span><span class="match-pair">' + esc(s.last_match.home_club_name) + '<span>—</span>' +
        esc(s.last_match.away_club_name) + '</span><span class="match-score">' + s.last_match.home_goals +
        ' : ' + s.last_match.away_goals + '</span></div>'
      : '<div class="empty-state">İlk maçın henüz oynanmadı.</div>';
    $('#page').innerHTML = '<div class="page-wrap">' +
      pageHeading('Genel bakış', 'Kulübünün durumunu gör ve bir sonraki maç kararını ver.') +
      '<div class="grid metric-grid"><div class="metric-card"><div class="metric-label">SEZON</div><div class="metric-value">' +
      s.season_no + '</div><div class="metric-note">Kariyer sezonu</div></div><div class="metric-card"><div class="metric-label">HAFTA</div><div class="metric-value">' +
      (s.finished ? '6 / 6' : s.next_week + ' / ' + s.last_week) + '</div><div class="metric-note">' +
      (s.finished ? 'Sezon tamamlandı' : played + ' hafta geride kaldı') + '</div></div><div class="metric-card"><div class="metric-label">KULÜP BÜTÇESİ</div><div class="metric-value">' +
      money(s.budget) + '</div><div class="metric-note">Transfer gelir ve giderleri dahil</div></div><div class="metric-card"><div class="metric-label">LİGDEKİ SIRA</div><div class="metric-value">' +
      (s.standings.findIndex(row => Number(row.club_id) === Number(s.club_id)) + 1 || '—') +
      '</div><div class="metric-note">' + s.standings.length + ' kulüplü lig</div></div></div>' +
      '<div class="grid home-grid"><div>' + feature + advance + '<section class="panel">' +
      panelHeading('Puan durumu', 'Galibiyet 3 · Beraberlik 1 puan') + standingsTable(s.standings) +
      '</section></div><div><section class="panel">' + panelHeading('Son maç', 'Maç raporunu açmak için seç') +
      recent + '</section><section class="panel">' + panelHeading('Ligin yapısı', 'Çift devreli lig') +
      '<div class="player-mini"><div><strong>4 kulüp</strong><span>Her hafta iki karşılaşma</span></div><div class="mini-value">12 maç</div></div>' +
      '<div class="player-mini"><div><strong>6 hafta</strong><span>Ev ve deplasman maçları</span></div><div class="mini-value">3 puan</div></div>' +
      '</section></div></div></div>';
  }

  async function renderLineup() {
    const results = await Promise.all([api(SEASON + '/lineup'), api(SEASON + '/formations')]);
    state.lineup = results[0];
    state.formations = results[1];
    const data = state.lineup;
    const picks = new Map(data.selections.map(item => [Number(item.slot_id), Number(item.player_id)]));
    const slots = data.formation_slots;
    const players = data.players.slice().sort((a, b) => Number(a.player_id) - Number(b.player_id));
    const chosen = Array.from(picks.values());
    const rows = slots.map(slot => {
      const selectedId = picks.get(Number(slot.slot_id));
      const usedElsewhere = chosen.filter(id => id !== selectedId);
      const options = players.filter(player => player.compatibility && player.compatibility[slot.position] &&
        (!usedElsewhere.includes(Number(player.player_id)) || Number(player.player_id) === selectedId))
        .sort((a, b) => (b.compatibility[slot.position] || 0) - (a.compatibility[slot.position] || 0));
      return '<div class="slot-row"><div><span class="slot-position">' + esc(slot.position) +
        '</span><span class="slot-num">' + String(slot.slot_id).padStart(2, '0') + '</span></div>' +
        '<div><strong style="font-size:10px">' + esc(posName(slot.position)) + '</strong><div class="muted" style="font-size:9px;margin-top:3px">' +
        (selectedId && data.players.find(p => Number(p.player_id) === selectedId)
          ? 'Uyum ' + (data.players.find(p => Number(p.player_id) === selectedId).compatibility[slot.position] || 0) + '%'
          : 'Mevki seç') + '</div></div><select data-slot-id="' + slot.slot_id + '" aria-label="' + esc(posName(slot.position)) + '">' +
        '<option value="">Oyuncu seç</option>' + options.map(player => '<option value="' + player.player_id + '"' +
          (Number(player.player_id) === selectedId ? ' selected' : '') + '>' + esc(playerName(player)) +
          ' · ' + esc(player.primary_position) + ' · uyum ' + player.compatibility[slot.position] + '%</option>').join('') +
        '</select></div>';
    }).join('');
    const power = data.power && data.power.final_power ? data.power : null;
    const powerHtml = power
      ? '<div class="power-grid">' + ['DEF', 'MID', 'ATT'].map((key, index) =>
        '<div class="power-box"><span>' + ['Savunma', 'Orta saha', 'Hücum'][index] +
        '</span><strong>' + power.final_power[key] + '</strong><small>temel ' + power.base_power[key] +
        ' · bonus ' + (power.bonus_percent && power.bonus_percent[key] || 0) + '%</small></div>').join('') + '</div>' +
        '<div style="margin-top:14px"><div class="muted" style="font-size:9px;margin-bottom:8px">İLK 11 ELEMENTLERİ</div>' +
        Object.keys(power.element_counts || {}).map(element => '<span style="margin:0 5px 5px 0">' +
          elementTag(element) + ' ×' + power.element_counts[element] + '</span>').join('') + '</div>'
      : '<div class="empty-state">Geçerli bir ilk 11 seçince takım gücü hesaplanır.</div>';
    const playerRows = players.map(player => '<div class="player-mini"><div><strong>' + esc(playerName(player)) +
      '</strong><span>' + esc(posName(player.primary_position)) + ' · ' + player.age + ' yaş · ' +
      esc(elementName(player.element)) + '</span></div><div class="mini-value">' + money(player.market_value) +
      '<br><span>' + player.shooting + ' ŞUT · ' + player.passing + ' PAS</span></div></div>').join('');
    const formOptions = state.formations.map(form => '<option value="' + esc(form.name) + '"' +
      (form.name === data.formation ? ' selected' : '') + '>' + esc(form.name) + '</option>').join('');
    $('#page').innerHTML = '<div class="page-wrap">' + pageHeading('Kadro ve taktik',
      'İlk 11’ini ve dizilişini belirle. Aynı oyuncuyu iki slota koyamazsın.',
      '<button class="button primary" data-action="save-lineup"' + (data.finished ? ' disabled' : '') + '>Kadroyu kaydet</button>') +
      (data.finished ? '<div class="notice">Sezon tamamlandığı için kadro değişikliği yeni sezon başlayınca açılır.</div>' : '') +
      '<div class="grid lineup-grid"><div><section class="panel">' + panelHeading('Sahaya çıkacak 11', 'Pozisyon uyumu takım gücünü etkiler') +
      '<div class="filter-row"><label class="compact">Diziliş<select id="formation-select">' + formOptions + '</select></label>' +
      '<span class="tag">Kulübünde ' + players.length + ' oyuncu var</span></div><div class="slot-list" id="slot-list">' + rows +
      '</div></section><section class="panel">' + panelHeading('Kadro', 'Piyasa değeri ve temel özellikler') +
      '<div class="player-list">' + playerRows + '</div></section></div><div><section class="panel">' +
      panelHeading('Takım gücü', 'Sunucu hesaplaması') + powerHtml + '</section><section class="panel">' +
      panelHeading('Bonus nasıl çalışır?', 'Element uyumları') +
      '<p class="muted" style="font-size:10px;line-height:1.6;margin-bottom:0">İlk 11’de aynı elementten yeterli sayıda oyuncu bulunduğunda takımın savunma, orta saha veya hücum gücü bonus alır. Elementsiz oyuncular bu sayıya katılmaz.</p>' +
      '</section></div></div></div>';
  }

  async function renderMatches() {
    await loadBase();
    if (state.fixtureSeason === null) state.fixtureSeason = state.season.season_no;
    const params = new URLSearchParams();
    params.set('season_no', state.fixtureSeason);
    if (state.fixtureWeek) params.set('week_no', state.fixtureWeek);
    const fixtures = await api(SEASON + '/fixtures?' + params.toString());
    const weekOptions = Array.from({length: state.season.last_week}, (_, index) => index + 1)
      .map(week => '<option value="' + week + '"' + (String(week) === String(state.fixtureWeek) ? ' selected' : '') +
        '>' + week + '. hafta</option>').join('');
    const seasons = Array.from({length: state.season.season_no}, (_, index) => state.season.season_no - index)
      .map(number => '<option value="' + number + '"' + (number === Number(state.fixtureSeason) ? ' selected' : '') +
        '>Sezon ' + number + '</option>').join('');
    $('#page').innerHTML = '<div class="page-wrap">' + pageHeading('Fikstür ve maçlar',
      'Maçın sonucunu, ilk 11’leri ve gol katkılarını incele.') +
      '<section class="panel">' + panelHeading('Karşılaşmalar', fixtures.length + ' maç') +
      '<div class="filter-row"><label class="compact">Sezon<select id="fixture-season">' + seasons +
      '</select></label><label class="compact">Hafta<select id="fixture-week"><option value="">Tüm haftalar</option>' +
      weekOptions + '</select></label></div>' +
      (fixtures.length ? '<div class="match-list">' + fixtures.map(match => matchRow(match, state.fixtureSeason)).join('') +
        '</div>' : '<div class="empty-state">Bu filtrelerle maç bulunamadı.</div>') + '</section></div>';
  }

  function playerStatsTable(rows, sortBy) {
    if (!rows.length) return '<div class="empty-state">Henüz maç verisi yok. Birkaç hafta oynadıktan sonra oyuncu istatistikleri burada görünür.</div>';
    return '<div class="table-wrap"><table class="data-table"><thead><tr><th>#</th><th>Oyuncu</th><th>Maç</th><th>Dakika</th><th>Gol</th><th>Asist</th>' +
      (sortBy === 'rating' ? '<th>Ort. puan</th><th>Son 5</th>' : '') +
      '</tr></thead><tbody>' + rows.map((row, index) => '<tr><td>' + (index + 1) + '</td><td><strong>' +
        esc(playerName(row)) + '</strong></td><td>' + row.matches_played + '</td><td>' + row.minutes_played +
        '</td><td>' + row.goals + '</td><td>' + row.assists + '</td>' +
        (sortBy === 'rating' ? '<td>' + row.avg_rating + '</td><td>' + row.last_5_rating + '</td>' : '') +
        '</tr>').join('') + '</tbody></table></div>';
  }
  async function renderStats() {
    await loadBase();
    const sortBy = ($('#stats-sort') || {}).value || 'goals';
    const minMatches = Number(($('#stats-min') || {}).value || 1);
    const params = new URLSearchParams({sort_by: sortBy, min_matches: String(minMatches), club_id: String(state.season.club_id)});
    const [rows, formations] = await Promise.all([
      api(SEASON + '/player-stats?' + params.toString()),
      api(SEASON + '/formation-stats?club_id=' + state.season.club_id)
    ]);
    const formationTable = formations.length
      ? '<div class="table-wrap"><table class="data-table"><thead><tr><th>Diziliş</th><th>Maç</th><th>G</th><th>B</th><th>M</th><th>Attığı</th><th>Yediği</th><th>Galibiyet %</th></tr></thead><tbody>' +
        formations.map(row => '<tr><td><strong>' + esc(row.formation) + '</strong></td><td>' + row.played +
          '</td><td>' + row.won + '</td><td>' + row.drawn + '</td><td>' + row.lost + '</td><td>' +
          row.goals_for + '</td><td>' + row.goals_against + '</td><td>' + row.win_pct + '%</td></tr>').join('') +
        '</tbody></table></div>'
      : '<div class="empty-state">Diziliş performansı için maç oynanması gerekiyor.</div>';
    $('#page').innerHTML = '<div class="page-wrap">' + pageHeading('İstatistikler',
      'Oyuncu katkısını ve sahaya sürdüğün dizilişlerin sonuçlarını karşılaştır.') +
      '<section class="panel">' + panelHeading('Oyuncu sıralaması', 'Yalnızca kulübündeki maç performansı') +
      '<div class="stat-controls"><label>Sıralama<select id="stats-sort"><option value="goals"' +
      (sortBy === 'goals' ? ' selected' : '') + '>Goller</option><option value="assists"' +
      (sortBy === 'assists' ? ' selected' : '') + '>Asistler</option><option value="rating"' +
      (sortBy === 'rating' ? ' selected' : '') + '>Maç puanı</option></select></label><label>En az maç<select id="stats-min">' +
      [1, 2, 3, 4, 5].map(number => '<option value="' + number + '"' + (number === minMatches ? ' selected' : '') +
        '>' + number + '</option>').join('') + '</select></label><button class="button secondary" data-action="apply-stats">Sırala</button></div>' +
      '<div style="height:14px"></div>' + playerStatsTable(rows, sortBy) + '</section><section class="panel">' +
      panelHeading('Diziliş performansı', 'Güncel sezon') + formationTable + '</section></div>';
  }

  function marketCard(player) {
    const attrs = ['pace', 'passing', 'shooting', 'defending'].map(key =>
      '<span>' + ATTRIBUTE_NAMES[key] + ' ' + player[key] + '</span>').join('');
    return '<article class="player-card"><div class="player-card-top"><div><h3>' + esc(playerName(player)) +
      '</h3><div class="meta">' + esc(player.club_name || clubName(player.club_id)) + ' · ' +
      esc(posName(player.primary_position)) + ' · ' + player.age + ' yaş</div></div>' + elementTag(player.element) +
      '</div><div class="price">' + money(player.market_value) + '</div><div class="player-attrs">' + attrs +
      '</div><form class="offer-form" data-player-id="' + player.player_id + '"><input type="number" name="amount" min="1" step="1" value="' +
      player.market_value + '" aria-label="Teklif tutarı"><button class="button primary small" type="submit"' +
      (state.season.finished ? ' disabled' : '') + '>Teklif ver</button></form></article>';
  }
  function offerRows(offers) {
    if (!offers.length) return '<div class="empty-state">Henüz teklif vermedin.</div>';
    return '<div class="table-wrap"><table class="data-table"><thead><tr><th>Oyuncu</th><th>Satıcı</th><th>Teklif</th><th>Durum</th><th>Sonuç</th><th></th></tr></thead><tbody>' +
      offers.map(offer => '<tr><td><strong>Oyuncu ' + offer.player_id + '</strong></td><td>' +
        esc(clubName(offer.seller_club_id)) + '</td><td>' + money(offer.amount) + '</td><td><span class="status ' +
        esc(offer.status) + '">' + ({PENDING: 'Bekliyor', ACCEPTED: 'Kabul edildi', REJECTED: 'Reddedildi', CANCELLED: 'Geri çekildi'}[offer.status] || offer.status) +
        '</span></td><td>' + esc(offer.reason || (offer.resolved_week ? offer.resolved_week + '. hafta' : '—')) + '</td><td>' +
        (offer.status === 'PENDING' ? '<button class="button ghost small" data-action="resolve-offer" data-offer-id="' +
          offer.offer_id + '">Değerlendir</button> <button class="button ghost small" data-action="cancel-offer" data-offer-id="' +
          offer.offer_id + '">Geri çek</button>' : '—') + '</td></tr>').join('') +
      '</tbody></table></div>';
  }
  async function renderTransfers() {
    await loadBase();
    const position = ($('#market-position') || {}).value || '';
    const element = ($('#market-element') || {}).value || '';
    const min = ($('#market-min') || {}).value || '';
    const max = ($('#market-max') || {}).value || '';
    const params = new URLSearchParams();
    if (position) params.set('position', position);
    if (element) params.set('element', element);
    if (min) params.set('min_value', min);
    if (max) params.set('max_value', max);
    const [market, offers] = await Promise.all([
      api(SEASON + '/transfer-market' + (params.size ? '?' + params.toString() : '')),
      api(SEASON + '/transfer-offers')
    ]);
    const positions = Object.keys(POSITION_NAMES).map(key => '<option value="' + key + '"' +
      (key === position ? ' selected' : '') + '>' + esc(key + ' · ' + POSITION_NAMES[key]) + '</option>').join('');
    $('#page').innerHTML = '<div class="page-wrap">' + pageHeading('Transfer pazarı',
      'Diğer kulüplerin kadrosunu incele, teklif ver ve sonucu değerlendir.',
      '<span class="tag">Bütçe ' + money(state.season.budget) + '</span>') +
      (state.season.finished ? '<div class="notice">Sezon bitti. Yeni sezon başlayınca teklif verebilirsin.</div>' : '') +
      '<section class="panel">' + panelHeading('Oyuncu ara', market.length + ' oyuncu') +
      '<div class="filter-row"><label class="compact">Mevki<select id="market-position"><option value="">Tüm mevkiler</option>' +
      positions + '</select></label><label class="compact">Element<select id="market-element"><option value="">Tümü</option>' +
      ['Fire', 'Earth', 'Air', 'Water'].map(item => '<option value="' + item + '"' +
        (element === item ? ' selected' : '') + '>' + elementName(item) + '</option>').join('') +
      '<option value="none"' + (element === 'none' ? ' selected' : '') + '>Elementsiz</option></select></label>' +
      '<label class="compact">En düşük değer<input id="market-min" type="number" min="0" value="' + esc(min) + '" placeholder="₺"></label>' +
      '<label class="compact">En yüksek değer<input id="market-max" type="number" min="0" value="' + esc(max) + '" placeholder="₺"></label>' +
      '<button class="button secondary" data-action="filter-market">Filtrele</button></div>' +
      (market.length ? '<div class="grid market-grid">' + market.map(marketCard).join('') + '</div>' :
        '<div class="empty-state">Bu filtrelerle oyuncu bulunamadı.</div>') +
      '</section><section class="panel">' + panelHeading('Tekliflerim', 'Bekleyen teklifleri değerlendir veya geri çek') +
      offerRows(offers) + '</section></div>';
  }

  async function renderFinance() {
    await loadBase();
    const data = await api(SEASON + '/finance');
    const transferData = await api(SEASON + '/transfers');
    const rows = data.movements || [];
    $('#page').innerHTML = '<div class="page-wrap">' + pageHeading('Finans',
      'Bütçen ve tamamlanan transferlerden gelen para hareketleri.') +
      '<div class="grid metric-grid"><div class="metric-card"><div class="metric-label">GÜNCEL BÜTÇE</div><div class="metric-value">' +
      money(data.budget) + '</div><div class="metric-note">Kullanılabilir kulüp bütçesi</div></div><div class="metric-card"><div class="metric-label">TRANSFER GELİRİ</div><div class="metric-value">' +
      money(data.transfer_income) + '</div><div class="metric-note">Oyuncu satışlarından</div></div><div class="metric-card"><div class="metric-label">TRANSFER GİDERİ</div><div class="metric-value">' +
      money(data.transfer_expense) + '</div><div class="metric-note">Oyuncu alımlarından</div></div><div class="metric-card"><div class="metric-label">NET TRANSFER</div><div class="metric-value">' +
      money(data.net_transfer) + '</div><div class="metric-note">Gelir eksi gider</div></div></div>' +
      '<section class="panel">' + panelHeading('Transfer hareketleri', rows.length + ' hareket') +
      (rows.length ? '<div class="table-wrap"><table class="data-table"><thead><tr><th>Sezon / hafta</th><th>Tür</th><th>Oyuncu</th><th>Diğer kulüp</th><th class="text-right">Tutar</th></tr></thead><tbody>' +
        rows.map(row => '<tr><td>' + row.season_no + ' / ' + row.week_no + '</td><td>' +
          (row.type === 'TRANSFER_OUT' ? 'Transfer gideri' : 'Transfer geliri') + '</td><td><strong>Oyuncu ' +
          row.player_id + '</strong></td><td>' + esc(clubName(row.other_club_id)) + '</td><td class="text-right">' +
          (row.amount < 0 ? '−' : '+') + money(Math.abs(row.amount)) + '</td></tr>').join('') +
        '</tbody></table></div>' : '<div class="empty-state">Henüz gerçekleşmiş transfer yok. Transfer pazarından oyuncu alabilirsin.</div>') +
      '</section><section class="panel">' + panelHeading('Transfer geçmişi', transferData.transfers.length + ' anlaşma') +
      (transferData.transfers.length ? '<div class="table-wrap"><table class="data-table"><thead><tr><th>Sezon / hafta</th><th>Oyuncu</th><th>Hareket</th><th>Bedel</th></tr></thead><tbody>' +
        transferData.transfers.map(row => '<tr><td>' + row.season_no + ' / ' + row.week_no + '</td><td><strong>Oyuncu ' +
          row.player_id + '</strong></td><td>' + esc(clubName(row.from_club_id)) + ' → ' +
          esc(clubName(row.to_club_id)) + '</td><td>' + money(row.fee) + '</td></tr>').join('') +
        '</tbody></table></div>' : '<div class="empty-state">Transfer tamamlanınca burada ve finans hareketlerinde görünür.</div>') +
      '</section></div>';
  }

  async function renderHistory() {
    await loadBase();
    const previousSeasons = Array.from({length: Math.max(0, state.season.season_no - 1)}, (_, index) => index + 1).reverse();
    if (state.archiveSeason === null && previousSeasons.length) state.archiveSeason = previousSeasons[0];
    let archive = null;
    if (state.archiveSeason) archive = await api(SEASON + '/history/' + state.archiveSeason);
    const archiveStandings = archive ? standingsTable(archive.standings.map(row => ({
      ...row,
      club_name: clubName(row.club_id),
      goal_difference: row.goal_difference === undefined ? row.goals_for - row.goals_against : row.goal_difference
    }))) : '';
    const archiveMatches = archive ? archive.matches.map(match => matchRow({
      ...match, status: 'played', home_club_name: clubName(match.home_club_id),
      away_club_name: clubName(match.away_club_id)
    }, archive.season_no)).join('') : '';
    const selector = previousSeasons.length
      ? '<label class="compact" style="min-width:130px">Sezon<select class="toolbar-select" id="archive-season">' +
        previousSeasons.map(number => '<option value="' + number + '"' +
          (number === Number(state.archiveSeason) ? ' selected' : '') + '>Sezon ' + number + '</option>').join('') +
        '</select></label>'
      : '';
    $('#page').innerHTML = '<div class="page-wrap">' + pageHeading('Sezon arşivi',
      'Tamamlanan sezonların puan tablosu ve maç sonuçları.') +
      (!previousSeasons.length
        ? '<section class="panel"><div class="empty-state">Arşivde tamamlanmış sezon yok. Altı haftayı tamamladıktan sonra yeni sezonu başlat; eski sezon burada saklanır.</div></section>'
        : '<section class="panel">' + panelHeading('Geçmiş sezon', 'Arşiv kayıtları değişmeden korunur') +
          '<div class="filter-row">' + selector + '</div><div class="grid home-grid"><div>' +
          '<section class="panel" style="box-shadow:none;padding:0;border:0">' + panelHeading('Puan durumu', 'Sezon ' + archive.season_no) +
          archiveStandings + '</section></div><div><section class="panel" style="box-shadow:none;padding:0;border:0">' +
          panelHeading('Maçlar', archive.matches.length + ' maç') + '<div class="match-list">' + archiveMatches +
          '</div></section></div></div></section>') + '</div>';
  }

  function openMatch(matchId, seasonNo) {
    $('#modal-root').innerHTML = '<div class="modal-backdrop" data-action="close-modal"><div class="modal" role="dialog" aria-modal="true"><div class="loading">Maç raporu yükleniyor…</div></div></div>';
    api(SEASON + '/matches/' + matchId + '?season_no=' + seasonNo).then(match => {
      const events = match.events || [];
      const lineups = match.lineups;
      const sidePlayers = side => lineups && lineups[side]
        ? lineups[side].map(player => '<div class="detail-player"><span>' + esc(player.position || '—') +
          ' · ' + esc(playerName(player)) + '</span><span>' + player.player_id + '</span></div>').join('')
        : '<div class="muted" style="font-size:10px">Maç henüz oynanmadı.</div>';
      const eventsHtml = events.length ? events.map(event => '<div class="event-row"><span class="event-minute">' +
        event.minute + '\'</span><span class="event-icon">' + (event.event_type === 'GOAL' ? '⚽' : '↗') +
        '</span><strong>' + esc(playerName(event)) + '</strong><span class="muted">' +
        (event.event_type === 'GOAL' ? 'Gol' : 'Asist') + ' · ' +
        esc(event.team === 'home' ? (match.home_club_name || clubName(match.home_club_id)) :
          (match.away_club_name || clubName(match.away_club_id))) + '</span></div>').join('')
        : '<div class="empty-state">Bu maçta henüz olay yok.</div>';
      const stats = match.player_stats || [];
      const statRows = stats.length ? '<section class="panel" style="margin-top:12px">' + panelHeading('Oyuncu performansı', 'Maç istatistikleri') +
        '<div class="table-wrap"><table class="data-table"><thead><tr><th>Oyuncu</th><th>Takım</th><th>Dakika</th><th>Gol</th><th>Asist</th><th>Puan</th></tr></thead><tbody>' +
        stats.map(row => '<tr><td><strong>' + esc(playerName(row)) + '</strong></td><td>' +
          esc(row.team === 'home' ? (match.home_club_name || clubName(match.home_club_id)) :
            (match.away_club_name || clubName(match.away_club_id))) + '</td><td>' + row.minutes_played +
          '</td><td>' + row.goals + '</td><td>' + row.assists + '</td><td class="rating">' +
          (row.rating === null || row.rating === undefined ? '—' : row.rating) + '</td></tr>').join('') +
        '</tbody></table></div></section>' : '';
      const modal = $('#modal-root .modal');
      if (!modal) return;
      modal.innerHTML = '<div class="modal-top"><div><h2>' + esc(match.home_club_name || clubName(match.home_club_id)) +
        ' ' + (match.status === 'played' ? match.home_goals + ' : ' + match.away_goals : '— : —') +
        ' ' + esc(match.away_club_name || clubName(match.away_club_id)) + '</h2><p>Sezon ' + seasonNo +
        ' · ' + match.week_no + '. hafta · Maç #' + match.match_id + '</p></div><button class="modal-close" data-action="close-modal" aria-label="Kapat">×</button></div>' +
        '<div class="grid match-detail-grid"><section class="detail-team"><h3>' +
        esc(match.home_club_name || clubName(match.home_club_id)) + ' · ' +
        esc(match.formations && match.formations.home || '—') + '</h3>' + sidePlayers('home') +
        '</section><section class="detail-team"><h3>' + esc(match.away_club_name || clubName(match.away_club_id)) +
        ' · ' + esc(match.formations && match.formations.away || '—') + '</h3>' + sidePlayers('away') +
        '</section></div><section class="panel" style="margin-top:12px">' + panelHeading('Gol ve asist olayları', events.length + ' olay') +
        eventsHtml + '</section>' + statRows;
    }).catch(error => {
      const modal = $('#modal-root .modal');
      if (modal) modal.innerHTML = '<div class="modal-top"><h2>Maç raporu</h2><button class="modal-close" data-action="close-modal">×</button></div><div class="notice error">' + esc(error.message) + '</div>';
    });
  }

  function compatibleAutoPicks(formation, oldSelections) {
    const players = state.lineup.players;
    const slots = formation.slots.slice();
    const oldByPlayer = new Map(oldSelections.map(item => [Number(item.player_id), Number(item.slot_id)]));
    const ordered = slots.slice().sort((a, b) => {
      const ac = players.filter(player => player.compatibility && player.compatibility[a.position]).length;
      const bc = players.filter(player => player.compatibility && player.compatibility[b.position]).length;
      return ac - bc || a.slot_id - b.slot_id;
    });
    const used = new Set();
    const result = [];
    ordered.forEach(slot => {
      const candidates = players.filter(player => player.compatibility && player.compatibility[slot.position] &&
        !used.has(Number(player.player_id))).sort((a, b) => {
        const scoreA = (a.compatibility[slot.position] || 0) + (oldByPlayer.has(Number(a.player_id)) ? 5 : 0);
        const scoreB = (b.compatibility[slot.position] || 0) + (oldByPlayer.has(Number(b.player_id)) ? 5 : 0);
        return scoreB - scoreA;
      });
      if (candidates.length) {
        used.add(Number(candidates[0].player_id));
        result.push({slot_id: slot.slot_id, player_id: Number(candidates[0].player_id)});
      }
    });
    return result.sort((a, b) => a.slot_id - b.slot_id);
  }

  async function handleAdvance() {
    if (!state.season || state.season.finished) return;
    const button = $('[data-action="advance"]');
    if (button) { button.disabled = true; button.textContent = 'Maçlar oynanıyor…'; }
    try {
      const result = await api(SEASON + '/advance', 'POST', {
        expected_season: state.season.season_no,
        expected_week: state.season.next_week
      });
      state.lastAdvance = {...result, season_no: state.season.season_no};
      await loadBase();
      state.view = 'home';
      await renderPage();
      notify(result.played_week + '. hafta tamamlandı. İki maçın sonucu hazır.');
    } catch (error) {
      notify(error.message, true);
      await loadBase().catch(() => {});
      await renderPage();
    }
  }
  async function handleNewSeason() {
    try {
      await api(SEASON + '/new-season', 'POST', {expected_season: state.season.season_no});
      state.lastAdvance = null;
      state.archiveSeason = state.season.season_no;
      await loadBase();
      state.view = 'home';
      await renderPage();
      notify('Yeni sezon başladı. Geçmiş sezon arşive eklendi.');
    } catch (error) { notify(error.message, true); }
  }
  async function saveLineup() {
    if (!state.lineup) return;
    const selections = $$('#slot-list select').map(select => ({
      slot_id: Number(select.dataset.slotId),
      player_id: Number(select.value)
    }));
    try {
      await api(SEASON + '/lineup', 'PUT', {
        expected_season: state.lineup.season_no,
        expected_week: state.lineup.next_week,
        formation: $('#formation-select').value,
        selections
      });
      notify('İlk 11 kaydedildi.');
      await renderPage();
    } catch (error) { notify(error.message, true); }
  }
  async function submitOffer(form) {
    const playerId = Number(form.dataset.playerId);
    const amount = Number(new FormData(form).get('amount'));
    if (!Number.isInteger(amount) || amount < 1) { notify('Teklif pozitif tam sayı olmalı.', true); return; }
    try {
      await api(SEASON + '/transfer-offers', 'POST', {
        player_id: playerId,
        amount,
        expected_season: state.season.season_no,
        expected_week: state.season.next_week
      });
      notify('Teklif oluşturuldu. Tekliflerim bölümünden sonucu değerlendirebilirsin.');
      await renderTransfers();
    } catch (error) { notify(error.message, true); }
  }
  async function resolveOffer(offerId) {
    try {
      const result = await api(SEASON + '/transfer-offers/' + offerId + '/resolve', 'POST');
      await loadBase();
      await renderTransfers();
      if (result.status === 'ACCEPTED') notify('Teklif kabul edildi. Oyuncu kadrona eklendi.');
      else notify(result.reason || 'Teklif reddedildi.', result.status === 'REJECTED');
    } catch (error) { notify(error.message, true); }
  }
  async function cancelOffer(offerId) {
    try {
      await api(SEASON + '/transfer-offers/' + offerId + '/cancel', 'POST');
      notify('Teklif geri çekildi.');
      await renderTransfers();
    } catch (error) { notify(error.message, true); }
  }
  async function logout() {
    try { await api('/auth/logout', 'POST'); } catch (_) {}
    state.token = '';
    state.user = null;
    state.club = null;
    state.season = null;
    sessionStorage.removeItem('bil372_token');
    $('#app-view').classList.add('hidden');
    $('#setup-view').classList.add('hidden');
    state.authMode = 'login';
    showAuth();
  }

  document.addEventListener('click', async event => {
    const authTab = event.target.closest('[data-auth-mode]');
    if (authTab) { state.authMode = authTab.dataset.authMode; renderAuthMode(); return; }
    const viewButton = event.target.closest('[data-view]');
    if (viewButton) {
      event.preventDefault();
      state.view = viewButton.dataset.view;
      await renderPage();
      return;
    }
    const actionButton = event.target.closest('[data-action]');
    if (!actionButton) return;
    const action = actionButton.dataset.action;
    if (action === 'advance') await handleAdvance();
    else if (action === 'new-season') await handleNewSeason();
    else if (action === 'save-lineup') await saveLineup();
    else if (action === 'match-detail') openMatch(actionButton.dataset.matchId, actionButton.dataset.seasonNo);
    else if (action === 'close-modal') {
      if (event.target === actionButton || actionButton.classList.contains('modal-close')) $('#modal-root').innerHTML = '';
    } else if (action === 'filter-market') await renderTransfers();
    else if (action === 'apply-stats') await renderStats();
    else if (action === 'resolve-offer') await resolveOffer(actionButton.dataset.offerId);
    else if (action === 'cancel-offer') await cancelOffer(actionButton.dataset.offerId);
    else if (action === 'refresh') await renderPage();
  });

  document.addEventListener('change', async event => {
    if (event.target.id === 'formation-select' && state.lineup) {
      const formation = state.formations.find(row => row.name === event.target.value);
      const picks = compatibleAutoPicks(formation, state.lineup.selections);
      const current = new Map(picks.map(row => [row.slot_id, row.player_id]));
      const slots = formation.slots;
      const players = state.lineup.players;
      const rendered = slots.map(slot => {
        const chosen = current.get(slot.slot_id);
        const options = players.filter(player => player.compatibility && player.compatibility[slot.position] &&
          (!Array.from(current.entries()).some(([id, playerId]) => id !== slot.slot_id && playerId === Number(player.player_id)) ||
            Number(player.player_id) === chosen));
        return '<div class="slot-row"><div><span class="slot-position">' + esc(slot.position) +
          '</span><span class="slot-num">' + String(slot.slot_id).padStart(2, '0') + '</span></div><div><strong style="font-size:10px">' +
          esc(posName(slot.position)) + '</strong><div class="muted" style="font-size:9px;margin-top:3px">' +
          (chosen ? 'Uyum ' + players.find(p => Number(p.player_id) === chosen).compatibility[slot.position] + '%' : 'Mevki seç') +
          '</div></div><select data-slot-id="' + slot.slot_id + '"><option value="">Oyuncu seç</option>' +
          options.map(player => '<option value="' + player.player_id + '"' + (Number(player.player_id) === chosen ? ' selected' : '') +
            '>' + esc(playerName(player)) + ' · uyum ' + player.compatibility[slot.position] + '%</option>').join('') +
          '</select></div>';
      }).join('');
      $('#slot-list').innerHTML = rendered;
    } else if (event.target.matches('#fixture-week')) {
      state.fixtureWeek = event.target.value;
      await renderMatches();
    } else if (event.target.matches('#fixture-season')) {
      state.fixtureSeason = Number(event.target.value);
      state.fixtureWeek = '';
      await renderMatches();
    } else if (event.target.matches('#archive-season')) {
      state.archiveSeason = Number(event.target.value);
      await renderHistory();
    } else if (event.target.matches('#stats-sort, #stats-min')) {
      await renderStats();
    } else if (event.target.matches('#market-position, #market-element')) {
      // Filtrele düğmesiyle birlikte uygulanır.
    }
  });

  document.addEventListener('submit', async event => {
    if (event.target.id === 'auth-form') {
      event.preventDefault();
      const values = new FormData(event.target);
      const credentials = {username: String(values.get('username')).trim(), password: String(values.get('password'))};
      const submit = $('#auth-submit');
      submit.disabled = true;
      try {
        if (state.authMode === 'register') await api('/auth/register', 'POST', credentials);
        const login = await api('/auth/login', 'POST', credentials);
        state.token = login.access_token;
        sessionStorage.setItem('bil372_token', state.token);
        state.user = login.user;
        await enterApp();
      } catch (error) { notify(error.message, true); }
      finally { submit.disabled = false; }
    } else if (event.target.id === 'club-form') {
      event.preventDefault();
      const name = String(new FormData(event.target).get('clubName')).trim();
      try {
        state.club = await api('/career/club', 'PUT', {name});
        $('#setup-view').classList.add('hidden');
        $('#app-view').classList.remove('hidden');
        state.view = 'home';
        await renderPage();
        notify('Kulübün hazır. İlk 11’ini kurup ilk haftayı oynatabilirsin.');
      } catch (error) { notify(error.message, true); }
    } else if (event.target.classList.contains('offer-form')) {
      event.preventDefault();
      await submitOffer(event.target);
    }
  });

  $('#logout-button').addEventListener('click', logout);
  $('.logout-setup').addEventListener('click', logout);
  document.addEventListener('click', event => {
    const backdrop = event.target.classList && event.target.classList.contains('modal-backdrop');
    if (backdrop) $('#modal-root').innerHTML = '';
  });

  if (state.token) enterApp(); else showAuth();
})();
