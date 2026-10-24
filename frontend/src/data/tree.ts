// Tree builders for the middle pane, the applicability filter, search and flattening for the virtual list.
import type { CiRow, CrEval, Evaluation } from '../api'
import { natCompare, type Index } from './catalogue'

export type NodeKind = 'sp' | 'sr' | 'cr' | 'ci' | 'obj' | 'dec' | 'group'
export type Status = 'ok' | 'na' | 'unknown' | 'subst'

export interface TreeNode {
  key: string                // unique path key
  id: string                 // entity ID (selection, links)
  kind: NodeKind
  title: string
  text: string
  badge?: string
  badgeColour?: string
  condition?: string         // link condition (source-specific applicability)
  status?: Status
  statusTip?: string
  muted?: boolean            // out of catalogue scope, N/A shown on request
  children: TreeNode[]
}

export interface ProjectCtx {
  ev: Evaluation
  cisByCr: Map<string, CiRow[]>
  selSp: Set<string>
  selSr: Set<string>
}

export function projectCtx(ev: Evaluation): ProjectCtx {
  const cisByCr = new Map<string, CiRow[]>()
  for (const c of ev.cis) {
    const a = cisByCr.get(c.cr_id)
    if (a) a.push(c); else cisByCr.set(c.cr_id, [c])
  }
  return { ev, cisByCr, selSp: new Set(ev.selection.sp), selSr: new Set(ev.selection.sr) }
}

export interface BuildOpts {
  project?: ProjectCtx
  applic?: Record<string, CrEval> | null     // catalogue mode: rule results for the tag filter
  allLinks?: boolean                          // also non-counting link types (catalogue mode)
}

// ------------------------------------------------------------------------------------------------ status
function leafStatus(e: CrEval | undefined): Status | undefined {
  if (!e) return undefined
  if (e.substituted_by.length) return 'subst'
  if (!e.leaf) return undefined
  return e.result === true ? 'ok' : e.result === false ? 'na' : 'unknown'
}

/** Status of a CR from rule results: leaves directly, parents as the best of their leaves. */
export function crStatus(crs: Record<string, CrEval> | null | undefined, id: string): { status?: Status; tip?: string } {
  if (!crs) return {}
  const e = crs[id]
  if (!e) return {}
  if (e.leaf) {
    const s = leafStatus(e)
    const tip = s === 'subst' ? `substituted by ${e.substituted_by.join(', ')}`
      : s === 'unknown' ? `undetermined: ${(e.unknown || []).join(', ')}`
        : s === 'na' ? `rule not met: ${e.eff_rule}` : e.eff_rule && e.eff_rule !== 'TRUE' ? `rule met: ${e.eff_rule}` : ''
    return { status: s, tip }
  }
  const st = e.expanded.map(l => leafStatus(crs[l])).filter(Boolean)
  const status = st.includes('ok') ? 'ok' : st.includes('unknown') ? 'unknown' : st.length && st.every(s => s === 'na') ? 'na' : undefined
  return { status, tip: status ? `${status === 'ok' ? 'applicable' : status === 'na' ? 'N/A' : 'undetermined'} (from leaves)` : '' }
}

function ciStatus(ctx: ProjectCtx, c: CiRow): { status: Status; tip: string } {
  const s = crStatus(ctx.ev.crs, c.cr_id)
  return { status: s.status === 'na' ? 'na' : s.status === 'unknown' ? 'unknown' : 'ok', tip: c.applicability_justification || c.rule_applicability }
}

// ------------------------------------------------------------------------------------------------ nodes
const short = (s: string, n = 140) => (s.length > n ? s.slice(0, n - 1) + '…' : s).replace(/\s+/g, ' ')

function ciNode(ctx: ProjectCtx, c: CiRow, path: string): TreeNode {
  const obj = ctx.ev.objects.find(o => o.object_id === c.object_id)
  const s = ciStatus(ctx, c)
  return {
    key: `${path}/ci:${c.ci_id}`, id: c.ci_id, kind: 'ci', title: c.object_id, text: obj?.name || '',
    badge: c.rule_applicability, status: s.status, statusTip: s.tip, children: [],
  }
}

function crBase(ix: Index, id: string, path: string, crs?: Record<string, CrEval> | null): TreeNode {
  const c = ix.crById.get(id)
  const s = crStatus(crs, id)
  return {
    key: `${path}/cr:${id}`, id, kind: 'cr', title: id, text: c ? c.title : '(unknown CR)',
    status: s.status, statusTip: s.tip, children: [],
  }
}

