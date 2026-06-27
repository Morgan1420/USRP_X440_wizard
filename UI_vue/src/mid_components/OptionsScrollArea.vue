<template>
  <div class="options-area">
    <div class="header">
      <h3>Options</h3>
      <button class="refresh-btn" @click="refresh">🗘</button>
    </div>

    <div class="list-header">
      <div class="col id-col">ID</div>
      <div class="col num-po-col"># Partial Options</div>
      <div class="col num-po-col"># Chans</div>
      <div class="col partial-options-col">
        <div class="po-col-title">Partial Option 1</div>
        <div class="subcols">
          <div>MCR</div>
          <div>FCR</div>
          <div>Channels</div>
        </div>
      </div>
      <div class="col partial-options-col">
        <div class="po-col-title">Partial Option 2</div>
        <div class="subcols">
          <div>MCR</div>
          <div>FCR</div>
          <div>Channels</div>
        </div>
      </div>
      <div class="col info-col">More Info</div>
    </div>

    <div class="list" ref="listRef">
      
      <div v-if="loading" class="loading">Loading...</div>
      <div v-else>
        <div v-if="items.length === 0" class="empty">No options available</div>
        <div v-for="(item, i) in items" :key="i" :class="['item', {selected: i === selectedIndex} ]" @click="select(i)">
          <div class="item-title">{{ item.complete_option_id }}</div>
          <div class="col item-num-po-col">{{countPartialOptions(item)}}</div>
          <div class="col item-num-po-col">{{item.chans_needed}}</div>
          <div class="col partial-options-col">
            <div class="subcols">
              <div>{{ getMCR(item, 0) }}</div>
              <div>{{ getFCR(item, 0) }}</div>
              <div>{{ getChans(item, 0) }}</div>
            </div>
          </div>
          <div class="col partial-options-col">
            <div class="subcols">
              <div>{{ getMCR(item, 1) }}</div>
              <div>{{ getFCR(item, 1) }}</div>
              <div>{{ getChans(item, 1) }}</div>
            </div>
          </div>
          <div class="col info-col"><button class="show-btn" @click.stop="showDetails(item, i)">Show</button></div>
        </div>
      </div>
    </div>

    
      
    
  </div>
</template>

<script setup>
  import { ref } from 'vue'

  // Variables i tal
  const emit = defineEmits(['show','start-capture'])
  const listRef = ref(null)
  const items = ref([])
  const loading = ref(false)
  const selectedIndex = ref(null)

  // Funció per seleccionar una fila
  function select(i) { selectedIndex.value = i }

  // Funció pel botó "mostra"
  function showDetails(item, i) { 
    selectedIndex.value = i; 
    emit('show', item) 
  }

  // Funció per calcular les opcions parcials dins d'una opció
  function countPartialOptions(option) {
    return option.partial_options.length
  }
  // Funcions getter
  function getMCR(option, poIndex) {
    if (option.partial_options[poIndex]?.mcr_mhz == null) 
      return null
    return option.partial_options[poIndex].mcr_mhz + ' MHz'
  }
  function getFCR(option, poIndex) {
    if (option.partial_options[poIndex]?.fcr_ghz == null) 
      return null
    return option.partial_options[poIndex].fcr_ghz + ' GHz'
  }
  function getChans(option, poIndex) {
    if (option.partial_options[poIndex]?.chans_needed == null) 
      return null
    return option.partial_options[poIndex].chans_needed
  }
  function getSelectedItem(){
    if (selectedIndex.value == null) return null
    return items.value[selectedIndex.value]
  }

  // Funció per obtenir les opcions des del backend
  async function fetchOptions() {
    loading.value = true
    // Fem un try/catch per si hi ha algun error en la crida al backend
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

  
  // Funció per refrescar les opcions, l'exposem als components pares
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
  max-height:360px; 
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
.id-col { width: 10% }
.num-po-col { width: 10% }
.partial-options-col { 
  width: 25%;
  display:flex;
  flex-direction: column;
  gap:4px;
}
.partial-options-col .subcols {
  width: 100%;
  display:flex;
  flex-direction: row;
  align-items:center;
  justify-content: space-around;
  gap:4px;
}
.partial-options-col .subcols div {
  width: 30%;
  display:flex;
  align-items:center;
  justify-content:center;
}
.partial-options-col .po-col-title {
  width: 100%;
  padding-bottom: 5px;
  display:flex;
  align-items:center;
  justify-content:center;
}
.info-col { width: 10%; display:flex; align-items:center; justify-content:center }

.item { 
  padding:8px; 
  
  border-bottom:1px solid #eee;
  
  display:flex; 
  justify-content:space-between;  
  
  cursor:pointer 
}
.item:hover { background:#f0f0f0 }
.item.selected { background:#eaf6ff }

.item .item-title {
  width: 10%;
  font-weight: 600;
  display:flex;
  align-items:center;
  justify-content:center;
}
.item .item-num-po-col {
  width: 10%;
  display:flex;
  align-items:center;
  justify-content:center;

}



.title { font-weight:600 }

.range { color:#555; font-size:0.9em }

.show-btn { width: 100%; padding:6px 10px }



.loading { padding:16px; color:#666 }

.empty { padding:16px; color:#666 }
</style>
