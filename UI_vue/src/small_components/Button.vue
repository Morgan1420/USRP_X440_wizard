<template>
  <button :class="['btn', variant]" @click="$emit('click')">
    {{ label }}
  </button>
</template>

<script setup>
const props = defineProps({
  label: { type: String, default: '' },
  variant: { type: String, default: 'primary' }
})
</script>

<style scoped>
.btn { 
    padding:12px 18px; 
    border-radius:6px; 
    border:1px solid transparent; 
    cursor:pointer; 
    
    font-size: 1.2rem;
    font-weight:600; 
}

.btn.primary { 
    background:#0078d4; 
    border-color:#0078d4;
    color:#fff; 
}
.btn.secondary { 
    background:#f3f3f3; 
    color:#111; 
    border-color:#ccc; }
.btn.ghost { 
    background:transparent; 
    color:#111; 
    border-color:transparent; 
}
</style>
