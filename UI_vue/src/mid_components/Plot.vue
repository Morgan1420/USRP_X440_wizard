<template>
  <svg :width="width" :height="height" class="plot-svg" role="img">
    <!-- Eix horitzontal -->
    <line :x1="axisStart" :y1="axisY" :x2="axisEnd" :y2="axisY" stroke="#000" stroke-width="2" />

    <!-- Marques de freqüència (1G, 2G, 3G i 4G) -->
    <g v-for="g in [1,2,3,4]" :key="g">
      <line :x1="mapToAxis(g*1e9)" :y1="axisY - tickHeight" :x2="mapToAxis(g*1e9)" :y2="axisY + tickHeight" stroke="#000" stroke-width="1" />
      <text :x="mapToAxis(g*1e9)" :y="axisY + 20" font-size="12" text-anchor="middle">{{ g }}G</text>
    </g>

    <!-- Desired bandwidth (red band) -->
    <rect
      v-if="option && option.f_start != null && option.f_end != null"
      :x="mapToAxis(option.f_start)"
      :y="axisY - bandHeight"
      :width="Math.max(2, mapToAxis(option.f_end) - mapToAxis(option.f_start))"
      :height="bandHeight"
      fill="rgba(200,40,40,0.25)"
      stroke="rgb(160,30,30)"
    />

    <!-- Blue partial boxes -->
    <g v-for="(pitem, pidx) in drawPartials" :key="pidx">
      <rect v-for="(r, ridx) in pitem.rects" :key="ridx"
        :x="r.x" :y="r.y" :width="r.w" :height="r.h"
        fill="rgba(60,130,220,0.28)" stroke="rgb(20,80,140)" />
    </g>

    <!-- Nyquist zones (gray) if applicable -->
    <g v-if="nyquistRects.length">
      <rect v-for="(nr, i) in nyquistRects" :key="i" :x="nr.x" :y="nr.y" :width="nr.w" :height="nr.h" fill="rgba(120,120,120,0.14)" stroke="rgba(90,90,90,0.35)" />
    </g>

    <!-- Legend -->
    <g :transform="'translate(' + (axisStart + 6) + ',' + 6 + ')'">
      <rect width="12" height="12" fill="rgb(200,40,40)" />
      <text x="20" y="10" font-size="12">red box = desired bandwidth</text>
      <g :transform="'translate(0,20)'">
        <rect width="12" height="12" fill="rgb(60,130,220)" />
        <text x="20" y="10" font-size="12">blue box = channels</text>
      </g>
      <g v-if="showGray" :transform="'translate(0,40)'">
        <rect width="12" height="12" fill="rgb(120,120,120)" />
        <text x="20" y="10" font-size="12">gray = Nyquist zones</text>
      </g>
    </g>

  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  option: { type: Object, default: () => ({}) },
  width: { type: Number, default: 640 },
  height: { type: Number, default: 160 },
  axisMin: { type: Number, default: 0 },
  axisMax: { type: Number, default: 4e9 },
  currentPartial: { type: [String, Number], default: null }
})

const margin = 20
const axisStart = margin
const axisEnd = computed(() => Math.max(margin + 10, props.width - margin))
const axisWidth = computed(() => Math.max(10, axisEnd.value - axisStart))
const axisY = computed(() => props.height - 28)
const tickHeight = 8
const bandHeight = Math.max(36, Math.floor(props.height / 4))

function mapToAxis(f) {
  if (f == null) return axisStart
  const fv = Number(f)
  const denom = props.axisMax - props.axisMin
  const t = denom === 0 ? 0 : (fv - props.axisMin) / denom
  const clamped = Math.max(0, Math.min(1, t))
  return Math.round(axisStart + clamped * axisWidth.value)
}

function partialId(p, idx) {
  return p?.partial_option_id ?? p?.id ?? p?.partial_id ?? idx
}

function numSubChannels(p) {
  if (!p) return 1
  if (Array.isArray(p.channels)) return Math.max(1, p.channels.length)
  for (const k of ['num_channels','num_chans','chans','chans_needed','n_chans']) {
    if (k in p) {
      const v = parseInt(Number(p[k]))
      if (!isNaN(v) && v > 0) return v
    }
  }
  return 1
}

const partials = computed(() => Array.isArray(props.option?.partial_options) ? props.option.partial_options : [])

const drawPartials = computed(() => {
  const res = []
  const target = props.currentPartial == null ? null : String(props.currentPartial)

  for (let idx = 0; idx < partials.value.length; idx++) {
    const p = partials.value[idx]
    // if a specific partial is requested, skip others
    if (target != null && String(partialId(p, idx)) !== target) continue

    const x1 = mapToAxis(p?.f_start)
    const x2 = mapToAxis(p?.f_end)
    if (x2 <= x1) continue
    const num = numSubChannels(p)
    const totalW = x2 - x1
    const pieceW = Math.max(2, Math.floor(totalW / num))
    const rects = []
    for (let s = 0; s < num; s++) {
      const sx1 = x1 + s * pieceW
      const sx2 = (s < num - 1) ? sx1 + pieceW : x2
      rects.push({ x: sx1, y: axisY.value - Math.max(36, Math.floor(props.height / 3)), w: Math.max(2, sx2 - sx1), h: Math.max(36, Math.floor(props.height / 3)) })
    }
    res.push({ idx, rects, partial: p })
    // if target specified, we've added the requested partial; break to avoid adding others
    if (target != null) break
  }
  return res
})

const showGray = computed(() => {
  if (props.currentPartial == null) return false
  for (let idx = 0; idx < partials.value.length; idx++) {
    const p = partials.value[idx]
    if (String(partialId(p, idx)) === String(props.currentPartial) && p?.fcr_ghz != null) return true
  }
  return false
})

const nyquistRects = computed(() => {
  const arr = []
  if (!showGray.value) return arr
  const p = partials.value.find((pp, idx) => String(partialId(pp, idx)) === String(props.currentPartial))
  if (!p || p.fcr_ghz == null) return arr
  const fcr = Number(p.fcr_ghz)
  const freqBoxHz = 0.5 * fcr * 1e9
  const denom = props.axisMax - props.axisMin
  if (denom === 0) return arr
  const pph = axisWidth.value / denom
  const pxBoxW = Math.max(2, Math.floor(freqBoxHz * pph))
  const boxH = Math.max(30, Math.floor(props.height / 10))
  let x = axisStart
  const maxX = axisStart + axisWidth.value
  while (x < maxX) {
    const w = Math.min(pxBoxW, maxX - x)
    arr.push({ x, y: axisY.value - boxH, w, h: boxH })
    x += pxBoxW
  }
  return arr
})
</script>

<style scoped>
.plot-svg { display:block; background: #fff; border: 1px solid #eee; border-radius: 4px; }
.plot-svg text { font-family: Arial, Helvetica, sans-serif; fill: #000; font-size: 12px; }
</style>
