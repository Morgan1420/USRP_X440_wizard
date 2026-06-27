<template>
  <svg :width="width" :height="height" class="plot-svg" role="img">
    <line :x1="axisStart" :y1="axisY" :x2="axisEnd" :y2="axisY" stroke="#000" stroke-width="2" />

    <g v-for="g in [1,2,3,4]" :key="g">
      <line :x1="mapToAxis(g*1e9)" :y1="axisY - tickHeight" :x2="mapToAxis(g*1e9)" :y2="axisY + tickHeight" stroke="#000" stroke-width="1" />
      <text :x="mapToAxis(g*1e9)" :y="axisY + 20" font-size="12" text-anchor="middle">{{ g }}G</text>
    </g>

    <rect
      v-if="option && option.f_start != null && option.f_end != null"
      :x="mapToAxis(option.f_start)"
      :y="axisY - bandHeight"
      :width="Math.max(2, mapToAxis(option.f_end) - mapToAxis(option.f_start))"
      :height="bandHeight"
      fill="rgba(200,40,40,0.25)"
      stroke="rgb(160,30,30)"
    />


    <g v-for="(pitem, pidx) in drawPartials" :key="pidx">
      <rect v-for="(r, ridx) in pitem.rects" :key="ridx"
        :x="r.x" :y="r.y" :width="r.w" :height="r.h"
        fill="rgba(60,130,220,0.28)" stroke="rgb(20,80,140)" />
    </g>

    <g v-if="nyquistRects.length">
      <rect v-for="(nr, i) in nyquistRects" :key="i" :x="nr.x" :y="nr.y" :width="nr.w" :height="nr.h" fill="rgba(120,120,120,0.14)" stroke="rgba(90,90,90,0.35)" />
    </g>

    <g :transform="'translate(' + (axisStart + 6) + ',' + 6 + ')'">
      <rect width="12" height="12" fill="rgb(200,40,40)" />
      <text x="20" y="10" font-size="12">red box = desired bandwidth</text>
      <g :transform="'translate(0,20)'">
        <rect width="12" height="12" fill="rgb(60,130,220)" />
        <text x="20" y="10" font-size="12">blue box = channels</text>
      </g>
      <g v-if="showNyquist" :transform="'translate(0,40)'">
        <rect width="12" height="12" fill="rgb(120,120,120)" />
        <text x="20" y="10" font-size="12">gray = Nyquist zones</text>
      </g>
    </g>

  </svg>
</template>

