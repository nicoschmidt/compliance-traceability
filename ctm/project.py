"""Project selection and applicability (spec § 5.4–5.5) on catalogue tables, without any workbook.

select_project(C, reg, basis, tags, objects) -> Selection
                                 C: {sheet: [row dict]} as store.to_tables() writes them (register labels);
                                 reg: {list: [entry dict]} as register.read_register() returns it, or
                                 register_from_vocab(); basis: [sd_id]; tags: {tag label: value label};
                                 objects: [dict(object_id, level=<label>, ...)]
checklist_rows(sel, sd_id)       rows of the checklist view V_CL_<SD> in the clause order of the source

Used by build_project.py (workbook) and backend/ (web viewer); the roll-up of verdicts stays in the workbook formulas.
"""
import re
from dataclasses import dataclass, field

from . import rules
from .vocab import DEFAULT

AUTO_PREFIX = 'Rule '   # auto-generated applicability justifications start with this


def split_refs(s):
    return [x.strip() for x in str(s or '').replace(',', ';').split(';') if x.strip()]


def natkey(s):
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', str(s))]


def split_full(s):
    """Cell "CR.X; CR.Y [SET]" of column refines_full -> [(cr_id, set)]."""
    out = []
    for x in split_refs(s):
        m = re.match(r'^(.*?)\s*(?:\[(.*)\])?$', x)
        out.append((m.group(1), (m.group(2) or '').strip()))
    return out


def register_from_vocab(reg=None):
    """ctm.vocab.DEFAULT in the form of register.read_register()."""
    return {lst: [dict(key=k, label=lab, colour=col or '', attr=attr or '', desc=desc or '', deprecated='')
                  for k, lab, col, attr, desc in entries]
            for lst, entries in (reg or DEFAULT).items()}


def _label(reg, lst, key):
    for e in reg[lst]:
        if e['key'] == key:
            return e['label']
    raise KeyError((lst, key))


@dataclass
class Selection:
    basis: list
    tags: dict
    objects: list
    link_counts: dict               # link type label -> counts for coverage
    sp: dict                        # sp_id -> SP row of the basis
    sr: dict                        # sr_id -> SR row of the basis (+ sd_id, refs)
    links: list                     # LINK_SR_CR rows of these SRs
    crs_all: dict                   # cr_id -> CR row, not deprecated
    crs: dict                       # selected CRs, natural order
    children: dict                  # cr_id -> [child cr_id] over crs_all
    corr: list
    eff_rule: dict = field(default_factory=dict)    # leaf cr_id -> effective rule (CR rule AND source conditions)
    guid: dict = field(default_factory=dict)        # leaf cr_id -> guidance incl. source guidance
    rule_res: dict = field(default_factory=dict)    # leaf cr_id -> (True | False | None, [unknown tags / error])
    subst: dict = field(default_factory=dict)       # substituted leaf cr_id -> [refining cr_id]
    ci_rows: list = field(default_factory=list)     # generated CIs (rule proposal only, no project entries)

    def leaves(self, k):
        ch = [c for c in self.children.get(k, []) if c in self.crs]
        return [k] if not ch else [x for c in ch for x in self.leaves(c)]

    def expand(self, k, seen=()):
        """leaves() with substituted CRs replaced by the leaves of their full refinements (for checklist views)."""
        out = []
        for l in self.leaves(k):
            if l in self.subst and l not in seen:
                for y in self.subst[l]:
                    out += [x for x in self.expand(y, seen + (l,)) if x not in out]
            elif l not in out:
                out.append(l)
        return out


