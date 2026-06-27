<template>
  <div class="sample-rate-options">
    <h4>Sample Rate</h4>
    <div class="options-grid">
      <div class="option-row">
        <div class="select-box" :class="{selected: selected === 'auto'}" @click="selectOption('auto')"></div>
        <div class="option-value">Automatic</div>
      </div>

      <div class="option-row" v-if="showManual">
        <div class="select-box" :class="{selected: selected === 'manual'}" @click="selectOption('manual')"></div>
        <div class="option-value">Manual</div>
        <div class="option-input"> <input v-if="selected === 'manual'" v-model="manualValue" class="manual-input" placeholder="e.g. 1e6" /> </div>
      </div>

      <div class="option-row-text" v-else>
        <div class="option-text">For options with one channel or more than 200MHz of bandwidth</div>
        <div class="option-text">the sample rate (Fs) cannot be edited manually.</div>
      </div>

      <div class="option-row">
        <div class="option-text" style="color: black;">Capture Time (s):</div>
        <div class="option-value"><input v-model="captureTime" type="number" min="0" class="manual-input" placeholder="e.g. 10" /></div>
      </div>

    </div>
  </div>
</template>

<script setup>

  import { ref, computed, watch } from 'vue'

  // Props i emits
  const props = defineProps({ option: { type: Object, default: null } })
  const emit = defineEmits(['update:sampleRate'])

  // Variables
  const selected = ref('auto')
  const manualValue = ref('')
  const captureTime = ref('')

  // Funció (computed) per obtenir la llista d'opcions parcials (partials) a partir de l'objecte option
  const partials = computed(() => {
    if (!props.option) return []
    return props.option.partial_options || props.option.partials || []
  })

  // Funció per calcular les amplades de banda de cada partial option
  function computeChannelBWsFromPartials(parts){
    const bws = []

    // Per cada partial option
    for (let pi = 0; pi < parts.length; pi++){
      // Recuperem l'opció parcial
      const p = parts[pi] 

      // Extraiem: freq. inicial, freq. final, nombre de canals i amplada de banda per canal
      const fs = Number(p?.f_start ?? p?.[0] ?? 0)
      const fe = Number(p?.f_end ?? p?.[1] ?? 0)
      const num = Math.max(1, Number(p?.chans_needed ?? p?.chansNeeded ?? p?.chans ?? 1))
      const total = Math.max(0, fe - fs)
      const piece = num > 0 ? total / num : total

      // Per cada canal, calculem la seva amplada de banda i l'afegim a la llista
      for (let i = 0; i < num; i++){
        const s = fs + i * piece
        const e = (i < num - 1) ? s + piece : fe
        const bw = Math.abs(e - s)
        bws.push(bw)
      }
    }
    return bws
  }
  // Extraiem les amplades de banda dels canals a partir de la funció anterior
  const channelBws = computed(() => computeChannelBWsFromPartials(partials.value))

  // Indiquem que es pot seleccionar l'opció manual per si totes les amplades de banda dels canals són menors a 200MHz (requisit de la USRP)
  const showManual = computed(() => {
    if (!channelBws.value || channelBws.value.length === 0) return true
    return channelBws.value.every(bw => bw < 200e6)
  })

  // Si l'opció manual no es mostra i estava seleccionada, canviem a automàtic
  watch(showManual, (v) => { if (!v && selected.value === 'manual') selected.value = 'auto' })

  // Funció per seleccionar una opció (auto/manual) i emetre l'event corresponent
  function selectOption(opt){
    if (opt === 'manual' && !showManual.value) return
    selected.value = opt
    emit('update:sampleRate', { mode: selected.value, manualValue: manualValue.value })
  }

  // Watcher per emetre l'event quan canvia qualsevol de les variables (selected, manualValue, captureTime)
  watch([selected, manualValue, captureTime], () => {
    emit('update:sampleRate', { mode: selected.value, manualValue: manualValue.value, captureTime: captureTime.value })
  })

  // Funció per obtenir la configuració actual (mode, valor manual i temps de captura)
  function getConfig(){
    return { mode: selected.value, manualValue: manualValue.value, captureTime: captureTime.value }
  }
  // Exposem getConfig als components pares
  defineExpose({ getConfig })
</script>


<style scoped>
.sample-rate-options{ 
  height: 100%;

  background:#f9f9f9;
  border:5px solid #ddd;
  border-radius:10px;
  
  display: flex;
  flex-direction: column;
  justify-content: top;
  gap: 20px;
}

h4 {
  width: 100%;
  padding:10px;
  margin:0;
  font-size:1.7rem;
  text-align: center;
}

.options-grid{ 
  display:flex;
  flex-direction:column;
  gap:20px;
}

.option-row{ 
  display:flex; 
  align-items:center;
  gap:12px;
}
.option-row-text{
  display:flex; 
  flex-direction: column;
  align-items:start;
}
.select-box{ width:20px; height:20px; border:2px solid #999; border-radius:4px; cursor:pointer }
.select-box.selected{ background:#2b80ff; border-color:#2b80ff }
.option-value{ font-weight:600 }
input{  
  width:100%; 
  padding:6px;
  margin-left: 5%;
  border:1px solid #ccc; 
  border-radius:4px;
}
.option-text{ color:#b00; font-size:1rem }
</style>