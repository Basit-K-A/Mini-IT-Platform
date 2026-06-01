/**
 * Ignore stale async results when a newer request was started (e.g. React StrictMode
 * double-mount, fast tab switches, or query changes).
 */
export function createRequestGuard() {
  let generation = 0

  return {
    /** Call at the start of each async load. */
    next() {
      generation += 1
      return generation
    },
    /** True only if no newer load was started after this id was issued. */
    isCurrent(id: number) {
      return id === generation
    },
  }
}
