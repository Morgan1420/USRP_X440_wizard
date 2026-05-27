<template>  
<div class="OptionsGeneration">

  <div class="inputs-display">
    <InputBox ref="fminRef" label="F_min:" placeholder="500" :multipliers="fcMultipliers" unit="Hz" :default-multiplier-index="0" />
    <InputBox ref="fmaxRef" label="F_max:" placeholder="750" :multipliers="fcMultipliers" unit="Hz" :default-multiplier-index="0" />
  </div>

  <div class="buttons-display">
    <Button label="Generar Opcions" variant="primary" @click="onGenerate" />
    
    <!-- NO TOCAR: Poso 2 botons perquè la variable showFilter es tornava boja en fer un toggle -->
    <Button v-if="!showFilter" label="Filters" variant="secondary" @click="openFilterPopUp" />
    <Button v-if="showFilter" label="Filters" variant="secondary" @click="closeFilterPopUp" />
  
  </div>

  <FilterPopUp v-if="showFilter" @save="closeFilterPopUp" @close="closeFilterPopUp" />

  <OptionsScrollArea ref="optionsRef" @show="onShowItem" />

  <OptionDetails v-if="showDetails" :option="detailOption" @close="closeDetail" />

  <div class="buttons-display">
    <Button label="Continuar amb l'opció seleccionada" variant="primary" @click="onContinue" />
  </div>

</div>

</template>

<script setup>
import { ref } from 'vue'
import InputBox from '../small_components/InputBox.vue'
import Button from '../small_components/Button.vue' 
import FilterPopUp from '../mid_components/FilterPopUp.vue'
import OptionsScrollArea from '../mid_components/OptionsScrollArea.vue'
import OptionDetails from './OptionDetails.vue'

const fcMultipliers = [{ label: 'M', value: 1e6 }, { label: 'G', value: 1e9 }]

const fminRef = ref(null)
const fmaxRef = ref(null)
const showFilter = ref(false)
const optionsRef = ref(null)
const detailOption = ref(null)
const showDetails = ref(false)
const emit = defineEmits(['continue'])

function onContinue() {
  // Prefer the option shown in the detail modal, otherwise use the selected row in the list
  let option = detailOption.value
  try{
    const sel = optionsRef.value?.getSelectedItem?.()
    if (!option && sel) option = sel
  }catch(e){ /* ignore */ }

  if (!option) {
    alert('Cal seleccionar una opció primer: fes clic en una fila o prem "Mostra" per obrir els detalls.')
    return
  }
  emit('continue', option)
}

function onGenerate() {
  // Recuperem els valors dels InputBox
  const fmin = fminRef.value?.getComputedValue?.()
  const fmax = fmaxRef.value?.getComputedValue?.()

  // Validem els valors
  if (fmin == null || fmax == null) {
    alert('Error: Cal introduir valors vàlids per F_min i F_max.')
    return
  }
  if (fmin > fmax) {
    alert('Error: El valor mínim ha de ser <= al valor màxim.')
    return
  }
  if (fmax > 4e9) {
    alert('Error: El valor màxim ha de ser <= a 4 GHz.')
    return
  }
  if (fmin < 0 || fmax < 0) {
    alert('Error: El valor mínim ha de ser no negatiu.')
    return
  }

  // Preparem l'objecte a enviar
  const obj = { f_min: fmin, f_max: fmax }
  // Enviem la petició al backend
  try{
    fetch('http://localhost:5000/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(obj)
    })
    .then(res => res.json())
    .then(data => {
      if (!data.ok) {
        alert('Error: ' + (data.message || 'Generació fallida'))
      } else {
        // refresh options list after successful generation
        try { optionsRef.value?.refresh?.() } catch (e) { console.error('refresh failed', e) }
      }
    })
    .catch(e => {
      console.error(e)
      alert('Error: Generació fallida')
    })
  }catch(e) {
    console.error(e)
    alert('Error: Generació fallida')
  }
  
  
}

function openFilterPopUp() {
  showFilter.value = true
}

function closeFilterPopUp() {
  showFilter.value = false
}

function onShowItem(item) {
  detailOption.value = item
  showDetails.value = true
}

function closeDetail() {
  showDetails.value = false
  detailOption.value = null
}

</script>

<style scoped>

.OptionsGeneration {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 20px;
}

.inputs-display{
  width: 70%;
  padding-inline: 15%;
  padding-block: 20px;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 20px;

}

.buttons-display{
  width: 70%;
  padding-inline: 15%;

  display: flex;
  align-items: center;
  justify-content: center;
  gap: 30px;
}
</style>