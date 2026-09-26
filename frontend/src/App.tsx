import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api } from './api'
import { EvidenceCanvas } from './components/EvidenceCanvas'
import { EvidenceViewer } from './components/EvidenceViewer'
import { MapPreview } from './components/MapPreview'
import { Landing } from './components/Landing'
import type { AnalysisResult, DataMode, LocationInput, MonitoredLocation, ObservationSearchResult, PlaceSearchResult, Polygon, PriceSummary, QueryPlan } from './types'

const initial = { name: 'Monitored area - Bengaluru', west: 77.55, south: 12.92, east: 77.565, north: 12.932, from: '2025-01-01', to: '2025-06-30' }

function rectangleFromBounds(bounds: Pick<typeof initial, 'west' | 'south' | 'east' | 'north'>): Polygon {
  return { type: 'Polygon', coordinates: [[[bounds.west, bounds.south], [bounds.east, bounds.south], [bounds.east, bounds.north], [bounds.west, bounds.north], [bounds.west, bounds.south]]] }
}

export default function App() {
  const [route, setRoute] = useState(window.location.hash)
  useEffect(() => {
    const navigate = () => { setRoute(window.location.hash); window.scrollTo(0, 0) }
    window.addEventListener('hashchange', navigate)
    return () => window.removeEventListener('hashchange', navigate)
  }, [])
  return route.startsWith('#/dashboard') ? <Dashboard /> : <Landing />
}

