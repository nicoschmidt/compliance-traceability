import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { api } from './api'
import { buildIndex } from './data/catalogue'
import { homeView, idKind, viewPath } from './data/ids'
import { IndexContext, SeedProvider, useIndex } from './state'
import { Workspace } from './components/Workspace'

/** /id/<ID>: opens an ID in its home view of the catalogue (permanent links from documents, mails, tickets). */
function IdRedirect() {
  const ix = useIndex()
  const id = decodeURIComponent(useLocation().pathname.replace(/^\/id\//, ''))
  const view = homeView(ix, id, idKind(ix, id), 'catalogue')
  return <Navigate to={view ? `${viewPath('catalogue', undefined, view)}?sel=${encodeURIComponent(id)}` : '/catalogue/CR'} replace />
}

export function App() {
  const q = useQuery({ queryKey: ['catalogue'], queryFn: api.catalogue, staleTime: Infinity })
  const ix = useMemo(() => (q.data ? buildIndex(q.data) : null), [q.data])
  if (q.isLoading) return <div className="splash">Loading catalogue…</div>
  if (!ix) return (
    <div className="splash warn">
      <p>Could not load the catalogue: {(q.error as Error)?.message}</p>
      <p className="muted">Start the API first: <code>python -m backend catalogue</code></p>
    </div>)
  return (
    <IndexContext.Provider value={ix}>
      <SeedProvider>
        <Routes>
          <Route path="/catalogue/:view" element={<Workspace mode="catalogue" />} />
          <Route path="/project/:pid/:view" element={<Workspace mode="project" />} />
          <Route path="/id/*" element={<IdRedirect />} />
          <Route path="*" element={<Navigate to="/catalogue/CR" replace />} />
        </Routes>
      </SeedProvider>
    </IndexContext.Provider>
  )
}