def select_project(C, reg, basis, tags, objects):
    YES = _label(reg, 'YN', 'YES')
    A = {e['key']: e['label'] for e in reg['APPL']}
    deprecated = _label(reg, 'CRSTATUS', 'DEPRECATED')
    link_counts = {e['label']: e['attr'] == YES for e in reg['LINKTYPE']}

    # ---- selection by basis
    basis = [b for b in basis if b]
    sp = {r['sp_id']: r for r in C['SP'] if r['sd_id'] in basis}
    sr = {}
    for r in C['SR']:
        refs = split_refs(r['sp_refs'])
        if refs and refs[0] in sp:
            r = dict(r, sd_id=sp[refs[0]]['sd_id'], refs=refs)
            sr[r['sr_id']] = r
    links = [l for l in C['LINK_SR_CR'] if l['sr_id'] in sr]
    crs_all = {r['cr_id']: r for r in C['CR'] if r['status'] != deprecated}
    children = {}
    for r in crs_all.values():
        if r['parent_cr']:
            children.setdefault(r['parent_cr'], []).append(r['cr_id'])
    sel = {l['cr_id'] for l in links if link_counts.get(l['link_type']) and l['cr_id'] in crs_all}
    stack = list(sel)
    while stack:                                   # descendants
        k = stack.pop()
        for c in children.get(k, []):
            if c not in sel: sel.add(c); stack.append(c)
    for k in list(sel):                            # ancestors
        p = crs_all[k]['parent_cr']
        while p and p in crs_all:
            sel.add(p); p = crs_all[p]['parent_cr']
    crs = {k: crs_all[k] for k in sorted(sel, key=natkey)}
    corr = [c for c in C['CORR'] if c['from_sp'] in sp or c['to_sp'] in sp]
    S = Selection(basis=basis, tags=tags, objects=objects, link_counts=link_counts, sp=sp, sr=sr, links=links,
                  crs_all=crs_all, crs=crs, children=children, corr=corr)

    # ---- source-specific link conditions and guidance (spec § 4.5, § 5.4): per source of the basis, the counting
    #      links on the nearest linked CR on the path leaf -> root decide. A leaf CR is applicable if its own rule holds
    #      and the condition of at least one source holds (OR); a link without condition always holds.
    on_cr = {}
    for l in links:
        if link_counts.get(l['link_type']) and l['cr_id'] in crs_all:
            on_cr.setdefault(l['cr_id'], []).append((sr[l['sr_id']]['sd_id'], str(l.get('condition') or '').strip(),
                                                     str(l.get('guidance') or '').strip()))

    def source_links(k):
        """{sd: [(condition, guidance)]} of the nearest CR on the path k -> root that the source links."""
        out, n, seen = {}, k, set()
        while n and n in crs_all and n not in seen:
            seen.add(n)
            for sd, c, g in on_cr.get(n, []):
                if out.setdefault(sd, (n, []))[0] == n:
                    out[sd][1].append((c, g))
            n = crs_all[n]['parent_cr']
        return {sd: v[1] for sd, v in out.items()}

    def effective_rule(k):
        base = str(crs[k]['applicability_rule'] or '').strip()
        conds = []
        for lst in source_links(k).values():
            if any(not c for c, _ in lst):
                conds = []; break                   # one source requires the CR without condition
            for c, _ in lst:
                if c not in conds:
                    conds.append(c)
        if not conds:
            return base or 'TRUE'
        cond = conds[0] if len(conds) == 1 else ' OR '.join(f'({c})' for c in conds)
        return cond if base in ('', 'TRUE') else f'({base}) AND ({cond})'

    def guidance(k):
        out = [str(crs[k]['assessor_guidance'] or '')] if crs[k]['assessor_guidance'] else []
        for sd, lst in source_links(k).items():
            out += [f'[{sd}] {g}' for _, g in lst if g and f'[{sd}] {g}' not in out]
        return '\n'.join(out)

    # ---- rule results of leaf CRs
    levels = {o['level'] for o in objects}
    rule_res, eff_rule, guid = S.rule_res, S.eff_rule, S.guid
    for k, r in crs.items():
        if any(c in crs for c in children.get(k, [])):
            continue                                # parents are rolled up, not assessed
        eff_rule[k], guid[k] = effective_rule(k), guidance(k)
        try:
            ast = rules.parse(eff_rule[k])
            rule_res[k] = (rules.evaluate(ast, tags), rules.unknown_tags(ast, tags))
        except rules.RuleError as ex:
            rule_res[k] = (None, [f'rule error: {ex}'])

    # ---- substitution by full refinements (D0033, D0045): a selected leaf CR with a complete set of full
    #      refinements (all members selected and applicable, i.e. at least one CI not N/A by rule) gets no own CIs;
    #      its status is rolled up from the members of all its complete sets
    full_sets = {}                                  # x -> {set: [y]} over the whole catalogue
    for y in sorted(crs_all, key=natkey):
        for x, st in split_full(crs_all[y].get('refines_full')):
            if x != y:
                full_sets.setdefault(x, {}).setdefault(st, []).append(y)
    sel_full = {x for x, sets in full_sets.items() if x in crs and any(y in crs for ys in sets.values() for y in ys)}

    def applicable(y):
        return any(rule_res[l][0] is not False and crs[l]['object_level'] in levels for l in S.leaves(y))
    chained = lambda y: any(l in sel_full for l in S.leaves(y))   # refiner substituted itself: not supported
    for x, sets in full_sets.items():
        if x not in rule_res:
            continue
        ys = [y for members in sets.values() if all(y in crs and applicable(y) and not chained(y) for y in members)
              for y in members]
        if ys:
            S.subst[x] = list(dict.fromkeys(ys))

    # ---- CI generation (rule proposal; build_project merges the project entries)
    for k, r in crs.items():
        if k not in rule_res or k in S.subst:
            continue                                # parents and substituted CRs have no own CIs
        res, unk = rule_res[k]
        for o in objects:
            if o['level'] != r['object_level']:
                continue
            if res is False:
                auto, just = A['NA_FEAT'], f'{AUTO_PREFIX}not met: {eff_rule[k]}'
            elif res is None:
                auto, just = A['APPLICABLE'], f'{AUTO_PREFIX}undetermined ({", ".join(unk)}) – assessor to confirm'
            else:
                auto, just = A['APPLICABLE'], ''
            S.ci_rows.append(dict(ci_id=f'{o["object_id"]}/{k}', object_id=o['object_id'], level=o['level'], cr_id=k,
                                  domain=r['domain'], title=r['title'], statement=r['statement'],
                                  acceptance_criterion=r['acceptance_criterion'], assessor_guidance=guid[k],
                                  expected_evidence=r['expected_evidence'], rule_applicability=auto,
                                  applicability=auto, applicability_justification=just))
    S.ci_rows.sort(key=lambda x: (natkey(x['cr_id']), x['object_id']))
    return S