function Dashboard() {
  const [form, setForm] = useState(initial)
  const [aoi, setAoi] = useState<Polygon>(() => rectangleFromBounds(initial))
  const [query, setQuery] = useState('Where has vegetation declined in this area?')
  const [mode, setMode] = useState<DataMode>('demo')
  const [plan, setPlan] = useState<QueryPlan | null>(null)
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [discovery, setDiscovery] = useState<ObservationSearchResult | null>(null)
  const [locationId, setLocationId] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [locationSearching, setLocationSearching] = useState(false)
  const [placeResults, setPlaceResults] = useState<PlaceSearchResult[]>([])
  const [locationSearchEnabled, setLocationSearchEnabled] = useState(false)
  const [savedLocations, setSavedLocations] = useState<MonitoredLocation[]>([])
  const performLocationSearch = useCallback(async (locationQuery: string, signal?: AbortSignal) => {
    setLocationSearching(true); setError(''); setPlaceResults([])
    try {
      const response = await api.searchLocations(locationQuery, signal)
      if (signal?.aborted) return
      setPlaceResults(response.results)
      if (!response.results.length) setError('No matching location was found. Try a city, village, district, or landmark.')
    } catch (cause) {
      if (!signal?.aborted) setError(cause instanceof Error ? cause.message : 'Location search failed')
    } finally {
      if (!signal?.aborted) setLocationSearching(false)
    }
  }, [])
  const refreshSavedLocations = useCallback(() => api.listLocations().then(result => setSavedLocations(result.locations)).catch(() => undefined), [])
  useEffect(() => { void refreshSavedLocations() }, [refreshSavedLocations])
  useEffect(() => {
    if (!locationSearchEnabled) return
    const locationQuery = form.name.trim()
    if (locationQuery.length < 2) { setPlaceResults([]); setLocationSearching(false); return }
    const controller = new AbortController()
    const timer = window.setTimeout(() => { void performLocationSearch(locationQuery, controller.signal) }, 400)
    return () => { window.clearTimeout(timer); controller.abort() }
  }, [form.name, locationSearchEnabled, performLocationSearch])
  function clearResults() {
    setPlan(null); setAnalysis(null); setDiscovery(null); setLocationId(null); setError('')
  }
  const update = (key: keyof typeof form, value: string) => {
    clearResults()
    const next = { ...form, [key]: key === 'name' || key === 'from' || key === 'to' ? value : Number(value) }
    if (key === 'west' || key === 'south' || key === 'east' || key === 'north') setAoi(rectangleFromBounds(next))
    setForm(next)
  }

  function applyDrawnAoi(nextAoi: Polygon) {
    clearResults()
    const ring = nextAoi.coordinates[0]
    const longitudes = ring.map(point => point[0])
    const latitudes = ring.map(point => point[1])
    setAoi(nextAoi)
    setForm(current => ({ ...current, west: Math.min(...longitudes), south: Math.min(...latitudes), east: Math.max(...longitudes), north: Math.max(...latitudes) }))
  }

  function locationInput(queryPlan: QueryPlan): LocationInput {
    return { name: form.name, sector: queryPlan.sector, aoi, period: { from: form.from, to: form.to } }
  }

  async function searchLocation() {
    if (form.name.trim().length < 2) { setError('Enter at least two characters to search for a location.'); return }
    setLocationSearchEnabled(true)
    await performLocationSearch(form.name.trim())
  }

  function selectPlace(place: PlaceSearchResult) {
    clearResults(); setPlaceResults([]); setLocationSearchEnabled(false); setLocationSearching(false)
    const bounds = place.bounds
    setForm(current => ({ ...current, name: place.display_name, ...bounds }))
    setAoi(rectangleFromBounds(bounds))
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (form.west >= form.east || form.south >= form.north || form.west < -180 || form.east > 180 || form.south < -90 || form.north > 90) {
      setError('Choose a non-zero area with west < east and south < north, within valid longitude and latitude bounds.')
      return
    }
    setBusy(true); clearResults()
    try {
      const queryPlan = await api.planQuery(query)
      setPlan(queryPlan)
      const input = locationInput(queryPlan)
      const location = await api.createLocation(input)
      setLocationId(location.id)
      if (queryPlan.workflow === 'observation_discovery') {
        setDiscovery(await api.searchObservations(input, mode))
      } else if (mode === 'live') {
        setDiscovery(await api.searchObservations(input, mode))
      } else {
        setAnalysis(await api.createAnalysis(location.id, mode, queryPlan.workflow, queryPlan.assessment_purpose))
        void refreshSavedLocations()
      }
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unexpected error') }
    finally { setBusy(false) }
  }

  async function runLiveAnalysis() {
    if (!locationId || !plan || plan.workflow === 'observation_discovery') return
    setBusy(true); setError('')
    try { setAnalysis(await api.createAnalysis(locationId, 'live', plan.workflow, plan.assessment_purpose)); void refreshSavedLocations() }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Unexpected error') }
    finally { setBusy(false) }
  }

  async function openSavedLocation(location: MonitoredLocation) {
    setBusy(true); setError('')
    try {
      const history = await api.listAnalyses(location.id)
      if (!history.analyses.length) throw new Error('This saved location has no completed analysis yet.')
      const ring = location.aoi.coordinates[0]
      const longitudes = ring.map(point => point[0]), latitudes = ring.map(point => point[1])
      setForm({ name: location.name, west: Math.min(...longitudes), south: Math.min(...latitudes), east: Math.max(...longitudes), north: Math.max(...latitudes), from: location.period.from, to: location.period.to })
      setAoi(location.aoi); setLocationId(location.id); setPlan(null); setDiscovery(null)
      setAnalysis(history.analyses[0])
      setMode(history.analyses[0].evidence.source_mode.startsWith('demo') ? 'demo' : 'live')
      document.getElementById('evidence')?.scrollIntoView({ behavior: 'smooth' })
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not open saved analysis') }
    finally { setBusy(false) }
  }

  return <>
    <header className="app-header"><a className="brand" href="#/"><span className="mark">S</span><span>SATCHETAK</span></a><span className="workspace-label">LAND INTELLIGENCE / WORKSPACE</span><div className="status"><i /> {mode === 'demo' ? 'Demo workspace' : 'Live · Copernicus'}</div></header>
    <div className="dashboard-shell"><aside className="dashboard-nav"><span className="nav-caption">WORKSPACE</span><a className="selected" href="#/dashboard">◎ Land explorer</a><a href="#evidence" onClick={event => { event.preventDefault(); document.getElementById('evidence')?.scrollIntoView({ behavior: 'smooth' }) }}>▤ Evidence report</a><div className="sidebar-note"><span>01 / DEFINE A PLACE</span><p>Draw an area. Ask a question. Inspect what the data supports.</p></div><a href="#/">← Back to overview</a></aside>
    <main className="dashboard-main">
      <section className="dashboard-heading"><div><p className="eyebrow">YOUR NEXT LAND DECISION</p><h1>Start with the ground truth.</h1><p>Explore agricultural potential, screen a purchase, or monitor development.</p></div><span className="mode-chip">{mode === 'demo' ? 'SIMULATED DATA' : 'LIVE OBSERVATIONS'}</span></section>
      <div className="query-presets" aria-label="Analysis templates">{[
        ['Land purchase', 'Is this land worth buying for agricultural use?'],
        ['Agriculture', 'Analyze vegetation condition and change in this field'],
        ['Development', 'Show urban development change and cleared land'],
        ['Commercial site', 'Assess this land purchase for commercial development'],
      ].map(([label, prompt]) => <button type="button" disabled={busy} key={label} className={query === prompt ? 'selected' : ''} onClick={() => { clearResults(); setQuery(prompt) }}>{label}<span>↗</span></button>)}</div>
      <section className="workspace">
        <form className="panel controls" onSubmit={submit}>
          <fieldset disabled={busy} className="request-fields">
          <div className="step"><b>01</b><span>LOCATION AND QUESTION</span></div>
          <div className="location-search"><label>Search location<input value={form.name} onChange={event => { update('name', event.target.value); setLocationSearchEnabled(true); setPlaceResults([]) }} placeholder="City, village, district, or landmark" autoComplete="off" required /></label><button type="button" className="location-search-button" disabled={locationSearching} onClick={searchLocation}>{locationSearching ? 'Searching...' : 'Find on map'}</button>{placeResults.length > 0 && <div className="location-results">{placeResults.map(place => <button type="button" key={`${place.latitude}-${place.longitude}-${place.display_name}`} onClick={() => selectPlace(place)}><strong>{place.display_name}</strong><small>{place.type.replaceAll('_', ' ')}</small></button>)}<span className="geocoder-credit">Search data © OpenStreetMap contributors</span></div>}</div>
          <label>What do you want to know?<textarea value={query} onChange={event => { clearResults(); setQuery(event.target.value) }} rows={3} required /></label>
          <div className="row">{(['west','south','east','north'] as const).map(key => <label key={key}>{key}<input type="number" step="any" min={key === 'west' || key === 'east' ? -180 : -90} max={key === 'west' || key === 'east' ? 180 : 90} value={form[key]} onChange={event => update(key,event.target.value)} required /></label>)}</div>
          <div className="step"><b>02</b><span>OBSERVATION POLICY</span></div>
          <div className="row"><label>From<input type="date" value={form.from} onChange={e => update('from',e.target.value)} required /></label><label>To<input type="date" value={form.to} onChange={e => update('to',e.target.value)} required /></label></div>
          <label>Data mode<select value={mode} onChange={e => { clearResults(); setMode(e.target.value as DataMode) }}><option value="demo">Demo - offline evidence</option><option value="live">Live - Copernicus</option></select></label>
          <button disabled={busy}>{busy ? 'Planning request...' : 'Plan and run request'} <span>→</span></button>
          {error && <p className="error" role="alert">{error}</p>}
          </fieldset>
        </form>
        <MapPreview aoi={aoi} onAoiChange={applyDrawnAoi} disabled={busy} />
      </section>

      {savedLocations.length > 0 && <SavedLocations locations={savedLocations.slice(0, 6)} busy={busy} onOpen={openSavedLocation} />}

      <div id="evidence" />
      {plan && <PlanSummary plan={plan} />}
      {discovery && !analysis && <Discovery result={discovery} plan={plan} busy={busy} onAnalyze={runLiveAnalysis} />}
      {analysis && <Results analysis={analysis} />}
      {error && discovery && <p className="error result-error" role="alert">{error}</p>}
      {!plan && <section className="empty-report"><span>▤</span><div><h2>Your evidence starts here</h2><p>Select an area and run a question. Dated observations, measured changes, and screening gaps will appear here.</p></div></section>}
    </main></div>
    <footer><span>SATCHETAK</span><span>Monitor land. Verify change.</span></footer>
  </>
}

function PlanSummary({ plan }: { plan: QueryPlan }) {
  return <section className="plan-summary"><div><span>REQUEST PLAN</span><strong>{plan.workflow.replaceAll('_', ' ')}</strong></div><div><span>SECTOR</span><strong>{plan.sector.replaceAll('_', ' ')}</strong></div><div><span>CONFIDENCE</span><strong>{plan.confidence}</strong></div><div><span>REQUIRED BANDS</span><strong>{plan.required_bands.join(', ') || 'metadata only'}</strong></div><p>{plan.rationale} {plan.claim_limitations.join(' ')}</p></section>
}

function SavedLocations({ locations, busy, onOpen }: { locations: MonitoredLocation[]; busy: boolean; onOpen: (location: MonitoredLocation) => void }) {
  return <section className="saved-locations"><div className="saved-locations-head"><div><p className="eyebrow">SAVED MONITORING</p><h2>Recent locations</h2></div><span>Reopen a completed evidence report</span></div><div className="saved-location-grid">{locations.map(location => <button type="button" disabled={busy} key={location.id} onClick={() => onOpen(location)}><span>{location.sector.replaceAll('_', ' ')}</span><strong>{location.name}</strong><small>{location.period.from} → {location.period.to}</small></button>)}</div></section>
}

function Discovery({ result, plan, busy, onAnalyze }: { result: ObservationSearchResult; plan: QueryPlan | null; busy: boolean; onAnalyze: () => void }) {
  const canAnalyze = plan && plan.workflow !== 'observation_discovery'
  const qualified = result.candidates.filter(item => item.quality_state !== 'rejected_cloud')
  const rejected = result.candidates.length - qualified.length
  return <section className="results observation-discovery"><p className="eyebrow">OBSERVATION RESULT</p><h2>{qualified.length} of {result.candidates.length} observations passed catalogue filtering</h2><div className="discovery-quality"><article><span>SELECTED BASELINE</span><strong>{result.selected.t1.acquisition_time.slice(0,10)}</strong><p>Earliest catalogue-qualified observation in the requested period.</p></article><article><span>SELECTED LATEST</span><strong>{result.selected.t2.acquisition_time.slice(0,10)}</strong><p>Latest catalogue-qualified observation, maximizing the comparison interval.</p></article><article><span>REJECTED</span><strong>{rejected}</strong><p>Excluded by the configured scene-cloud rule before pixel acquisition.</p></article></div><p className="catalogue-caveat">This is catalogue evidence only. Scene cloud, dates, provider, and band metadata support selection; AOI valid pixels are checked during processing.</p><details className="candidate-list"><summary>Inspect all observation candidates</summary>{result.candidates.map(item => <div key={item.provider_scene_id}><span>{item.acquisition_time.slice(0,10)}</span><span>{item.cloud_cover == null ? 'Cloud unknown' : `${item.cloud_cover}% cloud`}</span><strong>{item.quality_state.replaceAll('_', ' ')}</strong></div>)}</details>{canAnalyze && <button className="secondary-action" disabled={busy} onClick={onAnalyze}>{busy ? 'Acquiring pixels...' : `Acquire pixels and run ${plan.workflow.replaceAll('_',' ')}`} <span>→</span></button>}</section>
}

function Results({ analysis }: { analysis: AnalysisResult }) {
  const m = analysis.metrics, e = analysis.evidence
  const vegetation = analysis.workflow === 'vegetation_change'
  return <section className="results"><div className="result-head"><div><p className="eyebrow">{e.source_mode.startsWith('demo') ? 'SIMULATED RESULT' : 'MEASURED RESULT'}</p><h2>{vegetation ? 'Vegetation change evidence' : 'Generic land-change evidence'}</h2></div><span className="badge">{e.source_mode.replaceAll('_',' ').toUpperCase()}</span></div>
    <ReportActions analysis={analysis} />
    <ObservationReview summary={e.observation_summary} />
    <div className="observation-cards">{([['T1', analysis.t1], ['T2', analysis.t2]] as const).map(([label, observation]) => <article key={label}><span>{label} · {observation.acquisition_time.slice(0, 10)}</span><strong>{observation.satellite} / {observation.sensor}</strong><p>{observation.provider} · Scene cloud: {observation.cloud_cover == null ? 'unknown' : `${observation.cloud_cover}%`}</p><small>Scene-level cloud metadata is not the cloud fraction inside your area.</small></article>)}</div>
    {analysis.interpretation ? <InterpretationBrief interpretation={analysis.interpretation} /> : <div className="interpretation"><span>WHAT THE SATELLITE EVIDENCE SAYS</span><p>{analysis.explanation}</p></div>}
    <EvidenceViewer artifacts={analysis.artifacts} regions={e.change_regions} />
    {!vegetation && <BuyerEvidenceSummary metrics={m} effects={e.observable_effects ?? []} dates={e.observation_dates ?? [analysis.t1.acquisition_time.slice(0, 10), analysis.t2.acquisition_time.slice(0, 10)]} />}
    {vegetation ? <>
      <div className="metrics"><Metric label="MEAN ΔNDVI" value={signed(m.mean_delta_ndvi)} /><Metric label="DECLINE AREA" value={`${m.vegetation_decline_area_ha ?? m.vegetation_decline_area_ha_estimate} ha`} /><Metric label="INCREASE AREA" value={`${m.vegetation_increase_area_ha ?? m.vegetation_increase_area_ha_estimate} ha`} /><Metric label={e.source_mode.startsWith('demo') ? 'AOI AREA ESTIMATE' : 'VALID OVERLAP AREA'} value={`${m.aoi_area_ha_measured ?? m.aoi_area_ha_estimate} ha`} /></div>
      <div className="evidence-grid"><EvidenceCanvas grid={e.ndvi_t1!} validMask={e.valid_mask} mode="ndvi" label="T1 · NDVI" detail={analysis.t1.acquisition_time.slice(0,10)} /><EvidenceCanvas grid={e.ndvi_t2!} validMask={e.valid_mask} mode="ndvi" label="T2 · NDVI" detail={analysis.t2.acquisition_time.slice(0,10)} /><EvidenceCanvas grid={e.delta_ndvi!} validMask={e.valid_mask} mode="delta" label="ΔNDVI EVIDENCE" detail="≤ -0.12 / ≥ +0.12" /></div>
    </> : <>
      <details className="technical-evidence"><summary>Technical pixel measurements</summary>
      <div className="metrics"><Metric label="MEAN INDEX CHANGE" value={String(m.mean_spectral_change)} /><Metric label="CATEGORIZED AREA" value={`${m.changed_area_ha} ha`} /><Metric label="QUALIFYING PIXELS" value={String(m.changed_pixel_count)} /><Metric label="VALID AREA" value={`${m.valid_area_ha} ha`} /></div>
      <div className="evidence-grid single"><EvidenceCanvas grid={e.spectral_change_magnitude!} validMask={e.valid_mask} mode="change" label="SPECTRAL CHANGE MAGNITUDE" detail={`threshold ≥ ${m.change_threshold}`} /><EvidenceCanvas grid={e.change_mask!} validMask={e.valid_mask} mode="change" label="GENERIC CHANGE MASK" detail={`${m.changed_area_ha} ha`} /></div>
      </details>
    </>}
    {vegetation && m.ndvi_t2_median !== undefined && <section className="agriculture-details"><h3>A closer look at vegetation</h3><p>Statistics use mutually valid pixels. Two dates show change, not crop productivity or soil fertility.</p><div className="metrics"><Metric label="T1 → T2 MEAN NDVI" value={`${m.mean_ndvi_t1} → ${m.mean_ndvi_t2}`} /><Metric label="T2 MEDIAN NDVI" value={String(m.ndvi_t2_median)} /><Metric label="T2 P10 / P90" value={`${m.ndvi_t2_p10} / ${m.ndvi_t2_p90}`} /><Metric label="T2 NDVI VARIABILITY (SD)" value={String(m.ndvi_t2_std)} /></div><div className="change-shares"><span>Decline {m.decline_share_pct}%</span><span>Within thresholds {m.stable_share_pct}%</span><span>Increase {m.increase_share_pct}%</span></div><p>{m.valid_pixel_count} mutually valid pixels. Shares describe thresholded change, not the fraction of land suitable for farming.</p></section>}
    {analysis.assessment && <AssessmentReport assessment={analysis.assessment} />}
    <PricingEvidence locationId={analysis.location_id} />
    <details><summary>Provenance and warnings</summary><pre>{JSON.stringify({ workflow:analysis.workflow, t1:analysis.t1, t2:analysis.t2, crs:e.crs, resolution_m:e.resolution_m, thresholds:e.thresholds, warnings:analysis.warnings, explanation_source:analysis.explanation_source }, null, 2)}</pre></details>
  </section>
}

function PricingEvidence({ locationId }: { locationId: string }) {
  const [summary, setSummary] = useState<PriceSummary | null>(null)
  const [message, setMessage] = useState('')
  const [entry, setEntry] = useState({ transaction_date: new Date().toISOString().slice(0, 10), total_price: '', area_ha: '', currency: 'INR', source: '' })
  const load = useCallback(() => api.getPriceSummary(locationId).then(setSummary).catch(cause => setMessage(cause instanceof Error ? cause.message : 'Could not load market evidence')), [locationId])
  useEffect(() => { void load() }, [load])
  async function submitComparable(event: FormEvent) {
    event.preventDefault(); setMessage('')
    try {
      await api.addPriceComparable(locationId, { ...entry, total_price: Number(entry.total_price), area_ha: Number(entry.area_ha) })
      setEntry(current => ({ ...current, total_price: '', area_ha: '', source: '' })); await load(); setMessage('Comparable saved as verified user-provided evidence.')
    } catch (cause) { setMessage(cause instanceof Error ? cause.message : 'Could not save comparable') }
  }
  const money = (value: number | null) => value == null ? '—' : new Intl.NumberFormat('en-IN', { style: 'currency', currency: summary?.currency ?? 'INR', maximumFractionDigits: 0 }).format(value)
  return <details className="pricing-evidence"><summary>Market-price evidence ({summary?.comparable_count ?? 0} verified comparables)</summary><div className="pricing-body"><p>Satellite imagery does not determine land value. Add traceable asking-price or transaction records to keep market evidence separate from physical change evidence.</p>{summary && summary.comparable_count > 0 && <div className="pricing-stats"><div><span>MEDIAN / HA</span><strong>{money(summary.median_price_per_ha)}</strong></div><div><span>OBSERVED RANGE / HA</span><strong>{money(summary.min_price_per_ha)} – {money(summary.max_price_per_ha)}</strong></div><div><span>FIRST → LATEST</span><strong>{summary.first_to_latest_change_pct == null ? 'Need 2 records' : `${summary.first_to_latest_change_pct > 0 ? '+' : ''}${summary.first_to_latest_change_pct}%`}</strong></div></div>}<form className="price-form" onSubmit={submitComparable}><label>Date<input type="date" value={entry.transaction_date} onChange={event => setEntry({ ...entry, transaction_date: event.target.value })} required /></label><label>Total price<input type="number" min="1" value={entry.total_price} onChange={event => setEntry({ ...entry, total_price: event.target.value })} required /></label><label>Area (ha)<input type="number" min="0.0001" step="any" value={entry.area_ha} onChange={event => setEntry({ ...entry, area_ha: event.target.value })} required /></label><label>Evidence source<input value={entry.source} onChange={event => setEntry({ ...entry, source: event.target.value })} placeholder="Registry record or listing reference" required /></label><button type="submit">Add comparable</button></form>{summary && <small>{summary.caveat}</small>}{message && <p className="monitoring-message" role="status">{message}</p>}</div></details>
}

function ObservationReview({ summary }: { summary?: AnalysisResult['evidence']['observation_summary'] }) {
  if (!summary) return null
  return <section className="observation-review"><header><div><p className="eyebrow">OBSERVATION QUALITY</p><h3>Why these dates were used</h3></div><span>{summary.selected_span_days} day comparison</span></header><div className="observation-review-stats"><div><strong>{summary.candidate_count}</strong><span>CATALOGUE CANDIDATES</span></div><div><strong>{summary.qualified_count}</strong><span>CATALOGUE-QUALIFIED</span></div><div><strong>{summary.rejected_count}</strong><span>REJECTED</span></div><div><strong>{summary.intermediate_support_count}</strong><span>INTERMEDIATE CHECKS</span></div></div><p>{summary.selection_rationale}</p><small>{summary.quality_caveat}</small>{summary.candidates && <details className="candidate-list"><summary>Inspect observation audit trail</summary>{summary.candidates.map(item => <div key={item.scene_id}><span>{item.date}</span><span>{item.cloud_cover == null ? 'Cloud unknown' : `${item.cloud_cover}% cloud`}</span><strong>{item.quality_state.replaceAll('_', ' ')}</strong></div>)}</details>}</section>
}

function InterpretationBrief({ interpretation }: { interpretation: NonNullable<AnalysisResult['interpretation']> }) {
  return <section className="interpretation-brief">
    <header><div><p className="eyebrow">PLAIN-LANGUAGE ANSWER</p><h3>{interpretation.headline}</h3></div><span>{interpretation.confidence}</span></header>
    <p className="direct-answer">{interpretation.plain_language_summary ?? interpretation.direct_answer}</p>
    <div className="reasoning-grid"><section><h4>Why the evidence supports this</h4>{interpretation.evidence_points.map(point => <p key={point}>{point}</p>)}</section><section><h4>What this may mean for the decision</h4>{interpretation.decision_relevance.map(point => <p key={point}>{point}</p>)}</section></div>
    <div className="confidence-reason"><strong>How to read the confidence</strong><p>{interpretation.confidence_reason}</p></div>
    <details className="interpretation-limits"><summary>What this analysis does not prove</summary>{interpretation.limitations.map(item => <p key={item}>{item}</p>)}</details>
    <details className="interpretation-limits"><summary>Explanation provenance</summary><p>{interpretation.language_status ?? 'Verified deterministic explanation.'}</p><p>Source: {interpretation.language_source ?? interpretation.source}</p></details>
    <div className="brief-next-action"><strong>Recommended next verification</strong><p>{interpretation.next_action}</p></div>
  </section>
}

function BuyerEvidenceSummary({ metrics, effects, dates }: { metrics: Record<string, number>; effects: NonNullable<AnalysisResult['evidence']['observable_effects']>; dates: string[] }) {
  const share = metrics.changed_share_pct ?? (metrics.valid_area_ha ? metrics.changed_area_ha / metrics.valid_area_ha * 100 : 0)
  const clearing = metrics.vegetation_to_bare_area_ha ?? 0
  const built = metrics.built_up_like_area_ha ?? 0
  const other = metrics.other_change_area_ha ?? metrics.changed_area_ha
  return <section className="buyer-evidence-summary">
    <header><div><p className="eyebrow">PLAIN-LANGUAGE RESULT</p><h3>{metrics.changed_area_ha.toFixed(2)} ha changed across {share.toFixed(1)}% of the valid observed land</h3></div><span>{metrics.change_region_count ?? '—'} meaningful regions</span></header>
    <div className="change-category-grid">
      <article className="clearing"><span>VEGETATION → BARE / DISTURBED</span><strong>{clearing.toFixed(2)} ha</strong><p>Vegetation decreased while bare-soil signals increased.</p></article>
      <article className="built"><span>BUILT-UP-LIKE CHANGE</span><strong>{built.toFixed(2)} ha</strong><p>SWIR/NIR signals became more consistent with built or hardened surfaces.</p></article>
      <article className="other"><span>OTHER SURFACE CHANGE</span><strong>{other.toFixed(2)} ha</strong><p>Meaningful change was detected, but it did not meet either category rule.</p></article>
      <article><span>LARGEST CONNECTED REGION</span><strong>{(metrics.largest_region_area_ha ?? 0).toFixed(2)} ha</strong><p>Small isolated pixels were removed before area measurement.</p></article>
    </div>
    <div className="temporal-summary">
      <div><span>REPEATED ACROSS DATES</span><strong>{(metrics.repeat_observed_area_ha ?? 0).toFixed(2)} ha</strong><p>The same category appeared in at least two comparison observations.</p></div>
      <div><span>LATEST COMPARISON ONLY</span><strong>{(metrics.latest_only_area_ha ?? 0).toFixed(2)} ha</strong><p>Newer or unconfirmed signal; a later clear observation is needed to test persistence.</p></div>
      <div><span>USABLE DATES CHECKED</span><strong>{metrics.temporal_observation_count ?? 2}</strong><p>One baseline plus quality-qualified comparison dates.</p></div>
    </div>
    <p className="observation-date-list"><b>Dates used:</b> {dates.join(' · ')}</p>
    {effects.some(effect => effect.area_ha > 0) && <section className="observable-effects"><h4>What changed, and what it affects</h4>{effects.filter(effect => effect.area_ha > 0).map(effect => <article key={effect.category}><strong>{effect.area_ha.toFixed(2)} ha</strong><div><b>{effect.observed_effect}</b><p>{effect.decision_relevance}</p></div></article>)}</section>}
    <p className="screening-limit">These are conservative satellite screening categories—not confirmation of a building, legal development, ownership, or permitted use.</p>
  </section>
}

function ReportActions({ analysis }: { analysis: AnalysisResult }) {
  const [monitoringMessage, setMonitoringMessage] = useState('')
  const [checking, setChecking] = useState(false)
  function downloadEvidence() {
    const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url; link.download = `satchetak-${analysis.id}.json`; link.click()
    URL.revokeObjectURL(url)
  }
  async function checkMonitoring() {
    setChecking(true); setMonitoringMessage('')
    try {
      const mode: DataMode = analysis.evidence.source_mode.startsWith('demo') ? 'demo' : 'live'
      setMonitoringMessage((await api.checkMonitoring(analysis.location_id, mode)).message)
    } catch (cause) { setMonitoringMessage(cause instanceof Error ? cause.message : 'Monitoring check failed') }
    finally { setChecking(false) }
  }
  return <><div className="report-actions"><button type="button" disabled={checking} onClick={checkMonitoring}>{checking ? 'Checking imagery...' : 'Check for newer imagery'}</button><button type="button" onClick={() => window.print()}>Print / save PDF</button><button type="button" onClick={downloadEvidence}>Download evidence JSON</button></div>{monitoringMessage && <p className="monitoring-message" role="status">{monitoringMessage}</p>}</>
}

function AssessmentReport({ assessment }: { assessment: NonNullable<AnalysisResult['assessment']> }) {
  const heading = assessment.purpose === 'agriculture_purchase' ? 'Agricultural purchase context' : 'Development purchase context'
  return <section className="assessment-report compact-assessment">
    <p className="eyebrow">DECISION CONTEXT</p><h2>{heading}</h2>
    <p className="assessment-conclusion">{assessment.conclusion}</p>
    <div className="assessment-findings">{assessment.findings.map(finding => <p key={finding}>{finding}</p>)}</div>
    <details className="due-diligence"><summary>Checks satellite imagery cannot answer ({assessment.missing_checks.length})</summary><div className="check-grid">{assessment.missing_checks.map(check => <article key={check.name}><span>NOT MEASURED</span><h4>{check.name}</h4><p>{check.action}</p></article>)}</div></details>
    <div className="priority-actions"><strong>Recommended next action</strong><p>{assessment.next_steps[0]}</p></div>
  </section>
}

function signed(value: number) { return `${value >= 0 ? '+' : ''}${value}` }
function Metric({ label, value }: { label: string; value: string }) { return <article><span>{label}</span><strong>{value}</strong></article> }
