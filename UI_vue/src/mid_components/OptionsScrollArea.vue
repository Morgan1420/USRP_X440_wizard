<template>
  <div class="options-area">
    <div class="header">
      <h3>Options</h3>
      <button class="refresh-btn" @click="refresh">🗘</button>
    </div>

    <div class="list-header">
        <div class="col id-col">ID</div>
        <div class="col range-col">Rang de freqüències</div>
        <div class="col chans-col">Canals</div>
        <div class="col info-col">Més informació</div>
      </div>
    <div class="list" ref="listRef">
      
      <div v-if="loading" class="loading">Loading...</div>
      <div v-else>
        <div v-if="items.length === 0" class="empty">No options available</div>
        <div v-for="(item, i) in items" :key="i" :class="['item', {selected: i === selectedIndex} ]" @click="select(i)">
          <div class="title">{{ item.complete_option_id ?? ('Option ' + i) }}</div>
          <div class="range">{{ formatRange(item.f_start, item.f_end) }}</div>
          <div class="chans">chans: {{ item.chans_needed }}</div>
          <div><button class="show-btn" @click.stop="showDetails(item, i)">Mostra</button></div>
        </div>
      </div>
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
function onStartCapture() { if (selectedIndex.value == null) return; emit('start-capture', items.value[selectedIndex.value]) }

function showDetails(item, i) { selectedIndex.value = i; emit('show', item) }

function getSelectedItem(){
  if (selectedIndex.value == null) return null
  return items.value[selectedIndex.value]
}

// expose refresh for parent
function refresh() { fetchOptions() }

defineExpose({ refresh, getSelectedItem })

// initial fetch
fetchOptions()
</script>

<style scoped>
.options-area { 
  width: 80%; 
  padding:10px;
  max-height: 500px; 

  border:1px solid #ddd;  
  border-radius:6px; 
  background:#fafafa }

.header { 
  margin-bottom:8px;

  display:flex; 
  justify-content:center; 
  align-items:center;
  gap: 12px; 
  
  font-weight:700; 
}

.header h3 { 
  font-size: 1.2em; 
}

.refresh-btn { 
  padding:8px 12px;
  padding-top: 12px;
  font-size: 1.2em;
  background: none;
  border: transparent;
  cursor: pointer
}
.refresh-btn:hover { 
  color: #007BFF;
  font-weight: 700;
  font-size: 1.3em;
}


.list { 
  max-height:415px; 
  overflow:auto 
}

.list-header {
  padding:8px 12px;
  display:flex;
  justify-content:space-between;
  align-items:center;
  border-bottom:1px solid #eee;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
  font-weight:700;
  color:#333;
}
.list-header .col { 
  max-width: 25%;
  min-width: 10%;
  display:flex;
  align-items:center;
  justify-content:center;
}

.item { 
  padding:8px; 
  
  border-bottom:1px solid #eee;
  
  display:flex; 
  justify-content:space-between;  
  
  cursor:pointer 
}
.item:hover { background:#f0f0f0 }
.item.selected { background:#eaf6ff }

.item div { 
  max-width: 25%;
  min-width: 10%;

  display: flex;
  align-items: center;
  justify-content: center;
}


.title { font-weight:600 }

.range { color:#555; font-size:0.9em }

.show-btn { padding:6px 10px }



.loading { padding:16px; color:#666 }

.empty { padding:16px; color:#666 }
</style>
