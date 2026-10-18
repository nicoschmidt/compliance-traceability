"""Applicability rule language (spec § 4.6).

  rule    := 'TRUE' | 'FALSE' | expr
  expr    := term ('OR' term)*
  term    := factor ('AND' factor)*
  factor  := 'NOT' factor | '(' expr ')' | cmp
  cmp     := TAG '=' VALUE | TAG '!=' VALUE | TAG 'in' '{' VALUE (',' VALUE)* '}'

Evaluation is three-valued: True / False / None (unknown: tag unset or 'tbd').
An empty rule means TRUE.
"""
import re

TOKEN = re.compile(r'\s*(\(|\)|\{|\}|,|!=|=|[^\s(){},=!]+)')


class RuleError(ValueError):
    pass


def tokenize(s):
    s = s.strip()
    pos, out = 0, []
    while pos < len(s):
        m = TOKEN.match(s, pos)
        if not m or m.end() == pos:
            raise RuleError(f'cannot parse near: {s[pos:]!r}')
        out.append(m.group(1))
        pos = m.end()
    return out


def parse(rule):
    """Return AST. Nodes: ('const',bool) ('and',[..]) ('or',[..]) ('not',x) ('eq',tag,val) ('ne',tag,val) ('in',tag,[vals])"""
    if rule is None or str(rule).strip() == '':
        return ('const', True)
    toks = tokenize(str(rule))
    i = 0

    def peek():
        return toks[i] if i < len(toks) else None

    def take(expected=None):
        nonlocal i
        if i >= len(toks):
            raise RuleError('unexpected end of rule')
        t = toks[i]
        if expected and t.upper() != expected.upper():
            raise RuleError(f'expected {expected!r}, got {t!r}')
        i += 1
        return t

    def expr():
        items = [term()]
        while peek() and peek().upper() == 'OR':
            take(); items.append(term())
        return items[0] if len(items) == 1 else ('or', items)

    def term():
        items = [factor()]
        while peek() and peek().upper() == 'AND':
            take(); items.append(factor())
        return items[0] if len(items) == 1 else ('and', items)

    def factor():
        t = peek()
        if t is None:
            raise RuleError('unexpected end of rule')
        if t.upper() == 'NOT':
            take(); return ('not', factor())
        if t == '(':
            take(); e = expr(); take(')'); return e
        if t.upper() in ('TRUE', 'FALSE'):
            take(); return ('const', t.upper() == 'TRUE')
        tag = take()
        op = take()
        if op == '=':
            return ('eq', tag, take())
        if op == '!=':
            return ('ne', tag, take())
        if op.lower() == 'in':
            take('{'); vals = [take()]
            while peek() == ',':
                take(); vals.append(take())
            take('}')
            return ('in', tag, vals)
        raise RuleError(f'unknown operator {op!r} after tag {tag!r}')

    ast = expr()
    if i != len(toks):
        raise RuleError(f'unexpected token {toks[i]!r}')
    return ast


def refs(ast):
    """[(tag, [values])] referenced in the rule."""
    k = ast[0]
    if k == 'const':
        return []
    if k in ('and', 'or'):
        return [x for a in ast[1] for x in refs(a)]
    if k == 'not':
        return refs(ast[1])
    if k in ('eq', 'ne'):
        return [(ast[1], [ast[2]])]
    return [(ast[1], ast[2])]


UNKNOWN = {None, '', 'tbd'}


def evaluate(ast, tags):
    """tags: {tag: value}. Returns True/False/None."""
    k = ast[0]
    if k == 'const':
        return ast[1]
    if k == 'not':
        v = evaluate(ast[1], tags)
        return None if v is None else not v
    if k == 'and':
        vals = [evaluate(a, tags) for a in ast[1]]
        if False in vals: return False
        return None if None in vals else True
    if k == 'or':
        vals = [evaluate(a, tags) for a in ast[1]]
        if True in vals: return True
        return None if None in vals else False
    v = tags.get(ast[1])
    if v in UNKNOWN:
        return None
    v = str(v)
    if k == 'eq': return v == ast[2]
    if k == 'ne': return v != ast[2]
    return v in ast[2]


def unknown_tags(ast, tags):
    return sorted({t for t, _ in refs(ast) if tags.get(t) in UNKNOWN})
