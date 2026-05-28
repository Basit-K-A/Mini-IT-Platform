import type { BadgeVariant } from '../utils/status'

interface BadgeProps {
  label: string
  variant?: BadgeVariant
}

export function Badge({ label, variant = 'neutral' }: BadgeProps) {
  return <span className={`badge badge--${variant}`}>{label}</span>
}
