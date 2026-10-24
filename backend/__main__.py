"""Run the web viewer (local use only).

  python -m backend CATALOGUE_DIR [--pack DIR ...] [--public-only | --no-packs] [--internal]
                    [--projects DIR ...] [--host 127.0.0.1] [--port 8765]

Serves the API under /api and, when it has been built (cd frontend && npm run build), the frontend from frontend/dist.
Project seeds are read from --projects (repeatable; default: projects/ in the repository, if present).
"""
import argparse
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from check_catalogue import add_pack_options, pack_args   # noqa: E402
from backend.app import create_app                         # noqa: E402


def main():
    ap = argparse.ArgumentParser(prog='python -m backend')
    ap.add_argument('catalogue')
    ap.add_argument('--internal', action='store_true', help='serve verbatim text of licensed sources (spec § 7)')
    ap.add_argument('--projects', action='append', metavar='DIR', help='directory of project seeds (repeatable)')
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=8765)
    add_pack_options(ap)
    a = ap.parse_args()
    projects = a.projects or [p for p in [os.path.join(REPO, 'projects')] if os.path.isdir(p)]
    packs, defaults = pack_args(a)
    app = create_app(a.catalogue, packs, defaults, internal=a.internal, projects=projects,
                     static_dir=os.path.join(REPO, 'frontend', 'dist'))
    import uvicorn
    uvicorn.run(app, host=a.host, port=a.port)


if __name__ == '__main__':
    main()
