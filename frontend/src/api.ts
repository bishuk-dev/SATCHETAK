import type { AnalysisResult, AssessmentPurpose, DataMode, LocationInput, MonitoredLocation, MonitoringCheckResult, ObservationSearchResult, PlaceSearchResult, PriceComparableInput, PriceSummary, QueryPlan, Workflow } from './types'

async function request<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(path, { ...init, headers: { 'Content-Type': 'application/json', ...init.headers } })
  const body = await response.json() as T & { detail?: string | { msg?: string; loc?: (string | number)[] }[] }
  if (!response.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail.map(item => `${item.loc?.slice(1).join('.') || 'input'}: ${item.msg || 'invalid value'}`).join('; ')
      : body.detail
    throw new Error(detail || `Request failed (${response.status})`)
  }
  return body
}

export const api = {
  searchLocations: (query: string, signal?: AbortSignal) => request<{ results: PlaceSearchResult[] }>(`/api/v1/geocoding/search?q=${encodeURIComponent(query)}`, { signal }),
  listLocations: () => request<{ locations: MonitoredLocation[] }>('/api/v1/locations', {}),
  listAnalyses: (locationId: string) => request<{ analyses: AnalysisResult[] }>(`/api/v1/locations/${locationId}/analyses`, {}),
  createLocation: (input: LocationInput) => request<MonitoredLocation>('/api/v1/locations', { method: 'POST', body: JSON.stringify(input) }),
  planQuery: (query: string) => request<QueryPlan>('/api/v1/requests/plan', { method: 'POST', body: JSON.stringify({ query }) }),
  searchObservations: (input: LocationInput, mode: DataMode) => request<ObservationSearchResult>('/api/v1/observations/search', { method: 'POST', body: JSON.stringify({ aoi: input.aoi, period: input.period, mode }) }),
  createAnalysis: (locationId: string, mode: DataMode, workflow: Workflow, assessmentPurpose?: AssessmentPurpose | null) => request<AnalysisResult>('/api/v1/analyses', { method: 'POST', body: JSON.stringify({ location_id: locationId, mode, workflow, assessment_purpose: assessmentPurpose }) }),
  checkMonitoring: (locationId: string, mode: DataMode) => request<MonitoringCheckResult>(`/api/v1/locations/${locationId}/monitor/check`, { method: 'POST', body: JSON.stringify({ mode }) }),
  getPriceSummary: (locationId: string) => request<PriceSummary>(`/api/v1/locations/${locationId}/price-summary`, {}),
  addPriceComparable: (locationId: string, input: PriceComparableInput) => request(`/api/v1/locations/${locationId}/price-comparables`, { method: 'POST', body: JSON.stringify(input) }),
}
