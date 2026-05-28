interface StatCardProps {
  label: string
  value: string | number
  hint?: string
  accent?: 'default' | 'success' | 'warning' | 'danger'
}

export function StatCard({ label, value, hint, accent = 'default' }: StatCardProps) {
  return (
    <div className={`stat-card stat-card--${accent}`}>
      <p className="stat-card__label">{label}</p>
      <p className="stat-card__value">{value}</p>
      {hint ? <p className="stat-card__hint">{hint}</p> : null}
    </div>
  )
}