/** Project mode: a leaf gets its CIs; a parent or a substituted leaf its expanded leaves (with CIs). */
function crProjectNode(ix: Index, ctx: ProjectCtx, id: string, path: string, depth = 0): TreeNode {
  const n = crBase(ix, id, path, ctx.ev.crs)
  const e = ctx.ev.crs[id]
  if (!e || depth > 6) return n
  if (e.leaf && !e.substituted_by.length) {
    n.children = (ctx.cisByCr.get(id) || []).map(c => ciNode(ctx, c, n.key))
  } else {
    n.children = e.expanded.filter(x => x !== id).map(x => crProjectNode(ix, ctx, x, n.key, depth + 1))
  }
  return n
}

/** Catalogue mode: the CR hierarchy below the CR, plus its full refinements as groups. */
function crHierNode(ix: Index, id: string, path: string, applic?: Record<string, CrEval> | null, depth = 0): TreeNode {
  const n = crBase(ix, id, path, applic)
  if (depth > 6) return n
  n.children = (ix.crChildren.get(id) || []).map(c => crHierNode(ix, c, n.key, applic, depth + 1))
  const sets = new Map<string, string[]>()
  for (const r of ix.refinedBy.get(id) || []) if (r.full) sets.set(r.set, [...(sets.get(r.set) || []), r.cr])
  for (const [set, ys] of sets) {
    const g: TreeNode = { key: `${n.key}/set:${set}`, id, kind: 'group', title: `refined fully by${set ? ` [${set}]` : ''}`,
      text: '', children: [] }
    g.children = ys.map(y => crBase(ix, y, g.key, applic))
    n.children.push(g)
  }
  return n
}

function srNode(ix: Index, srId: string, path: string, o: BuildOpts): TreeNode {
  const r = ix.srById.get(srId)!
  const n: TreeNode = { key: `${path}/sr:${srId}`, id: srId, kind: 'sr', title: srId, text: short(r.statement),
    badge: r.obligation, children: [] }
  for (const l of ix.linksBySr.get(srId) || []) {
    const counts = ix.counting.has(l.link_type)
    if (o.project) {
      if (!counts || !o.project.ev.crs[l.cr_id]) continue
    } else if (!counts && !o.allLinks) continue
    const c = o.project ? crProjectNode(ix, o.project, l.cr_id, n.key) : crHierNode(ix, l.cr_id, n.key, o.applic)
    const lt = (ix.vocab.LINKTYPE || []).find(e => e.label === l.link_type)
    c.badge = l.link_type
    c.badgeColour = lt?.colour
    c.condition = l.condition || undefined
    n.children.push(c)
  }
  return n
}

function spNode(ix: Index, spId: string, path: string, o: BuildOpts): TreeNode {
  const p = ix.spById.get(spId)!
  const n: TreeNode = {
    key: `${path}/sp:${spId}`, id: spId, kind: 'sp', title: p.native_ref,
    text: short(p.heading || p.label || p.text || ''), badge: p.kind || undefined,
    muted: p.in_catalogue_scope === noLabel(ix), children: [],
  }
  for (const sr of ix.srBySp.get(spId) || []) {
    if (o.project && !o.project.selSr.has(sr)) continue
    n.children.push(srNode(ix, sr, n.key, o))
  }
  for (const ch of ix.spChildren.get(spId) || []) n.children.push(spNode(ix, ch, n.key, o))
  return n
}

const noLabel = (ix: Index) => (ix.vocab.YN || []).find(e => e.key === 'NO')?.label ?? 'no'

// ------------------------------------------------------------------------------------------------ views
/** Source document: SP tree, each SP with its SRs, each SR with its linked CRs (and CIs in project mode). */
export function buildDocTree(ix: Index, sd: string, o: BuildOpts = {}): TreeNode[] {
  return (ix.spRoots.get(sd) || []).map(sp => spNode(ix, sp, sd, o))
}

/** Master list: CR hierarchy (catalogue), or the CRs selected by the project basis. */
export function buildCrTree(ix: Index, o: BuildOpts = {}): TreeNode[] {
  if (!o.project) return ix.crRoots.map(c => crHierNode(ix, c, 'CR', o.applic))
  const crs = o.project.ev.crs
  const node = (id: string, path: string): TreeNode => {
    const e = crs[id]
    const n = crBase(ix, id, path, crs)
    const kids = (ix.crChildren.get(id) || []).filter(c => crs[c])
    if (kids.length) n.children = kids.map(c => node(c, n.key))
    else if (e && e.substituted_by.length) {
      const g: TreeNode = { key: `${n.key}/subst`, id, kind: 'group', title: 'substituted by', text: '', children: [] }
      g.children = e.substituted_by.map(y => crProjectNode(ix, o.project!, y, g.key))
      n.children = [g]
    } else n.children = (o.project!.cisByCr.get(id) || []).map(c => ciNode(o.project!, c, n.key))
    return n
  }
  return Object.keys(crs).filter(k => !crs[ix.crById.get(k)?.parent_cr || '']).sort(natCompare).map(k => node(k, 'CR'))
}

