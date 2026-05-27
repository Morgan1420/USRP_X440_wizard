<template>
  <div class="ports-row">
    <div v-for="(label, i) in labelsComputed" :key="i" class="port" :class="{selected: selected[i]}" @click="toggle(i)">
      <div class="dot" :aria-pressed="selected[i] ? 'true' : 'false'"></div>
      <div class="label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  numPorts: { type: Number, default: 8 },
  labels: { type: Array, default: () => [] },
  modelValue: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:modelValue', 'toggle'])

const selected = ref([])

function ensureLength() {
  const n = props.numPorts || 0
  const base = Array.from({ length: n }, (_, i) => !!(props.modelValue && props.modelValue[i]))
  if (selected.value.length !== n) selected.value = base
}

ensureLength()

watch(() => props.numPorts, ensureLength)
watch(() => props.modelValue, (v) => {
  ensureLength()
  for (let i = 0; i < Math.min(selected.value.length, (v || []).length); i++) selected.value[i] = !!v[i]
})

const labelsComputed = computed(() => {
  if (props.labels && props.labels.length >= props.numPorts) return props.labels.slice(0, props.numPorts)
  const out = []
  for (let i = 0; i < props.numPorts; i++) out.push('P' + (i + 1))
  return out
})

function toggle(i) {
  selected.value[i] = !selected.value[i]
  emit('update:modelValue', selected.value.slice())
  emit('toggle', i, selected.value[i])
}
</script>

<style scoped>
.ports-row{
  display:flex;
  gap:12px;
  align-items:center;
  flex-wrap:wrap;
}
.port{
  display:flex;
  flex-direction:column;
  align-items:center;
  cursor:pointer;
  user-select:none;
}
.dot{
  width:18px;
  height:18px;
  border-radius:50%;
  background:#e0e0e0;
  border:2px solid #bbb;
}
.port.selected .dot{
  background:#2b80ff;
  border-color:#164fdd;
}
.label{
  font-size:12px;
  margin-top:6px;
  color:#222;
}
</style>
