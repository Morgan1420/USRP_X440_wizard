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
      <NetworkConnections class="network-section" />
      <SampleRateOptions class="sample-rate-section" />
    </section>

    <div class="footer">
      <Button label="Auto-connect" @click="callAutoAssign"/>
      <Button label="Capture" @click="$emit('capture')"/>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import PartialOptionsBoxes from '../mid_components/PartialOptionsBoxes.vue'
import NetworkConnections from '../mid_components/NetworkConnections.vue'
import PortsConnections from '../mid_components/PortsConnections.vue'
import Button from '../small_components/Button.vue'

const props = defineProps({ option: { type: Object, default: null }, numPorts: { type: Number, default: 8 } })
const emit = defineEmits(['close','capture','mapping-changed'])

const portsRef = ref(null)

function forwardMapping(payload){
  emit('mapping-changed', payload)
}

function callAutoAssign(){
  if (portsRef.value && typeof portsRef.value.autoAssign === 'function') portsRef.value.autoAssign()
}

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


.content{ display:grid; grid-template-columns:1fr 1fr; gap:18px }
.partials-section, .network-section{ background:#fff; border:1px solid #eee; padding:12px; border-radius:6px }
.footer{ display:flex; gap:8px; justify-content:flex-end }

</style>
