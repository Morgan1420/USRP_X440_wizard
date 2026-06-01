<template>
  <div class="ports-shell" ref="containerRef">
    <section class="ports-section">
      
      <h4>Ports</h4>

      <div class="USRP-represent">
        <div class="h5">Representació dels ports de la USRP x440:</div>
        <div class="ports-box">
          <div class="empty-port"></div>
          <div v-for="i in leftCount" :key="'left-'+i" class="port" :ref="el => setPortRef(el, i-1)" :class="{assigned: portToPartial[i-1] != null}" @pointerdown.prevent="startDragFromPort(i-1, $event)">{{ portLabels[i-1] }}</div>
          <div class="empty-port"></div>
          <div v-for="i in rightCount" :key="'right-'+i" class="port" :ref="el => setPortRef(el, leftCount + (i-1))" :class="{assigned: portToPartial[leftCount + (i-1)] != null}" @pointerdown.prevent="startDragFromPort(leftCount + (i-1), $event)">{{ portLabels[leftCount + (i-1)] }}</div>
          <div class="empty-port"></div>
        </div>
      </div>
    <div class="zones-container">
      <div class="h5">Display dels canals de cadascuna de les opcions parcials:</div>
      <div class="partial-options-zones" v-if="partials && partials.length">
        <div class="partial-option" v-for="(p, pi) in partials" :key="p.option_id ?? pi">
          <div class="partial-title">Opció: {{ pi + 1 }}</div>
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

    <!-- SVG overlay for connection lines -->
    <svg class="connections-svg" v-if="containerRef">
      <line v-for="ln in lines" :key="ln.portIdx" :x1="ln.x1" :y1="ln.y1" :x2="ln.x2" :y2="ln.y2" stroke="#22c55e" stroke-width="4" stroke-linecap="round" @click="removeConnection(ln.portIdx)" />
      <line v-if="dragging.active && dragging.from" :x1="dragging.startX" :y1="dragging.startY" :x2="(dragging.x - (containerRef ? containerRef.getBoundingClientRect().left : 0))" :y2="(dragging.y - (containerRef ? containerRef.getBoundingClientRect().top : 0))" stroke="#22c55e" stroke-width="3" stroke-linecap="round" />
    </svg>
  </div>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'

const props = defineProps({ option: { type: Object, default: null }, numPorts: { type: Number, default: 8 } })
const emit = defineEmits(['mapping-changed'])

const leftCount = computed(() => Math.floor(props.numPorts / 2))
const rightCount = computed(() => props.numPorts - Math.floor(props.numPorts / 2))
const portLabels = computed(() => Array.from({ length: props.numPorts }, (_, i) => `P${i+1}`))
const portsSelected = ref(Array.from({ length: props.numPorts }, () => false))

// mapping state
const portToBox = ref({})
const boxToPorts = ref({})

const selectedBox = ref(null)

// DOM refs for ports and partial-port nodes
const containerRef = ref(null)
const portRefs = ref([])
const partialRefs = ref({})

// mapping: port index -> partialKey ("pi:si")
const portToPartial = ref({})
// reverse mapping: partialKey -> [portIdx,...]
const partialToPorts = ref({})

// derive partials / zoneBoxes from option when available
const partials = computed(() => {
  if (!props.option) return []
  return props.option.partial_options || props.option.partials || []
})

const zoneBoxes = computed(() => {
  if (props.option && props.option.zone_boxes) return props.option.zone_boxes
  const p = partials.value
  if (!p || !p.length) return []
  return [{ title: null, boxes: p.map(pp => [pp.f_start ?? pp[0], pp.f_end ?? pp[1]]) }]
})

// dragging state
const dragging = ref({ active: false, from: null, startX: 0, startY: 0, x: 0, y: 0 })

function setPortRef(el, idx){ if (!el) return; portRefs.value[idx] = el }
function setPartialRef(el, pi, si){ if (!el) return; partialRefs.value[`${pi}:${si}`] = el }

function getElementCenter(el){
  if (!el || !containerRef.value) return { x: 0, y: 0 }
  const crect = containerRef.value.getBoundingClientRect()
  const r = el.getBoundingClientRect()
  return { x: (r.left + r.right)/2 - crect.left, y: (r.top + r.bottom)/2 - crect.top }
}

