<template>
  <div class="sample-rate-options">
    <h4>Sample Rate</h4>
    <div class="options-grid">
      <div class="option-row">
        <div class="select-box" :class="{selected: selected === 'auto'}" @click="selectOption('auto')"></div>
        <div class="option-value">Automàtic</div>
      </div>

      <div class="option-row" v-if="showManual">
        <div class="select-box" :class="{selected: selected === 'manual'}" @click="selectOption('manual')"></div>
        <div class="option-value">Manual</div>
        <div class="option-input"> <input v-if="selected === 'manual'" v-model="manualValue" class="manual-input" placeholder="e.g. 1e6" /> </div>
      </div>

      <div class="option-row-text" v-else>
        <div class="option-text">Per a opcions amb un canal o més de >200MHz d'amplada de banda </div>
        <div class="option-text">no es pot editar la freqüència de mostreig (Fs) de forma manual.</div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({ option: { type: Object, default: null } })
const emit = defineEmits(['update:sampleRate'])

const selected = ref('auto')
const manualValue = ref('')

// derive partials from option similarly to PortsConnections
const partials = computed(() => {
  if (!props.option) return []
  return props.option.partial_options || props.option.partials || []
})

function computeChannelBWsFromPartials(parts){
  const bws = []
  for (let pi = 0; pi < parts.length; pi++){
    const p = parts[pi]
    const fs = Number(p?.f_start ?? p?.[0] ?? 0)
    const fe = Number(p?.f_end ?? p?.[1] ?? 0)
    const num = Math.max(1, Number(p?.chans_needed ?? p?.chansNeeded ?? p?.chans ?? 1))
    const total = Math.max(0, fe - fs)
    const piece = num > 0 ? total / num : total
    for (let i = 0; i < num; i++){
      const s = fs + i * piece
      const e = (i < num - 1) ? s + piece : fe
      const bw = Math.abs(e - s)
      bws.push(bw)
    }
  }
  return bws
}

const channelBws = computed(() => computeChannelBWsFromPartials(partials.value))

// show manual field only when all channels bw < 200 MHz, or if there are no channels
const showManual = computed(() => {
  if (!channelBws.value || channelBws.value.length === 0) return true
  return channelBws.value.every(bw => bw < 200e6)
})

// enforce single selection; if manual becomes unavailable, switch to auto
watch(showManual, (v) => { if (!v && selected.value === 'manual') selected.value = 'auto' })

function selectOption(opt){
  if (opt === 'manual' && !showManual.value) return
  selected.value = opt
  emit('update:sampleRate', { mode: selected.value, manualValue: manualValue.value })
}

watch([selected, manualValue], () => {
  emit('update:sampleRate', { mode: selected.value, manualValue: manualValue.value })
})
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