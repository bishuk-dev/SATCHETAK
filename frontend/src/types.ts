export type Position = [number, number]
export type Polygon = { type: 'Polygon'; coordinates: Position[][] }
export type Period = { from: string; to: string }
export type DataMode = 'demo' | 'live'
export type Workflow = 'observation_discovery' | 'vegetation_change' | 'generic_land_change'
export type AssessmentPurpose = 'agriculture_purchase' | 'development_purchase'
export interface AssessmentReport {
  purpose: AssessmentPurpose
  status: 'demo_only' | 'insufficient_evidence'
  conclusion: string
  findings: string[]
  missing_checks: { name: string; status: string; action: string }[]
  next_steps: string[]
}

export interface LocationInput {
  name: string
  sector: 'agriculture' | 'urban_land'
  aoi: Polygon
  period: Period
}

export interface PlaceSearchResult {
  display_name: string
  latitude: number
  longitude: number
  bounds: { west: number; south: number; east: number; north: number }
  type: string
}

export interface MonitoredLocation extends LocationInput {
  id: string
  created_at: string
}

export interface Observation {
  provider: string
  provider_scene_id: string
  satellite: string
  sensor: string
  acquisition_time: string
  cloud_cover: number | null
  product_level: string
  bands: string[]
  crs: string | null
  asset_references: Record<string, string>
  quality_state: string
  source_mode: string
}

export interface AnalysisArtifact {
  id: string
  role: 't1' | 't2' | 'change'
  kind: 'true_color' | 'change_overlay'
  title: string
  url: string
  media_type: 'image/png'
  coordinates: Position[]
  width: number
  height: number
  acquisition_time: string | null
  source_mode: string
  description: string
  legend: { label: string; color: string }[]
}

export interface AnalysisResult {
  assessment?: AssessmentReport | null
  id: string
  location_id: string
  created_at: string
  workflow: 'vegetation_change' | 'generic_land_change'
  t1: Observation
  t2: Observation
  metrics: Record<string, number>
  evidence: {
    grid_size: number | [number, number]
    ndvi_t1?: number[][]
    ndvi_t2?: number[][]
    delta_ndvi?: number[][]
    spectral_change_magnitude?: number[][]
    change_mask?: number[][]
    change_classification?: number[][]
    change_regions?: ChangeRegion[]
    temporal_support_count?: number[][]
    support_observation_dates?: string[]
    observation_dates?: string[]
    observable_effects?: ObservableEffect[]
    observation_summary?: ObservationSummary
    delta_ndbi?: number[][]
    delta_bsi?: number[][]
    valid_mask?: number[][]
    thresholds: Record<string, number | string>
    source_mode: string
    crs?: string
    resolution_m?: number
  }
  warnings: string[]
  explanation: string
  explanation_source: string
  interpretation?: EvidenceInterpretation | null
  artifacts?: AnalysisArtifact[]
}

export interface ObservationSummary {
  candidate_count: number
  qualified_count: number
  rejected_count: number
  selected_span_days: number
  intermediate_support_count: number
  selected_dates: string[]
  candidates?: { scene_id: string; date: string; cloud_cover: number | null; quality_state: string }[]
  selection_rationale: string
  quality_caveat: string
}

export interface EvidenceInterpretation {
  headline: string
  direct_answer: string
  confidence: string
  confidence_reason: string
  evidence_points: string[]
  decision_relevance: string[]
  limitations: string[]
  next_action: string
  source: string
  plain_language_summary?: string
  language_source?: string
  language_status?: string
}

export interface ChangeRegion {
  id: string
  category: 'vegetation_to_bare_candidate' | 'built_up_like_candidate' | 'other_surface_change'
  pixel_count: number
  area_ha: number
  location: string
  centroid_x_pct: number
  centroid_y_pct: number
  repeated_area_ha?: number
  latest_only_area_ha?: number
  temporal_status?: 'repeated' | 'latest_only'
}

export interface ObservableEffect {
  category: ChangeRegion['category']
  area_ha: number
  observed_effect: string
  decision_relevance: string
}

export interface QueryPlan {
  assessment_purpose?: AssessmentPurpose | null
  query: string
  sector: 'agriculture' | 'urban_land'
  workflow: Workflow
  confidence: 'high' | 'medium' | 'low'
  recognized_terms: string[]
  required_bands: string[]
  requested_outputs: string[]
  claim_limitations: string[]
  rationale: string
}

export interface ObservationSearchResult {
  mode: DataMode
  candidates: Observation[]
  selected: { t1: Observation; t2: Observation }
}

export interface MonitoringCheckResult {
  location_id: string
  status: 'new_observation_available' | 'up_to_date' | 'no_previous_analysis'
  checked_at: string
  previous_latest_date?: string | null
  latest_available_date?: string | null
  candidate_count: number
  message: string
}

export interface PriceComparableInput {
  transaction_date: string
  total_price: number
  area_ha: number
  currency: string
  source: string
  source_url?: string | null
  notes?: string | null
}

export interface PriceSummary {
  location_id: string
  comparable_count: number
  currency: string | null
  median_price_per_ha: number | null
  min_price_per_ha: number | null
  max_price_per_ha: number | null
  first_to_latest_change_pct: number | null
  trend_direction: 'up' | 'down' | 'flat' | 'insufficient_data'
  comparables: (PriceComparableInput & { id: string; location_id: string; price_per_ha: number; created_at: string })[]
  caveat: string
}
