<template>
  <div class="pop-up-box" role="dialog" aria-modal="true">
    <h3>Filter options</h3>
    <div class="rows">
      <InputBox ref="minRef" label="Min num of channels:   " placeholder="" :label-gap="labelGap" />
      <InputBox ref="maxRef" label="Max num of channels:   " placeholder="" :label-gap="labelGap" />
      <SelectBox ref="selectRef" label="Sorting option" :options="['max chan','min chan','min overlap']" :label-gap="labelGap" />
      <div class="actions">
        <Button label="Cancel" variant="secondary" @click="onCancel"></Button>
        <Button label="OK" variant="primary" @click="onOk"></Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import InputBox from '../small_components/InputBox.vue'
import SelectBox from '../small_components/SelectBox.vue'
import Button from '../small_components/Button.vue'

const emit = defineEmits(['save','close'])
const labelGap = 250

const minRef = ref(null)
const maxRef = ref(null)
const selectRef = ref(null)

function parseIntLike(s) {
  if (s == null) return null
  const t = String(s).trim()
  if (t === '') return null
  const n = parseInt(parseFloat(t))
  return Number.isNaN(n) ? null : n
}

async function onOk() {
  // Recuperem els valors dels InputBox i del SelectBox
  const minVal = parseIntLike(minRef.value?.getText?.() ?? '')
  const maxVal = parseIntLike(maxRef.value?.getText?.() ?? '')
  const sortVal = selectRef.value?.getValue?.() ?? ''

  // Validem els valors (per exemple, min ha de ser <= max)
  if ((minVal != null && minVal < 0) || (maxVal != null && maxVal < 0)) {
    alert('Error: Values must be non-negative.')
    return
  }
  if (minVal != null && maxVal != null && minVal > maxVal) {
    alert('Error: Min value must be <= max value.')
    return
  }
  
  // Preparem l'objecte a enviar
  const obj = { min_channels: minVal, max_channels: maxVal, sorting: sortVal }

  // Enviem l'objecte al backend
  // Fem un try catch per si hi hagués cap error amb el BE
  try {
    // 
    const res = await fetch('http://localhost:5000/api/store_filters', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(obj)
    })

    if (!res.ok) {
      let txt = ''
      try { txt = await res.text() } catch (e) { txt = String(res.status) }
      alert('Failed saving filters: ' + txt)
      return
    }

    const data = await res.json().catch(() => null)
    if (data && data.ok) {
      try { localStorage.setItem('filters', JSON.stringify(obj)) } catch (e) {}
      emit('save', obj)
      emit('close')
      return
    }

    alert('Failed saving filters: ' + (data && data.message ? data.message : 'unknown error'))
  } catch (e) {
    console.error('Error posting filters', e)
    alert('Error connecting to backend; ensure it is running on http://localhost:5000')
  }
}

onMounted(async () => {
  // Fem un try catch per si hi hagués cap error amb el BE
  try {
    // Recuperem els valors dels filtres
    const res = await fetch('http://localhost:5000/api/load_filters', { cache: 'no-store' })
    
    // Si la resposta és correcta, actualitzem els camps del pop-up
    if (res.ok) {
      // Recuperem les dades si existeixen
      const data = await res.json()
      const min = data.min_channels
      const max = data.max_channels
      const sorting = data.sorting 

      // Actualitzem el text dels InputBox
      if (minRef.value?.setText) minRef.value.setText(String(min))
      if (maxRef.value?.setText) maxRef.value.setText(String(max))

      // Actualitzem el SelectBox segons l'opció de sorting
      const opts = ['max chan','min chan','min overlap']
      const idx = opts.findIndex(o => (sorting || '').toLowerCase().includes(o))
      if (idx >= 0 && selectRef.value?.setSelected) 
        selectRef.value.setSelected(idx)
    }
  } catch (e) {
    console.error('Could not load filters via API:', e)
  }
})
</script>

<style scoped>

.pop-up-box { 
  position: absolute; 
  top: 32.5%; 
  left: 35%;
  width: 30%; 

  background:#fff; 
  padding:18px;
  border-radius:8px;
  box-shadow:0 8px 30px rgba(0,0,0,0.15);
}

.pop-up-box h3 { 
  font-size: 1.8rem;
  margin-top:0;
  text-align:center; 
}

.rows { 
  margin-bottom:12px;

  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:space-between;
  gap:15px;
}
.actions { 
  width:90%;
  display:flex; 
  justify-content:space-between; 
  gap:10px; 
  margin-top:8px; 
}
</style>
