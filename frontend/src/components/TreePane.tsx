import { useVirtualizer } from '@tanstack/react-virtual'
import { useEffect, useMemo, useRef, useState } from 'react'
import { flatten, pathTo, type Row, type TreeNode } from '../data/tree'

const ROW = 26
const KIND_LABEL: Record<string, string> = { sp: 'SP', sr: 'SR', cr: 'CR', ci: 'CI', obj: 'OBJ', dec: 'D', group: '' }
const STATUS_LABEL: Record<string, string> = { ok: '✓', na: 'N/A', unknown: '?', subst: 'substituted' }

interface Props {
  nodes: TreeNode[]
  selected: string | null
  onSelect: (id: string) => void
  forceOpen?: Set<string>          // search: keys that must be open
  empty?: string
}

export function TreePane({ nodes, selected, onSelect, forceOpen, empty }: Props) {
  const [open, setOpen] = useState<Set<string>>(() => new Set())
  const [selKey, setSelKey] = useState<string | null>(null)
  const scroller = useRef<HTMLDivElement>(null)
  const isOpen = (k: string) => open.has(k) || !!forceOpen?.has(k)
  const rows = useMemo(() => flatten(nodes, isOpen), [nodes, open, forceOpen]) 
  const virt = useVirtualizer({ count: rows.length, getScrollElement: () => scroller.current, estimateSize: () => ROW, overscan: 20 })

  // reveal the selected ID (from a link or the URL) unless the clicked row already shows it
  useEffect(() => {
    if (!selected) { setSelKey(null); return }
    const cur = selKey ? rows.find(r => r.node.key === selKey) : undefined
    if (cur && cur.node.id === selected) return
    const path = pathTo(nodes, selected)
    if (!path) { setSelKey(null); return }
    const key = path[path.length - 1]
    setSelKey(key)
    setOpen(o => {
      const n = new Set(o)
      path.slice(0, -1).forEach(k => n.add(k))
      return n
    })
  }, [selected, nodes]) 

  useEffect(() => {
    if (!selKey) return
    const i = rows.findIndex(r => r.node.key === selKey)
    if (i >= 0) virt.scrollToIndex(i, { align: 'auto' })
  }, [selKey, rows.length]) 

  const toggle = (k: string, v?: boolean) => setOpen(o => {
    const n = new Set(o)
    if (v ?? !n.has(k)) n.add(k); else n.delete(k)
    return n
  })
  const choose = (r: Row) => { setSelKey(r.node.key); if (r.node.kind !== 'group') onSelect(r.node.id) }

  const expandAll = (v: boolean) => {
    if (!v) { setOpen(new Set()); return }
    const n = new Set<string>()
    const walk = (ns: TreeNode[]) => ns.forEach(x => { if (x.children.length && x.kind !== 'cr') { n.add(x.key); walk(x.children) } })
    walk(nodes)
    setOpen(n)
  }

  const onKey = (e: React.KeyboardEvent) => {
    const i = rows.findIndex(r => r.node.key === selKey)
    const r = rows[i]
    const go = (j: number) => { if (rows[j]) { choose(rows[j]); virt.scrollToIndex(j) } }
    switch (e.key) {
      case 'ArrowDown': go(i < 0 ? 0 : i + 1); break
      case 'ArrowUp': go(Math.max(0, i - 1)); break
      case 'ArrowRight':
        if (!r) return
        if (r.node.children.length && !r.open) toggle(r.node.key, true); else go(i + 1)
        break
      case 'ArrowLeft':
        if (!r) return
        if (r.open) toggle(r.node.key, false)
        else if (r.parent) go(rows.findIndex(x => x.node.key === r.parent))
        break
      default: return
    }
    e.preventDefault()
  }

  if (!rows.length) return <div className="tree-empty">{empty ?? 'Nothing to show.'}</div>

  return (
    <div className="tree">
      <div className="tree-tools">
        <button onClick={() => expandAll(true)} title="Expand all levels down to the requirements">Expand</button>
        <button onClick={() => expandAll(false)}>Collapse</button>
        <span className="muted">{rows.length} rows</span>
      </div>
      <div className="tree-scroll" ref={scroller} tabIndex={0} onKeyDown={onKey} role="tree">
        <div style={{ height: virt.getTotalSize(), position: 'relative' }}>
          {virt.getVirtualItems().map(v => {
            const r = rows[v.index]
            const n = r.node
            return (
              <div key={n.key} role="treeitem" aria-expanded={n.children.length ? r.open : undefined}
                aria-selected={n.key === selKey}
                className={`row kind-${n.kind}${n.key === selKey ? ' selected' : ''}${n.muted ? ' muted-row' : ''}`}
                style={{ transform: `translateY(${v.start}px)`, height: ROW, paddingLeft: 6 + r.depth * 16 }}
                onClick={() => choose(r)} onDoubleClick={() => n.children.length && toggle(n.key)}>
                <span className={`chev${n.children.length ? '' : ' none'}`}
                  onClick={e => { e.stopPropagation(); if (n.children.length) toggle(n.key) }}>
                  {n.children.length ? (r.open ? '▾' : '▸') : ''}
                </span>
                {KIND_LABEL[n.kind] && <span className={`kind k-${n.kind}`}>{KIND_LABEL[n.kind]}</span>}
                {n.status && <span className={`status s-${n.status}`} title={n.statusTip}>{STATUS_LABEL[n.status]}</span>}
                <span className={n.kind === 'group' ? 'group-title' : 'title'}>{n.title}</span>
                {n.badge && <span className="badge" style={n.badgeColour ? { borderColor: `#${n.badgeColour}` } : undefined}>{n.badge}</span>}
                {n.condition && <span className="cond" title={`Condition: ${n.condition}`}>if</span>}
                <span className="text">{n.text}</span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
