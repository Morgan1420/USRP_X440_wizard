<template>
  <div class="options-area">
    <div class="header">Options</div>
    <div class="list" ref="listRef">
      <div v-if="loading" class="loading">Loading...</div>
      <div v-else>
        <div v-if="items.length === 0" class="empty">No options available</div>
        <div v-for="(item, i) in items" :key="i" :class="['item', {selected: i === selectedIndex}]" @click="select(i)">
          <div class="left">
            <div class="title">{{ item.complete_option_id ?? ('Option ' + i) }}</div>
            <div class="range">{{ formatRange(item.f_start, item.f_end) }}</div>
          </div>
          <div class="right">
            <div class="chans">chans: {{ item.chans_needed }}</div>
            <button class="show-btn" @click.stop="onShow(item)">Mostra</button>
          </div>
        </div>
      </div>
    </div>

    <div class="footer">
      <button class="start-btn" :disabled="selectedIndex === null" @click="onStartCapture">Start capture</button>
      <button class="refresh-btn" @click="refresh">Refresh</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['show','start-capture'])
const listRef = ref(null)
const items = ref([])
const loading = ref(false)
const selectedIndex = ref(null)

function formatRange(a,b) {
  if (a == null || b == null) return ''
  try { return Math.round(a) + ' - ' + Math.round(b) + ' Hz' } catch(e) { return '' }
}

async function fetchOptions() {
  loading.value = true
  try {
    const res = await fetch('http://localhost:5000/api/options')
    if (!res.ok) throw new Error('Failed fetching')
    const data = await res.json()
    items.value = Array.isArray(data) ? data : (data.items || [])
    if (items.value.length === 0) selectedIndex.value = null
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function select(i) { selectedIndex.value = i }
function onShow(item) { emit('show', item) }
function onStartCapture() { if (selectedIndex.value == null) return; emit('start-capture', items.value[selectedIndex.value]) }

// expose refresh for parent
function refresh() { fetchOptions() }

defineExpose({ refresh })

// initial fetch
fetchOptions()
</script>

<style scoped>
.options-area { width: 80%; max-height: 420px; border:1px solid #ddd; padding:10px; border-radius:6px; background:#fafafa }
.header { font-weight:700; margin-bottom:8px }
.list { max-height:340px; overflow:auto }
.item { display:flex; justify-content:space-between; padding:8px; border-bottom:1px solid #eee; cursor:pointer }
.item.selected { background:#eaf6ff }
.left .title { font-weight:600 }
.left .range { color:#555; font-size:0.9em }
.right { display:flex; align-items:center; gap:8px }
.show-btn { padding:6px 10px }
.footer { display:flex; gap:8px; margin-top:8px; justify-content:flex-end }
.start-btn { background:#0078d4; color:#fff; padding:8px 12px; border-radius:6px; border:0 }
.refresh-btn { padding:8px 12px }
.loading { padding:16px; color:#666 }
.empty { padding:16px; color:#666 }
</style>
