import { useMemo, useState } from 'react'
import { useIndex } from '../state'

export interface Toggles { showNA: boolean; onlyWithReqs: boolean; allLinks: boolean }

interface Props {
  query: string
  onQuery: (q: string) => void
  hits?: number
  toggles: Toggles
  onToggles: (t: Toggles) => void
  isDoc: boolean
  isProject: boolean
  base: Record<string, string>                 // project: tags of the seed
  tags: Record<string, string>                 // catalogue: filter tags; project: overrides
  onTags: (t: Record<string, string>) => void
  onDownload?: () => void
  busy?: boolean
  error?: string
}

/** Search, display toggles and the tag panel (applicability filter / project tag overrides). */
export function FilterBar(p: Props) {
  const ix = useIndex()
  const [open, setOpen] = useState(false)
  const groups = useMemo(() => {
    const g = new Map<string, { tag: string; desc: string; values: string[] }[]>()
    for (const e of ix.vocab.TAG || []) {
      const [grp, desc] = (e.desc || '').split(' | ')
      const values = (ix.vocab[e.attr] || []).map(x => x.label)
      g.set(grp, [...(g.get(grp) || []), { tag: e.label, desc: desc || '', values }])
    }
    return [...g.entries()]
  }, [ix])
  const effective = p.isProject ? { ...p.base, ...p.tags } : p.tags
  const nSet = Object.values(effective).filter(Boolean).length
  const nOverride = Object.keys(p.tags).length
  const set = (tag: string, value: string) => {
    const n = { ...p.tags }
    if (p.isProject) {
      if (value === (p.base[tag] || '')) delete n[tag]; else n[tag] = value
    } else if (value) n[tag] = value; else delete n[tag]
    p.onTags(n)
  }
  const t = p.toggles
  return (
    <div className="filterbar">
      <div className="filter-row">
        <input className="search" type="search" placeholder="Search IDs, headings, text…" value={p.query}
          onChange={e => p.onQuery(e.target.value)} />
        {p.query && <span className="muted small">{p.hits} hits</span>}
        <button className={`tag-btn${open ? ' on' : ''}${nSet ? ' active' : ''}`} onClick={() => setOpen(!open)}
          title="Scoping tags: items whose applicability rule is not met are hidden">
          Tags{nSet ? ` (${nSet}${p.isProject && nOverride ? `, ${nOverride} changed` : ''})` : ''} {open ? '▴' : '▾'}
        </button>
        {p.busy && <span className="muted small">evaluating…</span>}
      </div>
      <div className="filter-row toggles">
        <label><input type="checkbox" checked={t.showNA} onChange={e => p.onToggles({ ...t, showNA: e.target.checked })} /> show N/A</label>
        {p.isDoc && <label><input type="checkbox" checked={t.onlyWithReqs} onChange={e => p.onToggles({ ...t, onlyWithReqs: e.target.checked })} /> only provisions with requirements</label>}
        {!p.isProject && p.isDoc && <label><input type="checkbox" checked={t.allLinks} onChange={e => p.onToggles({ ...t, allLinks: e.target.checked })} /> non-counting links</label>}
      </div>
      {p.error && <div className="warn small pre">{p.error}</div>}
      {open && (
        <div className="tagpanel">
          <div className="tag-actions">
            {p.isProject
              ? <><button disabled={!nOverride} onClick={() => p.onTags({})}>Reset to seed</button>
                <button onClick={p.onDownload}>Download seed with these tags</button></>
              : <button disabled={!nSet} onClick={() => p.onTags({})}>Clear filter</button>}
            <span className="muted small">{p.isProject ? 'Changes are temporary overrides of the seed.' : 'Unset tags count as undetermined (shown with ?).'}</span>
          </div>
          {groups.map(([grp, tags]) => (
            <fieldset key={grp}>
              <legend>{grp}</legend>
              {tags.map(x => {
                const val = effective[x.tag] || ''
                const changed = p.isProject && x.tag in p.tags
                return (
                  <label key={x.tag} className={`tag${changed ? ' changed' : ''}`} title={x.desc}>
                    <span className="tag-name">{x.tag}</span>
                    <select value={val} onChange={e => set(x.tag, e.target.value)}>
                      <option value="">—</option>
                      {x.values.map(v => <option key={v} value={v}>{v}</option>)}
                    </select>
                  </label>
                )
              })}
            </fieldset>
          ))}
        </div>
      )}
    </div>
  )
}
