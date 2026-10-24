import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useRef, useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { api, type ProjectSeed } from '../api'
import { tagQuery, viewPath } from '../data/ids'
import { useIndex, useSeeds, useView } from '../state'

function Item({ to, label, sub, count, disabled }: { to: string; label: string; sub?: string; count?: number; disabled?: boolean }) {
  if (disabled) return <div className="nav-item disabled" title="not loaded">{label}<span className="nav-sub">{sub}</span></div>
  return (
    <NavLink to={to} className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`} title={sub}>
      <span className="nav-label">{label}</span>
      {count !== undefined && <span className="nav-count">{count}</span>}
      {sub && <span className="nav-sub">{sub}</span>}
    </NavLink>
  )
}

export function NavPane() {
  const ix = useIndex()
  const v = useView()
  const nav = useNavigate()
  const qc = useQueryClient()
  const { seeds, add } = useSeeds()
  const projects = useQuery({ queryKey: ['projects'], queryFn: api.projects })
  const file = useRef<HTMLInputElement>(null)
  const [err, setErr] = useState('')
  const [reloading, setReloading] = useState(false)
  const nSr = (sd: string) => [...ix.srSd.values()].filter(x => x === sd).length

  const load = async (f: File) => {
    setErr('')
    try {
      const s = JSON.parse(await f.text()) as ProjectSeed
      if (!s?.prj?.project_id) throw new Error('not a project seed (prj.project_id missing)')
      delete (s as unknown as Record<string, unknown>)['$schema']
      add(s)
      nav(viewPath('project', s.prj.project_id, s.basis?.[0]?.sd_id || 'CR'))
    } catch (e) { setErr(`${f.name}: ${(e as Error).message}`) }
  }

  const reload = async () => {
    setReloading(true)
    try { await api.reload(); await qc.invalidateQueries() } catch (e) { setErr((e as Error).message) } finally { setReloading(false) }
  }

  const ev = v.project?.ev
  const pq = v.mode === 'project' ? tagQuery(v.search) : ''
  const cq = v.mode === 'catalogue' ? tagQuery(v.search) : ''
  const server = projects.data || []
  const uploaded = Object.keys(seeds).filter(pid => !server.some(p => p.project_id === pid))

  return (
    <nav className="nav">
      {ev && (
        <section>
          <h3>Project {ev.seed.prj.project_id}</h3>
          <div className="nav-note">{ev.seed.prj.product}</div>
          {ev.basis.map(b => (
            <Item key={b.sd_id} to={viewPath('project', v.pid, b.sd_id) + pq}
              label={b.sd_id} sub={ix.sdById.get(b.sd_id)?.title} disabled={ev.missing_sources.includes(b.sd_id)}
              count={new Set(ev.views[b.sd_id]?.filter(r => r.ci_id).map(r => r.ci_id)).size} />
          ))}
          <Item to={viewPath('project', v.pid, 'CR') + pq} label="Selected CRs" count={ev.counts.cr} />
          <Item to={viewPath('project', v.pid, 'OBJ') + pq} label="Objects & check items" count={ev.counts.ci} />
          <Item to={viewPath('catalogue', undefined, 'CR')} label="← back to catalogue" />
        </section>
      )}
      <section>
        <h3>Catalogue <span className="muted small">{ix.data.meta.baseline}</span></h3>
        <Item to={viewPath('catalogue', undefined, 'CR') + cq} label="Master list (CRs)" count={ix.data.tables.CR.length} />
        {ix.sds.map(s => (
          <Item key={s.sd_id} to={viewPath('catalogue', undefined, s.sd_id) + cq}
            label={s.sd_id + (ix.licensed.has(s.sd_id) ? ' 🔒' : '')} sub={s.title} count={nSr(s.sd_id)} />
        ))}
        <Item to={viewPath('catalogue', undefined, 'DEC')} label="Decisions" count={ix.data.tables.DECISIONS.length} />
        {ix.data.meta.missing_packs.length > 0 && <div className="nav-note warn">Not loaded: {ix.data.meta.missing_packs.join(', ')}</div>}
      </section>
      <section>
        <h3>Projects</h3>
        {projects.isError && <div className="nav-note warn">{(projects.error as Error).message}</div>}
        {server.map(p => p.error
          ? <div key={p.file} className="nav-item disabled" title={p.error}>{p.project_id} <span className="warn small">invalid</span></div>
          : <Item key={p.project_id} to={viewPath('project', p.project_id, p.basis?.[0] || 'CR')} label={p.project_id} sub={p.product} />)}
        {uploaded.map(pid => (
          <Item key={pid} to={viewPath('project', pid, seeds[pid].basis?.[0]?.sd_id || 'CR')} label={`${pid} (file)`} sub={seeds[pid].prj.product} />
        ))}
        <button className="nav-btn" onClick={() => file.current?.click()}>Load seed JSON…</button>
        <input ref={file} type="file" accept=".json,application/json" hidden
          onChange={e => { const f = e.target.files?.[0]; if (f) load(f); e.target.value = '' }} />
        {err && <div className="nav-note warn">{err}</div>}
      </section>
      <section className="nav-foot">
        <button className="nav-btn" onClick={reload} disabled={reloading}>{reloading ? 'Reloading…' : 'Reload catalogue'}</button>
        <div className="nav-note">{ix.data.meta.packs.map(p => p.pack_id).join(' · ')}{ix.data.meta.internal ? ' · internal' : ''}</div>
        {ix.data.meta.load_errors.length > 0 && <div className="nav-note warn">{ix.data.meta.load_errors.length} load errors</div>}
      </section>
    </nav>
  )
}