function startDragFromPartial(pi, si, ev){
  const key = `${pi}:${si}`
  dragging.value.active = true
  dragging.value.from = { type: 'partial', key, pi, si }
  const el = partialRefs.value[key]
  const c = getElementCenter(el)
  dragging.value.startX = c.x; dragging.value.startY = c.y
  dragging.value.x = ev.clientX; dragging.value.y = ev.clientY
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
}

function startDragFromPort(portIdx, ev){
  dragging.value.active = true
  dragging.value.from = { type: 'port', portIdx }
  const el = portRefs.value[portIdx]
  const c = getElementCenter(el)
  dragging.value.startX = c.x; dragging.value.startY = c.y
  dragging.value.x = ev.clientX; dragging.value.y = ev.clientY
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp)
}

function onPointerMove(ev){
  dragging.value.x = ev.clientX
  dragging.value.y = ev.clientY
}

function flattenPartialPorts(){
  const list = []
  for (let pi = 0; pi < partials.value.length; pi++){
    const ports = computePorts(partials.value[pi])
    for (let si = 0; si < ports.length; si++) list.push({ key: `${pi}:${si}`, pi, si })
  }
  return list
}
function findPortAtClientPos(cx, cy){
  for (let i = 0; i < portRefs.value.length; i++){
    const el = portRefs.value[i]
    if (!el) continue
    const r = el.getBoundingClientRect()
    if (cx >= r.left && cx <= r.right && cy >= r.top && cy <= r.bottom) return i
  }
  return null
}

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

function onPointerUp(ev){
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
  if (!dragging.value.active) return
  const cx = ev.clientX, cy = ev.clientY
  const portIdx = findPortAtClientPos(cx, cy)
  const partialHit = findPartialAtClientPos(cx, cy)

  if (dragging.value.from.type === 'partial' && portIdx != null){
    const { pi, si } = dragging.value.from
    assignPortToPartial(portIdx, pi, si)
  } else if (dragging.value.from.type === 'port' && partialHit){
    assignPortToPartial(dragging.value.from.portIdx, partialHit.pi, partialHit.si)
  }

  dragging.value.active = false
  dragging.value.from = null
}

function assignPortToPartial(portIdx, pi, si){
  const key = `${pi}:${si}`
  const prev = portToPartial.value[portIdx]
  // enforce 2-partial partitioning rule: when exactly 2 partials, restrict port domains
  if (partials.value.length === 2) {
    if (pi === 0 && portIdx >= Math.floor(props.numPorts/2)){
      alert('L\'opció parcial 1 només es pot connectar als primers 4 ports')
      return
    }
    if (pi === 1 && portIdx < Math.floor(props.numPorts/2)){
      alert('L\'opció parcial 2 només es pot connectar als últims 4 ports')
      return
    }
  }
  if (prev === key) return

  if (prev != null){
    const arrPrev = (partialToPorts.value[prev] || []).filter(x => x !== portIdx)
    if (arrPrev.length === 0){
      // try to find an unassigned physical port to give to prev
      const unassignedIdx = Array.from({ length: props.numPorts }).findIndex((_, idx) => portToPartial.value[idx] == null && idx !== portIdx)
      if (unassignedIdx !== -1){
        portToPartial.value[unassignedIdx] = prev
        partialToPorts.value[prev] = [unassignedIdx]
      } else {
        // try to steal from a partial that has >1 ports
        let stolen = null
        for (let j = 0; j < props.numPorts; j++){
          if (j === portIdx) continue
          const pj = portToPartial.value[j]
          if (pj && (partialToPorts.value[pj] || []).length > 1){
            partialToPorts.value[pj] = partialToPorts.value[pj].filter(x => x !== j)
            portToPartial.value[j] = prev
            partialToPorts.value[prev] = [j]
            stolen = j
            break
          }
        }
        if (stolen == null){
          alert(' No es pot reassignar: l\'opció parcial anterior doncs es quedaria desconnectada i no hi ha ports disponibles.')
          return
        }
      }
    } else {
      partialToPorts.value[prev] = arrPrev
    }
  }

  portToPartial.value[portIdx] = key
  partialToPorts.value[key] = partialToPorts.value[key] || []
  if (!partialToPorts.value[key].includes(portIdx)) partialToPorts.value[key].push(portIdx)
  emit('mapping-changed', { portToPartial: portToPartial.value, partialToPorts: partialToPorts.value })
}

function removeConnection(portIdx){
  const prev = portToPartial.value[portIdx]
  if (prev == null) return
  const arr = partialToPorts.value[prev] || []
  if (arr.length <= 1){
    alert('No es pot eliminar la darrera connexió per aquest port parcial.')
    return
  }
  partialToPorts.value[prev] = arr.filter(x => x !== portIdx)
  delete portToPartial.value[portIdx]
  emit('mapping-changed', { portToPartial: portToPartial.value, partialToPorts: partialToPorts.value })
}

