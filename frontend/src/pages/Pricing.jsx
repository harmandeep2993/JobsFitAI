/**
 * Pricing page - free vs pro plan cards with full feature matrix.
 */
import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, useInView } from 'framer-motion'

function FadeIn({ children, delay = 0, y = 16, className = '' }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-60px' })
  return (
    <motion.div ref={ref} className={className}
      initial={{ opacity: 0, y }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.5, delay, ease: [0.25, 0.1, 0.25, 1] }}>
      {children}
    </motion.div>
  )
}

const CHECK  = <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="#16a34a" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M2.5 8l3.5 3.5 7.5-7"/></svg>
const CROSS  = <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="rgba(0,0,0,0.18)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3l10 10M13 3L3 13"/></svg>
const PROCHECK = <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M2.5 8l3.5 3.5 7.5-7"/></svg>

const MATRIX = [
  { section: 'Analyzer', rows: [
    { label: 'Resume analyzer (unlimited)', free: true, pro: true },
    { label: 'AI match score (0-100)',       free: true, pro: true },
    { label: 'Section-by-section breakdown', free: true, pro: true },
    { label: 'Keyword gap analysis',          free: true, pro: true },
    { label: 'AI strengths and gaps',         free: true, pro: true },
    { label: 'Profile summary',               free: true, pro: true },
  ]},
  { section: 'Resumes', rows: [
    { label: '3 resume slots',                free: true,  pro: true },
    { label: 'PDF and DOCX upload',           free: true,  pro: true },
    { label: 'In-app resume preview',         free: true,  pro: true },
    { label: 'Resume rename and labels',       free: true,  pro: true },
  ]},
  { section: 'Job matching', rows: [
    { label: 'Manual job description paste',   free: true,  pro: true },
    { label: 'Adzuna Germany live search',     free: true,  pro: true },
    { label: 'Arbeitnow feed',                 free: true,  pro: true },
    { label: 'Bundesagentur fur Arbeit',       free: true,  pro: true },
    { label: 'Scheduled auto-fetch',           free: false, pro: true },
    { label: 'Hourly or daily scan',           free: false, pro: true },
    { label: 'CSV export of all matches',      free: false, pro: true },
  ]},
  { section: 'ATS check', rows: [
    { label: 'ATS compatibility scan',        free: true,  pro: true },
    { label: 'Section completeness check',    free: true,  pro: true },
    { label: 'Formatting warnings',           free: true,  pro: true },
    { label: 'AI-powered ATS optimise',       free: false, pro: true },
  ]},
  { section: 'AI / LLM', rows: [
    { label: 'OpenAI GPT-4o',                 free: true,  pro: true },
    { label: 'Groq (fast, free tier)',        free: true,  pro: true },
    { label: 'Local Ollama model',            free: true,  pro: true },
    { label: 'Priority LLM routing',          free: false, pro: true },
  ]},
]

const FAQ_PRICING = [
  { q: 'Can I cancel my Pro subscription at any time?', a: 'Yes. You can cancel from your account settings with one click. Your Pro features stay active until the end of the billing period.' },
  { q: 'Is the free plan really free forever?', a: 'Yes. The free plan includes the full analyzer, ATS check, and resume storage with no time limit. We do not require a credit card to sign up.' },
  { q: 'What payment methods are accepted?', a: 'We accept all major credit cards (Visa, Mastercard, Amex) and SEPA direct debit for users in Germany and the EU.' },
  { q: 'Do you offer student or non-profit discounts?', a: 'Yes - send us a short note from your university or organisation email and we will apply a 50% discount to the Pro plan.' },
]

