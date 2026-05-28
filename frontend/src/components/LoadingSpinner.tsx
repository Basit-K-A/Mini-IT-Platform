export function LoadingSpinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="loading" role="status" aria-live="polite">
      <div className="loading__spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}
