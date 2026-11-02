// Sorora · mapa, directorio y alerta. En modo demo el punto del mapa es inventado: nunca se pide la ubicación real.
const START = { lat: 4.6351, lng: -74.0824 } // Bogotá, punto de ejemplo
const OSM = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'

const TEXT = {
  es: {
    crisisLead: 'Esto es una demostración: no avisa a nadie.',
    crisisBody: 'Los albergues son inventados. Si estás en peligro en Colombia, llama:',
    crisisLeadLive: 'Instancia privada: las alertas sí se envían.',
    crisisBodyLive: 'Si no recibes confirmación, llama de inmediato:',
    line155: 'orientación a mujeres', line123: 'emergencias',
    tagline: 'Directorio de refugios y señal de alerta.',
    mapTitle: 'El mapa', mapHint: 'Arrastra el marcador naranja o toca el mapa: es un punto de ejemplo, no tu ubicación.',
    mapHintLive: 'El marcador naranja es tu ubicación actual, si diste permiso. Puedes ajustarlo.',
    mapLabel: 'Mapa de albergues',
    directoryTitle: 'Directorio', fictional: 'Datos ficticios',
    signalTitle: 'La señal', signalBody: 'Muestra qué pasaría con una alerta desde ese punto. La ubicación no se guarda.',
    signalBodyLive: 'Envía la ubicación del marcador al contacto configurado.',
    keyLabel: 'Llave de acceso',
    sos: 'Simular alerta', sosLive: 'Enviar SOS', sending: 'Procesando…',
    kind: { emergency: 'Acogida de emergencia', transition: 'Vivienda de transición', legal: 'Asesoría legal' },
    room: (n) => (n === 1 ? '1 cupo' : `${n} cupos`), full: 'Sin cupo',
    km: (d) => `a ${d} km`,
    title: { simulated: 'Simulación: nadie fue avisado', sent: 'Aviso entregado', failed: 'No se pudo avisar. Llama al 123 ahora.' },
    wouldSend: 'Una instancia real enviaría esto al contacto de confianza:',
    preview: (lat, lng) => `¡ALERTA SOS!\nUbicación: ${lat.toFixed(4)}, ${lng.toFixed(4)}`,
    nearest: 'Con cupo más cerca:', none: 'Ningún albergue con cupo.',
    errorList: 'No se pudo cargar el directorio.',
    errorAlert: 'No se pudo procesar. Si es una emergencia, llama al 123.',
    errorKey: 'Llave inválida: la alerta no se envió. Llama al 123.',
    howTitle: 'Cómo está hecho',
    how1: 'Una API en FastAPI ordena los albergues por distancia y solo sugiere los que tienen cupo.',
    how2: 'En esta demo la alerta se calcula y se descarta: no se escribe en MongoDB ni se envía a Telegram.',
    how3: 'En una instancia privada exige una llave, reintenta el envío y reporta si de verdad llegó.',
    docs: 'Documentación de la API', code: 'Código fuente', by: 'Hecho por',
  },
  en: {
    crisisLead: 'This is a demo: nobody is notified.',
    crisisBody: 'The shelters are made up. If you are in danger in Colombia, call:',
    crisisLeadLive: 'Private instance: alerts are really sent.',
    crisisBodyLive: 'If you get no confirmation, call right away:',
    line155: 'women’s support line', line123: 'emergencies',
    tagline: 'A shelter directory and an alert signal.',
    mapTitle: 'The map', mapHint: 'Drag the orange marker or tap the map: it is a sample point, not your location.',
    mapHintLive: 'The orange marker is your current location, if you allowed it. You can adjust it.',
    mapLabel: 'Shelter map',
    directoryTitle: 'Directory', fictional: 'Fictional data',
    signalTitle: 'The signal', signalBody: 'Shows what would happen with an alert from that point. The location is not stored.',
    signalBodyLive: 'Sends the marker location to the configured contact.',
    keyLabel: 'Access key',
    sos: 'Simulate alert', sosLive: 'Send SOS', sending: 'Working…',
    kind: { emergency: 'Emergency shelter', transition: 'Transitional housing', legal: 'Legal counsel' },
    room: (n) => (n === 1 ? '1 spot' : `${n} spots`), full: 'Full',
    km: (d) => `${d} km away`,
    title: { simulated: 'Simulation: nobody was notified', sent: 'Alert delivered', failed: 'The alert failed. Call 123 now.' },
    wouldSend: 'A real instance would send this to the trusted contact:',
    preview: (lat, lng) => `SOS ALERT!\nLocation: ${lat.toFixed(4)}, ${lng.toFixed(4)}`,
    nearest: 'Nearest with room:', none: 'No shelter has room.',
    errorList: 'The directory could not be loaded.',
    errorAlert: 'This could not be processed. In an emergency, call 123.',
    errorKey: 'Invalid key: the alert was not sent. Call 123.',
    howTitle: 'How it is built',
    how1: 'A FastAPI service sorts shelters by distance and only suggests those with room.',
    how2: 'In this demo the alert is computed and discarded: nothing is written to MongoDB or sent to Telegram.',
    how3: 'A private instance requires a key, retries delivery and reports whether it really arrived.',
    docs: 'API documentation', code: 'Source code', by: 'Made by',
  },
}

const $ = (sel, root = document) => root.querySelector(sel)

let lang = 'es'
try { lang = localStorage.getItem('sorora-lang') || '' } catch { /* sin almacenamiento */ }
if (lang !== 'es' && lang !== 'en') lang = navigator.language.toLowerCase().startsWith('es') ? 'es' : 'en'

let mode = 'demo'
let shelters = []
let lastResult = null
const markers = new Map()

