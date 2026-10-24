import { useRef, type ReactNode } from 'react'
import { usePref } from '../state'

/** Three resizable columns: navigation | tree | detail (widths remembered per viewer). */
export function Panes({ left, middle, right }: { left: ReactNode; middle: ReactNode; right: ReactNode }) {
  const [w, setW] = usePref('panes', { left: 250, right: 520 })
  const root = useRef<HTMLDivElement>(null)
  const drag = (side: 'left' | 'right') => (e: React.PointerEvent) => {
    e.preventDefault()
    const x0 = e.clientX, w0 = w[side]
    const move = (ev: PointerEvent) => {
      const d = side === 'left' ? ev.clientX - x0 : x0 - ev.clientX
      setW({ ...w, [side]: Math.max(160, Math.min(w0 + d, (root.current?.clientWidth || 1600) * 0.6)) })
    }
    const up = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up) }
    window.addEventListener('pointermove', move)
    window.addEventListener('pointerup', up)
  }
  return (
    <div className="panes" ref={root} style={{ gridTemplateColumns: `${w.left}px 5px minmax(280px, 1fr) 5px ${w.right}px` }}>
      <aside className="pane pane-left">{left}</aside>
      <div className="splitter" onPointerDown={drag('left')} />
      <main className="pane pane-middle">{middle}</main>
      <div className="splitter" onPointerDown={drag('right')} />
      <aside className="pane pane-right">{right}</aside>
    </div>
  )
}
