import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useDeferredValue, useMemo, useState } from 'react'
import { Navigate, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api, type ProjectSeed } from '../api'
import { readTags, writeTags, type Mode } from '../data/ids'
import {
  buildCrTree, buildDecisionList, buildDocTree, buildObjectTree, collectIds, filterTree, projectCtx, searchTree,
} from '../data/tree'
import { useIndex, usePref, useSeeds, ViewContext, type ViewState } from '../state'
import { DetailPane } from './DetailPane'
import { FilterBar, type Toggles } from './FilterBar'
import { NavPane } from './NavPane'
import { Panes } from './Panes'
import { TreePane } from './TreePane'

function useSeed(pid: string | undefined) {
  const { seeds } = useSeeds()
  const local = pid ? seeds[pid] : undefined
  const q = useQuery({ queryKey: ['seed', pid], queryFn: () => api.project(pid!), enabled: !!pid && !local, retry: false })
  return { seed: local ?? q.data, error: local ? null : q.error as Error | null, loading: !local && q.isLoading }
}

export function Workspace({ mode }: { mode: Mode }) {
  const ix = useIndex()
  const { pid, view = 'CR' } = useParams()
  const [params, setParams] = useSearchParams()
  const loc = useLocation()
  const nav = useNavigate()
  const sel = params.get('sel')
  const tags = useMemo(() => readTags(params), [params])
  const tagKey = JSON.stringify(tags)
  const [query, setQuery] = useState('')
  const deferredQuery = useDeferredValue(query)
  const [toggles, setToggles] = usePref<Toggles>(`toggles.${mode}`,
    { showNA: false, onlyWithReqs: mode === 'project', allLinks: false })

  // ---- project evaluation (seed + tag overrides) or catalogue filter (tags)
  const { seed, error: seedError, loading: seedLoading } = useSeed(mode === 'project' ? pid : undefined)
  const evq = useQuery({
    queryKey: ['evaluate', pid, seed, tagKey], queryFn: () => api.evaluate(seed as ProjectSeed, tags),
    enabled: mode === 'project' && !!seed, placeholderData: keepPreviousData, retry: false,
  })
  const ev = mode === 'project' ? evq.data : undefined
  const isDoc = ix.sdById.has(view)
  const basis = isDoc ? [view] : ix.sds.map(s => s.sd_id)
  const filtering = mode === 'catalogue' && Object.values(tags).some(Boolean) && view !== 'DEC'
  const apq = useQuery({
    queryKey: ['applicability', basis.join(','), tagKey], queryFn: () => api.applicability(basis, tags),
    enabled: filtering, placeholderData: keepPreviousData, retry: false,
  })
  const applic = filtering ? apq.data?.crs ?? null : null

  const ctx = useMemo(() => (ev ? projectCtx(ev) : undefined), [ev])
  const tree = useMemo(() => {
    if (mode === 'project') {
      if (!ctx) return []
      if (view === 'CR') return buildCrTree(ix, { project: ctx })
      if (view === 'OBJ') return buildObjectTree(ix, ctx)
      return buildDocTree(ix, view, { project: ctx })
    }
    if (view === 'DEC') return buildDecisionList(ix)
    if (view === 'CR') return buildCrTree(ix, { applic })
    return buildDocTree(ix, view, { applic, allLinks: toggles.allLinks })
  }, [ix, mode, view, ctx, applic, toggles.allLinks])
  const filtered = useMemo(() => filterTree(tree, {
    active: mode === 'project' || !!applic, showNA: toggles.showNA, onlyWithReqs: isDoc && toggles.onlyWithReqs,
  }), [tree, mode, applic, toggles, isDoc])
  const searched = useMemo(() => searchTree(filtered, deferredQuery), [filtered, deferredQuery])
  const viewIds = useMemo(() => collectIds(tree), [tree])
  const shownIds = useMemo(() => collectIds(searched.nodes), [searched.nodes])

  const viewState: ViewState = useMemo(() => ({
    mode, pid, view, viewIds, search: loc.search, project: ctx,
    basis: ev ? new Set(ev.basis.map(b => b.sd_id)) : undefined,
    projectIds: ev ? { cis: new Set(ev.cis.map(c => c.ci_id)), objects: new Set(ev.objects.map(o => o.object_id)) } : undefined,
  }), [mode, pid, view, viewIds, loc.search, ctx, ev])

  if (mode === 'catalogue' && !isDoc && view !== 'CR' && view !== 'DEC') return <Navigate to="/catalogue/CR" replace />

  const select = (id: string) => {
    const n = new URLSearchParams(params)
    n.set('sel', id)
    setParams(n)
  }
  const setTags = (t: Record<string, string>) => setParams(writeTags(params, t))
  const download = () => {
    if (!ev) return
    const blob = new Blob([JSON.stringify(ev.seed, null, 2) + '\n'], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `${ev.seed.prj.project_id}.json`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  const title = mode === 'project'
    ? `${pid} · ${view === 'CR' ? 'Selected CRs' : view === 'OBJ' ? 'Objects & check items' : view}`
    : view === 'CR' ? 'Master list' : view === 'DEC' ? 'Decisions' : view
  const sub = isDoc ? ix.sdById.get(view)?.title : view === 'CR' && mode === 'catalogue' ? ix.data.meta.title : ''

  let middle
  if (mode === 'project' && (seedLoading || (!ev && evq.isLoading))) middle = <div className="tree-empty">Loading project…</div>
  else if (mode === 'project' && (seedError || !seed)) middle = (
    <div className="tree-empty warn">Project {pid} not found{seedError ? `: ${seedError.message}` : ''}.
      <button className="link" onClick={() => nav('/catalogue/CR')}>Back to the catalogue</button></div>)
  else if (mode === 'project' && !ev && evq.error) middle = <div className="tree-empty warn pre">{(evq.error as Error).message}</div>
  else middle = (
    <TreePane key={`${mode}/${pid}/${view}`} nodes={searched.nodes} selected={sel} onSelect={select}
      forceOpen={searched.expand} empty={deferredQuery ? 'No matches.' : 'No applicable items.'} />)

  return (
    <ViewContext.Provider value={viewState}>
      <Panes
        left={<NavPane />}
        middle={
          <div className="middle">
            <div className="pane-head">
              <h1>{title}</h1>
              {sub && <div className="pane-sub">{sub}</div>}
            </div>
            {view !== 'DEC' && (
              <FilterBar query={query} onQuery={setQuery} hits={searched.hits} toggles={toggles} onToggles={setToggles}
                isDoc={isDoc} isProject={mode === 'project'} base={ev?.seed.tags && seed ? seed.tags : {}} tags={tags}
                onTags={setTags} onDownload={download} busy={evq.isFetching || apq.isFetching}
                error={(evq.error as Error | null)?.message || (apq.error as Error | null)?.message} />
            )}
            {view === 'DEC' && (
              <div className="filterbar"><input className="search" type="search" placeholder="Search decisions…" value={query}
                onChange={e => setQuery(e.target.value)} /></div>
            )}
            {middle}
          </div>
        }
        right={<DetailPane sel={sel} view={view} hidden={!!sel && viewIds.has(sel) && !shownIds.has(sel)} />}
      />
    </ViewContext.Provider>
  )
}
