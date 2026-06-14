<template>
  <div class="flex items-center gap-1 bg-surface-card border border-surface-border rounded-xl p-1">
    <button
      v-for="opt in OPTIONS"
      :key="opt.label"
      class="tab"
      :class="selected === opt.label ? 'tab-active' : 'tab-inactive'"
      @click="select(opt)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

export interface DateRange { days: number; label: string }

const emit = defineEmits<{ (e: 'change', range: DateRange): void }>()

const OPTIONS: DateRange[] = [
  { label: '7d',  days: 7  },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
]

const selected = ref('30d')

function select(opt: DateRange) {
  selected.value = opt.label
  emit('change', opt)
}

// Emit default on mount
emit('change', OPTIONS[1])
</script>
