import { isValidElement, type ReactNode } from 'react'
import { crAncestors, decisionsMentioning, natCompare, spAncestors, splitFull, splitRefs, type Index } from '../data/catalogue'
import { idKind } from '../data/ids'
import { crStatus } from '../data/tree'
import { useIndex, useView } from '../state'
import { IdLink, IdText } from './IdText'

const cut = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + '…' : s)

const T = ({ v }: { v?: string | null }) => (v ? <IdText text={v} /> : null)

const isEmpty = (c: ReactNode): boolean => c === null || c === undefined || c === '' || c === false
  || (Array.isArray(c) && (!c.length || c.every(isEmpty)))
  || (isValidElement<{ v?: string | null }>(c) && c.type === T && !c.props.v)

function Field({ label, children, pre }: { label: string; children: ReactNode; pre?: boolean }) {
  if (isEmpty(children)) return null
  return (
    <div className="field">
      <div className="field-label">{label}</div>
      <div className={`field-value${pre ? ' pre' : ''}`}>{children}</div>
    </div>
  )
}

function Header({ kind, id, title, sub }: { kind: string; id: string; title?: string; sub?: ReactNode }) {
  return (
    <div className="detail-head">
      <div className="detail-id"><span className={`kind k-${kind}`}>{kind.toUpperCase()}</span> <span className="mono">{id}</span>
        <button className="copy" title="Copy link to this item" onClick={() => navigator.clipboard?.writeText(window.location.href)}>⧉</button>
      </div>
      {title && <h2>{title}</h2>}
      {sub && <div className="detail-sub">{sub}</div>}
    </div>
  )
}

function Status({ id }: { id: string }) {
  const v = useView()
  const s = crStatus(v.project?.ev.crs, id)
  if (!s.status) return null
  const label = { ok: 'Applicable', na: 'N/A by rule', unknown: 'Undetermined', subst: 'Substituted' }[s.status]
  return <span className={`status s-${s.status}`} title={s.tip}>{label}</span>
}

// ------------------------------------------------------------------------------------------------ per type
function SdDetail({ id }: { id: string }) {
  const ix = useIndex()
  const s = ix.sdById.get(id)!
  const nSp = ix.data.tables.SP.filter(p => p.sd_id === id).length
  const nSr = [...ix.srSd.values()].filter(x => x === id).length
  return (
    <>
      <Header kind="sd" id={id} title={s.title} sub={[s.doc_type, s.edition, s.lifecycle_status].filter(Boolean).join(' · ')} />
      <Field label="Normative strength">{s.normative_strength}</Field>
      <Field label="Licence">{s.licence_class}{ix.licensed.has(id) && !ix.data.meta.internal ? ' – verbatim text omitted (start the backend with --internal)' : ''}</Field>
      <Field label="Status date">{s.status_date}</Field>
      <Field label="Legal link"><T v={s.legal_link} /></Field>
      <Field label="Contents">{nSp} provisions, {nSr} source requirements</Field>
      <Field label="Notes" pre><T v={s.notes} /></Field>
    </>
  )
}

function SpDetail({ id }: { id: string }) {
  const ix = useIndex()
  const p = ix.spById.get(id)!
  const anc = spAncestors(ix, id)
  const kids = ix.spChildren.get(id) || []
  const srs = ix.srBySp.get(id) || []
  return (
    <>
      <div className="crumbs"><IdLink id={p.sd_id} />{anc.map(a => <span key={a}> › <IdLink id={a}>{ix.spById.get(a)!.native_ref}</IdLink></span>)}</div>
      <Header kind="sp" id={id} title={p.heading || p.label || undefined}
        sub={[p.kind, p.role, p.in_catalogue_scope === 'no' ? 'not in catalogue scope' : ''].filter(Boolean).join(' · ')} />
      <Field label="Text" pre>{p.text ? <T v={p.text} />
        : ix.licensed.has(p.sd_id) && !ix.data.meta.internal ? <span className="muted">Licensed source – text omitted.</span> : null}</Field>
      <Field label="Short label">{p.label}</Field>
      <Field label="Condition in text"><T v={p.condition_text} /></Field>
      <Field label="Scope note" pre><T v={p.scope_note} /></Field>
      <Field label="Amended by">{p.amended_by?.length ? p.amended_by.join(', ') : null}</Field>
      <Field label={`Source requirements (${srs.length})`}>{srs.length ? (
        <ul className="list">{srs.map(s => <li key={s}><IdLink id={s} /> <span className="muted">{cut(ix.srById.get(s)!.statement, 160)}</span></li>)}</ul>
      ) : null}</Field>
      <Field label={`Sub-provisions (${kids.length})`}>{kids.length ? (
        <ul className="list">{kids.map(k => { const c = ix.spById.get(k)!; return <li key={k}><IdLink id={k}>{c.native_ref}</IdLink> <span className="muted">{c.heading || c.label || cut(c.text, 120)}</span></li> })}</ul>
      ) : null}</Field>
    </>
  )
}

