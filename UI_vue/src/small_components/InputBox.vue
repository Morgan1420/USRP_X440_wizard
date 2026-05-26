<template>
  <div class="inputbox">
    <label class="label">{{ label }}</label>
    
    <input class="text-input" :value="text" @input="onInput" @keydown.enter="onEnter" :placeholder="placeholder"/>

    <div class="multipliers" v-if="normalizedMultipliers.length">
      <button
        v-for="(m, i) in normalizedMultipliers" :key="i" :class="['mult-btn', { selected: i === selectedMultiplier }]" 
          @click="selectMultiplier(i)"
      >
        {{ m.label }}
      </button>
      
      <div class="unit" v-if="unit">{{ unit }}</div>
    </div>
    
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  multipliers: { type: Array, default: () => [] },
  unit: { type: String, default: '' },
  defaultMultiplierIndex: { type: Number, default: 0 },
  labelGap: { type: Number, default: 100 }
})
const emit = defineEmits(['update:text', 'change'])

const text = ref(props.placeholder || '')
const active = ref(false)

const normalizedMultipliers = computed(() => {
  return props.multipliers.map(m => {
    if (Array.isArray(m) && m.length >= 2) return { label: String(m[0]), value: Number(m[1]) }
    if (m && typeof m === 'object') return { label: String(m.label ?? ''), value: Number(m.value ?? 1) }
    return { label: String(m), value: 1 }
  })
})

const selectedMultiplier = ref(
  normalizedMultipliers.value.length ? Math.max(0, Math.min(props.defaultMultiplierIndex, normalizedMultipliers.value.length - 1)) : null
)

watch(() => props.multipliers, () => {
  selectedMultiplier.value = normalizedMultipliers.value.length ? Math.max(0, Math.min(props.defaultMultiplierIndex, normalizedMultipliers.value.length - 1)) : null
})

function selectMultiplier(i) {
  selectedMultiplier.value = i
  emit('change', getComputedValue())
}

function onInput(e) {
  text.value = e.target.value
  emit('update:text', text.value)
  emit('change', getComputedValue())
}

function onEnter() {
  active.value = false
}

function getMultiplierValue() {
  return normalizedMultipliers.value.length && selectedMultiplier.value != null ? normalizedMultipliers.value[selectedMultiplier.value].value : 1.0
}

function getMultiplierLabel() {
  return normalizedMultipliers.value.length && selectedMultiplier.value != null ? normalizedMultipliers.value[selectedMultiplier.value].label : ''
}

function getComputedValue() {
  const n = parseFloat(text.value)
  if (Number.isNaN(n)) return null
  return n * getMultiplierValue()
}

defineExpose({
  getComputedValue,
  getMultiplierValue,
  getMultiplierLabel,
  getText: () => text.value,
  setText: (v) => {
    text.value = v
    emit('update:text', text.value)
    emit('change', getComputedValue())
  }
})

</script>

<style scoped>
.inputbox { 
  display: flex;
  align-items: center;
  font-family: Arial, Helvetica, sans-serif; 
  font-size: 1.5rem;
}

.label { 
  margin-right: 16px;
  color: #111;
}

.text-input { 
  min-width: 160px;
  padding: 6px 8px; 
  border: 2px solid #bbb; 
  border-radius: 4px; 
  font-size: 1.2rem;
}

.multipliers { 
  display: flex; 
  margin-left: 8px; 
}
.mult-btn { 
  margin-right: 6px;
  padding: 6px 10px;

  background: #fff; 
  border: 2px solid #aaa;  
  border-radius: 4px; 
  
  cursor: pointer;
  
  font-size: 1.2rem;
}
.mult-btn.selected { 
  background: #e6e6e6;
}
.unit { 
  margin-left: 8px;
  align-content: center;
}
</style>
