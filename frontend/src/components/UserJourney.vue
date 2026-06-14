<template>
  <div class="card flex flex-col gap-4">
    <!-- Header + filters -->
    <div class="flex flex-col sm:flex-row sm:items-center gap-3">
      <h2 class="text-sm font-medium text-ink flex-1">User journeys</h2>
      <input
        v-model="userFilter"
        placeholder="Filter by user ID…"
        class="bg-surface border border-surface-border text-sm text-ink rounded-lg px-3 py-1.5 w-full sm:w-48 placeholder:text-ink-faint focus:outline-none focus:border-brand"
        @keyup.enter="load"
      />
      <button
        class="tab tab-active text-xs px-3"
        @click="load"
      >Search</button>
    </div>

    <!-- Session list -->
    <div v-if="loading" class="text-ink-muted text-sm py-8 text-center">Loading sessions…</div>
    <div v-else-if="sessions.length === 0" class="text-ink-muted text-sm py-8 text-center">
      No sessions found. Try seeding the database first.
    </div>

    <div v-else class="flex flex-col gap-2 max-h-[600px] overflow-y-auto pr-1">
      <div
        v-for="session in sessions"
        :key="session.session_id"
        class="border border-surface-border rounded-xl overflow-hidden"
      >
        <!-- Session row header — click to expand -->
        <button
          class="w-full flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 text-left hover:bg-surface-card transition-colors"
          @click="toggleSession(session.session_id)"
        >
          <span class="pill bg-brand/10 text-brand">{{ session.user_id || 'anon' }}</span>
          <span class="font-mono text-xs text-ink-muted">{{ fmtDate(session.started_at) }}</span>
          <span class="text-xs text-ink-muted">{{ fmtDuration(session.duration_seconds) }}</span>
          <span class="text-xs text-ink-muted">{{ session.event_count }} events</span>
          <span class="text-xs text-ink-muted ml-auto truncate max-w-[180px]">
            {{ session.first_page }} → {{ session.last_page }}
          </span>
          <span class="text-ink-faint text-xs ml-2">
            {{ expandedId === session.session_id ? '▲' : '▼' }}
          </span>
        </button>

        <!-- Event timeline (expanded) -->
        <div v-if="expandedId === session.session_id" class="border-t border-surface-border bg-surface px-4 py-4">
          <div v-if="eventsLoading" class="text-ink-muted text-xs py-2">Loading events…</div>
          <div v-else class="flex flex-col">
            <div
              v-for="(ev, i) in sessionEvents"
              :key="i"
              class="flex gap-3"
            >
              <!-- Timeline spine -->
              <div class="flex flex-col items-center">
                <div
                  class="w-2 h-2 rounded-full mt-1 shrink-0"
                  :class="dotColor(ev.event_type)"
                />
                <div v-if="i < sessionEvents.length - 1" class="w-px flex-1 bg-surface-border my-1" />
              </div>

              <!-- Event content -->
              <div class="pb-4 min-w-0">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-mono text-xs font-medium text-ink">{{ ev.event_name }}</span>
                  <span class="pill" :class="pillClass(ev.event_type)">{{ ev.event_type }}</span>
                  <span class="font-mono text-xs text-ink-muted">{{ fmtTime(ev.timestamp) }}</span>
                </div>
                <div v-if="ev.page_path" class="text-xs text-ink-muted mt-0.5">{{ ev.page_path }}</div>

                <!-- Time gap to next event -->
                <div
                  v-if="i < sessionEvents.length - 1"
                  class="mt-2 text-xs text-ink-faint font-mono"
                >
                  +{{ timeDiff(sessionEvents[i].timestamp, sessionEvents[i + 1].timestamp) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { fetchSessions, fetchSessionEvents } from '../api'
import type { Session, RawEvent } from '../api'
import type { DateRange } from './TimeRangeSelector.vue'

const props = defineProps<{ range: DateRange }>()

const sessions      = ref<Session[]>([])
const loading       = ref(true)
const userFilter    = ref('')
const expandedId    = ref<string | null>(null)
const sessionEvents = ref<RawEvent[]>([])
const eventsLoading = ref(false)

async function load() {
  loading.value  = true
  expandedId.value = null
  try {
    sessions.value = await fetchSessions(props.range.days, userFilter.value || undefined)
  } finally {
    loading.value = false
  }
}

async function toggleSession(id: string) {
  if (expandedId.value === id) { expandedId.value = null; return }
  expandedId.value    = id
  eventsLoading.value = true
  sessionEvents.value = []
  try { sessionEvents.value = await fetchSessionEvents(id) }
  finally { eventsLoading.value = false }
}

watch(() => props.range, load)
onMounted(load)

// ── Formatting helpers ────────────────────────────────────────────────────────

function fmtDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleString('en-GB', { dateStyle: 'short', timeStyle: 'short', hour12: false })
}

function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-GB', { hour12: false })
}

function fmtDuration(secs: number) {
  if (secs < 60)   return `${secs}s`
  if (secs < 3600) return `${Math.round(secs / 60)}m`
  return `${(secs / 3600).toFixed(1)}h`
}

function timeDiff(a: string, b: string) {
  const diff = Math.round((new Date(b).getTime() - new Date(a).getTime()) / 1000)
  return fmtDuration(diff)
}

// ── Style helpers ─────────────────────────────────────────────────────────────

function dotColor(type: string) {
  return type === 'page_view' ? 'bg-brand'
       : type === 'click'     ? 'bg-teal'
       :                        'bg-amber-400'
}

function pillClass(type: string) {
  return type === 'page_view' ? 'bg-brand/10 text-brand'
       : type === 'click'     ? 'bg-teal/10 text-teal'
       :                        'bg-amber-400/10 text-amber-400'
}
</script>
