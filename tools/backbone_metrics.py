#!/usr/bin/env python3
"""Checkpoint metrics of a catalogue (docs/Checkpoint_P2-1_Legal_Backbone.md, §§ 1–2).

usage: python tools/backbone_metrics.py CATALOGUE_DIR [--json OUT.json] [--pack DIR ...] [--public-only | --no-packs]
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ctm import vocab                       # noqa: E402
from ctm.store import load_catalogue        # noqa: E402
from check_catalogue import add_pack_options, pack_args   # noqa: E402

STRUCTURAL = {'UMBRELLA', 'LEADIN', 'DEF', 'SCOPE', 'INFO', 'CATNA'}


def metrics(cat):
    sds = [sd for sd in cat.sds if any(p.sd_id == sd for p in cat.sps.values())]
    stats = {}
    for p in cat.sps.values():
        st = stats.setdefault(p.sd_id, dict(listed=0, atomised=0, oos=0, structural=0))
        st['listed'] += 1
        if p.role in STRUCTURAL:
            st['structural'] += 1
        else:
            st['atomised' if p.in_catalogue_scope else 'oos'] += 1
    links = [(cat.sr_sd[sr_id], l) for _, sr_id, l in cat.links()]
    reach = {}
    for sd, l in links:
        reach.setdefault(l.cr, set()).add(sd)
    first = sds[0]
    first_crs = {l.cr for sd, l in links if sd == first}
    parents = {c.parent_cr for c in cat.crs.values() if c.parent_cr}

    def covered(cid):                       # reached directly or via a linked ancestor
        while cid:
            if cid in reach: return True
            cid = cat.crs[cid].parent_cr
        return False

    leaves = [c for c in cat.crs.values() if c.cr_id not in parents]
    m = dict(stats=stats,
             sr={sd: sum(1 for v in cat.sr_sd.values() if v == sd) for sd in sds},
             links=len(links),
             links_by_type={vocab.label_of('LINKTYPE', k): sum(1 for _, l in links if l.type == k)
                            for k in vocab.keys('LINKTYPE')},
             cr_total=len(cat.crs), cr_parents=len(parents), cr_leaves=len(leaves),
             cr_reached_by={'+'.join(sorted(v)): n for v, n in
                            _count(frozenset(v) for v in reach.values()).items()},
             cr_unreached=[c.cr_id for c in leaves if not covered(c.cr_id)],
             packs_missing=cat.missing_packs(),
             reuse={sd: dict(links=sum(1 for s, _ in links if s == sd),
                             onto_first=sum(1 for s, l in links if s == sd and l.cr in first_crs))
                    for sd in sds[1:]},
             by_level=_count(c.object_level for c in leaves), by_domain=_count(c.domain for c in leaves))
    return m


def _count(it):
    out = {}
    for x in it:
        out[x] = out.get(x, 0) + 1
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('catalogue'); ap.add_argument('--json')
    add_pack_options(ap)
    a = ap.parse_args()
    m = metrics(load_catalogue(a.catalogue, *pack_args(a)))
    txt = json.dumps(m, indent=1, ensure_ascii=False)
    print(txt)
    if a.json:
        open(a.json, 'w', encoding='utf-8').write(txt)
