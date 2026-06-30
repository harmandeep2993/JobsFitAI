import { Link } from 'react-router-dom'

const features = [
  {
    title: 'Instant match score',
    desc: 'Get a 0-100 score comparing your resume skills, experience, and education against the role requirements.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="10" cy="10" r="8"/><path d="M10 6v4l3 3"/>
      </svg>
    ),
  },
  {
    title: 'Keyword analysis',
    desc: 'See exactly which keywords are required, which you have, and which are missing from your resume.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 10h12M4 6h8M4 14h6"/>
      </svg>
    ),
  },
  {
    title: 'Live Job Fetcher',
    desc: 'Pull listings from Adzuna, Arbeitnow, and Bundesagentur, then score each one against your resume.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 17l4-4 3 3 5-8 4 4"/>
      </svg>
    ),
  },
  {
    title: 'ATS check',
    desc: 'Structural scan for section completeness and formatting flags so your document passes ATS scanners.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8 1L2 4v4c0 3.3 2.5 5.8 6 7 3.5-1.2 6-3.7 6-7V4L8 1z"/>
        <polyline points="5.5,10 7.5,12 12,7"/>
      </svg>
    ),
  },
  {
    title: 'Resume slots',
    desc: 'Store up to 3 resume versions. Keep a base resume and tailored copies for different roles.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="11" height="14" rx="1.5"/><rect x="5" y="1" width="11" height="14" rx="1.5"/>
        <line x1="8" y1="7" x2="13" y2="7"/><line x1="8" y1="10" x2="11" y2="10"/>
      </svg>
    ),
  },
  {
    title: 'AI recommendations',
    desc: 'Actionable suggestions to improve your resume for the specific role, powered by your chosen LLM.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="10,2 12.5,7.5 18.5,8.2 14.2,12.3 15.4,18.2 10,15.3 4.6,18.2 5.8,12.3 1.5,8.2 7.5,7.5"/>
      </svg>
    ),
  },
]

export default function Landing({ dark, onToggleDark }) {
  return (
    <div className="min-h-screen bg-bg text-t1">
      {/* Nav */}
      <header className="sticky top-0 z-50 border-b border-border backdrop-blur-md bg-bg/80 flex items-center px-8 h-topbar gap-3">
        <div className="flex items-center gap-2 flex-1">
          <div className="w-7 h-7 rounded-[7px] bg-accent flex items-center justify-center text-white text-[11px] font-black">JF</div>
          <span className="text-[17px] font-black tracking-tight">Jobs<em className="text-accent not-italic">Fit</em>AI</span>
        </div>
        <nav className="flex items-center gap-2">
          <button
            onClick={onToggleDark}
            className="p-2 rounded-s text-t2 hover:text-t1 hover:bg-hover transition-colors"
            title="Toggle theme"
          >
            {dark ? (
              <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                <circle cx="10" cy="10" r="4"/><path d="M10 2v2M10 16v2M2 10h2M16 10h2M4.9 4.9l1.4 1.4M13.7 13.7l1.4 1.4M4.9 15.1l1.4-1.4M13.7 6.3l1.4-1.4"/>
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
                <path d="M17.5 12.5A7.5 7.5 0 017.5 2.5a7.5 7.5 0 100 15 7.5 7.5 0 0010-5z"/>
              </svg>
            )}
          </button>
          <Link to="/login" className="text-[13.5px] font-medium text-t2 hover:text-t1 px-3 py-1.5 rounded-s hover:bg-hover transition-colors">
            Sign in
          </Link>
          <Link to="/login" className="text-[13.5px] font-semibold bg-accent text-white px-4 py-1.5 rounded-s hover:bg-accent-h transition-colors shadow-sm">
            Get started
          </Link>
        </nav>
      </header>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-8 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-accent-s border border-accent/15 text-xs font-semibold text-accent mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-accent" />
          Resume-to-JD matcher
        </div>
        <h1 className="text-[clamp(32px,5vw,54px)] font-black tracking-[-1.5px] leading-[1.1] mb-5">
          Know your <em className="text-accent not-italic">fit</em><br />before you apply
        </h1>
        <p className="text-[17px] text-t2 leading-relaxed max-w-lg mx-auto mb-9">
          Upload your resume, paste a job description, and get an AI-powered match score with keyword gaps and recommendations in seconds.
        </p>
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <Link
            to="/login"
            className="inline-flex items-center gap-2 px-7 py-3 bg-accent text-white rounded-s text-[15px] font-bold hover:bg-accent-h transition-all hover:-translate-y-px shadow-[0_2px_8px_rgba(232,71,26,0.3),0_8px_24px_rgba(232,71,26,0.2)]"
          >
            Start analyzing
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 8h10M9 4l4 4-4 4"/>
            </svg>
          </Link>
          <Link to="/login" className="inline-flex items-center gap-2 px-7 py-3 bg-surface text-t1 border border-border rounded-s text-[15px] font-semibold hover:bg-surface-c transition-colors">
            Sign in
          </Link>
        </div>
        <p className="text-xs text-t3 mt-4">No credit card required.</p>
      </section>

      {/* Features */}
      <section className="max-w-4xl mx-auto px-8 pb-20">
        <p className="text-center text-[11px] font-bold uppercase tracking-[1.2px] text-t3 mb-9">What you get</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {features.map(f => (
            <div key={f.title} className="bg-surface border border-border rounded p-5 shadow-s hover:shadow hover:-translate-y-0.5 transition-all">
              <div className="w-9 h-9 rounded-[9px] bg-accent-s border border-accent/12 flex items-center justify-center text-accent mb-3">
                {f.icon}
              </div>
              <div className="text-sm font-bold mb-1.5">{f.title}</div>
              <p className="text-[13px] text-t2 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA strip */}
      <div className="bg-surface border-y border-border px-8 py-12 text-center">
        <h2 className="text-2xl font-black tracking-tight mb-2.5">
          Ready to find your <em className="text-accent not-italic">best fit?</em>
        </h2>
        <p className="text-sm text-t2 mb-6">Create a free account and run your first analysis in under a minute.</p>
        <Link
          to="/login"
          className="inline-flex items-center gap-2 px-7 py-3 bg-accent text-white rounded-s text-[15px] font-bold hover:bg-accent-h transition-all shadow-[0_2px_8px_rgba(232,71,26,0.3)]"
        >
          Get started free
          <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 8h10M9 4l4 4-4 4"/>
          </svg>
        </Link>
      </div>

      <footer className="text-center text-xs text-t3 py-5">
        JobsFitAI - AI-powered resume analysis
      </footer>
    </div>
  )
}
