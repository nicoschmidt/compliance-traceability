// IDs in free text -> links; routes of the viewer.
import { kindOf, type EntityKind, type Index } from './catalogue'

export type Token = string | { id: string; text: string }

const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

const CR = String.raw`CR\.[A-Z]+\.\d{3}(?:\.\d+)*`
const FIXED = [String.raw`SR\.[A-Za-z0-9\-]+\.\d{4}`, String.raw`P\d{5}-[A-Z]+-\d{2}(?:/${CR})?`, CR, String.raw`\bD\d{4}\b`]

const cache = new WeakMap<Index, RegExp>()

function idPattern(ix: Index): RegExp {
  let re = cache.get(ix)
  if (!re) {
    const sds = ix.sds.map(s => s.sd_id).sort((a, b) => b.length - a.length).map(esc)
    const sp = sds.length ? [String.raw`(?<![A-Za-z0-9\-])(?:${sds.join('|')}):[^\s;,]+`] : []
    re = new RegExp([...sp, ...FIXED].join('|'), 'g')
    cache.set(ix, re)
  }
  return re
}

/** Splits text into plain strings and known IDs. `known` adds project IDs (objects, CIs). SP references are
 *  shortened from the right until they name a known provision (e.g. a trailing ")" or "."). */
export function tokenize(ix: Index, text: string, known?: (id: string) => boolean): Token[] {
  const out: Token[] = []
  const re = idPattern(ix)
  re.lastIndex = 0
  let last = 0
  let m: RegExpExecArray | null
  const isKnown = (id: string) => kindOf(ix, id) !== null || !!known?.(id)
  while ((m = re.exec(text))) {
    let id = m[0]
    if (id.includes(':')) {
      while (id.length > 2 && !ix.spById.has(id)) id = id.slice(0, -1)
      if (!ix.spById.has(id)) continue
    } else {
      id = id.replace(/[.)]+$/, '')
      if (!isKnown(id)) continue
    }
    if (m.index > last) out.push(text.slice(last, m.index))
    out.push({ id, text: id })
    last = m.index + id.length
    re.lastIndex = last
  }
  if (last < text.length) out.push(text.slice(last))
  return out
}

export type Mode = 'catalogue' | 'project'

export interface RouteCtx {
  mode: Mode
  pid?: string
  view: string
  viewIds: Set<string>       // IDs present in the current tree (links stay in this view)
  search: string             // query string to keep (tags)
  basis?: Set<string>        // project: SDs with a view
}

/** Home view of an ID: the document of an SP/SR, the CR view of a CR, the decisions list for a decision. */
export function homeView(ix: Index, id: string, kind: EntityKind | null, mode: Mode): string | null {
  switch (kind) {
    case 'sp': return ix.spById.get(id)!.sd_id
    case 'sr': return ix.srSd.get(id) || null
    case 'sd': return id
    case 'cr': return 'CR'
    case 'dec': return 'DEC'
    case 'ci': return mode === 'project' ? 'CR' : null
    case 'obj': return mode === 'project' ? 'OBJ' : null
    default: return null
  }
}

export function idKind(ix: Index, id: string, projectIds?: { cis: Set<string>; objects: Set<string> }): EntityKind | null {
  const k = kindOf(ix, id)
  if (k) return k
  if (projectIds?.cis.has(id)) return 'ci'
  if (projectIds?.objects.has(id)) return 'obj'
  return null
}

export function viewPath(mode: Mode, pid: string | undefined, view: string): string {
  return mode === 'project' ? `/project/${encodeURIComponent(pid!)}/${encodeURIComponent(view)}`
    : `/catalogue/${encodeURIComponent(view)}`
}

export function withSel(search: string, id: string): string {
  const q = new URLSearchParams(search)
  q.set('sel', id)
  return `?${q.toString()}`
}

/** Link target of an ID from the current view: stay in the view when the ID is in its tree, otherwise go to the
 *  ID's home view (decisions always in the catalogue). */
export function hrefFor(ix: Index, id: string, kind: EntityKind | null, ctx: RouteCtx): string {
  if (ctx.viewIds.has(id)) return viewPath(ctx.mode, ctx.pid, ctx.view) + withSel(ctx.search, id)
  if (kind === 'dec') return viewPath('catalogue', undefined, 'DEC') + `?sel=${encodeURIComponent(id)}`
  let view = homeView(ix, id, kind, ctx.mode)
  if (ctx.mode === 'project' && view && view !== 'CR' && view !== 'OBJ' && !ctx.basis?.has(view)) {
    // a source outside the project basis: open it in the catalogue
    return viewPath('catalogue', undefined, view) + `?sel=${encodeURIComponent(id)}`
  }
  if (!view) view = ctx.view
  return viewPath(ctx.mode, ctx.pid, view) + withSel(ctx.search, id)
}

/** Tags in the query string: ?t=AI.learning:static&t=INT.PL:d ('' value = unset). */
export function readTags(q: URLSearchParams): Record<string, string> {
  const out: Record<string, string> = {}
  for (const t of q.getAll('t')) {
    const i = t.indexOf(':')
    if (i > 0) out[t.slice(0, i)] = t.slice(i + 1)
  }
  return out
}

export function writeTags(q: URLSearchParams, tags: Record<string, string>): URLSearchParams {
  const n = new URLSearchParams(q)
  n.delete('t')
  for (const k of Object.keys(tags).sort()) n.append('t', `${k}:${tags[k]}`)
  return n
}

/** The tag part of a query string (kept when switching views within the same mode). */
export function tagQuery(search: string): string {
  const n = new URLSearchParams()
  new URLSearchParams(search).getAll('t').forEach(t => n.append('t', t))
  const s = n.toString()
  return s ? `?${s}` : ''
}
