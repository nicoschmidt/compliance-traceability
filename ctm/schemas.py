"""Generate schemas/<name>.schema.json from ctm/model.py (referenced by "$schema" in every data file).

usage: python -m ctm.schemas
"""
import json
import os

from .model import FILE_MODELS
from .store import SCHEMA_DIR


def render():
    """{file name: schema text}"""
    out = {}
    for name, cls in FILE_MODELS.items():
        s = cls.model_json_schema(by_alias=True)
        s = {'$schema': 'https://json-schema.org/draft/2020-12/schema', '$id': f'{name}.schema.json', **s}
        out[f'{name}.schema.json'] = json.dumps(s, indent=2, ensure_ascii=False) + '\n'
    return out


def main():
    os.makedirs(SCHEMA_DIR, exist_ok=True)
    for fn, txt in render().items():
        with open(os.path.join(SCHEMA_DIR, fn), 'w', encoding='utf-8', newline='\n') as f:
            f.write(txt)
        print(os.path.join(SCHEMA_DIR, fn))


if __name__ == '__main__':
    main()
