/**
 * Shared UI primitives - used by every tab to guarantee consistent layout,
 * typography, spacing, and interactive patterns across the whole app.
 */

// === Page-level ===

export function PageHeader({ title, description, action }) {
  return (
    <div className="flex items-start justify-between gap-4 pb-5 mb-6 border-b border-border/10">
      <div>
        <h1 className="text-[19px] font-bold text-t1 leading-snug tracking-[-0.3px]">{title}</h1>
        {description && (
          <p className="text-[13.5px] text-t2 mt-1 leading-relaxed max-w-xl">{description}</p>
        )}
      </div>
      {action && <div className="flex-shrink-0 pt-0.5">{action}</div>}
    </div>
  )
}

// === Cards ===

export function Card({ children, className = '' }) {
  return (
    <div className={`card ${className}`}>
      {children}
    </div>
  )
}

export function CardBody({ children, className = '' }) {
  return <div className={`p-5 ${className}`}>{children}</div>
}

export function CardSection({ title, children, action }) {
  return (
    <Card>
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-border/8">
        <span className="text-[13px] font-semibold text-t1">{title}</span>
        {action && <div>{action}</div>}
      </div>
      <CardBody>{children}</CardBody>
    </Card>
  )
}

// === Typography ===

export function SectionLabel({ children }) {
  return (
    <div className="text-[11px] font-semibold text-t3 uppercase tracking-[0.07em] mb-3">
      {children}
    </div>
  )
}

export function FieldLabel({ children, hint }) {
  return (
    <label className="block text-[12.5px] font-medium text-t2 mb-1.5">
      {children}
      {hint && <span className="font-normal text-t3 ml-1">{hint}</span>}
    </label>
  )
}

// === States ===

export function Spinner({ size = 18, className = '' }) {
  return (
    <svg
      className={`animate-spin text-accent ${className}`}
      width={size} height={size}
      viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"
    >
      <path d="M21 12a9 9 0 11-6-8.5" />
    </svg>
  )
}

export function PageSpinner({ label = 'Loading...' }) {
  return (
    <Card>
      <CardBody className="py-16 flex flex-col items-center gap-3">
        <Spinner size={24} />
        <span className="text-[13px] text-t2">{label}</span>
      </CardBody>
    </Card>
  )
}

export function EmptyState({ icon, title, description, action }) {
  return (
    <Card>
      <CardBody className="py-16 flex flex-col items-center gap-2 text-center">
        {icon && (
          <div className="w-12 h-12 rounded-full bg-surface-2 flex items-center justify-center text-t3 mb-1">
            {icon}
          </div>
        )}
        <div className="text-[14px] font-semibold text-t1">{title}</div>
        {description && <p className="text-[13px] text-t2 max-w-xs leading-relaxed">{description}</p>}
        {action && <div className="mt-3">{action}</div>}
      </CardBody>
    </Card>
  )
}

export function ListRow({ children, className = '' }) {
  return (
    <div className={`bg-surface border border-border/8 rounded-lg px-4 py-3 flex items-center gap-3.5 ${className}`}>
      {children}
    </div>
  )
}

// === Score display ===

const SCORE_COLORS = {
  excellent: { hex: '#16a34a', bg: 'rgba(22,163,74,0.08)',   border: 'rgba(22,163,74,0.2)' },
  good:      { hex: '#6366f1', bg: 'rgba(99,102,241,0.08)',  border: 'rgba(99,102,241,0.2)' },
  partial:   { hex: '#d97706', bg: 'rgba(217,119,6,0.08)',   border: 'rgba(217,119,6,0.2)' },
  poor:      { hex: '#dc2626', bg: 'rgba(220,38,38,0.08)',   border: 'rgba(220,38,38,0.2)' },
}

function getScoreColors(score) {
  if (score >= 80) return SCORE_COLORS.excellent
  if (score >= 60) return SCORE_COLORS.good
  if (score >= 40) return SCORE_COLORS.partial
  return SCORE_COLORS.poor
}

export function ScoreBadge({ score, size = 'md' }) {
  const c = getScoreColors(score)
  const dim = size === 'sm' ? 'w-9 h-9 text-[12px]' : 'w-11 h-11 text-[13px]'
  return (
    <div
      className={`flex items-center justify-center rounded-lg font-bold border flex-shrink-0 ${dim}`}
      style={{ color: c.hex, background: c.bg, borderColor: c.border }}
    >
      {Math.round(score)}
    </div>
  )
}

export function ScorePill({ score }) {
  const c = getScoreColors(score)
  return (
    <span
      className="px-2 py-0.5 rounded-sm text-[12px] font-bold border flex-shrink-0"
      style={{ color: c.hex, background: c.bg, borderColor: c.border }}
    >
      {Math.round(score)}
    </span>
  )
}

export function ScoreLabel({ score }) {
  const c = getScoreColors(score)
  const label = score >= 80 ? 'Excellent' : score >= 60 ? 'Good' : score >= 40 ? 'Partial' : 'Poor'
  return <span className="text-[12.5px] font-semibold" style={{ color: c.hex }}>{label}</span>
}
