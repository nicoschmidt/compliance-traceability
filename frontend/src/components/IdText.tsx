import { Link } from 'react-router-dom'
import { hrefFor, idKind, tokenize } from '../data/ids'
import { useIndex, useView } from '../state'

/** Link to one ID (rendered as plain text if the ID is unknown). */
export function IdLink({ id, children }: { id: string; children?: React.ReactNode }) {
  const ix = useIndex()
  const view = useView()
  const kind = idKind(ix, id, view.projectIds)
  if (!kind) return <span className="id unknown" title="not in the loaded catalogue">{children ?? id}</span>
  return <Link className="id" to={hrefFor(ix, id, kind, view)}>{children ?? id}</Link>
}

/** Free text with every known ID turned into a link. */
export function IdText({ text, className }: { text: string | null | undefined; className?: string }) {
  const ix = useIndex()
  const view = useView()
  if (!text) return null
  const known = view.projectIds ? (id: string) => view.projectIds!.cis.has(id) || view.projectIds!.objects.has(id) : undefined
  return (
    <span className={className}>
      {tokenize(ix, String(text), known).map((t, i) => typeof t === 'string' ? t : <IdLink key={i} id={t.id} />)}
    </span>
  )
}
