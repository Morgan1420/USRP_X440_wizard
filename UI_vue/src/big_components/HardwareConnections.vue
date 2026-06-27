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
  // Imports
  import { ref, watch, onBeforeUnmount, onMounted } from 'vue'
  import PartialOptionsBoxes from '../mid_components/PartialOptionsBoxes.vue'
  import NetworkConnections from '../mid_components/NetworkConnections.vue'
  import PortsConnections from '../mid_components/PortsConnections.vue'
  import SampleRateOptions from '../mid_components/SampleRateOptions.vue'
  import Button from '../small_components/Button.vue'

  // Props i emits
  const props = defineProps({ option: { type: Object, default: null }, numPorts: { type: Number, default: 8 } })
  const emit = defineEmits(['close','capture','mapping-changed'])

  // Variables i constants
  const portsRef = ref(null)
  const networkRef = ref(null)
  const sampleRateRef = ref(null)
  const mappingData = ref(null)

  // Funció per calcular els ports assignats a cada partial option i sub-partial
  function computePortsForPartial(p){
    // Recuperem la freq. inicial, freq. final i nombre de canals
    const fs = Number(p?.f_start ?? p?.[0] ?? 0)
    const fe = Number(p?.f_end ?? p?.[1] ?? 0)
    const num = Math.max(1, Number(p?.chans_needed ?? p?.chansNeeded ?? p?.chans ?? 1))

    // Calculem l'amplada de banda total i l'amplada de banda per canal
    const total = Math.max(0, fe - fs)
    const piece = num > 0 ? total / num : total
    
    // Creem un array amb els ports assignats a cada sub-partial
    const out = []
    for (let i = 0; i < num; i++){
      // Calculem la freq. inicial i final del sub-partial
      const s = fs + i * piece 
      const e = (i < num - 1) ? s + piece : fe 
      const center = (s + e) / 2 
      const bw = Math.abs(e - s) 

      // Afegim l'objecte a l'array
      out.push({ f_start: s, f_end: e, f_center: center, bw: bw })
    }
    return out
  }

  // Funció per gestionar l'event de mapping-changed emès pel component PortsConnections
  function forwardMapping(payload){
    mappingData.value = payload
    emit('mapping-changed', payload)
  }

  // Funció per gestionar el clic al botó Capture
  async function handleCapture(){
    // Fem un try catch pq és una funció important
    try{
      // Recuperem les dades de l'opció parcial
      const optionData = props.option || {}

      // Recuperem les dades del mapping
      let mapping = mappingData.value
      if ((!mapping || Object.keys(mapping).length === 0) && portsRef.value && typeof portsRef.value.getMapping === 'function'){
        mapping = portsRef.value.getMapping()
      }

      // Construïm l'objecte de ports assignats a cada partial option i sub-partial
      const portsObj = {}
      if (mapping && mapping.partialToPorts){
        // Si els prots assignats no estan agrupats per partial option i sub-partial, els agrupem
        const grouped = {}
        for (const k in mapping.partialToPorts){
          const parts = k.split(':')
          const pi = Number(parts[0])
          const si = Number(parts[1])
          if (!grouped[pi]) grouped[pi] = []
          grouped[pi][si] = (mapping.partialToPorts[k] || []).map(idx => idx + 1)
        }

        // Per cada partial option, obtenim els ports assignats a cada sub-partial i les seves metadades
        const partials = (props.option && (props.option.partial_options || props.option.partials) || [])
        for (let pi = 0; pi < partials.length; pi++){
          // Recuperem partail option i metadades
          const p = partials[pi] || {}
          const portsMeta = computePortsForPartial(p)

          // Construïm l'array de ports assignats a cada sub-partial
          const sis = []
          for (const k in mapping.partialToPorts){
            const [ppi, psi] = k.split(':').map(Number)
            if (ppi === pi) sis.push(psi)
          }
          
          // Si no hi ha sub-partials assignats, utilitzem el nombre de ports com a sub-partials
          const maxSi = sis.length > 0 ? Math.max(...sis) : (portsMeta.length > 0 ? portsMeta.length - 1 : -1)
          
          // Construïm l'array de ports assignats a cada sub-partial amb les metadades corresponents
          const count = Math.max(portsMeta.length, maxSi + 1)
          
          // Afegim l'array a l'objecte de ports assignats a cada partial option
          const arr = []
          for (let si = 0; si < count; si++){
            const assigned = (grouped[pi] && grouped[pi][si]) ? grouped[pi][si] : []
            const meta = portsMeta[si] || { f_center: null, bw: null }
            arr.push({ [`Channel-${si+1}`]: assigned, f_center: meta.f_center, bw: meta.bw })
          }

          // Afegim l'array a l'objecte de ports assignats a cada partial option
          portsObj[`Partial-option-${pi+1}`] = arr
        }
      }

      // Recuperem les dades de connexió de xarxa del component NetworkConnections
      let networkConfig = []
      if (networkRef.value && typeof networkRef.value.getConfig === 'function') networkConfig = networkRef.value.getConfig()

      // Recuperem les dades de configuració de sample rate
      let sampleConf = { mode: 'auto', manualValue: '' }
      if (sampleRateRef.value && typeof sampleRateRef.value.getConfig === 'function') sampleConf = sampleRateRef.value.getConfig()
      const sampleRateObj = { Automàtic: sampleConf.mode === 'auto', 'Sample-rate': Number(sampleConf.manualValue) || 0, 'Temps de captura': Number(sampleConf.captureTime) || 0 }

      // Construïm l'objecte final amb totes les dades i fem la crida al backend per iniciar la captura
      const info = { Option: optionData, Ports: portsObj, Connections: networkConfig, 'Sample-rate': [sampleRateObj] }
      
      // Fem la crida al backend per iniciar la captura
      const resp = await fetch('http://127.0.0.1:5000/api/start_capture', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(info) })
      const data = await resp.json()
      if (data.ok){
        // Si tot ha anat bé, mostrem un missatge d'èxit i emetem l'event capture
        alert('Capture sent successfully')
        emit('capture')
      } else {
        // Si hi ha hagut algun error, mostrem un missatge d'error
        alert('Failed to send capture: ' + (data.message || 'unknown'))
      }
    } catch (e){
      // Si hi ha hagut algun error, mostrem un missatge d'error
      console.error(e)
      alert('Error sending capture: ' + e.message)
    }
  }

  // Funció per obtenir la configuració actual de l'opció, ports assignats...
  onMounted(() => {
    if (portsRef.value && typeof portsRef.value.autoAssign === 'function') portsRef.value.autoAssign()
  })

  // Watcher per quan canvia l'opció, per recalcular els ports assignats
  watch(() => props.option, (o) => {
    if (o && portsRef.value && typeof portsRef.value.autoAssign === 'function') portsRef.value.autoAssign()
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
