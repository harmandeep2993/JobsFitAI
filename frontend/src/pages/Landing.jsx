import { Link } from 'react-router-dom'

const FEATURES = [
  {
    title: 'Match score',
    desc: 'Get a 0-100 score comparing your skills, experience, and education against the job requirements.',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9"/>
        <path d="M12 7v5l3 3"/>
      </svg>
    ),
  },
  {
    title: 'Keyword analysis',
    desc: 'See exactly which keywords you have and which are missing so you can tailor your resume fast.',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 6h16M4 12h10M4 18h7"/>
      </svg>
    ),
  },
  {
    title: 'Live job fetcher',
    desc: 'Pull listings from Adzuna, Arbeitnow, and Bundesagentur - scored and ranked against your resume.',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
      </svg>
    ),
  },
  {
    title: 'ATS compatibility',
    desc: 'Structural scan for section completeness and formatting issues before you hit submit.',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-5M9 21H5a2 2 0 01-2-2v-5m0 0h18"/>
      </svg>
    ),
  },
  {
    title: 'Resume slots',
    desc: 'Store up to 3 versions - a base resume and tailored copies for specific roles or companies.',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <rect x="5" y="3" width="14" height="18" rx="2"/>
        <path d="M9 8h6M9 12h6M9 16h4"/>
      </svg>
    ),
  },
  {
    title: 'AI insights',
    desc: 'Get actionable strengths, gaps, and improvement suggestions powered by your chosen LLM.',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
      </svg>
    ),
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-bg text-t1">

      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-border bg-surface/80 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-6 h-topbar flex items-center gap-4" style={{ height: 'var(--topbar-h)' }}>
          <div className="flex items-center gap-2.5 flex-1">
            <div className="w-7 h-7 rounded-lg bg-accent flex items-center justify-center">
              <svg width="13" height="13" viewBox="0 0 16 16" fill="white">
                <path d="M8 1L1 4.5v4c0 3.5 2.8 6.2 7 7.5 4.2-1.3 7-4 7-7.5v-4L8 1z"/>
              </svg>
            </div>
            <span className="text-[15px] font-bold tracking-tight">
              Jobs<span className="text-accent">Fit</span>AI
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <Link
              to="/login"
              className="h-8 px-3.5 text-[13px] font-medium text-t2 hover:text-t1 hover:bg-hover rounded-sm transition-colors flex items-center"
            >
              Sign in
            </Link>
            <Link
              to="/login"
              className="h-8 px-4 text-[13px] font-semibold bg-accent text-white rounded-sm hover:bg-accent-h transition-colors flex items-center"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-6 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-accent-s border border-accent/15 text-[12px] font-semibold text-accent mb-7">
          <span className="w-1.5 h-1.5 rounded-full bg-accent" />
          Resume to job-description matcher
        </div>

        <h1 className="text-[clamp(34px,5.5vw,58px)] font-black tracking-tight leading-[1.1] mb-6" style={{ letterSpacing: '-1.5px' }}>
          Know your <em className="text-accent not-italic">fit</em>
          <br />before you apply
        </h1>

        <p className="text-[17px] text-t2 leading-relaxed max-w-xl mx-auto mb-9">
          Upload your resume, paste a job description, and get an AI-powered match score
          with keyword gaps and recommendations in seconds.
        </p>

        <div className="flex items-center justify-center gap-3">
          <Link
            to="/login"
            className="inline-flex items-center gap-2 h-11 px-7 bg-accent text-white rounded font-semibold text-[15px] hover:bg-accent-h transition-all hover:-translate-y-px shadow-md"
          >
            Start free
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 8h10M9 4l4 4-4 4"/>
            </svg>
          </Link>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 h-11 px-6 bg-surface text-t1 border border-border rounded font-medium text-[15px] hover:bg-hover transition-colors"
          >
            Sign in
          </Link>
        </div>
        <p className="text-[12px] text-t3 mt-4">No credit card required.</p>
      </section>

      {/* Features grid */}
      <section className="max-w-4xl mx-auto px-6 pb-20">
        <div className="text-center text-[11px] font-bold uppercase tracking-widest text-t3 mb-8">
          Everything you need
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {FEATURES.map(f => (
            <div
              key={f.title}
              className="card p-5 hover:shadow-md hover:-translate-y-0.5 transition-all cursor-default"
            >
              <div className="w-9 h-9 rounded-sm bg-accent-s border border-accent/12 flex items-center justify-center text-accent mb-3.5">
                {f.icon}
              </div>
              <div className="text-[13.5px] font-semibold text-t1 mb-1.5">{f.title}</div>
              <p className="text-[13px] text-t2 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <div className="border-t border-border bg-surface">
        <div className="max-w-3xl mx-auto px-6 py-16 text-center">
          <h2 className="text-[28px] font-black tracking-tight mb-3" style={{ letterSpacing: '-0.5px' }}>
            Ready to find your <em className="text-accent not-italic">best fit?</em>
          </h2>
          <p className="text-[14px] text-t2 mb-7">Create a free account and run your first analysis in under a minute.</p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 h-11 px-8 bg-accent text-white rounded font-semibold text-[15px] hover:bg-accent-h transition-all shadow-md"
          >
            Get started free
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 8h10M9 4l4 4-4 4"/>
            </svg>
          </Link>
        </div>
      </div>

      <footer className="text-center text-[12px] text-t3 py-5 border-t border-border">
        JobsFitAI - AI-powered resume analysis
      </footer>
    </div>
  )
}
