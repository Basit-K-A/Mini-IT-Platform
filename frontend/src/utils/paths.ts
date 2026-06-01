/**
 * App paths that work in dev (base /) and production behind nginx (/app/).
 */
export function toAppPath(path: string): string {
  const base = import.meta.env.BASE_URL.replace(/\/?$/, '/')
  const segment = path.replace(/^\//, '')
  return `${base}${segment}`
}
