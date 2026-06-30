/**
 * Shared UI primitives used across all tab pages.
 * Every tab must use these so layout, spacing, and typography are identical.
 */

// === Page-level ===

export function PageHeader({ title, description, action }) {
  return (
    <div className="flex items-start justify-between gap-4 pb-5 mb-6 border-b border-border">
      <div>
        <h1 className="text-[18px] font-semibold text-t1 leading-snug">{title}</h1>
        {description && (
          <p className="text-[13.5px] text-t2 mt-1 leading-relaxed">{description}</p>
        )}
      </div>
      {action && <div className="flex-shrink-0 pt-0.5">{action}</div>}
    </div>
  )
}

// === Cards ===

export function Card({ children, className = '' }) {
  return (
    <div className={`bg-surface border border-border rounded-lg ${className}`}>
      {children}
    </div>
  )
}

export function CardBody({ children, className = '' }) {
  return <div className={`p-5 ${className}`}>{children}</div>
}

// Card with an inline title bar
export function CardSection({ title, children, action }) {
  return (
    <Card>
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-border">
        <span className="text-[13px] font-semibold text-t1">{title}</span>
        {action && <div>{action}</div>}
      </div>
      <CardBody>{children}</CardBody>
    </Card>
  )
}

// === Labels ===

export function SectionLabel({ children }) {
  return (
    <div className="text-[11px] font-semibold text-t3 uppercase tracking-[0.06em] mb-2.5">
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

export function Spinner({ size = 20 }) {
  return (
    <svg
      className="animate-spin text-accent"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
    >
      <path d="M21 12a9 9 0 11-6-8.5" />
    </svg>
  )
}

export function PageSpinner({ label = 'Loading...' }) {
  return (
    <Card>
      <CardBody className="py-14 flex flex-col items-center gap-3 text-center">
        <Spinner size={24} />
        <span className="text-[13px] text-t2">{label}</span>
      </CardBody>
    </Card>
  )
}

export function EmptyState({ icon, title, description, action }) {
  return (
    <Card>
      <CardBody className="py-14 flex flex-col items-center gap-2 text-center">
        {icon && (
          <div className="w-11 h-11 rounded-full bg-surface-2 flex items-center justify-center text-t3 mb-1">
            {icon}
          </div>
        )}
        <div className="text-[14px] font-medium text-t1">{title}</div>
        {description && (
          <p className="text-[13px] text-t2 max-w-xs leading-relaxed">{description}</p>
        )}
        {action && <div className="mt-3">{action}</div>}
      </CardBody>
    </Card>
  )
}

// === List rows ===

export function ListRow({ children, className = '' }) {
  return (
    <div className={`bg-surface border border-border rounded-lg px-4 py-3 flex items-center gap-3.5 ${className}`}>
      {children}
    </div>
  )
}

// === Score badge ===

export function ScoreBadge({ score, size = 'md' }) {
  const color =
    score >= 80 ? { text: '#16a34a', bg: 'var(--green-bg)', border: 'var(--green-bd)' } :
    score >= 60 ? { text: '#4f46e5', bg: 'var(--blue-bg)',  border: 'var(--blue-bd)' } :
    score >= 40 ? { text: '#d97706', bg: 'var(--amber-bg)', border: 'var(--amber-bd)' } :
                  { text: '#dc2626', bg: 'var(--red-bg)',   border: 'var(--red-bd)' }

  const dim = size === 'sm' ? 'w-9 h-9 text-[12px]' : 'w-11 h-11 text-[13px]'

  return (
    <div
      className={`flex items-center justify-center rounded-lg font-bold border flex-shrink-0 ${dim}`}
      style={{ color: color.text, background: color.bg, borderColor: color.border }}
    >
      {Math.round(score)}
    </div>
  )
}

export function ScorePill({ score }) {
  const color =
    score >= 80 ? { text: '#16a34a', bg: 'var(--green-bg)', border: 'var(--green-bd)' } :
    score >= 60 ? { text: '#4f46e5', bg: 'var(--blue-bg)',  border: 'var(--blue-bd)' } :
    score >= 40 ? { text: '#d97706', bg: 'var(--amber-bg)', border: 'var(--amber-bd)' } :
                  { text: '#dc2626', bg: 'var(--red-bg)',   border: 'var(--red-bd)' }
  return (
    <span
      className="px-2 py-0.5 rounded-sm text-[12px] font-bold border flex-shrink-0"
      style={{ color: color.text, background: color.bg, borderColor: color.border }}
    >
      {Math.round(score)}
    </span>
  )
}

export function ScoreLabel({ score }) {
  if (score >= 80) return <span className="text-[12.5px] font-semibold" style={{ color: '#16a34a' }}>Excellent</span>
  if (score >= 60) return <span className="text-[12.5px] font-semibold" style={{ color: '#4f46e5' }}>Good</span>
  if (score >= 40) return <span className="text-[12.5px] font-semibold" style={{ color: '#d97706' }}>Partial</span>
  return <span className="text-[12.5px] font-semibold" style={{ color: '#dc2626' }}>Poor</span>
}
