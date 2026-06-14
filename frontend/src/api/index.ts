import axios from 'axios'

const api = axios.create({ baseURL: '' })

export interface DauRow       { date: string; unique_users: number; session_count: number; total_events: number }
export interface WauRow       { week: string; unique_users: number; session_count: number; total_events: number }
export interface MauRow       { month: string; unique_users: number; session_count: number; total_events: number }
export interface TopPage      { page_path: string; view_count: number }
export interface EventPoint   { date: string; count: number }
export interface TodayStats   { unique_users: number; session_count: number; total_events: number; top_page: string | null }

export interface Session {
  session_id:       string
  user_id:          string | null
  started_at:       string
  ended_at:         string
  first_page:       string | null
  last_page:        string | null
  event_count:      number
  duration_seconds: number
}

export interface RawEvent {
  timestamp:  string
  event_type: string
  event_name: string
  page_path:  string | null
  properties: Record<string, unknown>
}

export const fetchDau          = (days = 30)             => api.get<DauRow[]>(`/dau?days=${days}`).then(r => r.data)
export const fetchWau          = (weeks = 12)            => api.get<WauRow[]>(`/wau?weeks=${weeks}`).then(r => r.data)
export const fetchMau          = (months = 6)            => api.get<MauRow[]>(`/mau?months=${months}`).then(r => r.data)
export const fetchTopPages     = (days = 7)              => api.get<TopPage[]>(`/top-pages?days=${days}`).then(r => r.data)
export const fetchEventTimeline = (name: string, days = 30) => api.get<EventPoint[]>(`/events/timeline?event_name=${name}&days=${days}`).then(r => r.data)
export const fetchStatsToday   = ()                      => api.get<TodayStats>('/stats/today').then(r => r.data)
export const fetchSessions     = (days = 7, userId?: string) => {
  const u = userId ? `&user_id=${userId}` : ''
  return api.get<Session[]>(`/sessions?days=${days}${u}`).then(r => r.data)
}
export const fetchSessionEvents = (sessionId: string)   => api.get<RawEvent[]>(`/sessions/${sessionId}/events`).then(r => r.data)
