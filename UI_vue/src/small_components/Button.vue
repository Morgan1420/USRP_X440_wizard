<template>
  <button :class="['btn', variant]" @click="handleClick">
    {{ label }}
  </button>
</template>

<script setup>

  // Props i emits
  const props = defineProps({
    label: { type: String, default: '' },
    variant: { type: String, default: 'primary' }
  })
  const emit = defineEmits(['click'])

  // Funció de "Handle"
  function handleClick(e) {
    console.log('Button clicked:', props.label)
    emit('click', e)
  }
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
  .btn:hover { 
    transform: scale(1.05);
    transition: transform 0.1s ease-in-out;
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