function SrDetail({ id }: { id: string }) {
  const ix = useIndex()
  const v = useView()
  const r = ix.srById.get(id)!
  const links = ix.linksBySr.get(id) || []
  return (
    <>
      <div className="crumbs"><IdLink id={ix.srSd.get(id) || ''} /></div>
      <Header kind="sr" id={id} sub={[r.obligation, r.origin, r.coverage_complete === 'yes' ? 'coverage complete' : 'coverage incomplete'].filter(Boolean).join(' · ')} />
      <Field label="Statement" pre><T v={r.statement} /></Field>
      <Field label="Provisions">{splitRefs(r.sp_refs).map((s, i) => <span key={s}>{i ? ', ' : ''}<IdLink id={s} /></span>)}</Field>
      <Field label="Parameters">{r.parameters}</Field>
      <Field label="Measure rating">{r.measure_rating}</Field>
      <Field label="Rationale" pre><T v={r.rationale} /></Field>
      <Field label="Notes" pre><T v={r.notes} /></Field>
      <Field label={`Coverage links (${links.length})`}>{links.length ? (
        <table className="tbl">
          <thead><tr><th>CR</th><th>Type</th><th>Condition / guidance</th></tr></thead>
          <tbody>{links.map(l => (
            <tr key={l.cr_id} className={ix.counting.has(l.link_type) ? '' : 'muted'}>
              <td><IdLink id={l.cr_id} /> {v.project && <Status id={l.cr_id} />}<div className="muted small">{ix.crById.get(l.cr_id)?.title}</div></td>
              <td>{l.link_type}</td>
              <td>{l.condition && <div><span className="cond">if</span> <code>{l.condition}</code></div>}
                {l.guidance && <div className="small"><IdText text={l.guidance} /></div>}
                {l.rationale && <div className="muted small"><IdText text={l.rationale} /></div>}</td>
            </tr>))}</tbody>
        </table>) : null}</Field>
      <Field label="Author / date">{[r.author, r.date].filter(Boolean).join(' · ')}</Field>
    </>
  )
}

function reachedBy(ix: Index, id: string) {
  const bySd = new Map<string, { sr: string; type: string; condition: string }[]>()
  for (const l of ix.linksByCr.get(id) || []) {
    const sd = ix.srSd.get(l.sr_id) || '?'
    bySd.set(sd, [...(bySd.get(sd) || []), { sr: l.sr_id, type: l.link_type, condition: l.condition }])
  }
  return [...bySd.entries()].sort((a, b) => natCompare(a[0], b[0]))
}

