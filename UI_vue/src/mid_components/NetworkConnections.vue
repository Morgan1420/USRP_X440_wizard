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
      <div class="col validated"> <span :class="{ok: r.validated === 'valid', invalid: r.validated === 'invalid', validating: r.validated === 'validating'}">{{ r.validated || '-' }}</span> </div>
    </div>

    <div class="actions">
      <button @click="validateAll">Validate Connections</button>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const props = defineProps({ rowsCount: { type: Number, default: 2 } })

const rows = reactive([])
for (let i = 0; i < props.rowsCount; i++) rows.push({ name: `QSFP28_${i+1}`, ipA: '', ipB: '', connected: false, validated: '-' })

function toggleConnected(i){ rows[i].connected = !rows[i].connected;}

function isIPv4(ip){
  if (!ip) return false
  const re = /^(25[0-5]|2[0-4]\d|1?\d?\d)(\.(25[0-5]|2[0-4]\d|1?\d?\d)){3}$/
  return re.test(ip.trim())
}

async function validateAll(){
  const toValidate = []
  rows.forEach(r => {
    if (!r.connected) {
      r.validated = '-'
      return
    }
    if (!isIPv4(r.ipA) && !isIPv4(r.ipB)) {
      r.validated = 'invalid'
      return
    }
    r.validated = 'validating...'
    toValidate.push({ name: r.name, ipA: r.ipA, ipB: r.ipB, connected: r.connected })
  })
  
  if (toValidate.length === 0) return

  try {
    const resp = await fetch('http://127.0.0.1:5000/api/validate_connections', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rows: toValidate })
    })
    const data = await resp.json()
    if (data.ok && Array.isArray(data.results)) {
      data.results.forEach(rres => {
        const idx = rows.findIndex(rr => rr.name === rres.name)
        if (idx !== -1) rows[idx].validated = rres.status
      })
    } else {
      toValidate.forEach(t => {
        const idx = rows.findIndex(rr => rr.name === t.name)
        if (idx !== -1) rows[idx].validated = 'invalid'
      })
    }
  } catch (e) {
    console.error(e)
    toValidate.forEach(t => {
      const idx = rows.findIndex(rr => rr.name === t.name)
      if (idx !== -1) rows[idx].validated = 'invalid'
    })
  }
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
.validated .invalid{ color:crimson; font-weight:600 }
.validated .validating{ color:#f39c12; font-weight:600 }
.actions{ display:flex; justify-content:flex-end; margin-top:8px }
.actions button{ padding:8px 12px; border-radius:6px }
</style>
