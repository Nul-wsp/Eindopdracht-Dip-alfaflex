'use strict';
const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function notice(message, success = false) {
  const box = $('#notice');
  box.textContent = message;
  box.className = `alert alert-${success ? 'success' : 'danger'}`;
  box.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}
async function api(path, options = {}) {
  const response = await fetch(path, {...options, headers: {
    'Content-Type':'application/json', 'X-CSRF-Token':$('meta[name="csrf-token"]').content,
    ...options.headers
  }});
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'De actie is mislukt.');
  return data;
}
function filmPayload(form) {
  const data = Object.fromEntries(new FormData(form));
  delete data.id;
  for (const name of ['year', 'tmdb_id']) data[name] = data[name] ? Number(data[name]) : null;
  return data;
}
let filmsById = new Map();
let latestLoad = 0;
async function loadFilms() {
  const generation = ++latestLoad;
  const catalogue = $('#catalogue');
  const params = new URLSearchParams(new FormData($('#filters')));
  const films = await api(`/api/films?${params}`);
  if (generation !== latestLoad) return;
  filmsById = new Map(films.map(f => [f.id, f]));
  if (!films.length) {
    catalogue.innerHTML = '<p class="empty">Geen DVD’s gevonden. Probeer een andere zoekopdracht.</p>';
    return;
  }
  const admin = catalogue.dataset.admin === 'true';
  catalogue.innerHTML = films.map(f => {
    const title = escapeHtml(f.title);
    const button = (action, label, primary=false) => `<button type="button" class="btn btn-sm ${primary?'btn-dark':'btn-outline-dark'}" data-id="${f.id}" data-action="${action}">${label}</button>`;
    let actions = '';
    if (f.status === 'beschikbaar') actions = button('lenen', 'Lenen', true) + button('reserveren', 'Reserveren');
    if ((f.mine || admin) && f.status === 'uitgeleend') actions = button('terugbrengen', 'Terugbrengen', true);
    if ((f.mine || admin) && f.status === 'gereserveerd') actions = button('annuleren', 'Reservering annuleren');
    if (admin) actions += button('edit', 'Bewerken') + button('tmdb', 'Filmgegevens ophalen');
    const poster = f.poster_url ? `<img class="film-poster" loading="lazy" src="${escapeHtml(f.poster_url)}" alt="Filmposter ${title}">` : `<div class="poster-placeholder"><small>ALFAFLIX SELECTIE</small><strong>${title}</strong><small>${escapeHtml(f.year || 'DVD')}</small></div>`;
    return `<article class="col-md-6 col-xl-4"><div class="film-card">${poster}<div class="film-body"><span class="badge status-${f.status}">${f.status}${f.mine?' · van jou':''}</span><p class="film-meta">${escapeHtml(f.genre || 'DVD')} · ${escapeHtml(f.year || 'Jaar onbekend')}</p><h2>${title}</h2><details><summary>Over deze film</summary><p class="mt-2">${escapeHtml(f.description || 'Nog geen omschrijving beschikbaar.')}</p></details><div class="film-actions">${actions || '<span class="small text-secondary">Tijdelijk niet beschikbaar</span>'}</div></div></div></article>`;
  }).join('');
}
async function loadAdmin() {
  const films = await api('/api/films');
  $('#admin-list').innerHTML = films.map(f => `<div class="admin-row"><div><strong>${escapeHtml(f.title)}</strong><br><small>${f.status} · #${f.id}</small></div><button class="btn btn-outline-danger btn-sm" data-delete="${f.id}" ${f.status !== 'beschikbaar' ? 'disabled' : ''}>Verwijderen</button></div>`).join('') || '<p>Nog geen DVD’s in de collectie.</p>';
}
async function init() {
  if ($('#catalogue')) {
    await loadFilms();
    $('#filters').addEventListener('submit', event => {event.preventDefault();loadFilms().catch(e=>notice(e.message));});
    $('#catalogue').addEventListener('click', async event => {
      const button = event.target.closest('button[data-action]');
      if (!button) return;
      const id = Number(button.dataset.id), action = button.dataset.action;
      if (action === 'edit') {
        const form = $('#edit-form'), film = filmsById.get(id);
        for (const key of ['id','title','genre','year','tmdb_id','description']) form.elements[key].value = film[key] ?? '';
        $('#edit-error').textContent = '';
        $('#edit-dialog').showModal();
        return;
      }
      button.disabled = true;
      try {
        await api(`/api/films/${id}/${action}`, {method:'POST'});
        notice({lenen:'DVD uitgeleend. Veel kijkplezier!',reserveren:'DVD gereserveerd. Je kunt deze later ophalen.',terugbrengen:'DVD teruggebracht. Bedankt!',annuleren:'Reservering geannuleerd.',tmdb:'Omschrijving en poster opgehaald.'}[action], true);
        await loadFilms();
      } catch (e) {notice(e.message);} finally {button.disabled = false;}
    });
  }
  if ($('#edit-form')) {
    $('#close-dialog').addEventListener('click', () => $('#edit-dialog').close());
    $('#edit-form').addEventListener('submit', async event => {
      event.preventDefault();
      const form = event.target, button=form.querySelector('button');
      button.disabled=true;
      try {
        await api(`/api/films/${form.elements.id.value}`, {method:'PATCH',body:JSON.stringify(filmPayload(form))});
        $('#edit-dialog').close();
        notice('DVD bijgewerkt.',true);
        await loadFilms();
      } catch(e) {$('#edit-error').textContent=e.message;} finally {button.disabled=false;}
    });
  }
  if ($('#admin-list')) {
    await loadAdmin();
    $('#create-form').addEventListener('submit', async event => {
      event.preventDefault(); const button=event.target.querySelector('button'); button.disabled=true;
      try {
        await api('/api/films', {method:'POST',body:JSON.stringify(filmPayload(event.target))});
        event.target.reset();notice('DVD toegevoegd.',true);await loadAdmin();
      } catch(e) {notice(e.message);} finally {button.disabled=false;}
    });
    $('#admin-list').addEventListener('click', async event => {
      const button = event.target.closest('[data-delete]');
      if (!button || !confirm('Deze DVD uit de collectie verwijderen? De geschiedenis blijft bewaard.')) return;
      button.disabled=true;
      try {await api(`/api/films/${button.dataset.delete}`,{method:'DELETE'});notice('DVD verwijderd.',true);await loadAdmin();}
      catch(e) {notice(e.message);} finally {button.disabled=false;}
    });
  }
  if ($('#log-list')) {
    const logs = await api('/api/logs');
    $('#log-list').innerHTML = logs.map(l => `<tr><td>${escapeHtml(l.title)}</td><td>${l.action}</td><td>${escapeHtml(l.username)}</td><td>${escapeHtml(new Date(l.timestamp).toLocaleString('nl-NL'))}</td></tr>`).join('') || '<tr><td colspan="4">Nog geen handelingen.</td></tr>';
  }
}
init().catch(e => notice(e.message));
