import { useEffect, useRef } from 'react'

type Props = { grid: number[][]; mode: 'ndvi' | 'delta' | 'change'; label: string; detail: string; validMask?: number[][] }

export function EvidenceCanvas({ grid, mode, label, detail, validMask }: Props) {
  const ref = useRef<HTMLCanvasElement>(null)
  useEffect(() => {
    const canvas = ref.current
    if (!canvas || !grid.length) return
    const rows = grid.length
    const columns = grid[0]?.length ?? 0
    const scale = Math.max(1, Math.floor(768 / Math.max(rows, columns)))
    canvas.width = columns * scale
    canvas.height = rows * scale
    const context = canvas.getContext('2d')
    if (!context) return
    grid.forEach((row, y) => row.forEach((value, x) => {
      if (validMask && !validMask[y]?.[x]) context.fillStyle = '#777b75'
      else if (mode === 'delta') context.fillStyle = value <= -0.12 ? '#d95f3f' : value >= 0.12 ? '#c9e56c' : '#d8d5c8'
      else if (mode === 'change') context.fillStyle = value >= 0.12 ? '#df7043' : '#d8d5c8'
      else {
        const portion = Math.max(0, Math.min(1, (value + 0.1) / 0.8))
        context.fillStyle = `rgb(${190 - 120 * portion},${150 + 80 * portion},${92 - 45 * portion})`
      }
      context.fillRect(x * scale, y * scale, scale, scale)
    }))
  }, [grid, mode, validMask])
  return <figure><figcaption><span>{label}</span><b>{detail}</b></figcaption><canvas ref={ref} /></figure>
}
