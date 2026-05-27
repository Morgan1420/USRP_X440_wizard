<template>
  <div class="ports-shell" ref="containerRef">
    <section class="ports-section">
      <h4>Ports</h4>
      
      <div class="ports-box">
        <div class="empty-port"></div>
        <div v-for="i in leftCount" :key="'left-'+i" class="port" :ref="el => setPortRef(el, i-1)" :class="{assigned: portToPartial[i-1] != null}" @pointerdown.prevent="startDragFromPort(i-1, $event)">{{ portLabels[i-1] }}</div>
        <div class="empty-port"></div>
        <div v-for="i in rightCount" :key="'right-'+i" class="port" :ref="el => setPortRef(el, leftCount + (i-1))" :class="{assigned: portToPartial[leftCount + (i-1)] != null}" @pointerdown.prevent="startDragFromPort(leftCount + (i-1), $event)">{{ portLabels[leftCount + (i-1)] }}</div>
        <div class="empty-port"></div>
      </div>

      <div class="partial-options-zones" v-if="partials && partials.length">
        <div class="partial-option" v-for="(p, pi) in partials" :key="p.option_id ?? pi">
          <div class="partial-title">Option {{ pi + 1 }}</div>
          <div class="partial-ports">
            <div class="partial-port" v-for="(port, si) in computePorts(p)" :key="si">
              <div class="dot-port" :ref="el => setPartialRef(el, pi, si)" @pointerdown.prevent="startDragFromPartial(pi, si, $event)"></div>
              <div class="freqs">
                <div class="freq">{{ formatFreq(port.f_start) }}</div>
                <div class="freq">{{ formatFreq(port.f_end) }}</div>
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

function flattenPartialPorts(){
  const list = []
  for (let pi = 0; pi < partials.value.length; pi++){
    const ports = computePorts(partials.value[pi])
    for (let si = 0; si < ports.length; si++) list.push({ key: `${pi}:${si}`, pi, si })
  }
  return list
}

const lines = computed(() => {
  const out = []
  for (const [portIdxStr, key] of Object.entries(portToPartial.value)){
    const portIdx = Number(portIdxStr)
    const portEl = portRefs.value[portIdx]
    const partEl = partialRefs.value[key]
    if (!portEl || !partEl) continue
    const a = getElementCenter(partEl)
    const b = getElementCenter(portEl)
    out.push({ portIdx, key, x1: a.x, y1: a.y, x2: b.x, y2: b.y })
  }
  return out
})

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

function onNetworkUpdate(cfg){ emit('network-update', cfg) }

function autoAssign(){
  const plist = flattenPartialPorts()
  portToPartial.value = {}
  partialToPorts.value = {}
  if (partials.value.length === 2) {
    const leftPorts = Array.from({ length: Math.floor(props.numPorts/2) }, (_, i) => i)
    const rightPorts = Array.from({ length: Math.ceil(props.numPorts/2) }, (_, i) => i + Math.floor(props.numPorts/2))
    const p0 = plist.filter(x => x.pi === 0)
    for (let i = 0; i < p0.length && i < leftPorts.length; i++){
      const key = p0[i].key
      const portIdx = leftPorts[i]
      portToPartial.value[portIdx] = key
      partialToPorts.value[key] = [portIdx]
      portsSelected.value[portIdx] = true
    }
    const p1 = plist.filter(x => x.pi === 1)
    for (let i = 0; i < p1.length && i < rightPorts.length; i++){
      const key = p1[i].key
      const portIdx = rightPorts[i]
      portToPartial.value[portIdx] = key
      partialToPorts.value[key] = [portIdx]
      portsSelected.value[portIdx] = true
    }
    for (let i = p0.length; i < leftPorts.length; i++){
      const key = p0[i % p0.length]?.key || (p0[0] && p0[0].key)
      if (!key) break
      const portIdx = leftPorts[i]
      portToPartial.value[portIdx] = key
      partialToPorts.value[key] = partialToPorts.value[key] || []
      partialToPorts.value[key].push(portIdx)
      portsSelected.value[portIdx] = true
    }
    for (let i = p1.length; i < rightPorts.length; i++){
      const key = p1[i % Math.max(1,p1.length)]?.key || (p1[0] && p1[0].key)
      if (!key) break
      const portIdx = rightPorts[i]
      portToPartial.value[portIdx] = key
      partialToPorts.value[key] = partialToPorts.value[key] || []
      partialToPorts.value[key].push(portIdx)
      portsSelected.value[portIdx] = true
    }
  } else {
    const pcount = plist.length
    let assigned = 0
    for (let i = 0; i < Math.min(props.numPorts, pcount); i++){
      const key = plist[i].key
      portToPartial.value[i] = key
      partialToPorts.value[key] = [i]
      portsSelected.value[i] = true
      assigned++
    }
    for (let i = assigned; i < props.numPorts; i++){
      const target = plist[(i - assigned) % Math.max(1, pcount)]
      const key = target.key
      portToPartial.value[i] = key
      partialToPorts.value[key] = partialToPorts.value[key] || []
      partialToPorts.value[key].push(i)
      portsSelected.value[i] = true
    }
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
    out.push({ f_start: s, f_end: e })
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

// initialize mapping if option provided
watch(() => props.option, (o) => { if (o) autoAssign() })

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerup', onPointerUp)
})

defineExpose({ autoAssign })
</script>

<style scoped>
.ports-shell{ position:relative }
.ports-box{ 
  display: flex;
  justify-content: space-between;
  gap:12px; 
  padding:12px; 
  border:1px solid #eee; 
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
  border:2px solid #bbb;
  border-radius:100%;

  display:flex;
  justify-content:center;
  align-items:center;

  font-size:12px;
  color:#555;
}

.port.assigned{ 
  box-shadow:0 0 0 3px rgba(34,197,94,0.12);
  background:#22c55e; 

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
  
  border:1px solid #f3f6fb; 
  border-radius:8px; 
  background:#fff; 
}
.partial-title{ font-weight:700; text-align:center; margin-bottom:6px }
.partial-ports{ display:flex; gap:8px; align-items:flex-start; justify-content:center; flex-wrap:wrap }
.partial-port{ display:flex; gap:8px; align-items:center; padding:6px 8px; border-radius:6px; background:#fafafa; border:1px solid #eee; min-width:140px }
.dot-port{ 
  width:12px;
  height:12px;
  border-radius:50%;
  background:#2b80ff;
  border:2px solid #164fdd;
 }
.freqs{ display:flex; flex-direction:column }
.freq{ font-size:12px; color:#222 }

.connections-svg{ position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none }
.connections-svg line{ pointer-events:stroke; cursor:pointer }

.ports-section{ background:#fff; border:1px solid #eee; padding:12px; border-radius:6px }

</style>
