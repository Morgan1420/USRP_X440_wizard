<template>
  <div class="app">
    <h2>USRP X440 UI (Vue)</h2>
    
    <OptionsGeneration />


</div>
    
</template>

<script setup>
import { ref } from 'vue'
import InputBox from './small_components/InputBox.vue'
import Button from './small_components/Button.vue'
import FilterPopUp from './mid_components/FilterPopUp.vue'
import OptionsScrollArea from './small_components/OptionsScrollArea.vue'

import OptionsGeneration from './big_components/OptionsGeneration.vue'

const fcMultipliers = [{ label: 'M', value: 1e6 }, { label: 'G', value: 1e9 }]

const fminRef = ref(null)
const fmaxRef = ref(null)
const showFilter = ref(false)
const status = ref('')
const optionsRef = ref(null)

async function onGenerate() {
  const fmin = fminRef.value?.getComputedValue?.()
  const fmax = fmaxRef.value?.getComputedValue?.()
  const time = 1
  if (fmin == null || fmax == null) {
    status.value = 'Error: Please enter valid numeric values.'
    return
  }
  status.value = 'Generating options...'
  try {
    const res = await fetch('http://localhost:5000/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ f_min: fmin, f_max: fmax, time })
    })
    const data = await res.json()
    if (!res.ok || !data.ok) {
      status.value = 'Error: ' + (data.message || res.statusText)
      return
    }
    status.value = `Generated ${data.count || (data.items && data.items.length) || 0} options` 
    // refresh options list
    optionsRef.value?.refresh?.()
  } catch (e) {
    console.error(e)
    status.value = 'Error: Generation failed'
  }
}

function openFilter() {
  showFilter.value = true
}

async function onFilterSave(obj) {
  try {
    const res = await fetch('http://localhost:5000/api/filters', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(obj)
    })
    if (!res.ok) throw new Error('Save failed')
    status.value = 'Filters saved'
  } catch (e) {
    console.error(e)
    status.value = 'Error: could not save filters'
  } finally {
    showFilter.value = false
  }
}
</script>

<style scoped>
.app { padding:20px; font-family: Arial, Helvetica, sans-serif; }
.top-row { display:flex; align-items:center; gap:12px; }
.buttons { display:flex; gap:8px; align-items:center; margin-left:8px; }
.status { margin-top:12px; color: #333; }
</style>
