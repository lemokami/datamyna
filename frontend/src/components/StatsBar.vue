<template>
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
    <div v-for="stat in stats" :key="stat.label" class="card flex flex-col gap-2">
      <span class="label">{{ stat.label }}</span>
      <span v-if="loading" class="stat-number animate-pulse text-ink-faint">—</span>
      <span v-else class="stat-number">{{ stat.value }}</span>
      <span v-if="stat.sub" class="text-xs text-ink-muted truncate">{{ stat.sub }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { fetchStatsToday } from '../api'

const loading = ref(true)
const data    = ref({ unique_users: 0, session_count: 0, total_events: 0, top_page: null as string | null })

onMounted(async () => {
  try   { data.value = await fetchStatsToday() }
  finally { loading.value = false }
})

const stats = computed(() => [
  { label: 'Users today',    value: fmt(data.value.unique_users),  sub: '' },
  { label: 'Sessions today', value: fmt(data.value.session_count), sub: '' },
  { label: 'Events today',   value: fmt(data.value.total_events),  sub: '' },
  { label: 'Top page',       value: data.value.top_page || '—',    sub: '' },
])

function fmt(n: number) { return n.toLocaleString() }
</script>
