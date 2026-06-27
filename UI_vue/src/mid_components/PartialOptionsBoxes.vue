<template>
  <div class="partials-wrapper">
    <div class="zone" v-for="(zone, zi) in zoneBoxesComputed" :key="zi">
      <div class="zone-title" v-if="zone.title">{{ zone.title }}</div>
      <div class="boxes-row">
        <div v-for="(b, bi) in zone.boxes" :key="b._flatIndex" class="box" :class="{selected: selectedIndex === b._flatIndex}" @click="onBoxClick(b._flatIndex)">
          <div class="dot"></div>
          <div class="lines">
            <div class="line">{{ formatFreq(b[0]) }}</div>
            <div class="line">{{ formatFreq(b[1]) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { computed, ref } from 'vue'

  // Props i emits
  const props = defineProps({
    zoneBoxes: { type: Array, default: () => [] },
    partials: { type: Array, default: () => [] },
    modelValue: { type: [Number, null], default: null }
  })
  const emit = defineEmits(['update:modelValue', 'box-click'])

  // Variables
  const selectedIndex = ref(props.modelValue)

  // Funció per gestionar el clic en un rectangle
  function onBoxClick(idx) {
    selectedIndex.value = idx
    emit('update:modelValue', idx)
    emit('box-click', idx)
  }

  // Funció per formatar les freqüències en Hz, kHz o GHz
  function formatFreq(f){
    try{
      const v = Number(f)
      if (isNaN(v)) return String(f)
      if (v >= 1e9) return (v/1e9).toFixed(3) + ' GHz'
      if (v >= 1e6) return (v/1e6).toFixed(0) + ' kHz'
      return v + ' Hz'
    }catch(e){ return String(f) }
  }

  // Funció (computed) per obtenir les zones i els rectangles a partir de les props zoneBoxes o partial options
  const zoneBoxesComputed = computed(() => {
    // Si s'ha passat la prop zoneBoxes, la utilitzem directament
    if (props.zoneBoxes && props.zoneBoxes.length) {
      let flat = 0
      // Mapejar cada zona i cada rectangle, afegint un índex pla per a la selecció 
      return props.zoneBoxes.map((z, zi) => ({
        title: z.title || null,
        boxes: (z.boxes || z).map((b) => {
          const box = Array.isArray(b) ? [b[0], b[1]] : [b.f_start ?? b[0], b.f_end ?? b[1]]
          box._flatIndex = flat++
          return box
        })
      }))
    }

    // Si no s'ha passat la prop zoneBoxes, utilitzem les partial options per generar les zones i els rectangles
    const zones = []
    let flat = 0
    if (props.partials && props.partials.length) {
      // Creem una zona amb títol null i els rectangles corresponents a cada partial option
      zones.push({ title: null, boxes: props.partials.map((p) => {
        const b = [p.f_start ?? p[0], p.f_end ?? p[1]]
        b._flatIndex = flat++
        return b
      })})
    }
    return zones
  })

  
</script>

<style scoped>
  .partials-wrapper{ 
    display:flex;
    flex-direction:column;
    gap:8px;
  }
  .zone-title{ 
    font-weight:600; 
    margin-bottom:6px
  }
  .boxes-row{ 
    display:flex;
    gap:10px;
    flex-wrap:wrap
  }
  .box{ 
    display:flex; 
    align-items:center; 
    gap:8px; 
    padding:8px 10px; 
    border-radius:6px;
    background:#fafafa; 
    border:1px solid #ddd; 
    cursor:pointer 
  }
  .box.selected{ 
    background:#e8f0ff;
    border-color:#4a7fff 
  }
  .dot{ 
    width:10px; 
    height:10px; 
    border-radius:50%; 
    background:#9aa 
  }
  .lines{ 
    display:flex; 
    flex-direction:column 
  }
  .line{ 
    font-size:12px; 
    color:#222 
  }
</style>
