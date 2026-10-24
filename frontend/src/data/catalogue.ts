// In-memory indexes over the catalogue tables (all hierarchies are flat lists with parent pointers).
import type { CatalogueData, CrRow, DecisionRow, LinkRow, SdRow, SpRow, SrRow, VocabEntry } from '../api'

export function natCompare(a: string, b: string): number {
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' })
}

export function splitRefs(s: string | null | undefined): string[] {
  return String(s || '').replace(/,/g, ';').split(';').map(x => x.trim()).filter(Boolean)
}

/** "CR.X; CR.Y [SET]" -> [{cr, set}] (column refines_full). */
export function splitFull(s: string | null | undefined): { cr: string; set: string }[] {
  return splitRefs(s).map(x => {
    const m = /^(.*?)\s*(?:\[(.*)\])?$/.exec(x)!
    return { cr: m[1], set: (m[2] || '').trim() }
  })
}

export interface Index {
  data: CatalogueData
  sds: SdRow[]
  sdById: Map<string, SdRow>
  spById: Map<string, SpRow>
  spRoots: Map<string, string[]>          // sd_id -> root sp_ids, document order
  spChildren: Map<string, string[]>       // sp_id -> child sp_ids, document order
  srById: Map<string, SrRow>
  srRefs: Map<string, string[]>           // sr_id -> sp_refs
  srSd: Map<string, string>               // sr_id -> sd_id of its first SP
  srBySp: Map<string, string[]>           // sp_id -> sr_ids referencing it
  linksBySr: Map<string, LinkRow[]>
  linksByCr: Map<string, LinkRow[]>
  crById: Map<string, CrRow>
  crRoots: string[]
  crChildren: Map<string, string[]>
  refinedBy: Map<string, { cr: string; full: boolean; set: string }[]>   // refined CR -> refining CRs
  decById: Map<string, DecisionRow>
  vocab: Record<string, VocabEntry[]>
  counting: Set<string>                   // link type labels that count for coverage (attribute yes)
  licensed: Set<string>
}

function push<K, V>(m: Map<K, V[]>, k: K, v: V) {
  const a = m.get(k)
  if (a) a.push(v); else m.set(k, [v])
}

export function buildIndex(data: CatalogueData): Index {
  const t = data.tables
  const sdById = new Map(t.SD.map(r => [r.sd_id, r]))
  const sps = [...t.SP].sort((a, b) => a.seq - b.seq)
  const spById = new Map(sps.map(r => [r.sp_id, r]))
  const spRoots = new Map<string, string[]>()
  const spChildren = new Map<string, string[]>()
  for (const p of sps) {
    if (p.parent_sp && spById.has(p.parent_sp)) push(spChildren, p.parent_sp, p.sp_id)
    else push(spRoots, p.sd_id, p.sp_id)
  }
  const srById = new Map(t.SR.map(r => [r.sr_id, r]))
  const srRefs = new Map<string, string[]>()
  const srSd = new Map<string, string>()
  const srBySp = new Map<string, string[]>()
  for (const r of t.SR) {
    const refs = splitRefs(r.sp_refs)
    srRefs.set(r.sr_id, refs)
    const first = spById.get(refs[0])
    srSd.set(r.sr_id, first ? first.sd_id : r.sr_id.split('.').slice(1, -1).join('.'))
    for (const ref of refs) push(srBySp, ref, r.sr_id)
  }
  for (const a of srBySp.values()) a.sort(natCompare)
  const linksBySr = new Map<string, LinkRow[]>()
  const linksByCr = new Map<string, LinkRow[]>()
  for (const l of t.LINK_SR_CR) { push(linksBySr, l.sr_id, l); push(linksByCr, l.cr_id, l) }
  const crs = [...t.CR].sort((a, b) => natCompare(a.cr_id, b.cr_id))
  const crById = new Map(crs.map(r => [r.cr_id, r]))
  const crRoots: string[] = []
  const crChildren = new Map<string, string[]>()
  const refinedBy = new Map<string, { cr: string; full: boolean; set: string }[]>()
  for (const c of crs) {
    if (c.parent_cr && crById.has(c.parent_cr)) push(crChildren, c.parent_cr, c.cr_id)
    else crRoots.push(c.cr_id)
    const full = splitFull(c.refines_full)
    for (const x of splitRefs(c.refines)) {
      const f = full.find(y => y.cr === x)
      push(refinedBy, x, { cr: c.cr_id, full: !!f, set: f ? f.set : '' })
    }
  }
  const yes = (data.vocab.YN || []).find(e => e.key === 'YES')?.label ?? 'yes'
  const counting = new Set((data.vocab.LINKTYPE || []).filter(e => e.attr === yes).map(e => e.label))
  return {
    data, sds: t.SD, sdById, spById, spRoots, spChildren, srById, srRefs, srSd, srBySp, linksBySr, linksByCr,
    crById, crRoots, crChildren, refinedBy, decById: new Map(t.DECISIONS.map(d => [d.dec_id, d])),
    vocab: data.vocab, counting, licensed: new Set(data.meta.licensed),
  }
}

export function spAncestors(ix: Index, spId: string): string[] {
  const out: string[] = []
  let p = ix.spById.get(spId)?.parent_sp
  while (p && ix.spById.has(p) && !out.includes(p)) { out.unshift(p); p = ix.spById.get(p)!.parent_sp }
  return out
}

export function crAncestors(ix: Index, crId: string): string[] {
  const out: string[] = []
  let p = ix.crById.get(crId)?.parent_cr
  while (p && ix.crById.has(p) && !out.includes(p)) { out.unshift(p); p = ix.crById.get(p)!.parent_cr }
  return out
}

export function crLeaves(ix: Index, crId: string): string[] {
  const ch = ix.crChildren.get(crId) || []
  return ch.length ? ch.flatMap(c => crLeaves(ix, c)) : [crId]
}

/** Decisions that mention an ID in their affected IDs or rationale. */
export function decisionsMentioning(ix: Index, id: string): DecisionRow[] {
  const re = new RegExp(`(^|[^A-Za-z0-9.])${id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![A-Za-z0-9]|\\.\\d)`)
  return ix.data.tables.DECISIONS.filter(d => re.test(d.affected_ids) || re.test(d.rationale))
}

export type EntityKind = 'sd' | 'sp' | 'sr' | 'cr' | 'dec' | 'ci' | 'obj'

/** Kind of a catalogue ID, or null if it is not in the catalogue. */
export function kindOf(ix: Index, id: string): EntityKind | null {
  if (ix.spById.has(id)) return 'sp'
  if (ix.srById.has(id)) return 'sr'
  if (ix.crById.has(id)) return 'cr'
  if (ix.decById.has(id)) return 'dec'
  if (ix.sdById.has(id)) return 'sd'
  return null
}

export function vocabEntry(ix: Index, list: string, label: string): VocabEntry | undefined {
  return (ix.vocab[list] || []).find(e => e.label === label)
}
