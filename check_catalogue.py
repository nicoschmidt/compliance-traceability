#!/usr/bin/env python3
"""Catalogue release check (spec § 5.1, § 5.2, § 6.3, § 7) of the master list and its packs.

usage: python check_catalogue.py CATALOGUE_DIR [--pack DIR ...] [--public-only | --no-packs] [--report report.md] [--fmt]
CATALOGUE_DIR is the master list directory (catalogue/). Its public packs are always loaded (unless --no-packs), extra
packs per --pack, CTM_PACKS or ctm.local.json (unless --public-only); spec § 8.3.
--fmt rewrites every JSON file in canonical form first (2-space indent, model field order, defaults omitted).
Exit code 1 if a file does not validate or errors were found (warnings do not fail).
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ctm import checks
from ctm.store import CatalogueError, format_tree, load_catalogue, resolve_packs


def add_pack_options(ap):
    ap.add_argument('--pack', action='append', metavar='DIR',
                    help='extra pack, or directory of packs (repeatable); default: CTM_PACKS or ctm.local.json')
    ap.add_argument('--public-only', action='store_true', help='master list + its public packs only (no extra packs)')
    ap.add_argument('--no-packs', action='store_true', help='master list only')


def pack_args(a):
    """(packs, defaults) for load_catalogue / resolve_packs from the options of add_pack_options."""
    return ([] if a.public_only or a.no_packs else a.pack), not a.no_packs


def check(root, packs=None, defaults=True, missing_out=None):
    """(errors, warnings, stats); a file that does not validate is reported as the only error.
    missing_out (list) receives the known packs that are not loaded."""
    try:
        cat = load_catalogue(root, packs, defaults)
    except CatalogueError as ex:
        return [str(ex)], [], {}
    if missing_out is not None:
        missing_out += cat.missing_packs()
    return checks.check(cat)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('catalogue'); ap.add_argument('--report')
    ap.add_argument('--fmt', action='store_true')
    add_pack_options(ap)
    a = ap.parse_args()
    packs, defaults = pack_args(a)
    if a.fmt:
        try:
            for p in format_tree(a.catalogue, resolve_packs(a.catalogue, packs, defaults)):
                print('formatted', p)
        except CatalogueError as ex:
            print(ex); sys.exit(1)
    missing = []
    E, W, stats = check(a.catalogue, packs, defaults, missing)
    txt = checks.report(os.path.basename(os.path.abspath(a.catalogue)), E, W, stats, missing)
    print(txt)
    if a.report:
        open(a.report, 'w', encoding='utf-8').write(txt)
    sys.exit(1 if E else 0)
