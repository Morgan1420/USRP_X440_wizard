<template>
  <div class="app">
    <h2>USRP X440 - wizard</h2>
    
    <OptionsGeneration v-if="!showHardware" @continue="openHardware" />

    <HardwareConnections v-if="showHardware" :option="hardwareOption" @close="showHardware = false" />

</div>
    
</template>

<script setup>
  import { ref } from 'vue'

  // Importar components
  import InputBox from './small_components/InputBox.vue'
  import Button from './small_components/Button.vue'
  import FilterPopUp from './mid_components/FilterPopUp.vue'
  import OptionsScrollArea from './mid_components/OptionsScrollArea.vue'
  import OptionsGeneration from './big_components/OptionsGeneration.vue'
  import HardwareConnections from './big_components/HardwareConnections.vue'

  // Definir les variables i lògica del canvi de component
  const showHardware = ref(false)
  const hardwareOption = ref(null)
  function openHardware(option) {
    hardwareOption.value = option || null
    showHardware.value = true
  }

</script>

<style scoped>

  .app { font-family: Arial, Helvetica, sans-serif; }
  .top-row { display:flex; align-items:center; gap:12px; }
  .buttons { display:flex; gap:8px; align-items:center; margin-left:8px; }

  h2 {
    top: 0;
    margin: 0;
    margin-left: -12px;
    margin-top: -12px;
    padding: 32px;
    width: 100%;
    text-align: center;
    font-size: 35px;
    color: #3c3c3c;
    background: #c7defb;
  }
</style>
