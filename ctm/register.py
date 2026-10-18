"""REGISTER sheet: writes the vocabularies of ctm/vocab.py into workbooks and reads them back (spec § 6.3, rules V1-V5).

Sheet layout (one row per entry, lists in contiguous blocks):
  A List | B Key | C Label | D Order | E Colour | F Attribute | G Description | H Deprecated
Defined names written into every workbook:
  L_<LIST>       -> label range of the list (drop-downs)
  <LIST>_<KEY>   -> the single label cell (formulas, conditional formatting)
  REG_LIST / REG_KEY / REG_LABEL / REG_ATTR -> whole columns (attribute look-ups)
"""
import re
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.styles import Font, PatternFill, Alignment

from .vocab import DEFAULT

NAME_SAFE = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


def write_register(wb, reg=None):
    """Write the REGISTER sheet and all defined names. Returns {list: {key: cell_ref}}."""
    reg = reg or DEFAULT
    ws = wb.create_sheet('REGISTER')
    hdr = ['List', 'Key', 'Label', 'Order', 'Colour', 'Attribute', 'Description', 'Deprecated']
    for j, h in enumerate(hdr, 1):
        c = ws.cell(row=1, column=j, value=h)
        c.font = Font(name='Arial', bold=True, color='FFFFFF', size=10)
        c.fill = PatternFill('solid', fgColor='1F3864')
    for col, w in zip('ABCDEFGH', [11, 14, 26, 7, 9, 12, 70, 10]):
        ws.column_dimensions[col].width = w
    r = 2
    refs = {}
    body = Font(name='Arial', size=10)
    for lst, entries in reg.items():
        first = r
        refs[lst] = {}
        for i, (key, label, colour, attr, desc) in enumerate(entries, 1):
            assert NAME_SAFE.match(f'{lst}_{key}'), (lst, key)
            vals = [lst, key, label, i, colour, attr, desc, '']
            for j, v in enumerate(vals, 1):
                c = ws.cell(row=r, column=j, value=v)
                c.font = body
            if colour:
                ws.cell(row=r, column=5).fill = PatternFill('solid', fgColor=colour)
            name = f'{lst}_{key}'
            ref = f"REGISTER!$C${r}"
            wb.defined_names[name] = DefinedName(name, attr_text=ref)
            refs[lst][key] = ref
            r += 1
        wb.defined_names[f'L_{lst}'] = DefinedName(f'L_{lst}', attr_text=f"REGISTER!$C${first}:$C${r - 1}")
    last = r - 1
    for nm, col in [('REG_LIST', 'A'), ('REG_KEY', 'B'), ('REG_LABEL', 'C'), ('REG_ATTR', 'F')]:
        wb.defined_names[nm] = DefinedName(nm, attr_text=f"REGISTER!${col}$2:${col}${last}")
    ws.freeze_panes = 'C2'
    ws.auto_filter.ref = f'A1:H{last}'
    return refs


def read_register(wb):
    """Read REGISTER sheet -> {list: [dict(key,label,colour,attr,desc,deprecated)]} (keeps edits made in Excel)."""
    ws = wb['REGISTER']
    out = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        lst, key, label, order, colour, attr, desc, dep = (list(row) + [None] * 8)[:8]
        out.setdefault(lst, []).append(dict(key=key, label=label, colour=colour or '', attr=attr or '',
                                            desc=desc or '', deprecated=(dep or '')))
    return out


def as_default_format(reg_read):
    return {lst: [(e['key'], e['label'], e['colour'], e['attr'], e['desc']) for e in entries]
            for lst, entries in reg_read.items()}


def labels(reg_read, lst, include_deprecated=False):
    return [e['label'] for e in reg_read[lst] if include_deprecated or not e['deprecated']]


def label(reg_read, lst, key):
    for e in reg_read[lst]:
        if e['key'] == key:
            return e['label']
    raise KeyError((lst, key))
