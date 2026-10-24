// Shared state: catalogue index, uploaded seeds, the current view (for ID links) and per-viewer preferences.
import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'
import type { ProjectSeed } from './api'
import type { Index } from './data/catalogue'
import type { RouteCtx } from './data/ids'
import type { ProjectCtx } from './data/tree'

export const IndexContext = createContext<Index | null>(null)

export function useIndex(): Index {
  const ix = useContext(IndexContext)
  if (!ix) throw new Error('catalogue not loaded')
  return ix
}

export interface ViewState extends RouteCtx {
  project?: ProjectCtx
  projectIds?: { cis: Set<string>; objects: Set<string> }
}

export const ViewContext = createContext<ViewState>({ mode: 'catalogue', view: '', viewIds: new Set(), search: '' })
export const useView = () => useContext(ViewContext)

// ------------------------------------------------------------------------------------------------ uploaded seeds
const SEED_KEY = 'ctm.seeds'

function readSeeds(): Record<string, ProjectSeed> {
  try { return JSON.parse(sessionStorage.getItem(SEED_KEY) || '{}') } catch { return {} }
}

interface SeedStore { seeds: Record<string, ProjectSeed>; add: (s: ProjectSeed) => void; remove: (pid: string) => void }
const SeedContext = createContext<SeedStore>({ seeds: {}, add: () => {}, remove: () => {} })
export const useSeeds = () => useContext(SeedContext)

export function SeedProvider({ children }: { children: ReactNode }) {
  const [seeds, setSeeds] = useState<Record<string, ProjectSeed>>(readSeeds)
  const save = (s: Record<string, ProjectSeed>) => {
    try { sessionStorage.setItem(SEED_KEY, JSON.stringify(s)) } catch { /* storage unavailable */ }
    return s
  }
  const add = useCallback((s: ProjectSeed) => setSeeds(old => save({ ...old, [s.prj.project_id]: s })), [])
  const remove = useCallback((pid: string) => setSeeds(old => {
    const n = { ...old }; delete n[pid]; return save(n)
  }), [])
  return <SeedContext.Provider value={{ seeds, add, remove }}>{children}</SeedContext.Provider>
}

// ------------------------------------------------------------------------------------------------ preferences
export function usePref<T>(key: string, initial: T): [T, (v: T) => void] {
  const [v, setV] = useState<T>(() => {
    try {
      const s = localStorage.getItem(`ctm.${key}`)
      return s === null ? initial : (JSON.parse(s) as T)
    } catch { return initial }
  })
  const set = useCallback((x: T) => {
    setV(x)
    try { localStorage.setItem(`ctm.${key}`, JSON.stringify(x)) } catch { /* storage unavailable */ }
  }, [key])
  return [v, set]
}
