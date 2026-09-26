import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { GeoJSONSource, Map, MapMouseEvent } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import type { Polygon, Position } from '../types'

maplibregl.setWorkerUrl(workerUrl)

type Props = { aoi: Polygon; onAoiChange: (aoi: Polygon) => void; disabled?: boolean }
type Cursor = { longitude: number; latitude: number; x: number; y: number; precision: number }
type Basemap = 'satellite' | 'streets' | 'bhuvan'

const bhuvanTileUrl = import.meta.env.VITE_BHUVAN_WMS_TILE_URL as string | undefined

function rectangle(first: Position, second: Position): Polygon {
  const west = Math.min(first[0], second[0]), east = Math.max(first[0], second[0])
  const south = Math.min(first[1], second[1]), north = Math.max(first[1], second[1])
  return { type: 'Polygon', coordinates: [[[west, south], [east, south], [east, north], [west, north], [west, south]]] }
}

function boundsOf(aoi: Polygon) {
  return aoi.coordinates[0].reduce(
    (bounds, point) => bounds.extend(point),
    new maplibregl.LngLatBounds(aoi.coordinates[0][0], aoi.coordinates[0][0]),
  )
}

function feature(aoi: Polygon | null): GeoJSON.FeatureCollection {
  return { type: 'FeatureCollection', features: aoi ? [{ type: 'Feature', properties: {}, geometry: aoi }] : [] }
}