/** Project: assessment objects with their CIs. */
export function buildObjectTree(ix: Index, ctx: ProjectCtx): TreeNode[] {
  return ctx.ev.objects.map(o => ({
    key: `obj:${o.object_id}`, id: o.object_id, kind: 'obj' as const, title: o.object_id, text: o.name || '', badge: o.level,
    children: ctx.ev.cis.filter(c => c.object_id === o.object_id).map(c => {
      const n = ciNode(ctx, c, `obj:${o.object_id}`)
      n.title = c.cr_id
      n.text = ix.crById.get(c.cr_id)?.title || ''
      return n
    }),
  }))
}

export function buildDecisionList(ix: Index): TreeNode[] {
  return ix.data.tables.DECISIONS.map(d => ({
    key: `dec:${d.dec_id}`, id: d.dec_id, kind: 'dec' as const, title: d.dec_id, text: short(d.rationale), badge: d.type,
    children: [],
  }))
}

// ------------------------------------------------------------------------------------------------ filter + search
export interface FilterOpts {
  active: boolean          // a rule evaluation is present (tag filter or project)
  showNA: boolean          // keep N/A items (muted) instead of hiding them
  onlyWithReqs: boolean    // hide provisions without (visible) source requirements
}

/** Applies the applicability filter: N/A CRs and CIs are hidden (or muted), SRs whose links all vanished are hidden,
 *  provisions are kept while they or a descendant still have requirements (if onlyWithReqs). */
export function filterTree(nodes: TreeNode[], f: FilterOpts): TreeNode[] {
  const visit = (n: TreeNode): TreeNode | null => {
    const kids = n.children.map(visit).filter((x): x is TreeNode => !!x)
    if ((n.kind === 'cr' || n.kind === 'ci') && f.active && n.status === 'na') {
      if (!f.showNA) return null
      return { ...n, muted: true, children: kids }
    }
    if (n.kind === 'sr' && f.active && n.children.length && !kids.length) return null
    if (n.kind === 'sp' && f.onlyWithReqs && !kids.length) return null
    return kids.length === n.children.length && kids.every((k, i) => k === n.children[i]) ? n : { ...n, children: kids }
  }
  return nodes.map(visit).filter((x): x is TreeNode => !!x)
}

export function matches(n: TreeNode, q: string): boolean {
  return n.title.toLowerCase().includes(q) || n.text.toLowerCase().includes(q) || n.id.toLowerCase().includes(q)
}

/** Keeps matching nodes and their ancestors; returns the keys to expand so that every match is visible. */
export function searchTree(nodes: TreeNode[], query: string): { nodes: TreeNode[]; expand: Set<string>; hits: number } {
  const q = query.trim().toLowerCase()
  const expand = new Set<string>()
  let hits = 0
  if (!q) return { nodes, expand, hits }
  const visit = (n: TreeNode): TreeNode | null => {
    const hit = matches(n, q)
    if (hit) hits++
    const kids = n.children.map(visit).filter((x): x is TreeNode => !!x)
    if (kids.length) expand.add(n.key)
    if (!hit && !kids.length) return null
    return { ...n, children: hit && !kids.length ? n.children : kids }
  }
  return { nodes: nodes.map(visit).filter((x): x is TreeNode => !!x), expand, hits }
}

export interface Row { node: TreeNode; depth: number; open: boolean; parent: string | null }

export function flatten(nodes: TreeNode[], isOpen: (key: string) => boolean): Row[] {
  const out: Row[] = []
  const walk = (ns: TreeNode[], depth: number, parent: string | null) => {
    for (const n of ns) {
      const open = n.children.length > 0 && isOpen(n.key)
      out.push({ node: n, depth, open, parent })
      if (open) walk(n.children, depth + 1, n.key)
    }
  }
  walk(nodes, 0, null)
  return out
}

/** Keys of the ancestors of the first node (document order) with this ID, and the node's own key. */
export function pathTo(nodes: TreeNode[], id: string): string[] | null {
  const stack: string[] = []
  const walk = (ns: TreeNode[]): boolean => {
    for (const n of ns) {
      stack.push(n.key)
      if (n.id === id && n.kind !== 'group') return true
      if (walk(n.children)) return true
      stack.pop()
    }
    return false
  }
  return walk(nodes) ? [...stack] : null
}

export function collectIds(nodes: TreeNode[], out = new Set<string>()): Set<string> {
  for (const n of nodes) { out.add(n.id); collectIds(n.children, out) }
  return out
}