function onBoxClick(idx){ selectedBox.value = idx }

function onPortToggle(i, isSelected){
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

function autoAssign(){
  // Iterate every partial option and assign every band (sub-port) to the first
  // available physical port that respects the connection rules.
  portToPartial.value = {}
  partialToPorts.value = {}
  portsSelected.value = Array.from({ length: props.numPorts }, () => false)

  if (!partials.value || partials.value.length === 0) {
    emit('mapping-changed', { portToPartial: portToPartial.value, partialToPorts: partialToPorts.value })
    return
  }

  const nPorts = Number(props.numPorts || 0)
  const leftCountLocal = Math.floor(nPorts/2)
  const leftPorts = Array.from({ length: leftCountLocal }, (_, i) => i)
  const rightPorts = Array.from({ length: nPorts - leftCountLocal }, (_, i) => i + leftCountLocal)

  function allowedPortsForPartial(pi){
    if (partials.value.length === 2){
      return (pi === 0) ? leftPorts : rightPorts
    }
    return Array.from({ length: nPorts }, (_, i) => i)
  }

  const unassigned = []

  for (let pi = 0; pi < partials.value.length; pi++){
    const bands = computePorts(partials.value[pi])
    for (let si = 0; si < bands.length; si++){
      const key = `${pi}:${si}`
      const candidates = allowedPortsForPartial(pi)

      // 1) choose first unassigned candidate port
      let chosen = candidates.find(p => portToPartial.value[p] == null)

      // 2) if none free, prefer a port already assigned to the same partial (same pi)
      if (chosen == null){
        chosen = candidates.find(p => {
          const v = portToPartial.value[p]
          return v != null && v.split(':')[0] === String(pi)
        })
      }

      // 3) if still none, we cannot assign this band
      if (chosen == null){
        unassigned.push({ pi, si, key })
        continue
      }

      // Assign
      portToPartial.value[chosen] = key
      partialToPorts.value[key] = partialToPorts.value[key] || []
      if (!partialToPorts.value[key].includes(chosen)) partialToPorts.value[key].push(chosen)
      portsSelected.value[chosen] = true
    }
  }

  if (unassigned.length > 0){
    // Inform user that not all bands could be connected
    alert(`No hi ha ports disponibles per connectar ${unassigned.length} canals; deixats sense assignar.`)
  }

  emit('mapping-changed', { portToPartial: portToPartial.value, partialToPorts: partialToPorts.value })
}

function computePorts(p){
  const fs = Number(p?.f_start ?? p?.[0] ?? 0)
  const fe = Number(p?.f_end ?? p?.[1] ?? 0)
  const num = Math.max(1, Number(p?.chans_needed ?? p?.chansNeeded ?? p?.chans ?? 1))
  const total = Math.max(0, fe - fs)
  const piece = num > 0 ? total / num : total
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

function formatFreq(f){
  const v = Number(f)
  if (isNaN(v)) return String(f)
  if (v >= 1e9) return (v/1e9).toFixed(3) + ' GHz'
  if (v >= 1e6) return (v/1e6).toFixed(3) + ' MHz'
  if (v >= 1e3) return (v/1e3).toFixed(0) + ' kHz'
  return v + ' Hz'
}

const lines = computed(() => {
  const out = []
  if (!containerRef.value) return out
  const crect = containerRef.value.getBoundingClientRect()
  const n = Number(props.numPorts || 0)
  for (let i = 0; i < n; i++){
    const key = portToPartial.value[i]
    if (!key) continue
    const portEl = portRefs.value[i]
    const partialEl = partialRefs.value[key]
    if (!portEl || !partialEl) continue
    const pr = portEl.getBoundingClientRect()
    const br = partialEl.getBoundingClientRect()
    const x1 = (pr.left + pr.right)/2 - crect.left
    const y1 = (pr.top + pr.bottom)/2 - crect.top
    const x2 = (br.left + br.right)/2 - crect.left
    const y2 = (br.top + br.bottom)/2 - crect.top
    out.push({ portIdx: i, x1, y1, x2, y2 })
  }
  return out
})

// initialize mapping if option provided
watch(() => props.option, (o) => { if (o) autoAssign() })

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
})

defineExpose({ autoAssign })
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
