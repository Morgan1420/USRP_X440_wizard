<template>
  <div class="selectbox" ref="wrapperRef">
    <label class="label">{{ label }}</label>
    
    <div class="control" @click.stop="toggle">
      <div class="selected">{{ selectedLabel }}</div>
      <div class="arrow" :class="{open: expanded}">▾</div>
    </div>

    <div v-if="expanded" class="dropdown" ref="dropdownRef" :class="{up: expandUp}" :style="{left: getLengthLabelPx() + 'px', width: getWidthControlPx() + 'px'}">
      <div v-for="(opt, i) in options" :key="i" class="option" @click.stop="selectOption(i)">
        {{ opt }}
      </div>
    </div>
    
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  options: { type: Array, default: () => [] },
  defaultIndex: { type: Number, default: 0 },
  labelGap: { type: Number, default: 100 }
})
const emit = defineEmits(['change'])

const wrapperRef = ref(null)
const dropdownRef = ref(null)
const expanded = ref(false)
const expandUp = ref(false)
const selected = ref(props.options.length ? Math.max(0, Math.min(props.defaultIndex, props.options.length - 1)) : null)

const selectedLabel = computed(() => selected.value != null ? props.options[selected.value] : '')

function toggle() {
  if (expanded.value) {
    expanded.value = false
    return
  }
  expanded.value = true
  nextTick(() => {
    if (!wrapperRef.value || !dropdownRef.value) return
    const wrapperRect = wrapperRef.value.getBoundingClientRect()
    const dropdownHeight = dropdownRef.value.getBoundingClientRect().height
    expandUp.value = (wrapperRect.bottom + dropdownHeight) > window.innerHeight
  })
}

function selectOption(i) {
  selected.value = i
  emit('change', props.options[i])
  expanded.value = false
}

function handleDocumentClick(e) {
  if (!wrapperRef.value) return
  if (!wrapperRef.value.contains(e.target)) {
    expanded.value = false
  }
}

function getLengthLabelPx() {
  if (!wrapperRef.value) return 0
  const labelEl = wrapperRef.value.querySelector('.label')
  return labelEl ? labelEl.getBoundingClientRect().width + 16 : 0 
}

function getWidthControlPx() {
  if (!wrapperRef.value) return 0
  const controlEl = wrapperRef.value.querySelector('.control')
  return controlEl ? controlEl.getBoundingClientRect().width : 0 
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})

function getValue() { return selected.value != null ? props.options[selected.value] : null }

defineExpose({ getValue, setSelected: (i) => { selected.value = i } })
</script>

<style scoped>
.selectbox { display:flex; align-items: center; position:relative; font-family: Arial, Helvetica, sans-serif; font-size: 1.5rem; }
.label { 
  margin-right: 16px; 
  color: #111; 
}
.control {
  display:flex;
  align-items:center;
  border: 2px solid #bbb;
  padding: 6px 8px;
  background: #fff;
  cursor: pointer;
  border-radius: 4px;
}
.selected { 
  min-width: 160px;
  font-size: 1.2rem;
}
.arrow { 
  margin-left: 8px;
}

.dropdown {
  position: absolute;
  top: 100%;
  z-index: 20;
  background: #fff;
  border: 1px solid #ccc;
  width: 220px;
  border-radius: 4px;
  margin-top: 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.dropdown.up { 
  bottom: 100%; 
  top: auto;
  margin-top: 0; 
  margin-bottom: 6px; 
}
.option { 
  padding: 8px 10px; 
  border-bottom: 1px solid #eee; 
  cursor: pointer; 
  font-size: 1.2rem;
}
.option:last-child { 
  border-bottom: none
}
.option:hover {
  background: #f5f5f5
}
</style>
