import { useState } from 'react'
import type { AnalysisArtifact, ChangeRegion } from '../types'

type Props = { artifacts?: AnalysisArtifact[] | null; regions?: ChangeRegion[] }

const categoryText: Record<ChangeRegion['category'], string> = {
  vegetation_to_bare_candidate: 'Vegetation to bare / disturbed',
  built_up_like_candidate: 'Built-up-like change',
  other_surface_change: 'Other surface change',
}

export function EvidenceViewer({ artifacts = [], regions = [] }: Props) {
  const [opacity, setOpacity] = useState(72)
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null)
  const available = artifacts ?? []
  const t1 = available.find(item => item.role === 't1')
  const t2 = available.find(item => item.role === 't2')
  const change = available.find(item => item.role === 'change')
  if (!t1 || !t2 || !change) return <section className="evidence-unavailable" role="status">
    <div><p className="eyebrow">PIXEL EVIDENCE UNAVAILABLE</p><h3>This result has no dated imagery artifacts</h3></div>
    <p>Restart the FastAPI backend and rerun this analysis. Results created by the older backend contain numerical grids but cannot be upgraded into T1/T2 imagery without reacquiring the source pixels.</p>
  </section>
  const simulated = t1.source_mode.startsWith('demo')
  const selected = regions.find(region => region.id === selectedRegion) ?? regions[0]

  return <section className="evidence-viewer" aria-labelledby="dated-imagery-title">
    <div className="evidence-viewer-head">
      <div><p className="eyebrow">BEFORE / AFTER EVIDENCE</p><h3 id="dated-imagery-title">What changed on the selected land</h3></div>
      <span className={simulated ? 'artifact-state simulated' : 'artifact-state'}>{simulated ? 'SIMULATED PIXELS' : 'SENTINEL-2 PIXELS'}</span>
    </div>
    <p className="artifact-note">Compare the dated satellite observations, then read the coloured overlay on the latest image. Only connected regions large enough for credible screening are highlighted.</p>
    <div className="dated-image-grid">
      {[t1, t2].map(artifact => <figure className="dated-image" key={artifact.id}>
        <figcaption><span>{artifact.title}</span><b>{artifact.acquisition_time?.slice(0, 10)}</b></figcaption>
        <div className="raster-frame"><img src={artifact.url} alt={`${artifact.title} acquired ${artifact.acquisition_time?.slice(0, 10)}`} /></div>
        <small>{artifact.description}</small>
      </figure>)}
      <figure className="dated-image overlay-figure">
        <figcaption><span>Change categories on latest image</span><b>{t2.acquisition_time?.slice(0, 10)}</b></figcaption>
        <div className="raster-frame evidence-overlay">
          <img src={t2.url} alt="T2 true-color base" />
          <img className="change-pixels" style={{ opacity: opacity / 100 }} src={change.url} alt="Thresholded change pixels aligned over T2" />
          {regions.slice(0, 8).map((region, index) => <button
            type="button"
            className={`region-marker ${region.category} ${selected?.id === region.id ? 'selected' : ''}`}
            style={{ left: `${region.centroid_x_pct}%`, top: `${region.centroid_y_pct}%` }}
            aria-label={`Inspect region ${index + 1}: ${categoryText[region.category]}, ${region.area_ha} hectares`}
            onClick={() => setSelectedRegion(region.id)}
            key={region.id}
          >{index + 1}</button>)}
        </div>
        <label className="opacity-control">Overlay opacity <input aria-label="Change overlay opacity" type="range" min="0" max="100" value={opacity} onChange={event => setOpacity(Number(event.target.value))} /><output>{opacity}%</output></label>
      </figure>
    </div>
    <div className="artifact-legend">{change.legend.map(item => <span key={item.label}><i style={{ backgroundColor: item.color }} />{item.label}</span>)}<small>{change.width} × {change.height} analytical pixels · georeferenced to the selected area</small></div>
    {selected ? <section className="region-inspector" aria-live="polite">
      <div><span>SELECTED CHANGE REGION</span><strong>{categoryText[selected.category]}</strong></div>
      <div><span>AREA</span><strong>{selected.area_ha.toFixed(2)} ha</strong></div>
      <div><span>LOCATION IN SELECTION</span><strong>{selected.location}</strong></div>
      <p><b>{selected.temporal_status === 'repeated' ? `Repeated across dates (${(selected.repeated_area_ha ?? 0).toFixed(2)} ha of this region).` : selected.temporal_status === 'latest_only' ? 'Latest comparison only; not yet repeated.' : 'Temporal repetition was not calculated for this older result.'}</b>{' '}{selected.category === 'vegetation_to_bare_candidate'
        ? 'Vegetation decreased while the bare-surface signal increased. This is consistent with clearing, exposed soil, harvest, or earthworks.'
        : selected.category === 'built_up_like_candidate'
          ? 'The spectral response shifted toward built or hardened surfaces. Confirm with later observations or higher-resolution reference imagery.'
          : 'The surface changed enough to form a meaningful region, but it did not satisfy the clearing or built-up-like rules.'}</p>
    </section> : <p className="no-regions">No connected region passed the minimum size and category rules. Isolated pixels were excluded from the measured result.</p>}
  </section>
}