def checklist_rows(sel, sd_id, ci_rows=None):
    """Checklist view of one basis source: [(sp_row, heading, sr_row, cr_id | None, ci_row | None)] - SRs in clause
    order, each with the CIs of the leaves (substitution expanded) of its counting links; an SR without CI gets one
    row with cr_id None. ci_rows defaults to sel.ci_rows."""
    ci_by_cr = {}
    for c in (sel.ci_rows if ci_rows is None else ci_rows):
        ci_by_cr.setdefault(c['cr_id'], []).append(c)
    sp = sel.sp
    rows = []
    srs = sorted([r for r in sel.sr.values() if r['sd_id'] == sd_id],
                 key=lambda r: (float(sp[r['refs'][0]]['seq'] or 0), natkey(r['sr_id'])))
    for r in srs:
        p = sp[r['refs'][0]]
        heading = p['heading'] or (sp.get(p['parent_sp'], {}).get('heading') if p['parent_sp'] else '') or ''
        counted = [l['cr_id'] for l in sel.links
                   if l['sr_id'] == r['sr_id'] and sel.link_counts.get(l['link_type']) and l['cr_id'] in sel.crs]
        items = [(cr, c) for k in counted for cr in sel.expand(k) for c in ci_by_cr.get(cr, [])]
        if not items:
            rows.append((p, heading, r, None, None))
        for cr, c in items:
            rows.append((p, heading, r, cr, c))
    return rows
