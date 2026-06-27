<template>
  <div class="ports-shell" ref="containerRef">
    <section class="ports-section">
      
      <h4>Ports</h4>

      <div class="USRP-represent">
        <div class="h5">Port representation of the USRP x440:</div>
        <div class="ports-box">
          <div class="empty-port"></div>
          <div v-for="i in leftCount" :key="'left-'+i" class="port" :ref="el => setPortRef(el, i-1)" :class="{assigned: portToPartial[i-1] != null}" @pointerdown.prevent="startDragFromPort(i-1, $event)">{{ portLabels[i-1] }}</div>
          <div class="empty-port"></div>
          <div v-for="i in rightCount" :key="'right-'+i" class="port" :ref="el => setPortRef(el, leftCount + (i-1))" :class="{assigned: portToPartial[leftCount + (i-1)] != null}" @pointerdown.prevent="startDragFromPort(leftCount + (i-1), $event)">{{ portLabels[leftCount + (i-1)] }}</div>
          <div class="empty-port"></div>
        </div>
      </div>
    <div class="zones-container">
      <div class="h5">Display of the channels for each of the partial options:</div>
      <div class="partial-options-zones" v-if="partials && partials.length">
        <div class="partial-option" v-for="(p, pi) in partials" :key="p.option_id ?? pi">
          <div class="partial-title">Option: {{ pi + 1 }}</div>
          <div class="partial-ports">
            <div class="partial-port" v-for="(port, si) in computePorts(p)" :key="si">
              <div class="dot-port" :ref="el => setPartialRef(el, pi, si)" @pointerdown.prevent="startDragFromPartial(pi, si, $event)"></div>
              <div class="freqs">
                <div class="freq"><b>F_c:</b> {{ formatFreq(port.f_center) }}</div>
                <div class="freq"><b>BW:</b> {{ formatFreq(port.bw) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    </section>

    <svg class="connections-svg" v-if="containerRef">
      <line v-for="ln in lines" :key="ln.portIdx" :x1="ln.x1" :y1="ln.y1" :x2="ln.x2" :y2="ln.y2" stroke="#22c55e" stroke-width="4" stroke-linecap="round" @click="removeConnection(ln.portIdx)" />
      <line v-if="dragging.active && dragging.from" :x1="dragging.startX" :y1="dragging.startY" :x2="(dragging.x - (containerRef ? containerRef.getBoundingClientRect().left : 0))" :y2="(dragging.y - (containerRef ? containerRef.getBoundingClientRect().top : 0))" stroke="#22c55e" stroke-width="3" stroke-linecap="round" />
    </svg>
  </div>
</template>

<script setup>
  import { ref, computed, watch, onBeforeUnmount } from 'vue'

  // Props i emits
  const props = defineProps({ option: { type: Object, default: null }, numPorts: { type: Number, default: 8 } })
  const emit = defineEmits(['mapping-changed'])

  // Variables
  const leftCount = computed(() => Math.floor(props.numPorts / 2))
  const rightCount = computed(() => props.numPorts - Math.floor(props.numPorts / 2))
  const portLabels = computed(() => Array.from({ length: props.numPorts }, (_, i) => `P${i+1}`))
  const portsSelected = ref(Array.from({ length: props.numPorts }, () => false))

  // Estat de les assignacions de ports a partials
  const portToBox = ref({})
  const boxToPorts = ref({})
  const selectedBox = ref(null)

  // Refs per al DOM
  const containerRef = ref(null)
  const portRefs = ref([])
  const partialRefs = ref({})

  // mapping: port index -> partialKey ("pi:si")
  const portToPartial = ref({})
  // reverse mapping: partialKey -> [portIdx,...]
  const partialToPorts = ref({})

  // Funció (computed) per obtenir la llista de partial options
  const partials = computed(() => {     
    if (!props.option) return []
    return props.option.partial_options || props.option.partials || []
  })

  // Funció (computed) per obtenir la llista de zones de cada partial option a partir de l'objecte option
  const zoneBoxes = computed(() => {
    if (props.option && props.option.zone_boxes) return props.option.zone_boxes
    const p = partials.value
    if (!p || !p.length) return []
    return [{ title: null, boxes: p.map(pp => [pp.f_start ?? pp[0], pp.f_end ?? pp[1]]) }]
  })

  // Estat de l'arrossegament de connexions
  const dragging = ref({ active: false, from: null, startX: 0, startY: 0, x: 0, y: 0 })

  // Funcions per establir referències als elements del DOM
  function setPortRef(el, idx){ if (!el) return; portRefs.value[idx] = el }
  function setPartialRef(el, pi, si){ if (!el) return; partialRefs.value[`${pi}:${si}`] = el }

  // Funció per obtenir el centre d'un element dins del contenidor
  function getElementCenter(el){
    if (!el || !containerRef.value) return { x: 0, y: 0 }
    const crect = containerRef.value.getBoundingClientRect()
    const r = el.getBoundingClientRect()
    return { x: (r.left + r.right)/2 - crect.left, y: (r.top + r.bottom)/2 - crect.top }
  }

  // Funció per iniciar l'arrossegament d'una connexió des d'una partial option
  function startDragFromPartial(pi, si, ev){
    // Extraiem la clau de la partial option
    const key = `${pi}:${si}`
    // Activem l'estat d'arrossegament
    dragging.value.active = true
    // Indiquem el punt d'origen de l'arrossegament (en aquest caas d'una opció parcial)
    dragging.value.from = { type: 'partial', key, pi, si }
    const el = partialRefs.value[key]
    const c = getElementCenter(el)
    dragging.value.startX = c.x; dragging.value.startY = c.y
    dragging.value.x = ev.clientX; dragging.value.y = ev.clientY
    // Afegim els listeners per al moviment i la solta del ratolí
    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', onPointerUp)
  }
  // Funció per iniciar l'arrossegament d'una connexió des d'un port
  function startDragFromPort(portIdx, ev){
    // Activem l'estat d'arrossegament
    dragging.value.active = true
    // Indiquem el punt d'origen de l'arrossegament (en aquest cas d'un port)
    dragging.value.from = { type: 'port', portIdx }
    const el = portRefs.value[portIdx]
    const c = getElementCenter(el)
    dragging.value.startX = c.x; dragging.value.startY = c.y
    dragging.value.x = ev.clientX; dragging.value.y = ev.clientY
    // Afegim els listeners per al moviment i la solta del ratolí
    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', onPointerUp)
  }

  // Funció per gestionar el moviment del ratolí durant l'arrossegament
  function onPointerMove(ev){
    dragging.value.x = ev.clientX
    dragging.value.y = ev.clientY
  }

  // Funció per aplanar els ports parcial
  function flattenPartialPorts(){
    const list = []
    for (let pi = 0; pi < partials.value.length; pi++){
      const ports = computePorts(partials.value[pi])
      for (let si = 0; si < ports.length; si++) list.push({ key: `${pi}:${si}`, pi, si })
    }
    return list
  }

  // Funció per trobar el port físic a partir de la posició del "client" (lo del client ho deia el tutorial i s'ha quedat)
  function findPortAtClientPos(cx, cy){
    for (let i = 0; i < portRefs.value.length; i++){
      const el = portRefs.value[i]
      if (!el) continue
      const r = el.getBoundingClientRect()
      if (cx >= r.left && cx <= r.right && cy >= r.top && cy <= r.bottom) return i
    }
    return null
  }

  // Funció per trobar el partial a partir de la posició del "client"
  function findPartialAtClientPos(cx, cy){
    for (const [k, el] of Object.entries(partialRefs.value)){
      const r = el.getBoundingClientRect()
      if (cx >= r.left && cx <= r.right && cy >= r.top && cy <= r.bottom) {
        const [pi, si] = k.split(':').map(Number)
        return { key: k, pi, si }
      }
    }
    return null
  }

  // Funció per gestionar l'aixecada del ratolí durant l'arrossegament
  function onPointerUp(ev){
    // Eliminem els listeners per al moviment i l'aixecada del ratolí
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerup', onPointerUp)

    // Si no hi ha un arrossegament actiu, sortim
    if (!dragging.value.active) return

    // Extraiem la posició del ratolí i busquem el port físic i el partial corresponent
    const cx = ev.clientX, cy = ev.clientY
    const portIdx = findPortAtClientPos(cx, cy)
    const partialHit = findPartialAtClientPos(cx, cy)
    
    // Si l'arrossegament prové d'una partial i s'ha aixecat sobre un port, assignem el port a la partial
    if (dragging.value.from.type === 'partial' && portIdx != null){
      const { pi, si } = dragging.value.from
      assignPortToPartial(portIdx, pi, si)
    } else if (dragging.value.from.type === 'port' && partialHit){
      assignPortToPartial(dragging.value.from.portIdx, partialHit.pi, partialHit.si)
    }

    // Reiniciem l'estat d'arrossegament
    dragging.value.active = false
    dragging.value.from = null
  }

  // Funció per calcular els ports (freq. i BW) a partir d'una partial option
  function assignPortToPartial(portIdx, pi, si){
    // Extraiem la clau de la partial option
    const key = `${pi}:${si}`
    const prev = portToPartial.value[portIdx]

    // Si hi ha dues partial options, apliquem les regles de connexió: 
    // → La primera només pot connectar-se als primers 4 ports i la segona només als últims 4 ports
    if (partials.value.length === 2) {
      if (pi === 0 && portIdx >= Math.floor(props.numPorts/2)){
        alert(' The partial option 1 can only be connected to the first 4 ports')
        return
      }
      if (pi === 1 && portIdx < Math.floor(props.numPorts/2)){
        alert(' The partial option 2 can only be connected to the last 4 ports')
        return
      }
    }

    // Si el port ja estava assignat a la mateixa partial, no fem res
    if (prev === key) return

    // Si el port estava assignat a una altra partial, el desassignem d'aquesta
    if (prev != null){
      // Recollim tots els ports als que la opció parcial estava connectada
      const arrPrev = (partialToPorts.value[prev] || []).filter(x => x !== portIdx)
      // Si no hi ha més ports connectats a la partial anterior, intentem assignar-la a un altre port disponible
      if (arrPrev.length === 0){
        const unassignedIdx = Array.from({ length: props.numPorts }).findIndex((_, idx) => portToPartial.value[idx] == null && idx !== portIdx)
        // Si hi ha un port disponible, l'assignem a la partial anterior; si no, intentem "robar" un port d'una altra partial que tingui més d'un port connectat
        if (unassignedIdx !== -1){
          portToPartial.value[unassignedIdx] = prev
          partialToPorts.value[prev] = [unassignedIdx]
        } else {
          // Roba un port d'una que tingui més d'un port connectat
          let stolen = null
          // Per cada port
          for (let j = 0; j < props.numPorts; j++){
            if (j === portIdx) continue
            // Extraiem la partial a la que està connectat aquest port
            const pj = portToPartial.value[j]
            // Si la partial té més d'un port connectat, la desconnectem d'aquest port i l'assignem a la partial anterior
            if (pj && (partialToPorts.value[pj] || []).length > 1){
              partialToPorts.value[pj] = partialToPorts.value[pj].filter(x => x !== j)
              portToPartial.value[j] = prev
              partialToPorts.value[prev] = [j]
              stolen = j
              break
            }
          }
          // Si no hem pogut robar cap port, alertem a l'usuari que no es pot reassignar
          if (stolen == null){
            alert(' Can not reassign: the previous partial option would be left disconnected and there are no available ports.')
            return
          }
        }
      } else {
        partialToPorts.value[prev] = arrPrev
      }
    }

    // Assignem el port a la nova partial option
    portToPartial.value[portIdx] = key
    partialToPorts.value[key] = partialToPorts.value[key] || []
    
    // Si el port no estava ja assignat a la partial, l'afegim a la llista de ports connectats a aquesta partial
    if (!partialToPorts.value[key].includes(portIdx)) partialToPorts.value[key].push(portIdx)
    
    // Emitim l'event amb el mapping actualitzat
    emit('mapping-changed', { portToPartial: portToPartial.value, partialToPorts: partialToPorts.value })
  }

  // Funció per eliminar la connexió d'un port a una partial option
  function removeConnection(portIdx){
    const prev = portToPartial.value[portIdx]
    if (prev == null) return
    const arr = partialToPorts.value[prev] || []
    if (arr.length <= 1){
      alert('Can not remove the last connection for this partial port.')
      return
    }
    partialToPorts.value[prev] = arr.filter(x => x !== portIdx)
    delete portToPartial.value[portIdx]
    emit('mapping-changed', { portToPartial: portToPartial.value, partialToPorts: partialToPorts.value })
  }

  // Funció per gestionar el click sobre una caixa de partial option
  function onBoxClick(idx){ selectedBox.value = idx }

  // Funció per gestionar quan es toca una connexió (es crea o borra)
  function onPortToggle(i, isSelected){
    // Si hi ha una caixa seleccionada i s'ha seleccionat el port, assignem el port a la caixa; si s'ha deseleccionat, el desassignem
    if (selectedBox.value != null && isSelected){
      portToBox.value[i] = selectedBox.value
      if (!boxToPorts.value[selectedBox.value]) boxToPorts.value[selectedBox.value] = []
      if (!boxToPorts.value[selectedBox.value].includes(i)) boxToPorts.value[selectedBox.value].push(i)
    } else if (!isSelected){
      const b = portToBox.value[i]
      delete portToBox.value[i]
      if (b != null && boxToPorts.value[b]) boxToPorts.value[b] = boxToPorts.value[b].filter(x => x !== i)
    }
    emit('mapping-changed', { portToBox: portToBox.value, boxToPorts: boxToPorts.value })
  }

  // Funció per assignar automàticament els ports a les partial options
  function autoAssign(){
    // Iterem per cada partial option i assignem els ports disponibles segons les regles establertes
    portToPartial.value = {}
    partialToPorts.value = {}
    portsSelected.value = Array.from({ length: props.numPorts }, () => false)

    // Si no hi ha partial options, emetem l'event amb els mappings buits i sortim (no hauria de passar mai)
    if (!partials.value || partials.value.length === 0) {
      emit('mapping-changed', { portToPartial: portToPartial.value, partialToPorts: partialToPorts.value })
      return
    }

    // Extraiem el nombre de ports i calculem quants ports assignar a cada partial option
    const nPorts = Number(props.numPorts || 0)
    const leftCountLocal = Math.floor(nPorts/2)
    const leftPorts = Array.from({ length: leftCountLocal }, (_, i) => i)
    const rightPorts = Array.from({ length: nPorts - leftCountLocal }, (_, i) => i + leftCountLocal)

    // Funció per obtenir tots els ports disponibles per a cada partial option
    function allowedPortsForPartial(pi){
      if (partials.value.length === 2){
        return (pi === 0) ? leftPorts : rightPorts
      }
      return Array.from({ length: nPorts }, (_, i) => i)
    }

    // Llista per recollir els canals que no s'han pogut assignar a cap port
    const unassigned = []

    // Iterem per cada partial option 
    for (let pi = 0; pi < partials.value.length; pi++){
      // Extraiem els canals (freq. i BW) de la partial option
      const bands = computePorts(partials.value[pi])

      // Iterem per cada canal de la partial option
      for (let si = 0; si < bands.length; si++){
        // Extraiem la clau de la partial option
        const key = `${pi}:${si}`

        // Mirem quins ports són possibles candidats per a aquesta p.o.
        const candidates = allowedPortsForPartial(pi)

        // La primera opció seria un port que estigui lliure (no assignat a cap altra partial)
        let chosen = candidates.find(p => portToPartial.value[p] == null)

        // Si i no n'hi ha cap lliure (cas rar però bueno), preferim un port que estigui assignat a una partial diferent (per robar-li el port)
        if (chosen == null){
          chosen = candidates.find(p => {
            const v = portToPartial.value[p]
            return v != null && v.split(':')[0] === String(pi)
          })
        }

        // Si no hi ha cap port disponible, afegim aquest canal a la llista d'unassigned i continuem amb el següent
        if (chosen == null){
          unassigned.push({ pi, si, key })
          continue
        }

        // Si hem trobat un port disponible, l'assignem a la partial option i actualitzem els mappings
        portToPartial.value[chosen] = key
        partialToPorts.value[key] = partialToPorts.value[key] || []
        if (!partialToPorts.value[key].includes(chosen)) partialToPorts.value[key].push(chosen)
        portsSelected.value[chosen] = true
      }
    }

    // Si hi ha canals que no s'han pogut assignar a cap port, alertem a l'usuari
    if (unassigned.length > 0){
      // Inform user that not all bands could be connected
      alert(`Can not connect ${unassigned.length} channels; left unassigned.`)
    }

    // Emitim l'event amb els mappings actualitzats
    emit('mapping-changed', { portToPartial: portToPartial.value, partialToPorts: partialToPorts.value })
  }

  // Funció per calcular els ports (freq. i BW) a partir d'una partial option
  function computePorts(p){
    // Extraiem: freq. inicial, freq. final, nombre de canals i amplada de banda per canal
    const fs = Number(p?.f_start ?? p?.[0] ?? 0)
    const fe = Number(p?.f_end ?? p?.[1] ?? 0)
    const num = Math.max(1, Number(p?.chans_needed ?? p?.chansNeeded ?? p?.chans ?? 1))
    const total = Math.max(0, fe - fs)
    const piece = num > 0 ? total / num : total

    // Generem un array amb totes les dades
    const out = []
    for (let i = 0; i < num; i++){
      const s = fs + i * piece
      const e = (i < num - 1) ? s + piece : fe
      const center = (s + e) / 2
      const bw = Math.abs(e - s)
      out.push({ f_start: s, f_end: e, f_center: center, bw: bw })
    }
    return out
  }

  // Funció per formatejar la freqüència per evitar tindre tants 0s
  function formatFreq(f){
    const v = Number(f)
    if (isNaN(v)) return String(f)
    if (v >= 1e9) return (v/1e9).toFixed(3) + ' GHz'
    if (v >= 1e6) return (v/1e6).toFixed(3) + ' MHz'
    if (v >= 1e3) return (v/1e3).toFixed(0) + ' kHz'
    return v + ' Hz'
  }

  // Funció (computed) per calcular les línies de connexió entre ports i partial options
  const lines = computed(() => {
    // Array de linies
    const out = []

    // Si no hi ha contenidor, retornem l'array buit
    if (!containerRef.value) return out

    // Extraiem el rectangle del contenidor per calcular les coordenades relatives
    const crect = containerRef.value.getBoundingClientRect()
    
    // Iterem per cada port
    const n = Number(props.numPorts || 0) // Num portsw
    for (let i = 0; i < n; i++){
      // Extraiem la partial option assignada a aquest port
      const key = portToPartial.value[i]
      if (!key) continue 

      // Extraiem la partial option i el seu índex
      const portEl = portRefs.value[i]
      const partialEl = partialRefs.value[key]
      if (!portEl || !partialEl) continue

      // Extraiem les coordenades dels rectangles del port i de la partial option
      const pr = portEl.getBoundingClientRect()
      const br = partialEl.getBoundingClientRect()
      const x1 = (pr.left + pr.right)/2 - crect.left
      const y1 = (pr.top + pr.bottom)/2 - crect.top
      const x2 = (br.left + br.right)/2 - crect.left
      const y2 = (br.top + br.bottom)/2 - crect.top

      // Afegim la línia a l'array de linies
      out.push({ portIdx: i, x1, y1, x2, y2 })
    }
    return out
  })

// Watcher per reiniciar l'assignació automàtica quan canvia l'objecte option
watch(() => props.option, (o) => { if (o) autoAssign() })

// Funció per netejar els listeners quan es desmunta el component
onBeforeUnmount(() => {
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
})

// Funció per obtenir el mapping actual de ports a partials i viceversa
function getMapping(){
  return { portToPartial: portToPartial.value, partialToPorts: partialToPorts.value }
}

// Exposem autoAssign i getMapping 
defineExpose({ autoAssign, getMapping })
</script>

<style scoped>
.ports-shell{ 
  position:relative;
}
.ports-section{ 
  background:#f9f9f9; 
  
  padding:12px;
  padding-inline: 5%;
  
  border:5px solid #ddd; 
  border-radius:10px; 

  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 15px
}

h4{
  font-size: 1.8rem;
  margin: 10px;
}

.USRP-represent{
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.h5 {
  margin-left: 15px;
}

.ports-box{ 
  width: 100%;

  display: flex;
  justify-content: space-between;
  gap:12px; 
  padding:20px;

  border:5px solid #e0e0e0;  
  border-radius:6px;
}
.empty-port{ 
  width: 30px;
  height:30px;
  border-radius:50%;
}
.port{
  width:30px;
  height:30px;

  border-radius:50%;
  background:#e0e0e0;
  border:2px solid #555;
  border-radius:100%;

  display:flex;
  justify-content:center;
  align-items:center;

  font-size:12px;
  color:#555;
}

.port.assigned{ 
  border-color: #22c55e;
  background:#22c55e; 

}

.zones-container{
  width: 100%;
  margin-top: 15px;

  display: flex;
  flex-direction: column;
  gap: 15px
}

.partial-options-zones{ 
  width:100%;
  display:flex; 
  gap:20px; 
  align-items:center;
}

.partial-option{ 
  min-width:45%;
  padding:8px; 

  display:flex; 
  flex-direction:column; 
  gap:8px; 
  
  border:5px solid #e0e0e0; 
  border-radius:8px; 
  background:#ffffff36; 
}
.partial-title{ font-weight:700; text-align:center; margin-bottom:6px }
.partial-ports{ display:flex; gap:8px; align-items:flex-start; justify-content:center; flex-wrap:wrap }
.partial-port{ 
  display:flex;
  gap:8px;
  align-items:center;
  padding:6px 8px;
  border-radius:6px;
  background:#fafafa;
  border:2px solid #ccc;
  min-width:140px }
.dot-port{ 
  width:12px;
  height:12px;
  border-radius:50%;
  background:#22c55e;
  border:2px solid #22c55e;
 }
.freqs{ display:flex; flex-direction:column }
.freq{ font-size:12px; color:#222 }

.connections-svg{ position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none }
.connections-svg line{ pointer-events:stroke; cursor:pointer }


</style>