const map = L.map('map', { zoomControl: true }).setView(START, 12)
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: OSM }).addTo(map)

const me = L.marker(START, {
  draggable: true,
  icon: L.divIcon({ className: '', html: '<div class="me"></div>', iconSize: [30, 30], iconAnchor: [15, 34] }),
  zIndexOffset: 1000,
}).addTo(map)

function moved() {
  lastResult = null
  $('#result').hidden = true
  loadShelters()
}
me.on('dragend', moved)
map.on('click', (event) => { me.setLatLng(event.latlng); moved() })

function liveKey(key) {
  return mode === 'live' && TEXT[lang][`${key}Live`] ? `${key}Live` : key
}

function applyText() {
  const t = TEXT[lang]
  document.documentElement.lang = lang
  document.querySelectorAll('[data-i18n]').forEach((el) => {
    el.textContent = t[liveKey(el.dataset.i18n)]
  })
  $('#map').setAttribute('aria-label', t.mapLabel)
  $('#sos').textContent = t[liveKey('sos')]
  $('#key-field').hidden = mode !== 'live'
  document.querySelectorAll('[data-lang]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.lang === lang)))
}

function renderShelters() {
  const t = TEXT[lang]
  const list = $('#shelters')
  markers.forEach((m) => m.remove())
  markers.clear()
  const nearestId = shelters.find((s) => s.occupancy < s.capacity)?.id

  list.replaceChildren(...shelters.map((s, i) => {
    const room = s.capacity - s.occupancy
    const row = $('#shelter-row').content.firstElementChild.cloneNode(true)
    row.classList.toggle('shelter--full', room === 0)
    $('.shelter__number', row).textContent = i + 1
    $('.shelter__name', row).textContent = s.name
    $('.shelter__meta', row).textContent = `${t.kind[s.purpose]} · ${t.km(s.distance_km.toLocaleString(lang))}`
    $('.shelter__room', row).textContent = room ? t.room(room) : t.full
    $('.shelter__button', row).addEventListener('click', () => {
      map.flyTo([s.latitude, s.longitude], 14, { duration: matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 0.6 })
    })

    const kind = room === 0 ? 'pin--full' : s.id === nearestId ? 'pin--near' : ''
    const marker = L.marker([s.latitude, s.longitude], {
      title: s.name,
      alt: s.name,
      icon: L.divIcon({ className: '', html: `<div class="pin ${kind}">${i + 1}</div>`, iconSize: [34, 34], iconAnchor: [17, 17] }),
    }).addTo(map)
    marker.bindTooltip(s.name)
    markers.set(s.id, marker)
    return row
  }))
}

function renderResult() {
  const box = $('#result')
  if (!lastResult) { box.hidden = true; return }
  const t = TEXT[lang]
  box.hidden = false
  box.replaceChildren()
  const add = (cls, text) => {
    const el = document.createElement('p')
    el.className = cls
    el.textContent = text
    box.append(el)
  }

  if (lastResult.error) {
    box.dataset.status = 'failed'
    add('result__title', t[lastResult.error])
    return
  }
  const { data, lat, lng } = lastResult
  box.dataset.status = data.status
  add('result__title', t.title[data.status])
  if (data.status === 'simulated') {
    add('', t.wouldSend)
    add('result__preview', t.preview(lat, lng))
  }
  const near = data.nearest.map((s) => `${s.name} (${t.km(s.distance_km.toLocaleString(lang))})`).join(' · ')
  add('result__near', near ? `${t.nearest} ${near}` : t.none)
}

async function loadShelters() {
  const { lat, lng } = me.getLatLng()
  try {
    const res = await fetch(`/api/shelters?lat=${lat.toFixed(5)}&lng=${lng.toFixed(5)}`)
    if (!res.ok) throw new Error(res.status)
    shelters = await res.json()
    renderShelters()
  } catch {
    const row = document.createElement('li')
    row.className = 'shelter__meta'
    row.textContent = TEXT[lang].errorList
    $('#shelters').replaceChildren(row)
  }
}

$('#sos').addEventListener('click', async () => {
  const button = $('#sos')
  const { lat, lng } = me.getLatLng()
  button.disabled = true
  button.textContent = TEXT[lang].sending
  try {
    const headers = { 'Content-Type': 'application/json' }
    if (mode === 'live') headers['X-Alert-Key'] = $('#alert-key').value
    const res = await fetch('/api/alerts', { method: 'POST', headers, body: JSON.stringify({ latitude: lat, longitude: lng }) })
    if (res.status === 401) lastResult = { error: 'errorKey' }
    else if (res.status === 201 || res.status === 502) lastResult = { data: await res.json(), lat, lng }
    else lastResult = { error: 'errorAlert' }
  } catch {
    lastResult = { error: 'errorAlert' }
  }
  button.disabled = false
  applyText()
  renderResult()
  $('#result').scrollIntoView({ block: 'nearest' })
})

document.querySelectorAll('[data-lang]').forEach((button) => {
  button.addEventListener('click', () => {
    lang = button.dataset.lang
    try { localStorage.setItem('sorora-lang', lang) } catch { /* sin almacenamiento */ }
    applyText()
    renderShelters()
    renderResult()
  })
})

async function start() {
  try {
    const res = await fetch('/api/config')
    if (res.ok) mode = (await res.json()).mode
  } catch { /* se queda en demo */ }
  applyText()
  // Solo una instancia privada pide la ubicación real.
  if (mode === 'live' && navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      me.setLatLng([coords.latitude, coords.longitude])
      map.setView([coords.latitude, coords.longitude], 13)
      moved()
    })
  }
  loadShelters()
}

applyText()
start()
