<template>
  <div class="hardware-shell" ref="containerRef">
    <div class="header">
      <div><Button label="Back" variant="secondary" @click="$emit('close')"/></div>
      <h3>Hardware Connections</h3>
      <div class="empty_class"></div>
    </div>

    <section class="top-section">
      <PortsConnections ref="portsRef" :option="option" :numPorts="numPorts" @mapping-changed="forwardMapping" />
    </section>
    

    <section class="bottom-section">
      <NetworkConnections ref="networkRef" class="network-section" />
      <SampleRateOptions ref="sampleRateRef" class="sample-rate-section" :option="option" />
    </section>

    <div class="footer">
        <Button label="Capture" @click="handleCapture"/>
      </div>
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount, onMounted } from 'vue'
import PartialOptionsBoxes from '../mid_components/PartialOptionsBoxes.vue'
import NetworkConnections from '../mid_components/NetworkConnections.vue'
import PortsConnections from '../mid_components/PortsConnections.vue'
import SampleRateOptions from '../mid_components/SampleRateOptions.vue'
import Button from '../small_components/Button.vue'

const props = defineProps({ option: { type: Object, default: null }, numPorts: { type: Number, default: 8 } })
const emit = defineEmits(['close','capture','mapping-changed'])

const portsRef = ref(null)
const networkRef = ref(null)
const sampleRateRef = ref(null)
const mappingData = ref(null)

// Helper to split a partial option into its sub-channels (center freq + bw)
function computePortsForPartial(p){
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

function forwardMapping(payload){
  mappingData.value = payload
  emit('mapping-changed', payload)
}

async function handleCapture(){
  try{
    const optionData = props.option || {}

    // get mapping either from emitted payload or directly from child
    let mapping = mappingData.value
    if ((!mapping || Object.keys(mapping).length === 0) && portsRef.value && typeof portsRef.value.getMapping === 'function'){
      mapping = portsRef.value.getMapping()
    }

    const portsObj = {}
    if (mapping && mapping.partialToPorts){
      const grouped = {}
      for (const k in mapping.partialToPorts){
        const parts = k.split(':')
        const pi = Number(parts[0])
        const si = Number(parts[1])
        if (!grouped[pi]) grouped[pi] = []
        grouped[pi][si] = (mapping.partialToPorts[k] || []).map(idx => idx + 1)
      }

      const partials = (props.option && (props.option.partial_options || props.option.partials) || [])
      for (let pi = 0; pi < partials.length; pi++){
        const p = partials[pi] || {}
        const portsMeta = computePortsForPartial(p)

        const sis = []
        // find all si for this pi
        for (const k in mapping.partialToPorts){
          const [ppi, psi] = k.split(':').map(Number)
          if (ppi === pi) sis.push(psi)
        }
        const maxSi = sis.length > 0 ? Math.max(...sis) : (portsMeta.length > 0 ? portsMeta.length - 1 : -1)
        const count = Math.max(portsMeta.length, maxSi + 1)
        const arr = []
        for (let si = 0; si < count; si++){
          const assigned = (grouped[pi] && grouped[pi][si]) ? grouped[pi][si] : []
          const meta = portsMeta[si] || { f_center: null, bw: null }
          arr.push({ [`Channel-${si+1}`]: assigned, f_center: meta.f_center, bw: meta.bw })
        }
        portsObj[`Partial-option-${pi+1}`] = arr
      }
    }

    // network connections
    let networkConfig = []
    if (networkRef.value && typeof networkRef.value.getConfig === 'function') networkConfig = networkRef.value.getConfig()

    // sample rate
    let sampleConf = { mode: 'auto', manualValue: '' }
    if (sampleRateRef.value && typeof sampleRateRef.value.getConfig === 'function') sampleConf = sampleRateRef.value.getConfig()
    const sampleRateObj = { Automàtic: sampleConf.mode === 'auto', 'Sample-rate': Number(sampleConf.manualValue) || 0, 'Temps de captura': Number(sampleConf.captureTime) || 0 }

    const info = { Option: optionData, Ports: portsObj, Connections: networkConfig, 'Sample-rate': [sampleRateObj] }

    const resp = await fetch('http://127.0.0.1:5000/api/start_capture', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(info) })
    const data = await resp.json()
    if (data.ok){
      alert('Capture saved successfully')
      emit('capture')
    } else {
      alert('Failed to save capture: ' + (data.message || 'unknown'))
    }
  } catch (e){
    console.error(e)
    alert('Error saving capture: ' + e.message)
  }
}

// Automatically assign when this screen is mounted and whenever the option changes
onMounted(() => {
  if (portsRef.value && typeof portsRef.value.autoAssign === 'function') portsRef.value.autoAssign()
})

watch(() => props.option, (o) => {
  if (o && portsRef.value && typeof portsRef.value.autoAssign === 'function') portsRef.value.autoAssign()
})

onBeforeUnmount(() => {
  // child PortsConnections will remove its own listeners
})
</script>

<style scoped>
.hardware-shell{ padding:12px; display:flex; flex-direction:column; gap:12px }
.hardware-shell{ position:relative }

.header{ 
  display:flex; 
  justify-content:space-between; 
  align-items:center 
}
.header h3, .header div{ 
  width:30%;
}
.header h3{ 
  text-align:center; 
  font-size:1.6em; 
  font-weight:700;
}

.bottom-section{ 
  width:100%;
  display:flex; 
  gap:18px; 
  justify-content:space-between; 
  align-items:center;
  flex-wrap:wrap; 
}



.content{ display:grid; grid-template-columns:1fr 1fr; gap:18px }
.partials-section, .network-section{ 
  width:60%;
  height: 230px;
 }
.sample-rate-section{
  width: 30%;
  height: 230px;
  padding-block: 12px;
  padding-inline: 2.5%;
}

.footer{ display:flex; gap:8px; justify-content:flex-end }

</style>