<script setup>
  import { computed } from 'vue'

  // Props
  const props = defineProps({
    option: { type: Object, default: () => ({}) },
    width: { type: Number, default: 640 },
    height: { type: Number, default: 160 },
    axisMin: { type: Number, default: 0 },
    axisMax: { type: Number, default: 4e9 },
    currentPartial: { type: [String, Number], default: null }
  })

  // Constants i variables
  const margin = 20
  const axisStart = margin
  const axisEnd = computed(() => Math.max(margin + 10, props.width - margin))
  const axisWidth = computed(() => Math.max(10, axisEnd.value - axisStart))
  const axisY = computed(() => props.height - 28)
  const tickHeight = 8
  const bandHeight = Math.max(36, Math.floor(props.height / 4))

  // Funció per obtenir l'ID d'una partial option
  function partialId(p, idx) {
    return p?.partial_option_id ?? p?.id ?? p?.partial_id ?? idx
  }

  // Funció per mapear una freqüència a la posició de l'eix X
  function mapToAxis(f) {
    if (f == null) return axisStart
    const fv = Number(f)
    // Determinem la posició relativa de la freqüència dins del rang de l'eix
    const denom = props.axisMax - props.axisMin

    // Calculem la posició proporcional dins de l'eix
    const t = denom === 0 ? 0 : (fv - props.axisMin) / denom
    
    // Normalitzem la posició entre 0 i 1
    const clamped = Math.max(0, Math.min(1, t))

    // Retornem la posició final en píxels dins de l'eix
    return Math.round(axisStart + clamped * axisWidth.value)
  }

  // Funció per obtenir el nombre de subcanals d'una partial option
  function numSubChannels(p) {
    if (!p) return 1 
    // 
    if (Array.isArray(p.channels)) return Math.max(1, p.channels.length)
    
    // !! Cal revisar els demés codis, sobretot com faig els JSON pel tema NaN i el "no standard" del nom, de moment això és queda així
    // Com que he anat canviant el nom del numero de canals dels JSONs miro tots els noms possibles ¨:)
    for (const k of ['num_channels','num_chans','chans','chans_needed','n_chans']) {
      if (k in p) {
        const v = parseInt(Number(p[k]))
        if (!isNaN(v) && v > 0) return v // Segurament és un numero però en un moment tb podia ser NaN així que em curo en salut
      }
    }
    return 1
  }

  // Partial options
  const partials = computed(() => Array.isArray(props.option?.partial_options) ? props.option.partial_options : [])

  // Funció per fibuixar les partial options
  const drawPartials = computed(() => {
    const res = []

    // Si només es vol mostrar un partial option (cas dels plots inferiors) es pot indicar des del component pare
    const target = props.currentPartial == null ? null : String(props.currentPartial)

    // Per cada partial_option
    for (let idx = 0; idx < partials.value.length; idx++) {
      // Recuperem la partial option actual
      const p = partials.value[idx]

      // Si volem un partial option concret saltem els demés
      if (target != null && String(partialId(p, idx)) !== target) continue

      // Extraiem les coordenades dins del mapa
      const x1 = mapToAxis(p?.f_start)
      const x2 = mapToAxis(p?.f_end)

      // Extraiem el nombre de subcanals i calculem l'amplada de banda de cada subcanal
      const num = numSubChannels(p)
      const totalW = x2 - x1
      const pieceW = Math.max(2, Math.floor(totalW / num))
      
      // Per cada subcanal, calculem el rectangle corresponent i l'afegim a la llista
      const rects = []
      for (let s = 0; s < num; s++) {
        const sx1 = x1 + s * pieceW
        const sx2 = (s < num - 1) ? sx1 + pieceW : x2
        rects.push({ x: sx1, y: axisY.value - Math.max(36, Math.floor(props.height / 3)), w: Math.max(2, sx2 - sx1), h: Math.max(36, Math.floor(props.height / 3)) })
      }
      res.push({ idx, rects, partial: p })

      // Si volem un partial option concret i ja l'hem trobat, sortim del bucle
      if (target != null) break
    }

    // Retornem la llista de partial options amb els seus rectangles corresponents
    return res
  })

  // Funció per determinar si s'han de mostrar les Zones de Nyquist
  const showNyquist = computed(() => {
    // Si es vol mostrar més d'un partial option, no es mostra el gris 
    if (props.currentPartial == null) return false
    
    // Per cada partial option, si coincideix amb la partial option actual i té fcr_ghz definit, es mostra la ZN
    for (let idx = 0; idx < partials.value.length; idx++) {
      const p = partials.value[idx]
      if (String(partialId(p, idx)) === String(props.currentPartial) && p?.fcr_ghz != null) return true
    }
    return false
  })

  // Funció per calcular els rectangles de les zones de Nyquist
  const nyquistRects = computed(() => {
    const arr = []
    // Si no s'ha de mostrar cap zona de Nyquist, retornem un array buit
    if (!showNyquist.value) return arr

    // Busquem la partial option actual
    const p = partials.value.find((pp, idx) => String(partialId(pp, idx)) === String(props.currentPartial))
    
    // Extraiem la freqüència FCR i la passem a Hz
    const fcr = Number(p.fcr_ghz)
    const freqBoxHz = 0.5 * fcr * 1e9 // L'amplada de Banda de la ZN és la meitat de la FCR

    // Calculem la posició i l'amplada de cada rectangle de la zona de Nyquist
    const denom = props.axisMax - props.axisMin

    // Calculem els píxels per Hz dins de l'eix
    const pph = axisWidth.value / denom

    // Calculem l'amplada en píxels de cada rectangle i l'altura dels rectangles
    const pxBoxW = Math.max(2, Math.floor(freqBoxHz * pph))
    const boxH = Math.max(30, Math.floor(props.height / 10))

    // Iterem des de l'inici de l'eix fins al final, creant rectangles de mida pxBoxW
    let x = axisStart
    const maxX = axisStart + axisWidth.value
    while (x < maxX) {
      const w = Math.min(pxBoxW, maxX - x)
      arr.push({ x, y: axisY.value - boxH, w, h: boxH })
      x += pxBoxW
    }

    // Retornem l'array de rectangles de les zones de Nyquist
    return arr
  })
  
</script>

<style scoped>
.plot-svg { display:block; background: #fff; border: 1px solid #eee; border-radius: 4px; }
.plot-svg text { font-family: Arial, Helvetica, sans-serif; fill: #000; font-size: 12px; }
</style>
