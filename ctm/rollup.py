"""Reference implementation of the roll-up rules (spec § 5.6) in plain Python.

Used by the test suite to verify the Excel formulas independently. Works on register LABELS.
"""
ORDER = ['FAIL', 'GAP', 'NOTASS', 'OPEN', 'PASS', 'NA']   # precedence; NOTINST / NOREQ are not counted


def bucket(key):
    return {'OOS': 'NOTASS'}.get(key, key)


def combine(keys, empty):
    present = {bucket(k) for k in keys if k not in ('NOTINST', 'NOREQ')}
    for k in ORDER:
        if k in present:
            return k
    return empty


def compute(reg, ci_rows, crs, links, srs, sps, corr, sd_status, cat_crs=None):
    """All inputs as dicts with labels. Returns dict of status KEYS per CI, CR, SR, SP and presumption flags.
    crs = CRs of the project; cat_crs = all catalogue CRs (members of refinement sets; default crs)."""
    lab = {lst: {e['label']: e['key'] for e in reg[lst]} for lst in reg}
    A = lab['APPL']; V = lab['VERDICT']
    ci_status = {}
    for c in ci_rows:
        a = c.get('applicability') or ''
        if not a:
            ci_status[c['ci_id']] = ''
        elif A[a] == 'APPLICABLE':
            ci_status[c['ci_id']] = ('V', V[c['verdict']] if c.get('verdict') else 'PEND')
        else:
            ci_status[c['ci_id']] = ('A', A[a])
    cimap = {'V:FAIL': 'FAIL', 'A:NIS': 'NOTASS', 'V:INFO': 'OPEN', 'V:PEND': 'OPEN', 'V:PASS': 'PASS',
             'A:INHERITED': 'PASS', 'A:NA_FEAT': 'NA', 'A:NA_HAZ': 'NA'}
    own = {}
    for c in ci_rows:
        s = ci_status[c['ci_id']]
        if s:
            own.setdefault(c['cr_id'], []).append(cimap[f'{s[0]}:{s[1]}'])
    children = {}
    for k, r in crs.items():
        if r['parent_cr'] in crs:
            children.setdefault(r['parent_cr'], []).append(k)

    # substitution by full refinements (D0033) – same condition as build_project
    def leaves(k):
        ch = children.get(k, [])
        return [k] if not ch else [x for c in ch for x in leaves(c)]
    ci_crs = {}
    for c in ci_rows:
        ci_crs.setdefault(c['cr_id'], []).append(A.get(c.get('rule_applicability') or '', ''))
    applicable = lambda y: any(any(a != 'NA_FEAT' for a in ci_crs.get(l, [])) for l in leaves(y))
    sets = {}                                                     # x -> {set: [y]}, cell "CR.X; CR.Y [SET]"
    for y, r in (cat_crs or crs).items():
        for t in [t.strip() for t in str(r.get('refines_full') or '').split(';') if t.strip()]:
            x, st = t[:-1].split(' [', 1) if t.endswith(']') and ' [' in t else (t, '')
            if x.strip() != y:
                sets.setdefault(x.strip(), {}).setdefault(st.strip(), []).append(y)
    sel_full = {x for x, ss in sets.items() if x in crs and any(y in crs for ys in ss.values() for y in ys)}
    chained = lambda y: any(l in sel_full for l in leaves(y))     # as build_project: no substitution chains
    subst = {}
    for x, ss in sets.items():                                    # D0045: substituted if at least one set is complete
        if x in crs and x not in children:
            ys = [y for ms in ss.values() if all(y in crs and applicable(y) and not chained(y) for y in ms) for y in ms]
            if ys:
                subst[x] = ys
    cr_final = {}

    def cr_f(k):
        if k in cr_final:
            return cr_final[k]
        if k in subst:
            cr_final[k] = combine([cr_f(y) for y in subst[k]], 'NOTINST')
            return cr_final[k]
        s0 = combine(own.get(k, []), 'NOTINST')
        ch = [cr_f(c) for c in children.get(k, [])]
        if crs[k]['decomposition'] == 'OR' and 'PASS' in ch and s0 != 'FAIL':
            res = 'PASS'
        else:
            res = combine([s0] + ch, s0)
        cr_final[k] = res
        return res
    for k in crs:
        cr_f(k)

    counts = {e['label']: e['attr'] == 'yes' for e in reg['LINKTYPE']}
    sr_status = {}
    for k, r in srs.items():
        if r['coverage_complete'] != 'yes':
            sr_status[k] = 'GAP'; continue
        cl = [l for l in links if l['sr_id'] == k and counts[l['link_type']]]
        if not cl:
            sr_status[k] = 'GAP'; continue
        sr_status[k] = combine([cr_final.get(l['cr_id'], 'NOTINST') for l in cl], 'NOTINST')

    role_attr = {e['label']: e['attr'] for e in reg['SPROLE']}
    own_sr = {}
    for k, r in srs.items():
        for x in r['refs']:
            own_sr.setdefault(x, []).append(sr_status[k])
    sp_children = {}
    for k, r in sps.items():
        if r['parent_sp'] in sps:
            sp_children.setdefault(r['parent_sp'], []).append(k)
    sp_final = {}

    def sp_f(k):
        if k in sp_final:
            return sp_final[k]
        r = sps[k]; attr = role_attr[r['role']]
        if attr == 'none':
            res = 'NOREQ'
        elif r['in_catalogue_scope'] == 'no':
            res = 'OOS'
        else:
            o = own_sr.get(k, [])
            s0 = (combine(o, 'NOTINST') if o else ('NOREQ' if attr == 'children' else 'GAP'))
            res = combine(o + [sp_f(c) for c in sp_children.get(k, [])], s0)
        sp_final[k] = res
        return res
    for k in sps:
        sp_f(k)

    pres = {}
    for c in corr:
        frm = sp_final.get(c['from_sp'], '')
        if c['basis'] == 'Annex ZA':
            pres[c['corr_id']] = 'yes' if (sd_status.get(c['claimant_sd']) == 'Cited in OJ' and frm == 'PASS') else 'no'
        else:
            pres[c['corr_id']] = 'yes' if frm == 'PASS' else 'no'
    return dict(ci=ci_status, cr=cr_final, sr=sr_status, sp=sp_final, pres=pres)
