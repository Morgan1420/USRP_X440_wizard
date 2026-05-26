<template>  
  <div class="inputs-display">
    <InputBox ref="fminRef" label="F_min:" placeholder="1" :multipliers="fcMultipliers" unit="Hz" :default-multiplier-index="0" />
    <InputBox ref="fmaxRef" label="F_max:" placeholder="2" :multipliers="fcMultipliers" unit="Hz" :default-multiplier-index="0" />
  </div>

  <div class="buttons-display">
    <Button label="Generar Opcions" variant="primary" @click="onGenerate" />
    <Button label="Filters" variant="secondary" @click="openFilter" />
  </div>

  <FilterPopUp v-if="showFilter" @save="onFilterSave" @close="showFilter = false" />

</template>

<script setup>
import { ref } from 'vue'
import InputBox from '../small_components/InputBox.vue'
import Button from '../small_components/Button.vue' 
import FilterPopUp from '../mid_components/FilterPopUp.vue'
import OptionsScrollArea from '../small_components/OptionsScrollArea.vue'

const fcMultipliers = [{ label: 'M', value: 1e6 }, { label: 'G', value: 1e9 }]

const fminRef = ref(null)
const fmaxRef = ref(null)
const showFilter = ref(false)

function onGenerate() {
  const fmin = fminRef.value?.getComputedValue?.()
  const fmax = fmaxRef.value?.getComputedValue?.()
  const time = 1
  if (fmin == null || fmax == null) {
    alert('Error: Please enter valid numeric values.')
    return
  }
}

function openFilter() {
  showFilter.value = true
}

function onFilterSave(obj) {
  showFilter.value = false
}
</script>

<style scoped>
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