export default function Pricing() {
  const [open, setOpen] = useState(null)
  return (
    <div className="min-h-screen" style={{ background: 'rgb(248,248,250)', color: 'rgb(15,15,20)' }}>

      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-black/[0.07]"
        style={{ background: 'rgba(255,255,255,0.88)', backdropFilter: 'blur(16px)' }}>
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2.5 flex-1">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'rgb(99,102,241)' }}>
              <svg width="13" height="13" viewBox="0 0 16 16" fill="white"><path d="M8 1L1 4.5v4c0 3.5 2.8 6.2 7 7.5 4.2-1.3 7-4 7-7.5v-4L8 1z"/></svg>
            </div>
            <span className="text-[15px] font-bold tracking-tight" style={{ fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
              Jobs<span style={{ color: 'rgb(99,102,241)' }}>Fit</span>AI
            </span>
          </Link>
          <Link to="/login"
            className="h-8 px-4 text-[13px] font-semibold text-white rounded-lg flex items-center"
            style={{ background: 'rgb(99,102,241)' }}
            onMouseEnter={e => e.currentTarget.style.background='rgb(79,70,229)'}
            onMouseLeave={e => e.currentTarget.style.background='rgb(99,102,241)'}>
            Get started
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-6 pt-16 pb-12 text-center">
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: 'rgb(156,163,175)' }}>Pricing</div>
          <h1 className="text-[clamp(30px,5vw,48px)] font-black leading-tight mb-4"
            style={{ letterSpacing: '-1.5px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
            Simple, honest pricing
          </h1>
          <p className="text-[16px] leading-relaxed" style={{ color: 'rgb(107,114,128)' }}>
            Start free and upgrade when you are ready to automate your job search.
          </p>
          <div className="mt-5 inline-flex items-center gap-2 px-4 py-2 rounded-full text-[13px] font-medium"
            style={{ background: 'rgba(99,102,241,0.08)', color: 'rgb(99,102,241)' }}>
            <span className="w-2 h-2 rounded-full" style={{ background: 'rgb(99,102,241)' }} />
            JobFitAI is currently in beta: everything is free while we test with invited users. Paid plans launch later.
          </div>
        </motion.div>
      </section>

      {/* Plan cards */}
      <section className="max-w-3xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Free */}
          <FadeIn delay={0.05}>
            <div className="rounded-2xl border p-8 h-full flex flex-col border-black/[0.08]" style={{ background: 'white' }}>
              <div className="text-[13px] font-bold uppercase tracking-wide mb-2" style={{ color: 'rgb(107,114,128)' }}>Free</div>
              <div className="text-[46px] font-black leading-none mb-1"
                style={{ fontFamily: "'Plus Jakarta Sans',Inter,sans-serif", letterSpacing: '-2px' }}>
                0 <span className="text-[18px] font-semibold" style={{ color: 'rgb(107,114,128)' }}>EUR/mo</span>
              </div>
              <p className="text-[13px] mb-7" style={{ color: 'rgb(107,114,128)' }}>Full analyzer, forever free.</p>
              <Link to="/login"
                className="w-full h-11 flex items-center justify-center rounded-xl font-semibold text-[14px] border mb-7 transition-colors"
                style={{ color: 'rgb(99,102,241)', borderColor: 'rgba(99,102,241,0.3)', background: 'rgba(99,102,241,0.05)' }}
                onMouseEnter={e => e.currentTarget.style.background='rgba(99,102,241,0.1)'}
                onMouseLeave={e => e.currentTarget.style.background='rgba(99,102,241,0.05)'}>
                Get started free
              </Link>
              <ul className="space-y-2.5 flex-1">
                {['Resume analyzer (unlimited)', 'ATS compatibility check', 'Keyword gap analysis', 'AI profile summary', '3 resume slots', 'Manual job search', 'All LLM providers'].map(f => (
                  <li key={f} className="flex items-center gap-2.5 text-[13.5px]" style={{ color: 'rgb(55,65,81)' }}>
                    {CHECK} {f}
                  </li>
                ))}
              </ul>
            </div>
          </FadeIn>
          {/* Pro */}
          <FadeIn delay={0.1}>
            <div className="rounded-2xl p-8 h-full flex flex-col relative overflow-hidden"
              style={{ background: 'linear-gradient(145deg, rgb(99,102,241), rgb(124,58,237))', boxShadow: '0 8px 40px rgba(99,102,241,0.4)' }}>
              <div className="absolute top-5 right-5 px-2.5 py-1 rounded-full text-[11px] font-bold"
                style={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}>Popular</div>
              <div className="text-[13px] font-bold uppercase tracking-wide mb-2" style={{ color: 'rgba(255,255,255,0.7)' }}>Pro</div>
              <div className="text-[46px] font-black leading-none text-white mb-1"
                style={{ fontFamily: "'Plus Jakarta Sans',Inter,sans-serif", letterSpacing: '-2px' }}>
                9 <span className="text-[18px] font-semibold" style={{ color: 'rgba(255,255,255,0.7)' }}>EUR/mo</span>
              </div>
              <p className="text-[13px] mb-7" style={{ color: 'rgba(255,255,255,0.7)' }}>Automated job hunting on autopilot.</p>
              <Link to="/login"
                className="w-full h-11 flex items-center justify-center rounded-xl font-bold text-[14px] mb-7 transition-all"
                style={{ background: 'white', color: 'rgb(99,102,241)' }}
                onMouseEnter={e => e.currentTarget.style.boxShadow='0 4px 20px rgba(0,0,0,0.2)'}
                onMouseLeave={e => e.currentTarget.style.boxShadow='none'}>
                Start Pro trial
              </Link>
              <ul className="space-y-2.5 flex-1">
                {['Everything in Free', 'Scheduled auto-fetch (hourly / daily)', 'Live job board scan (200+ per run)', 'Priority LLM routing', 'AI-powered ATS optimise', 'CSV export of all matches', 'Early access to new features'].map(f => (
                  <li key={f} className="flex items-center gap-2.5 text-[13.5px] text-white">
                    {PROCHECK} {f}
                  </li>
                ))}
              </ul>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* Feature matrix */}
      <section className="border-t border-black/[0.06] py-16" style={{ background: 'white' }}>
        <div className="max-w-4xl mx-auto px-6">
          <FadeIn className="mb-10 text-center">
            <h2 className="text-[24px] font-black"
              style={{ letterSpacing: '-0.5px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
              Full feature comparison
            </h2>
          </FadeIn>
          <FadeIn>
            <div className="rounded-2xl border border-black/[0.08] overflow-hidden shadow-sm">
              <table className="w-full text-[13.5px]">
                <thead>
                  <tr style={{ background: 'rgb(248,248,250)', borderBottom: '1px solid rgba(0,0,0,0.07)' }}>
                    <th className="px-5 py-3.5 text-left font-semibold" style={{ color: 'rgb(107,114,128)' }}>Feature</th>
                    <th className="px-5 py-3.5 text-center font-semibold w-24" style={{ color: 'rgb(107,114,128)' }}>Free</th>
                    <th className="px-5 py-3.5 text-center font-bold w-24" style={{ color: 'rgb(99,102,241)' }}>Pro</th>
                  </tr>
                </thead>
                <tbody>
                  {MATRIX.map(group => (
                    <>
                      <tr key={group.section + '_header'}
                        style={{ background: 'rgba(99,102,241,0.04)', borderTop: '1px solid rgba(0,0,0,0.06)', borderBottom: '1px solid rgba(0,0,0,0.06)' }}>
                        <td colSpan={3} className="px-5 py-2 text-[11px] font-bold uppercase tracking-widest"
                          style={{ color: 'rgb(99,102,241)' }}>{group.section}</td>
                      </tr>
                      {group.rows.map((row, ri) => (
                        <tr key={row.label}
                          style={{ borderBottom: '1px solid rgba(0,0,0,0.05)', background: ri % 2 === 0 ? 'white' : 'rgb(250,250,252)' }}>
                          <td className="px-5 py-3" style={{ color: 'rgb(55,65,81)' }}>{row.label}</td>
                          <td className="px-5 py-3 text-center">{row.free ? CHECK : CROSS}</td>
                          <td className="px-5 py-3 text-center">{row.pro ? CHECK : CROSS}</td>
                        </tr>
                      ))}
                    </>
                  ))}
                </tbody>
              </table>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* Pricing FAQ */}
      <section className="max-w-3xl mx-auto px-6 py-16">
        <FadeIn className="mb-8">
          <h2 className="text-[22px] font-black text-center"
            style={{ letterSpacing: '-0.5px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
            Questions about pricing
          </h2>
        </FadeIn>
        <div className="space-y-2">
          {FAQ_PRICING.map((item, i) => (
            <FadeIn key={i} delay={i * 0.05}>
              <div className="rounded-xl border overflow-hidden border-black/[0.08]" style={{ background: 'white' }}>
                <button onClick={() => setOpen(open === i ? null : i)}
                  className="w-full flex items-center justify-between px-5 py-4 text-left transition-colors"
                  style={{ background: open === i ? 'rgba(99,102,241,0.04)' : 'transparent' }}>
                  <span className="text-[14px] font-semibold pr-4" style={{ color: 'rgb(15,15,20)' }}>{item.q}</span>
                  <motion.div animate={{ rotate: open === i ? 45 : 0 }} transition={{ duration: 0.2 }}
                    className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center"
                    style={{ background: open === i ? 'rgb(99,102,241)' : 'rgba(0,0,0,0.07)', color: open === i ? 'white' : 'rgb(107,114,128)' }}>
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M5 1v8M1 5h8"/></svg>
                  </motion.div>
                </button>
                <motion.div initial={false}
                  animate={{ height: open === i ? 'auto' : 0, opacity: open === i ? 1 : 0 }}
                  transition={{ duration: 0.25, ease: [0.4,0,0.2,1] }}
                  style={{ overflow: 'hidden' }}>
                  <p className="px-5 pb-4 text-[13.5px] leading-relaxed" style={{ color: 'rgb(107,114,128)' }}>{item.a}</p>
                </motion.div>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-black/[0.06] py-6 text-center" style={{ background: 'white' }}>
        <div className="flex items-center justify-center gap-5 text-[12.5px]" style={{ color: 'rgb(156,163,175)' }}>
          <Link to="/" className="hover:text-gray-700 transition-colors">Home</Link>
          <Link to="/about" className="hover:text-gray-700 transition-colors">About</Link>
          <Link to="/privacy" className="hover:text-gray-700 transition-colors">Privacy</Link>
        </div>
      </footer>
    </div>
  )
}
