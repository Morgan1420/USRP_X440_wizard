<template>
  <h4>Network</h4>
  <div class="network-grid">
    <div class="header-row">
      <div class="col name">Connection</div>
      <div class="col ip">IP Address </div>
      <div class="col connected">Connected</div>
      <div class="col validated">Validated</div>
    </div>

    <div class="row" v-for="(r, i) in rows" :key="i">
      <div class="col name">{{ r.name }}</div>
      <div class="col ip"><input v-model="r.ipA" type="text" placeholder="0.0.0.0" /></div>
      <div class="col connected"><button :class="{on:r.connected}" @click="toggleConnected(i)">{{ r.connected ? 'Yes' : 'No' }}</button></div>
      <div class="col validated"> <span :class="{ok: r.validated}">{{ r.validated ? 'OK' : '-' }}</span> </div>
    </div>

    <div class="actions">
      <button @click="validateAll">Validate Connections</button>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const props = defineProps({ rowsCount: { type: Number, default: 2 } })
const emit = defineEmits(['update:config'])

const rows = reactive([])
for (let i = 0; i < props.rowsCount; i++) rows.push({ name: `QSFP28_${i+1}`, ipA: '', ipB: '', connected: false, validated: false })

function toggleConnected(i){ rows[i].connected = !rows[i].connected; emit('update:config', getConfig()) }

function isIPv4(ip){
  if (!ip) return false
  const re = /^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$/
  return re.test(ip.trim())
}

function validateAll(){
  rows.forEach(r => {
    r.validated = isIPv4(r.ipA) || isIPv4(r.ipB)
  })
  emit('update:config', getConfig())
}

function getConfig(){
  return rows.map(r => ({ name: r.name, ipA: r.ipA, ipB: r.ipB, connected: r.connected, validated: r.validated }))
}
</script>

<style scoped>
.network-grid{ display:flex; flex-direction:column; gap:8px }
.header-row, .row{ 
  display:flex; 
  justify-content:space-between; 
  align-items:center;
  gap:8px; 
  align-items:center 
}
.col.name{ 
  width: 10%;
  font-weight:600;
  display:flex;
  align-items:center;
  gap:6px;
  justify-content:center;
}
.col.ip{ width: 30%; }
.col.connected,.col.validated{ 
  width: 20%;
  display:flex;
  justify-content:center;
}

.row input{ width:100%; padding:6px; border:1px solid #ccc; border-radius:4px }
.connected button{ padding:6px 8px; border-radius:6px }
.connected button.on{ background:#2b80ff; color:white }
.validated .ok{ color:green; font-weight:600 }
.actions{ display:flex; justify-content:flex-end; margin-top:8px }
.actions button{ padding:8px 12px; border-radius:6px }
</style>