export function MapPreview({ aoi, onAoiChange, disabled = false }: Props) {
  const container = useRef<HTMLDivElement>(null)
  const mapRef = useRef<Map | null>(null)
  const aoiRef = useRef(aoi)
  const onChangeRef = useRef(onAoiChange)
  const enabledRef = useRef(false)
  const startRef = useRef<Position | null>(null)
  const releaseRef = useRef<(() => void) | null>(null)
  const restoreGesturesRef = useRef<(() => void) | null>(null)
  const [ready, setReady] = useState(false)
  const [enabled, setEnabledState] = useState(false)
  const [preview, setPreview] = useState<Polygon | null>(null)
  const [cursor, setCursor] = useState<Cursor | null>(null)
  const [basemap, setBasemap] = useState<Basemap>('satellite')
  const [tileError, setTileError] = useState(false)

  function setDrawingEnabled(next: boolean) {
    releaseRef.current?.()
    enabledRef.current = next
    startRef.current = null
    setPreview(null)
    setEnabledState(next)
    const map = mapRef.current
    if (!map) return
    map.getCanvas().style.cursor = next ? 'crosshair' : ''
    if (next && !restoreGesturesRef.current) {
      map.stop()
      const gestures = [map.dragPan, map.dragRotate, map.boxZoom, map.doubleClickZoom, map.scrollZoom, map.touchZoomRotate, map.touchPitch, map.keyboard]
      const enabledGestures = gestures.filter(gesture => gesture.isEnabled())
      gestures.forEach(gesture => gesture.disable())
      restoreGesturesRef.current = () => enabledGestures.forEach(gesture => gesture.enable())
    } else if (!next) {
      restoreGesturesRef.current?.()
      restoreGesturesRef.current = null
    }
    map.getCanvas().style.touchAction = next ? 'none' : ''
  }

  useEffect(() => { aoiRef.current = aoi }, [aoi])
  useEffect(() => { onChangeRef.current = onAoiChange }, [onAoiChange])
  useEffect(() => { if (disabled) setDrawingEnabled(false) }, [disabled])

  useEffect(() => {
    if (!container.current) return
    const map = new maplibregl.Map({
      container: container.current,
      style: { version: 8, sources: {
        osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors' },
        satellite: { type: 'raster', tiles: [import.meta.env.VITE_SATELLITE_TILE_URL || 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'], tileSize: 256, maxzoom: 19, attribution: import.meta.env.VITE_SATELLITE_ATTRIBUTION || 'Powered by Esri | Sources: Esri, Maxar, Earthstar Geographics, and the GIS User Community' },
        ...(bhuvanTileUrl ? { bhuvan: { type: 'raster' as const, tiles: [bhuvanTileUrl], tileSize: 256, attribution: 'Bhuvan / NRSC / ISRO' } } : {}),
      }, layers: [{ id: 'osm', type: 'raster', source: 'osm', layout: { visibility: 'none' } }, { id: 'satellite', type: 'raster', source: 'satellite' }, ...(bhuvanTileUrl ? [{ id: 'bhuvan', type: 'raster' as const, source: 'bhuvan', layout: { visibility: 'none' as const } }] : [])] },
      bounds: boundsOf(aoiRef.current), fitBoundsOptions: { padding: 72 }, attributionControl: {},
      renderWorldCopies: false,
    })
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    map.on('error', event => { if ('sourceId' in event && event.sourceId === 'satellite') setTileError(true) })
    map.on('style.load', () => {
      map.addSource('aoi', { type: 'geojson', data: feature(aoiRef.current) })
      map.addLayer({ id: 'aoi-fill', type: 'fill', source: 'aoi', paint: { 'fill-color': '#c9e56c', 'fill-opacity': 0.38 } })
      map.addLayer({ id: 'aoi-line', type: 'line', source: 'aoi', paint: { 'line-color': '#f3ffca', 'line-width': 3 } })
      map.addSource('rectangle-preview', { type: 'geojson', data: feature(null) })
      map.addLayer({ id: 'rectangle-preview-fill', type: 'fill', source: 'rectangle-preview', paint: { 'fill-color': '#df7043', 'fill-opacity': 0.25 } })
      map.addLayer({ id: 'rectangle-preview-line', type: 'line', source: 'rectangle-preview', paint: { 'line-color': '#df7043', 'line-width': 3, 'line-dasharray': [2, 1] } })
      setReady(true)
    })
    let cursorPoint: { x: number; y: number } | null = null
    const refreshCursor = () => {
      if (!cursorPoint) return
      const location = map.unproject([cursorPoint.x, cursorPoint.y])
      // Show approximately one tenth of a screen pixel in angular precision.
      const precision = Math.max(0, Math.min(7, Math.ceil(Math.log10(512 * 2 ** map.getZoom() / 360)) + 1))
      setCursor({ longitude: location.wrap().lng, latitude: location.lat, ...cursorPoint, precision })
    }
    map.on('mousemove', (event: MapMouseEvent) => {
      cursorPoint = { x: event.point.x, y: event.point.y }
      refreshCursor()
    })
    map.on('move', refreshCursor)
    map.on('mouseout', () => { cursorPoint = null; setCursor(null) })
    const canvas = map.getCanvas()
    let pointer: number | null = null
    let startPixel: [number, number] | null = null
    const position = (event: PointerEvent): Position => {
      const rect = canvas.getBoundingClientRect()
      const point = map.unproject([Math.max(0, Math.min(rect.width, event.clientX - rect.left)), Math.max(0, Math.min(rect.height, event.clientY - rect.top))])
      return [Math.max(-180, Math.min(180, point.lng)), point.lat]
    }
    const down = (event: PointerEvent) => {
      if (!enabledRef.current || event.button !== 0 || pointer !== null) return
      event.preventDefault()
      pointer = event.pointerId
      startPixel = [event.clientX, event.clientY]
      canvas.setPointerCapture(pointer)
      startRef.current = position(event)
      setPreview(rectangle(startRef.current, startRef.current))
    }
    const move = (event: PointerEvent) => {
      if (event.pointerId === pointer && startRef.current) setPreview(rectangle(startRef.current, position(event)))
    }
    const release = () => {
      const previous = pointer
      pointer = null
      if (previous !== null && canvas.hasPointerCapture(previous)) canvas.releasePointerCapture(previous)
    }
    releaseRef.current = release
    const cancel = () => { release(); setDrawingEnabled(false) }
    const up = (event: PointerEvent) => {
      if (event.pointerId !== pointer) return
      if (!enabledRef.current || !startRef.current) { release(); return }
      const completed = rectangle(startRef.current, position(event))
      const ring = completed.coordinates[0]
      const hasArea = ring[0][0] !== ring[2][0] && ring[0][1] !== ring[2][1]
        && startPixel !== null && Math.abs(event.clientX - startPixel[0]) >= 4 && Math.abs(event.clientY - startPixel[1]) >= 4
      if (hasArea) onChangeRef.current(completed)
      cancel()
    }
    const keydown = (event: KeyboardEvent) => { if (event.key === 'Escape' && enabledRef.current) cancel() }
    const lostCapture = () => { if (pointer !== null) cancel() }
    canvas.addEventListener('pointerdown', down)
    canvas.addEventListener('pointermove', move)
    canvas.addEventListener('pointerup', up)
    canvas.addEventListener('pointercancel', cancel)
    canvas.addEventListener('lostpointercapture', lostCapture)
    window.addEventListener('keydown', keydown)
    window.addEventListener('blur', cancel)
    mapRef.current = map
    return () => {
      canvas.removeEventListener('pointerdown', down)
      canvas.removeEventListener('pointermove', move)
      canvas.removeEventListener('pointerup', up)
      canvas.removeEventListener('pointercancel', cancel)
      canvas.removeEventListener('lostpointercapture', lostCapture)
      window.removeEventListener('keydown', keydown)
      window.removeEventListener('blur', cancel)
      releaseRef.current = null
      restoreGesturesRef.current = null
      map.remove(); mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !ready) return
    if (aoi.coordinates[0].some(([lng, lat]) => !Number.isFinite(lng) || !Number.isFinite(lat) || Math.abs(lng) > 180 || Math.abs(lat) > 90)) return
    ;(map.getSource('aoi') as GeoJSONSource | undefined)?.setData(feature(aoi))
    map.fitBounds(boundsOf(aoi), { padding: 72, duration: 400 })
  }, [aoi, ready])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !ready) return
    ;(map.getSource('rectangle-preview') as GeoJSONSource | undefined)?.setData(feature(preview))
  }, [preview, ready])

  useEffect(() => {
    const map = mapRef.current
    if (!map || !ready) return
    map.setLayoutProperty('satellite', 'visibility', basemap === 'satellite' ? 'visible' : 'none')
    map.setLayoutProperty('osm', 'visibility', basemap === 'streets' ? 'visible' : 'none')
    if (bhuvanTileUrl) map.setLayoutProperty('bhuvan', 'visibility', basemap === 'bhuvan' ? 'visible' : 'none')
  }, [basemap, ready])

  const previewPoints = preview && mapRef.current ? preview.coordinates[0].map(point => {
    const projected = mapRef.current!.project(point)
    return `${projected.x},${projected.y}`
  }).join(' ') : null

  return <div className="map-panel">
    <div ref={container} className="map" />
    {previewPoints && <svg className="draw-overlay" aria-label="Rectangle being drawn" data-testid="draw-preview"><polygon points={previewPoints} /></svg>}
    <div className="rectangle-tool">
      <button type="button" disabled={disabled || !ready} aria-pressed={enabled} className={enabled ? 'active' : ''} onClick={() => setDrawingEnabled(!enabled)}>{enabled ? 'Cancel drawing' : 'Draw rectangle'}</button>
    </div>
    <div className="basemap-switch" aria-label="Basemap">{(['satellite', 'streets', ...(bhuvanTileUrl ? ['bhuvan' as const] : [])] as Basemap[]).map(value => <button type="button" key={value} disabled={!ready || enabled} aria-pressed={basemap === value} onClick={() => setBasemap(value)}>{value === 'satellite' ? 'Satellite' : value === 'bhuvan' ? 'Bhuvan layer' : 'Streets'}</button>)}</div>
    {tileError && basemap === 'satellite' && <div className="map-tile-error" role="status">Satellite tiles unavailable. Switch to Streets to continue.</div>}
    {enabled && <div className="draw-help" role="status">Drag from one corner to the opposite corner. Press Escape to cancel.</div>}
    {cursor && <div className="map-coordinate-tooltip" style={{ left: cursor.x + 14, top: cursor.y + 14 }}>{cursor.latitude.toFixed(cursor.precision)}°, {cursor.longitude.toFixed(cursor.precision)}°</div>}
    <div className="map-meta"><strong>{enabled ? 'Drawing your area' : 'Area of interest'}</strong><span>{enabled ? 'Release to select rectangle' : 'Basemap for context · acquisition date varies'}</span></div>
  </div>
}
