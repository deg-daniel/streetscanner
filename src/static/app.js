function showOverlay() {
  overlay.style.display = "flex"
}

function hideOverlay() {
  overlay.style.display = "none"
}

// ------- openstreetmap map

const map = L.map('map').setView([48.8566, 2.3522], 13)

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '© OpenStreetMap'
}).addTo(map)

let fromMarker = null
let toMarker = null
let fromLatLng = null
let toLatLng = null

async function snap(lat, lng) {
  const url = `https://router.project-osrm.org/nearest/v1/driving/${lng},${lat}`
  const res = await fetch(url)
  const data = await res.json()

  return data.waypoints[0].location // [lng, lat]
}

map.on("click", async (e) => {
  const snapped = await snap(e.latlng.lat, e.latlng.lng)

  const lat = snapped[1]
  const lng = snapped[0]

  // first click = FROM
  if (!fromLatLng) {
    fromLatLng = e.latlng

    if (fromMarker) map.removeLayer(fromMarker)

    fromMarker = L.marker([lat, lng]).addTo(map).bindPopup("FROM").openPopup()

    document.getElementById("from").value = `${lat},${lng}`
    return
  }

  // second click = TO
  if (!toLatLng) {
    toLatLng = e.latlng

    if (toMarker) map.removeLayer(toMarker)

    toMarker = L.marker([lat, lng]).addTo(map).bindPopup("TO").openPopup()

    document.getElementById("to").value = `${lat},${lng}`
    return
  }

  // reset if click again
  fromLatLng = e.latlng
  toLatLng = null

  if (fromMarker) map.removeLayer(fromMarker)

  fromMarker = L.marker([lat, lng] ).addTo(map).bindPopup("FROM").openPopup()

  document.getElementById("from").value = `${lat},${lng}`
})


async function startSocketJob(action, params, onMessage, options = { showOverlay: false }) {
  if (options.showOverlay) showOverlay()
  
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/${action}`
  const socket = new WebSocket(wsUrl)

  socket.onopen = () => {
    socket.send(JSON.stringify(params))
  }

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data)
    
    if (data.error) {
      console.error(`Error in ${action}:`, data)
      alert(`Error: ${data.details || data.error}`)
      if (options.showOverlay) hideOverlay()
      return
    }

    onMessage(data)
  }

  socket.onerror = (err) => {
    console.error("WS Error:", err)
    if (options.showOverlay) hideOverlay()
  }

  socket.onclose = () => {
    console.log(`${action} flow closed`)
    if (options.showOverlay) hideOverlay()
  }

  return socket
}

// ------- getItinerary -------

let routeLayer = null
let currentCoords = []
let currentMarker = null


async function getItinerary() {
  function renderRouteOnMap(data) {
    const coords = data.itinary
    currentCoords = coords
    if (routeLayer) map.removeLayer(routeLayer)
    routeLayer = L.polyline(coords, { color: "blue" }).addTo(map)
    map.fitBounds(routeLayer.getBounds())
    
    coords.forEach(c => L.circleMarker(c, { radius: 3 }).addTo(map))
    statusInline.textContent = `${coords.length} pins`
  }
  await startSocketJob('itinary', { a: document.getElementById("from").value, b: document.getElementById("to").value }, renderRouteOnMap, {showOverlay: true} )
}

// ------- getAndAnalyze -------

function updateCurrentPoint(index) {
  if (!currentCoords[index]) return
  
  const c = currentCoords[index]
  if (!currentMarker) {
	currentMarker = L.circleMarker(c, {
	  radius: 8,
	  color: "red"
	}).addTo(map)
  } else {
    currentMarker.setLatLng(c)
  }
}

const calculateETA = (start, current, total) => {
  if (!start || current <= 0) return ""

  const elapsed = (Date.now() - start) / 1000
  const remaining = (elapsed / current) * (total - current)

  const h = Math.floor(remaining / 3600)
  const m = Math.floor((remaining % 3600) / 60)
  const s = Math.floor(remaining % 60)

  return ` | ETA ${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

async function process(mode) {
  let jobStartTime = null
	
  const params = {
    a: document.getElementById("from").value,
    b: document.getElementById("to").value,
    desc: desc.value
  }

  function renderProcessStep(data) {
	hideOverlay()
    updateCurrentPoint(data.index)

	if (!jobStartTime) jobStartTime = Date.now()
	
	const current = data.index + 1
    const total = data.total
    
    const progressEl = document.getElementById("progress")
    progressEl.max = total
    progressEl.value = current
	
	const etaStr = calculateETA(jobStartTime, current, total)
	
    if (data.filename) {
      preview.src = `${data.filename}`
    } 

    statusInline.textContent = `Processing: ${data.index+1}/${data.total}${etaStr}`
	
	if (data.score != null) {
		analyzeInline.textContent = `score: ${data.score}${data?.match?'🔥':''}`
	}
	
	if (data.match) {
		const link = document.createElement("a")
		link.target = "_blank"
		
		// <img src="streetview_images/img 48.87167,2.34137.jpg">
		const coordsMatch = data.filename.match(/img\s+([^,]+),([^,]+)/)
		if (coordsMatch) {
			const lat = coordsMatch[1]
			const lon = coordsMatch[2].replace('.jpg', '')
			link.href = `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lon}`
		}
		const img = document.createElement("img")
		img.src = data.filename
		link.appendChild(img)
		
		document.getElementById("right").appendChild(link);		
		document.getElementById("right").scrollTop = document.getElementById("right").scrollHeight
	  }
  }
  showOverlay()
  await startSocketJob(mode, params, renderProcessStep, { showOverlay: false })
}

async function analyze() {
	await process("analyze")
}

async function getAndAnalyze() {
	await process("getandanalyze")
}

async function getImages() {
	await process("getimages")
}