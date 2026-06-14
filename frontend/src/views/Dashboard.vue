<template>
  <div class="min-h-screen bg-surface px-4 py-6 md:px-8 md:py-8 space-y-6">

    <!-- Topbar -->
    <header class="flex flex-col sm:flex-row sm:items-center gap-4">
      <div class="flex items-center gap-3">
        <div class="w-7 h-7 rounded-lg bg-brand flex items-center justify-center">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2 10 L5 6 L8 8 L12 3" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <span class="text-base font-medium tracking-tight">DataMyna</span>
      </div>
      <div class="sm:ml-auto">
        <TimeRangeSelector @change="onRangeChange" />
      </div>
    </header>

    <!-- KPI cards -->
    <StatsBar />

    <!-- Charts row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <LineChart :range="range" />
      <BarChart  :range="range" />
    </div>

    <!-- User journeys -->
    <UserJourney :range="range" />

  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import TimeRangeSelector from '../components/TimeRangeSelector.vue'
import StatsBar          from '../components/StatsBar.vue'
import LineChart         from '../components/LineChart.vue'
import BarChart          from '../components/BarChart.vue'
import UserJourney       from '../components/UserJourney.vue'
import type { DateRange } from '../components/TimeRangeSelector.vue'

const range = ref<DateRange>({ label: '30d', days: 30 })
function onRangeChange(r: DateRange) { range.value = r }
</script>
