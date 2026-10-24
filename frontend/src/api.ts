// Types and calls of the local API (backend/app.py). Table rows carry register labels, as in the catalogue workbook.

export interface SdRow {
  sd_id: string; title: string; edition: string; doc_type: string; lifecycle_status: string; status_date: string
  normative_strength: string; legal_link: string; licence_class: string; notes: string
}
export interface SpRow {
  sp_id: string; sd_id: string; native_ref: string; seq: number; parent_sp: string; role: string; heading: string
  label: string; text: string; condition_text: string; in_catalogue_scope: string; scope_note: string
  kind: string; amended_by: string[]
}
export interface SrRow {
  sr_id: string; sp_refs: string; statement: string; obligation: string; origin: string; author: string; date: string
  rationale: string; parameters: string; measure_rating: string; coverage_complete: string; notes: string
}
export interface CrRow {
  cr_id: string; domain: string; title: string; statement: string; parent_cr: string; decomposition: string
  refines: string; refines_full: string; cr_type: string; object_level: string; verification_method: string
  acceptance_criterion: string; criterion_source: string; assessor_guidance: string; expected_evidence: string
  lifecycle_phase: string; applicability_rule: string; tension_flag: string; status: string; author: string; notes: string
}
export interface LinkRow {
  link_id: string; sr_id: string; cr_id: string; link_type: string; condition: string; guidance: string
  rationale: string; author: string; date: string
}
export interface CorrRow {
  corr_id: string; basis: string; claimant_sd: string; from_sp: string; to_sp: string; declared_coverage: string; remarks: string
}
export interface DecisionRow {
  dec_id: string; date: string; author: string; type: string; affected_ids: string; rationale: string; source_refs: string
}
export interface VocabEntry { key: string; label: string; colour: string; attr: string; desc: string }

export interface CatalogueData {
  meta: {
    baseline: string; title: string; internal: boolean; licensed: string[]; missing_packs: string[]; load_errors: string[]
    packs: { pack_id: string; title: string; sources: string[] }[]
  }
  vocab: Record<string, VocabEntry[]>
  tables: {
    SD: SdRow[]; SP: SpRow[]; SR: SrRow[]; CR: CrRow[]; LINK_SR_CR: LinkRow[]; CORR: CorrRow[]; DECISIONS: DecisionRow[]
  }
}

/** Rule result: true = applicable, false = not met (N/A), null = undetermined (tags unknown). */
export type RuleResult = boolean | null

export interface CrEval {
  leaf: boolean
  leaves: string[]
  expanded: string[]          // leaves with substituted CRs replaced by their full refinements
  substituted_by: string[]
  substitutes: string[]
  eff_rule?: string
  result?: RuleResult
  unknown?: string[]
  guidance?: string
}

export interface ProjectSeed {
  prj: Record<string, string> & { project_id: string }
  basis: { sd_id: string; edition?: string; use_case?: string; note?: string }[]
  tags: Record<string, string>
  objects: { object_id: string; level: string; name?: string; description?: string; parent_object?: string }[]
  ev?: Record<string, string>[]
}

export interface CiRow {
  ci_id: string; object_id: string; level: string; cr_id: string; rule_applicability: string
  applicability_justification: string
}

export interface ViewRow { sp_id: string; clause: string; heading: string; sr_id: string; cr_id: string | null; ci_id: string | null }

export interface Evaluation {
  seed: ProjectSeed
  tags: Record<string, string>
  objects: { object_id: string; level: string; name?: string; description?: string; parent_object?: string }[]
  basis: { sd_id: string; edition?: string; use_case?: string; note?: string }[]
  missing_sources: string[]
  selection: { sp: string[]; sr: string[] }
  crs: Record<string, CrEval>
  cis: CiRow[]
  views: Record<string, ViewRow[]>
  counts: Record<string, number>
}

export interface ProjectInfo { project_id: string; product?: string; client?: string; basis?: string[]; file: string; error?: string }

async function call<T>(url: string, body?: unknown): Promise<T> {
  const r = await fetch(url, body === undefined ? undefined : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  })
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`
    try {
      const j = await r.json()
      msg = typeof j.detail === 'string' ? j.detail
        : Array.isArray(j.detail) ? j.detail.map((d: { msg: string; loc?: unknown[] }) => `${(d.loc || []).join('.')}: ${d.msg}`).join('\n')
          : msg
    } catch { /* not JSON */ }
    throw new Error(msg)
  }
  return r.json() as Promise<T>
}

export const api = {
  catalogue: () => call<CatalogueData>('/api/catalogue'),
  reload: () => call<CatalogueData['meta']>('/api/reload', {}),
  projects: () => call<ProjectInfo[]>('/api/projects'),
  project: (pid: string) => call<ProjectSeed>(`/api/projects/${encodeURIComponent(pid)}`),
  evaluate: (seed: ProjectSeed, tags?: Record<string, string>) => call<Evaluation>('/api/project/evaluate', { seed, tags }),
  applicability: (basis: string[], tags: Record<string, string>) =>
    call<{ crs: Record<string, CrEval> }>('/api/applicability', { basis, tags }),
}
