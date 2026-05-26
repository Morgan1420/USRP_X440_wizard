<template>
  <div class="overlay" role="dialog" aria-modal="true">
    <div class="panel">
      <div class="panel-header">
        <p class="empty"></p>
        <h3>Option {{ option?.complete_option_id ?? '' }}</h3>
        <button class="close-btn" @click="$emit('close')">Tornar</button>
      </div>

      <div class="meta">
        <div><strong>chans_needed:</strong> {{ option?.chans_needed ?? '' }}</div>
        <div><strong>f_start:</strong> {{ option?.f_start ?? '' }}</div>
        <div><strong>f_end:</strong> {{ option?.f_end ?? '' }}</div>
        <div><strong>is_complete:</strong> {{ option?.is_complete ?? '' }}</div>
      </div>

      <Plot class="plot" :option="option" :width="plotWidth" :height="220" />

      <div class="partials" v-if="option?.partial_options && option.partial_options.length">
        <div v-for="(p, idx) in option.partial_options" :key="idx" class="partial">
          <h4>Partial option {{ idx }}:</h4>
          <div class="partial-meta-1">
            <div><strong>MCR <i>(Master Clock Rate)</i>: </strong>{{ p?.mcr_mhz ?? '' }} MHz</div>
            <div><strong>Fs <i>(Converter Sample Rate)</i>: </strong>{{ p?.fcr_ghz ?? '' }} GHz</div>
            <div><strong>Canals necessaris:</strong> {{ p?.chans_needed ?? '' }}</div>
          </div>
          <div class="partial-meta-2">
            <div><strong>Freqüència Inicial</strong> {{ p?.f_start ?? '' }}</div>
            <div><strong>Freqüència Final</strong> {{ p?.f_end ?? '' }}</div>
            <div><strong>Zona de Nyquist:</strong> {{ p?.nyquist_zone ?? '' }}</div>
          </div>
          <Plot class="plot-partial" :option="option" :currentPartial="getPartialId(p, idx)" :width="plotWidth" :height="140" />
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import Plot from '../mid_components/Plot.vue'

const props = defineProps({ option: { type: Object, default: () => ({}) } })
const emit = defineEmits(['close'])

function getPartialId(p, idx) {
  return p?.partial_option_id ?? p?.id ?? p?.partial_id ?? idx
}

function formatValue(v) {
  if (v == null) return ''
  if (Array.isArray(v)) return `<${v.length}>`
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

const plotWidth = computed(() => Math.min(900, Math.max(300, (window?.innerWidth || 900) - 160)))
</script>

<style scoped>
.overlay { 
    position: fixed; 
    inset: 0; 
    display:flex; 
    align-items:center; 
    justify-content:center; 
    background: rgba(0,0,0,0.45); 
    z-index: 60; 
}
.panel { 
    width: 90%; 
    max-width: 1000px; 
    max-height: 90vh; 
    padding:16px;

    overflow:auto; 
    background:#fff; 
    border-radius:8px; 
     
    box-shadow: 0 8px 30px rgba(0,0,0,0.2); 
}

.panel-header { 
    padding-left:5%;
    padding-right:2%;
    padding-top:12px;
    margin-bottom:30px;
    display:flex; 
    justify-content:space-between; 
    align-items:center; 
    gap:12px; 
}
.panel-header h3 { 
    margin:0; 
    font-size:1.5rem; 
}

.close-btn { 
    padding:8px 12px;
    background:#d54545; 
    color:#fff;
    border-radius:6px; 
    border:none;
    cursor:pointer 
}

.meta { 
    width:80%; 
    padding-inline: 10%;
    margin-top:12px; 

    display:flex; 
    justify-content:space-between;
    gap:18px;
    flex-wrap:wrap
}

.plot { 
  width:90%;
  margin-inline:5%; 
  
  margin-top:18px;
  border:1px solid #eee; 
  border-radius:6px;
  background:#fafafa
}
.plot-partial { 
  width:100%;
  margin-top:12px;
  border:1px solid #eee; 
  border-radius:6px;
  background:#fafafa
}


.partial { 
  width:90%;
  margin-inline:5%;
  margin-top:18px;
  padding-top:12px;
  border-top:1px solid #eee 
}
.partial-meta-1, .partial-meta-2 { 
    display:flex; 
    justify-content:space-between;
    gap:18px; 
    flex-wrap:wrap;
    margin-bottom:12px;
}
.partial-meta-1 div, .partial-meta-2 div { 
  max-width:35%;
  text-align: center;
}
.meta-line { margin:6px 0 }
</style>
