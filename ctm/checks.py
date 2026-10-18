"""Catalogue release check (spec § 5.1, § 5.2, § 6.3, § 7) on a loaded Catalogue.

Schema-level rules (required fields, register values, ID patterns of SR/CR/decisions) are enforced by ctm/model.py
when the files are loaded; this module checks references, hierarchy, coverage and methodology rules.
check(cat) -> (errors, warnings, stats)
"""
from . import rules, vocab
from .schema import CR_MAX_DEPTH, SP_MAX_DEPTH


def _depth(parent_of, k, seen=()):
    p = parent_of(k)
    if not p:
        return 0
    if p in seen or p == k:
        raise ValueError(k)
    return 1 + _depth(parent_of, p, seen + (k,))


def check(cat):
    E, W = list(cat.load_errors), []

    # register integrity
    for lst, entries in vocab.DEFAULT.items():
        keys = [e[0] for e in entries]; labs = [e[1] for e in entries]
        if len(set(keys)) != len(keys): E.append(f'REGISTER {lst}: duplicate keys')
        if len(set(labs)) != len(labs): E.append(f'REGISTER {lst}: duplicate labels')

    sd, sp, sr, cr = cat.sds, cat.sps, cat.srs, cat.crs

    # packs (spec § 8.3): links point from a pack to the master list; correspondences may reference provisions of the
    # own pack and of the packs it requires
    packs = cat.packs
    known = {k.pack_id: k for k in cat.manifest.known_packs}
    for pid, (_, man) in packs.items():
        if pid not in known: W.append(f'PACK {pid}: not a known pack of the master list (catalogue.json known_packs)')
        for q in man.requires:
            if q not in packs: E.append(f'PACK {pid}: requires pack {q}, which is not loaded')
    allowed = {pid: {pid, *man.requires} for pid, (_, man) in packs.items()}
    p_sd = lambda x: cat.pack_of_sd.get(x, '')
    missing = cat.missing_packs()
    tag_list = {e[1]: e[3] for e in vocab.DEFAULT['TAG']}

    def check_rule(where, rule):
        try:
            for tag, vals in rules.refs(rules.parse(rule)):
                if tag not in tag_list: E.append(f'{where}: rule uses unknown tag {tag}'); continue
                for v in vals:
                    if v not in vocab.labels(tag_list[tag]): E.append(f'{where}: rule value "{v}" not allowed for {tag}')
        except rules.RuleError as ex:
            E.append(f'{where}: rule syntax: {ex}')
    role_attr = {e[0]: e[3] for e in vocab.DEFAULT['SPROLE']}
    counts = {e[0]: e[3] == 'yes' for e in vocab.DEFAULT['LINKTYPE']}

    # SP
    for k, r in sp.items():
        if r.parent_sp and r.parent_sp not in sp: E.append(f'SP {k}: unknown parent {r.parent_sp}')
        # licensed text may be kept in raw.json (internal store, D0025); exports strip it (store.to_tables)
    for k in sp:
        try:
            if _depth(lambda x: sp[x].parent_sp if x in sp and sp[x].parent_sp in sp else '', k) > SP_MAX_DEPTH:
                E.append(f'SP {k}: deeper than {SP_MAX_DEPTH} levels')
        except ValueError: E.append(f'SP {k}: parent cycle')
    for k in cr:
        try:
            if _depth(lambda x: cr[x].parent_cr if x in cr and cr[x].parent_cr in cr else '', k) > CR_MAX_DEPTH:
                E.append(f'CR {k}: deeper than {CR_MAX_DEPTH} levels')
        except ValueError: E.append(f'CR {k}: parent cycle')

    # SR and links
    sr_of_sp = {}
    in_links = {}                     # counting links only: CRs reached only by supporting links are never assessed
    nlinks = nconds = 0
    for k, r in sr.items():
        home = cat.sr_sd[k]
        if k.split('.')[1] != home: E.append(f'SR {k}: ID names SD {k.split(".")[1]} but is stored with {home}')
        for x in r.sp_refs:
            if x not in sp: E.append(f'SR {k}: unknown SP {x}'); continue
            if sp[x].sd_id != home: E.append(f'SR {k}: SP {x} belongs to another SD')
            sr_of_sp.setdefault(x, []).append(k)
            if not sp[x].in_catalogue_scope: W.append(f'SR {k}: references out-of-catalogue-scope SP {x}')
        if r.origin == 'DERIVED' and (not r.author or not r.rationale):
            E.append(f'SR {k}: Derived SR needs author and rationale')
        seen = set()
        for l in r.links:
            nlinks += 1
            if l.cr not in cr: E.append(f'SR {k}: link to unknown CR {l.cr}')
            if l.cr in seen: E.append(f'SR {k}: duplicate link to {l.cr}')
            seen.add(l.cr)
            if counts[l.type]: in_links.setdefault(l.cr, []).append(k)
            if l.condition.strip():
                nconds += 1
                check_rule(f'SR {k} -> {l.cr} condition', l.condition)
                if not counts[l.type]: W.append(f'SR {k} -> {l.cr}: condition on a non-counting link has no effect')
        if r.coverage_complete and not any(counts[l.type] for l in r.links):
            E.append(f'SR {k}: coverage complete but no counting link')
        if not r.coverage_complete:
            W.append(f'SR {k}: coverage incomplete -> reported as Gap')
    has_child_sp = {r.parent_sp for r in sp.values() if r.parent_sp}
    for k, r in sp.items():
        if role_attr[r.role] == 'own' and r.in_catalogue_scope and k not in sr_of_sp:
            W.append(f'SP {k}: atomic, in scope, but no SR (not atomised -> Gap)')
        if role_attr[r.role] == 'children' and k not in has_child_sp and k not in sr_of_sp:
            W.append(f'SP {k}: umbrella/lead-in without children or SRs')

    # CR
    children = {}
    for k, r in cr.items():
        if r.parent_cr: children.setdefault(r.parent_cr, []).append(k)

    def reached(x):
        return x in in_links or any(reached(c) for c in children.get(x, []))

    def ancestor_linked(x):
        p = cr[x].parent_cr
        while p:
            if p in in_links: return True
            p = cr[p].parent_cr if p in cr else ''
        return False

    def ancestors(x):
        out, p = set(), cr[x].parent_cr
        while p in cr and p not in out:
            out.add(p); p = cr[p].parent_cr
        return out

    fully_refined = {f.cr for c in cr.values() for f in c.refines if f.coverage == 'FULL'}

    def descendants(x):
        out = []
        for c in children.get(x, []):
            out += [c] + descendants(c)
        return out

    def chained(k):
        """k or one of its descendants is itself fully refined: substitution chains are not supported."""
        return any(d in fully_refined for d in [k] + descendants(k))

    def refines_cycle(x):
        stack, seen = [x], set()
        while stack:
            for t in (ref.cr for ref in cr[stack.pop()].refines):
                if t == x: return True
                if t in cr and t not in seen: seen.add(t); stack.append(t)
        return False

    unreached = 0
    for k, r in cr.items():
        if r.parent_cr and r.parent_cr not in cr: E.append(f'CR {k}: unknown parent {r.parent_cr}')
        if k in children and not r.decomposition: E.append(f'CR {k}: has children but no decomposition (AND/OR)')
        for t in (x.cr for x in r.refines):
            if t not in cr: E.append(f'CR {k}: refines unknown CR {t}')
            elif t == k: E.append(f'CR {k}: refines itself')
            elif t in ancestors(k): W.append(f'CR {k}: refines its ancestor {t} (already expressed by parent_cr)')
        tgt = [x.cr for x in r.refines]
        if len(set(tgt)) != len(tgt): E.append(f'CR {k}: duplicate refines entry')
        if tgt and k not in tgt and refines_cycle(k): E.append(f'CR {k}: refines cycle')
        for x in r.refines:
            if x.set and x.coverage != 'FULL': W.append(f'CR {k}: refinement set "{x.set}" on a partial refinement of {x.cr} has no effect')
            if x.coverage == 'FULL' and x.cr in children:
                W.append(f'CR {k}: full refinement of parent CR {x.cr} is not substituted (only leaf CRs are)')
            if x.coverage == 'FULL' and chained(k):
                W.append(f'CR {k}: full refinement of {x.cr} is chained ({k} or a descendant is fully refined itself); '
                         f'{x.cr} is not substituted')
        if r.status != 'DEPRECATED' and not reached(k) and not ancestor_linked(k):
            if missing:
                unreached += 1        # may be reached by a known pack that is not loaded: counted, not warned
            else:
                W.append(f'CR {k}: no counting SR link on itself, its ancestors or descendants (orphan – never assessed)')
        if not r.acceptance_criterion and k not in children:
            W.append(f'CR {k}: no acceptance criterion')
        check_rule(f'CR {k}', r.applicability_rule)

    # CORR, decisions
    seen = set()
    for claimant, c in cat.corr:
        if c.corr_id in seen: E.append(f'CORR {c.corr_id}: duplicate ID')
        seen.add(c.corr_id)
        for x in (c.from_sp, c.to_sp):
            if x not in sp: E.append(f'CORR {c.corr_id}: unknown SP {x}')
            elif p_sd(sp[x].sd_id) not in allowed.get(p_sd(claimant), {p_sd(claimant)}):
                E.append(f'CORR {c.corr_id}: SP {x} of pack {p_sd(sp[x].sd_id)} not visible from pack {p_sd(claimant)} '
                         f'(add it to "requires")')
    ids = [d.dec_id for d in cat.decisions]
    for d in sorted({x for x in ids if ids.count(x) > 1}): E.append(f'DECISIONS {d}: duplicate ID')

    stats = dict(PACKS=len(packs), SD=len(sd), SP=len(sp), SR=len(sr), CR=len(cr), UNREACHED=unreached, LINK=nlinks,
                 COND=nconds, CORR=len(cat.corr))
    return E, W, stats


def report(name, E, W, stats, missing=()):
    """Markdown report; `missing` = known packs not loaded (their CRs are counted as UNREACHED, not warned)."""
    info = ([f'Known packs not loaded: {", ".join(missing)}. CRs not reached by the loaded packs are counted as '
             f'UNREACHED ({stats.get("UNREACHED", 0)}) instead of being warned as orphans.', ''] if missing else [])
    lines = [f'# Catalogue check – {name}', '',
             '| ' + ' | '.join(stats) + ' |', '|' + '---|' * len(stats), '| ' + ' | '.join(str(v) for v in stats.values()) + ' |', '',
             *info, f'## Errors ({len(E)})'] + [f'- {e}' for e in E] + ['', f'## Warnings ({len(W)})'] + [f'- {w}' for w in W]
    return '\n'.join(lines)
