<template>
  <div class="network-connections">
    <h4>Connexions QSFP28</h4>
    <div class="network-grid">
          <div class="header-row">
            <div class="col name">Connexió:</div>
            <div class="col ip">Adreça IP:</div>
            <div class="col connected">Estan connectats?</div>
            <div class="col validated">La connexió és vàlida?</div>
          </div>

          <div class="row" v-for="(r, i) in rows" :key="i">
            <div class="col name">{{ r.name }}</div>
            <div class="col ip"><input v-model="r.ipAddr" type="text" placeholder="0.0.0.0" /></div>
            <div class="col connected"><button :class="{on:r.connected}" @click="toggleConnected(i)">{{ r.connected ? 'Yes' : 'No' }}</button></div>
            <div class="col validated"> <span :class="{ok: r.validated === 'Si', invalid: r.validated === 'No', validating: r.validated === 'validant...'}">{{ r.validated || '-' }}</span> </div>
          </div>

      <div class="actions">
        <button @click="validateAll">Validar Connexions</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const props = defineProps({ rowsCount: { type: Number, default: 2 } })

const rows = reactive([])
for (let i = 0; i < props.rowsCount; i++) rows.push({ name: `QSFP28_${i+1}`, ipAddr: '', connected: false, validated: '-' })

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
      if (!isIPv4(r.ipAddr)) {
        r.validated = 'No'
        return
      }
      r.validated = 'validant...'
      toValidate.push({ name: r.name, ipAddr: r.ipAddr, connected: r.connected })
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
        if (idx !== -1) rows[idx].validated = 'No'
      })
    }
  } catch (e) {
    console.error(e)
    toValidate.forEach(t => {
      const idx = rows.findIndex(rr => rr.name === t.name)
      if (idx !== -1) rows[idx].validated = 'No'
    })
  }
}

function getConfig(){
  return rows.map(r => ({ name: r.name, ipAddr: r.ipAddr, connected: r.connected, validated: r.validated }))
}

defineExpose({ getConfig })
</script>

<style scoped>

.network-connections{ 
  padding:12px; 
  background:#f9f9f9; 
  border:5px solid #ddd; 
  border-radius:10px;

  display:flex;
  flex-direction:column;
  align-items:center;
  gap:12px;
}

h4 {
  padding:10px;
  margin:0;
  font-size:1.7rem;
}

.network-grid{ 
  width:90%;
  display:flex;
  flex-direction:column;
  gap:8px;
}
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
.connected button{ 
  padding:6px 8px; 
  border-radius:6px;
  border:2px solid #ccc;
}
.connected button.on{ 
  background:#2b80ff; 
  color:white;
  border:2px solid #2b80ff;
}
.col.connected button:hover{ 
  transform:scale(1.1);
}
.validated .ok{ color:green; font-weight:600 }
.validated .invalid{ color:crimson; font-weight:600 }
.validated .validating{ color:#f39c12; font-weight:600 }
.actions{ 
  padding-right:15px;
  display:flex; 
  justify-content:flex-end; 
  margin-top:8px }
.actions button{ 
  padding:8px 12px; 
  border-radius:6px;
  background:#2b80ff;
  color:white;
  font-weight:600;
  font-size:1em;
  border:2px solid #2b80ff
}
.actions button:hover{ 
  transform:scale(1.05);
}
</style>