function CrDetail({ id }: { id: string }) {
  const ix = useIndex()
  const v = useView()
  const c = ix.crById.get(id)!
  const anc = crAncestors(ix, id)
  const kids = ix.crChildren.get(id) || []
  const refines = splitRefs(c.refines)
  const full = splitFull(c.refines_full)
  const refinedBy = ix.refinedBy.get(id) || []
  const decs = decisionsMentioning(ix, id)
  const e = v.project?.ev.crs[id]
  const cis = v.project?.cisByCr.get(id) || []
  return (
    <>
      <div className="crumbs">{anc.map((a, i) => <span key={a}>{i ? ' › ' : ''}<IdLink id={a} /></span>)}</div>
      <Header kind="cr" id={id} title={c.title}
        sub={<>{[c.domain, c.cr_type, c.object_level, c.status].filter(Boolean).join(' · ')} {v.project && <Status id={id} />}</>} />
      <Field label="Statement" pre><T v={c.statement} /></Field>
      <Field label="Acceptance criterion (PASS)" pre><T v={c.acceptance_criterion} /></Field>
      <Field label="Criterion source"><T v={c.criterion_source} /></Field>
      <Field label="Assessor guidance" pre><T v={e?.guidance ?? c.assessor_guidance} /></Field>
      <Field label="Expected evidence" pre><T v={c.expected_evidence} /></Field>
      <Field label="Verification · phase">{[c.verification_method, c.lifecycle_phase].filter(Boolean).join(' · ')}</Field>
      <Field label="Applicability rule">{c.applicability_rule && c.applicability_rule !== 'TRUE' ? <code>{c.applicability_rule}</code> : null}</Field>
      {e && e.leaf && <>
        <Field label="Effective rule (project)"><code>{e.eff_rule}</code></Field>
        <Field label="Undetermined by">{e.unknown?.length ? e.unknown.join(', ') : null}</Field>
      </>}
      {e && e.substituted_by.length > 0 && <Field label="Substituted by (full refinements)">
        {e.substituted_by.map((x, i) => <span key={x}>{i ? ', ' : ''}<IdLink id={x} /></span>)}</Field>}
      {e && e.substitutes.length > 0 && <Field label="Substitutes">
        {e.substitutes.map((x, i) => <span key={x}>{i ? ', ' : ''}<IdLink id={x} /></span>)}</Field>}
      <Field label={`Check items (${cis.length})`}>{cis.length ? (
        <ul className="list">{cis.map(ci => <li key={ci.ci_id}><IdLink id={ci.ci_id} /> <span className="muted">{ci.rule_applicability}</span></li>)}</ul>
      ) : null}</Field>
      <Field label={`Child CRs (${kids.length}, ${c.decomposition || 'AND'})`}>{kids.length ? (
        <ul className="list">{kids.map(k => <li key={k}><IdLink id={k} /> {v.project && <Status id={k} />} <span className="muted">{ix.crById.get(k)!.title}</span></li>)}</ul>
      ) : null}</Field>
      <Field label="Refines">{refines.length ? (
        <ul className="list">{refines.map(r => { const f = full.find(x => x.cr === r); return (
          <li key={r}><IdLink id={r} /> <span className="muted">{f ? `fully${f.set ? ` [${f.set}]` : ''}` : 'partly'} · {ix.crById.get(r)?.title}</span></li>) })}</ul>
      ) : null}</Field>
      <Field label="Refined by">{refinedBy.length ? (
        <ul className="list">{refinedBy.map(r => <li key={r.cr}><IdLink id={r.cr} /> <span className="muted">{r.full ? `fully${r.set ? ` [${r.set}]` : ''}` : 'partly'} · {ix.crById.get(r.cr)?.title}</span></li>)}</ul>
      ) : null}</Field>
      <Field label="Reached by source requirements">{reachedBy(ix, id).map(([sd, ls]) => (
        <div key={sd} className="reach"><strong>{sd}</strong>{' '}
          {ls.map((l, i) => <span key={l.sr + i}>{i ? ', ' : ''}<IdLink id={l.sr} />
            <span className="muted small"> ({l.type}{l.condition ? ', conditional' : ''})</span></span>)}</div>))}</Field>
      <Field label="Decisions">{decs.length ? decs.map((d, i) => <span key={d.dec_id}>{i ? ', ' : ''}<IdLink id={d.dec_id} /></span>) : null}</Field>
      <Field label="Notes" pre><T v={c.notes} /></Field>
      <Field label="Author">{c.author}</Field>
    </>
  )
}

function DecDetail({ id }: { id: string }) {
  const ix = useIndex()
  const d = ix.decById.get(id)!
  return (
    <>
      <Header kind="dec" id={id} sub={[d.type, d.date, d.author].filter(Boolean).join(' · ')} />
      <Field label="Affected IDs"><T v={d.affected_ids} /></Field>
      <Field label="Rationale" pre><T v={d.rationale} /></Field>
      <Field label="Source refs"><T v={d.source_refs} /></Field>
    </>
  )
}

