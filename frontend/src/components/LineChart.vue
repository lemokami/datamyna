<template>
  <div class="card flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <h2 class="text-sm font-medium text-ink">Active users</h2>
      <div class="flex items-center gap-1 bg-surface border border-surface-border rounded-lg p-0.5">
        <button
          v-for="m in MODES"
          :key="m"
          class="tab text-xs"
          :class="mode === m ? 'tab-active' : 'tab-inactive'"
          @click="setMode(m)"
        >{{ m }}</button>
      </div>
    </div>

    <div v-if="loading" class="h-56 flex items-center justify-center text-ink-muted text-sm">
      Loading…
    </div>
    <div v-else-if="error" class="h-56 flex items-center justify-center text-red-400 text-sm">
      Failed to load — {{ error }}
    </div>
    <v-chart v-else :option="option" class="h-56" autoresize />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { use }       from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { fetchDau, fetchWau, fetchMau } from '../api'
import type { DateRange } from './TimeRangeSelector.vue'

use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{ range: DateRange }>()

type Mode = 'DAU' | 'WAU' | 'MAU'
const MODES: Mode[] = ['DAU', 'WAU', 'MAU']
const mode    = ref<Mode>('DAU')
const loading = ref(true)
const error   = ref<string | null>(null)
const rows    = ref<{ label: string; value: number }[]>([])

async function load() {
  loading.value = true
  error.value   = null
  try {
    if (mode.value === 'DAU') {
      const data = await fetchDau(props.range.days)
      rows.value = data.map(r => ({ label: r.date, value: r.unique_users }))
    } else if (mode.value === 'WAU') {
      const data = await fetchWau(Math.ceil(props.range.days / 7))
      rows.value = data.map(r => ({ label: r.week, value: r.unique_users }))
    } else {
      const data = await fetchMau(Math.ceil(props.range.days / 30) || 1)
      rows.value = data.map(r => ({ label: r.month, value: r.unique_users }))
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Unknown error'
  } finally {
    loading.value = false
  }
}

function setMode(m: Mode) { mode.value = m; load() }

watch(() => props.range, load)
onMounted(load)

const option = computed(() => ({
  backgroundColor: 'transparent',
  grid:    { left: 48, right: 16, top: 12, bottom: 28 },
  tooltip: { trigger: 'axis', backgroundColor: '#18181f', borderColor: '#26262f', textStyle: { color: '#e2e2f0', fontSize: 12 } },
  xAxis: {
    type: 'category',
    data: rows.value.map(r => r.label),
    axisLine:  { lineStyle: { color: '#26262f' } },
    axisLabel: { color: '#8282a0', fontSize: 11 },
    splitLine: { show: false },
  },
  yAxis: {
    type:      'value',
    axisLabel: { color: '#8282a0', fontSize: 11 },
    splitLine: { lineStyle: { color: '#1e1e2a', type: 'dashed' } },
  },
  series: [{
    type:      'line',
    data:      rows.value.map(r => r.value),
    smooth:    true,
    symbol:    'circle',
    symbolSize: 5,
    lineStyle: { color: '#7c6ef8', width: 2 },
    itemStyle: { color: '#7c6ef8' },
    areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(124,110,248,0.25)' }, { offset: 1, color: 'rgba(124,110,248,0)' }] } },
  }],
}))
</script>
