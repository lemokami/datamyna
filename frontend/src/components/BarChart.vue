<template>
  <div class="card flex flex-col gap-4">
    <h2 class="text-sm font-medium text-ink">Top pages</h2>

    <div v-if="loading" class="h-56 flex items-center justify-center text-ink-muted text-sm">Loading…</div>
    <div v-else-if="error" class="h-56 flex items-center justify-center text-red-400 text-sm">{{ error }}</div>
    <v-chart v-else :option="option" class="h-56" autoresize />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { use }      from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import VChart from 'vue-echarts'
import { fetchTopPages } from '../api'
import type { DateRange } from './TimeRangeSelector.vue'

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const props   = defineProps<{ range: DateRange }>()
const loading = ref(true)
const error   = ref<string | null>(null)
const pages   = ref<{ path: string; views: number }[]>([])

async function load() {
  loading.value = true
  error.value   = null
  try {
    const data = await fetchTopPages(props.range.days)
    pages.value = data.map(r => ({ path: r.page_path, views: r.view_count })).reverse()
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : 'Unknown error'
  } finally {
    loading.value = false
  }
}

watch(() => props.range, load)
onMounted(load)

const option = computed(() => ({
  backgroundColor: 'transparent',
  grid:    { left: 100, right: 40, top: 8, bottom: 20 },
  tooltip: { trigger: 'axis', backgroundColor: '#18181f', borderColor: '#26262f', textStyle: { color: '#e2e2f0', fontSize: 12 } },
  xAxis: {
    type:      'value',
    axisLabel: { color: '#8282a0', fontSize: 11 },
    splitLine: { lineStyle: { color: '#1e1e2a', type: 'dashed' } },
  },
  yAxis: {
    type:      'category',
    data:      pages.value.map(p => p.path),
    axisLabel: { color: '#8282a0', fontSize: 11, width: 90, overflow: 'truncate' },
    axisLine:  { lineStyle: { color: '#26262f' } },
  },
  series: [{
    type:      'bar',
    data:      pages.value.map(p => p.views),
    barMaxWidth: 16,
    itemStyle: {
      color:        '#2dd4bf',
      borderRadius: [0, 4, 4, 0],
    },
  }],
}))
</script>