function CiDetail({ id }: { id: string }) {
  const ix = useIndex()
  const v = useView()
  const c = v.project!.ev.cis.find(x => x.ci_id === id)!
  const o = v.project!.ev.objects.find(x => x.object_id === c.object_id)
  const e = v.project!.ev.crs[c.cr_id]
  return (
    <>
      <Header kind="ci" id={id} title={ix.crById.get(c.cr_id)?.title} sub={<>{c.level} · {c.rule_applicability} <Status id={c.cr_id} /></>} />
      <Field label="Object"><IdLink id={c.object_id} /> {o?.name}</Field>
      <Field label="Common requirement"><IdLink id={c.cr_id} /></Field>
      <Field label="Justification (rule)">{c.applicability_justification}</Field>
      <Field label="Effective rule">{e?.eff_rule ? <code>{e.eff_rule}</code> : null}</Field>
      <Field label="Statement" pre><T v={ix.crById.get(c.cr_id)?.statement} /></Field>
      <Field label="Acceptance criterion (PASS)" pre><T v={ix.crById.get(c.cr_id)?.acceptance_criterion} /></Field>
      <Field label="Guidance" pre><T v={e?.guidance} /></Field>
      <Field label="Expected evidence" pre><T v={ix.crById.get(c.cr_id)?.expected_evidence} /></Field>
      <p className="muted small">Verdicts and evidence are entered in the project workbook (sheet CI); the viewer shows the rule proposal.</p>
    </>
  )
}

function ObjDetail({ id }: { id: string }) {
  const v = useView()
  const o = v.project!.ev.objects.find(x => x.object_id === id)!
  const cis = v.project!.ev.cis.filter(c => c.object_id === id)
  return (
    <>
      <Header kind="obj" id={id} title={o.name} sub={o.level} />
      <Field label="Description" pre>{o.description}</Field>
      <Field label="Parent object">{o.parent_object ? <IdLink id={o.parent_object} /> : null}</Field>
      <Field label="Check items">{cis.length}</Field>
    </>
  )
}

function ProjectOverview() {
  const v = useView()
  const ev = v.project!.ev
  const p = ev.seed.prj
  const by = (s: string) => ev.cis.filter(c => crStatus(ev.crs, c.cr_id).status === s).length
  return (
    <>
      <Header kind="prj" id={p.project_id} title={p.product} sub={[p.client, p.catalogue_baseline].filter(Boolean).join(' · ')} />
      <Field label="Description" pre>{p.description}</Field>
      <Field label="Boundary" pre>{p.boundary_statement}</Field>
      <Field label="Agreed exclusions" pre>{p.agreed_exclusions}</Field>
      <Field label="Basis">{ev.basis.map(b => <div key={b.sd_id}><IdLink id={b.sd_id} /> <span className="muted">{[b.edition, b.use_case].filter(Boolean).join(' · ')}</span>
        {ev.missing_sources.includes(b.sd_id) && <span className="warn"> not loaded</span>}</div>)}</Field>
      <Field label="Check items">{ev.counts.ci} – applicable {by('ok')}, undetermined {by('unknown')}, N/A by rule {by('na')}</Field>
      <Field label="Selection">{ev.counts.cr} CRs ({ev.counts.substituted} substituted), {ev.counts.sr} SRs, {ev.counts.links} links</Field>
      <Field label="Assessor / reviewer">{[p.assessor, p.reviewer].filter(Boolean).join(' / ')}</Field>
    </>
  )
}

export function DetailPane({ sel, view, hidden }: { sel: string | null; view: string; hidden?: boolean }) {
  const ix = useIndex()
  const v = useView()
  const id = sel || (ix.sdById.has(view) ? view : null)
  const kind = id ? idKind(ix, id, v.projectIds) : null
  let body: ReactNode
  if (!id || !kind) {
    body = v.project ? <ProjectOverview /> : (
      <div className="muted placeholder">{sel ? <>Unknown ID <code>{sel}</code>.</> : 'Select an item in the tree to see its details.'}</div>)
  } else {
    body = { sd: <SdDetail id={id} />, sp: <SpDetail id={id} />, sr: <SrDetail id={id} />, cr: <CrDetail id={id} />,
      dec: <DecDetail id={id} />, ci: <CiDetail id={id} />, obj: <ObjDetail id={id} /> }[kind]
  }
  return (
    <div className="detail">
      {hidden && <div className="hint">Hidden in the tree by the current filter or search.</div>}
      {body}
    </div>
  )
}
