/**
 * Landing page - hero, app mockup, how it works, comparison, pricing, FAQ, CTA.
 * Audience: job seekers applying for roles in Germany.
 */
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, useInView, animate } from 'framer-motion'

// === Scroll-triggered fade-in ===
function FadeIn({ children, delay = 0, y = 18, className = '' }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true, margin: '-60px' })
  return (
    <motion.div ref={ref} className={className}
      initial={{ opacity: 0, y }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.55, delay, ease: [0.25, 0.1, 0.25, 1] }}>
      {children}
    </motion.div>
  )
}

// === Animated counter ===
function Counter({ to, suffix = '' }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true })
  const [val, setVal] = useState(0)
  useEffect(() => {
    if (!inView) return
    const ctrl = animate(0, to, { duration: 1.4, ease: 'easeOut', onUpdate: v => setVal(Math.round(v)) })
    return () => ctrl.stop()
  }, [inView, to])
  return <span ref={ref}>{val}{suffix}</span>
}

// === Animated score ring - always indigo in the mockup ===
function ScoreRingAnim({ score, size = 110 }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true })
  const [current, setCurrent] = useState(0)
  const r = size * 0.36
  const circ = 2 * Math.PI * r
  const color = 'rgb(99,102,241)'
  const trackColor = 'rgba(99,102,241,0.12)'
  useEffect(() => {
    if (!inView) return
    const ctrl = animate(0, score, { duration: 1.6, ease: [0.25, 0.1, 0.25, 1], onUpdate: v => setCurrent(Math.round(v)) })
    return () => ctrl.stop()
  }, [inView, score])
  const offset = circ - (current / 100) * circ
  return (
    <svg ref={ref} width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={trackColor} strokeWidth={size*0.055}/>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color}
        strokeWidth={size*0.055} strokeLinecap="round"
        strokeDasharray={circ} strokeDashoffset={offset}
        transform={`rotate(-90 ${size/2} ${size/2})`}/>
      <text x={size/2} y={size/2-5} textAnchor="middle" fontSize={size*0.22} fontWeight="800"
        fill={color} fontFamily="'Plus Jakarta Sans',Inter,sans-serif">{current}</text>
      <text x={size/2} y={size/2+size*0.14} textAnchor="middle" fontSize={size*0.09}
        fill="rgba(99,102,241,0.5)" fontFamily="Inter,sans-serif">/ 100</text>
    </svg>
  )
}

// === Animated score bar - indigo palette throughout the mockup ===
function ScoreBarAnim({ label, value, delay = 0 }) {
  const ref = useRef(null)
  const inView = useInView(ref, { once: true })
  // Lighter shade for lower scores, full indigo for high - all within the accent family
  const opacity = 0.45 + (value / 100) * 0.55
  const barColor = `rgba(99,102,241,${opacity.toFixed(2)})`
  const textColor = value >= 70 ? 'rgb(99,102,241)' : 'rgb(139,142,255)'
  return (
    <div ref={ref} className="flex items-center gap-2.5">
      <div className="w-24 text-[11.5px] capitalize flex-shrink-0" style={{ color: 'rgb(107,114,128)' }}>{label}</div>
      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(99,102,241,0.1)' }}>
        <motion.div className="h-full rounded-full" style={{ background: barColor }}
          initial={{ width: 0 }}
          animate={inView ? { width: `${value}%` } : {}}
          transition={{ duration: 0.7, delay, ease: [0.4,0,0.2,1] }}/>
      </div>
      <div className="w-6 text-[11px] font-bold text-right flex-shrink-0" style={{ color: textColor }}>{value}</div>
    </div>
  )
}

// === App mockup ===
function AppMockup() {
  const keywords = {
    matched: ['Python', 'FastAPI', 'Docker', 'PostgreSQL', 'REST APIs', 'Git'],
    missing: ['Kubernetes', 'Terraform', 'AWS'],
  }
  const breakdown = [
    { label: 'Skills',     value: 88, delay: 0.1 },
    { label: 'Experience', value: 74, delay: 0.2 },
    { label: 'Education',  value: 91, delay: 0.3 },
    { label: 'Keywords',   value: 67, delay: 0.4 },
  ]
  return (
    <motion.div initial={{ opacity: 0, y: 28, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.7, delay: 0.35, ease: [0.25,0.1,0.25,1] }}
      className="relative">
      <div className="absolute -inset-4 rounded-3xl opacity-25 blur-3xl pointer-events-none"
        style={{ background: 'radial-gradient(ellipse at 60% 40%, rgba(99,102,241,0.6), transparent 70%)' }}/>
      <div className="relative rounded-2xl overflow-hidden shadow-2xl"
        style={{ background: 'white', border: '1.5px solid rgba(99,102,241,0.15)', boxShadow: '0 20px 60px rgba(99,102,241,0.18), 0 4px 16px rgba(0,0,0,0.08)' }}>
        <div className="flex items-center gap-1.5 px-4 py-3 border-b"
          style={{ background: 'rgba(99,102,241,0.04)', borderColor: 'rgba(99,102,241,0.1)' }}>
          <div className="w-2.5 h-2.5 rounded-full" style={{ background: 'rgba(99,102,241,0.25)' }}/>
          <div className="w-2.5 h-2.5 rounded-full" style={{ background: 'rgba(99,102,241,0.18)' }}/>
          <div className="w-2.5 h-2.5 rounded-full" style={{ background: 'rgba(99,102,241,0.12)' }}/>
          <div className="flex-1 mx-3 h-5 rounded flex items-center px-3"
            style={{ background: 'rgba(99,102,241,0.07)' }}>
            <span className="text-[10px]" style={{ color: 'rgba(99,102,241,0.6)' }}>jobsfitai.app / analyze</span>
          </div>
        </div>
        <div className="p-5 space-y-4">
          <div className="flex items-start gap-5">
            <ScoreRingAnim score={82} size={100}/>
            <div className="flex-1 pt-1 space-y-2.5">
              <div>
                <div className="text-[10.5px] font-bold uppercase tracking-widest mb-0.5" style={{ color: 'rgb(156,163,175)' }}>Match Score</div>
                <div className="text-[13.5px] font-semibold" style={{ color: 'rgb(15,15,20)' }}>Strong match</div>
              </div>
              {breakdown.map(b => <ScoreBarAnim key={b.label} {...b}/>)}
            </div>
          </div>
          <div className="pt-2 space-y-2.5" style={{ borderTop: '1px solid rgba(0,0,0,0.05)' }}>
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest mb-1.5" style={{ color: 'rgb(156,163,175)' }}>Matched</div>
              <div className="flex flex-wrap gap-1">
                {keywords.matched.map((k, i) => (
                  <motion.span key={k} initial={{ opacity: 0, scale: 0.85 }} animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.9 + i * 0.07 }}
                    className="px-2 py-0.5 rounded text-[11px] font-medium"
                    style={{ background: 'rgba(99,102,241,0.1)', color: 'rgb(99,102,241)', border: '1px solid rgba(99,102,241,0.22)' }}>{k}</motion.span>
                ))}
              </div>
            </div>
            <div>
              <div className="text-[10px] font-bold uppercase tracking-widest mb-1.5" style={{ color: 'rgb(156,163,175)' }}>Missing</div>
              <div className="flex flex-wrap gap-1">
                {keywords.missing.map((k, i) => (
                  <motion.span key={k} initial={{ opacity: 0, scale: 0.85 }} animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 1.5 + i * 0.07 }}
                    className="px-2 py-0.5 rounded text-[11px] font-medium"
                    style={{ background: 'rgba(99,102,241,0.05)', color: 'rgba(99,102,241,0.5)', border: '1px solid rgba(99,102,241,0.15)' }}>{k}</motion.span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
      <motion.div initial={{ opacity: 0, x: 20, y: -10 }} animate={{ opacity: 1, x: 0, y: 0 }}
        transition={{ delay: 1.1, duration: 0.5 }}
        className="absolute -right-8 top-10 rounded-xl shadow-xl border border-black/[0.07] px-3.5 py-3 w-52"
        style={{ background: 'white' }}>
        <div className="flex items-center gap-2 mb-1.5">
          <div className="w-6 h-6 rounded flex items-center justify-center text-[10px] font-bold text-indigo-600"
            style={{ background: 'rgba(99,102,241,0.1)' }}>A</div>
          <div>
            <div className="text-[11.5px] font-semibold" style={{ color: 'rgb(15,15,20)' }}>Backend Engineer</div>
            <div className="text-[10px]" style={{ color: 'rgb(156,163,175)' }}>Berlin, Germany</div>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="flex-1 h-1 rounded-full" style={{ background: 'rgba(0,0,0,0.06)' }}>
            <div className="h-full rounded-full" style={{ width: '76%', background: 'rgb(99,102,241)' }}/>
          </div>
          <span className="text-[10.5px] font-bold" style={{ color: 'rgb(99,102,241)' }}>76%</span>
        </div>
      </motion.div>
      <motion.div initial={{ opacity: 0, x: -20, y: 10 }} animate={{ opacity: 1, x: 0, y: 0 }}
        transition={{ delay: 1.3, duration: 0.5 }}
        className="absolute -left-8 bottom-12 rounded-xl shadow-xl border border-black/[0.07] px-3.5 py-2.5 flex items-center gap-2.5"
        style={{ background: 'white' }}>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
          style={{ background: 'rgba(22,163,74,0.12)' }}>
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="#16a34a" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M2.5 8l3.5 3.5 7.5-7"/>
          </svg>
        </div>
        <div>
          <div className="text-[11.5px] font-semibold" style={{ color: 'rgb(15,15,20)' }}>ATS Ready</div>
          <div className="text-[10px] font-medium" style={{ color: '#16a34a' }}>93 / 100</div>
        </div>
      </motion.div>
    </motion.div>
  )
}

// === Scrolling job ticker ===
const TICKER_JOBS = [
  'Software Engineer', 'Data Scientist', 'ML Engineer', 'DevOps Engineer',
  'Product Manager', 'Backend Developer', 'Cloud Architect', 'AI Researcher',
  'Full-Stack Developer', 'Platform Engineer', 'Python Developer', 'NLP Engineer',
]
function Ticker() {
  return (
    <div className="overflow-hidden py-1"
      style={{ maskImage: 'linear-gradient(to right, transparent, black 8%, black 92%, transparent)' }}>
      <motion.div className="flex gap-3 whitespace-nowrap"
        animate={{ x: ['0%', '-50%'] }}
        transition={{ duration: 24, ease: 'linear', repeat: Infinity }}>
        {[...TICKER_JOBS, ...TICKER_JOBS].map((job, i) => (
          <span key={i} className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[12px] font-medium border flex-shrink-0"
            style={{ background: 'white', borderColor: 'rgba(99,102,241,0.2)', color: 'rgb(99,102,241)' }}>
            <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: 'rgb(99,102,241)' }}/>
            {job}
          </span>
        ))}
      </motion.div>
    </div>
  )
}

// === FAQ accordion ===
const FAQ_ITEMS = [
  { q: 'Which job boards do you pull from?', a: 'We connect to Adzuna Germany, Arbeitnow, and the Bundesagentur fur Arbeit - three of the largest job boards for the German market. Each run can fetch up to 200 listings per search title.' },
  { q: 'What resume formats are supported?', a: 'PDF and DOCX. We extract the text automatically - no manual copy-paste needed. Files up to 10 MB are accepted.' },
  { q: 'How is the match score calculated?', a: 'The score is a weighted average across six dimensions: skills, experience, education, keywords, language, and role seniority. You can see the per-section breakdown after each analysis.' },
  { q: 'Which AI models power the analysis?', a: 'You can choose between OpenAI (GPT-4o), Groq (fast and free tier available), or a locally running Ollama model. The active provider is shown in Settings and can be switched at any time.' },
  { q: 'Is my resume data private?', a: 'Your resume and analysis results are stored only in your account and never shared with third parties or used to train any model. See our Privacy Policy for full details.' },
  { q: 'Can I store multiple resume versions?', a: 'Yes - up to 3 resume slots are available. Use one for your base resume and the others for role-specific or company-tailored versions. You can switch between them with one click.' },
  { q: 'Does it work for non-German-speaking roles?', a: 'Yes. While the job sources focus on Germany, many listings are in English. Our language detection flags the job language and the scoring works for both German and English resumes.' },
  { q: 'Is there a free plan?', a: 'Yes. The free plan gives you full access to the analyzer, ATS check, and resume storage. The Pro plan adds scheduled auto-fetching, priority LLM routing, and export features.' },
]
function FAQ() {
  const [open, setOpen] = useState(null)
  return (
    <div className="space-y-2">
      {FAQ_ITEMS.map((item, i) => (
        <FadeIn key={i} delay={i * 0.04}>
          <div className="rounded-xl border overflow-hidden"
            style={{ borderColor: 'rgba(0,0,0,0.08)', background: 'white' }}>
            <button
              onClick={() => setOpen(open === i ? null : i)}
              className="w-full flex items-center justify-between px-5 py-4 text-left"
              style={{ background: open === i ? 'rgba(99,102,241,0.04)' : 'transparent' }}>
              <span className="text-[14px] font-semibold pr-4" style={{ color: 'rgb(15,15,20)' }}>{item.q}</span>
              <motion.div animate={{ rotate: open === i ? 45 : 0 }} transition={{ duration: 0.2 }}
                className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center"
                style={{ background: open === i ? 'rgb(99,102,241)' : 'rgba(0,0,0,0.07)', color: open === i ? 'white' : 'rgb(107,114,128)' }}>
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M5 1v8M1 5h8"/>
                </svg>
              </motion.div>
            </button>
            <motion.div
              initial={false}
              animate={{ height: open === i ? 'auto' : 0, opacity: open === i ? 1 : 0 }}
              transition={{ duration: 0.25, ease: [0.4,0,0.2,1] }}
              style={{ overflow: 'hidden' }}>
              <p className="px-5 pb-4 text-[13.5px] leading-relaxed" style={{ color: 'rgb(107,114,128)' }}>{item.a}</p>
            </motion.div>
          </div>
        </FadeIn>
      ))}
    </div>
  )
}

// === Comparison table ===
const COMPARE_ROWS = [
  { feature: 'AI match score (0-100)',      us: true,   jobscan: true,   manual: false },
  { feature: 'Section-by-section breakdown', us: true,  jobscan: true,   manual: false },
  { feature: 'Keyword gap analysis',          us: true,  jobscan: true,   manual: 'partial' },
  { feature: 'Live German job board fetch',   us: true,  jobscan: false,  manual: false },
  { feature: 'Adzuna + Arbeitnow + BA fetch', us: true,  jobscan: false,  manual: false },
  { feature: 'ATS compatibility scan',        us: true,  jobscan: true,   manual: false },
  { feature: 'Multiple resume slots',         us: true,  jobscan: false,  manual: false },
  { feature: 'Own LLM (OpenAI / Groq / Ollama)', us: true, jobscan: false, manual: false },
  { feature: 'Works offline with Ollama',     us: true,  jobscan: false,  manual: false },
  { feature: 'Free tier available',           us: true,  jobscan: 'partial', manual: true },
]
function Check({ val }) {
  if (val === true) return <span className="text-green-600 font-bold text-[15px]">&#10003;</span>
  if (val === false) return <span className="text-gray-300 font-bold text-[15px]">&#10007;</span>
  return <span className="text-amber-500 text-[12px] font-semibold">Partial</span>
}

// === Pricing tier ===
const FREE_FEATURES  = ['Resume analyzer (unlimited)', 'ATS compatibility check', 'Keyword gap analysis', 'AI profile summary', '3 resume slots', 'Manual job search']
const PRO_FEATURES   = ['Everything in Free', 'Scheduled auto-fetch (hourly / daily)', 'Live job board scan (200+ per run)', 'Priority LLM routing', 'CSV export of all matches', 'Early access to new features']

export default function Landing() {
  return (
    <div className="min-h-screen overflow-x-hidden" style={{ background: 'rgb(248,248,250)', color: 'rgb(15,15,20)' }}>

      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-black/[0.07]"
        style={{ background: 'rgba(255,255,255,0.88)', backdropFilter: 'blur(16px)' }}>
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center gap-4">
          <div className="flex items-center gap-2.5 flex-1">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'rgb(99,102,241)' }}>
              <svg width="13" height="13" viewBox="0 0 16 16" fill="white">
                <path d="M8 1L1 4.5v4c0 3.5 2.8 6.2 7 7.5 4.2-1.3 7-4 7-7.5v-4L8 1z"/>
              </svg>
            </div>
            <span className="text-[15px] font-bold tracking-tight" style={{ fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
              Jobs<span style={{ color: 'rgb(99,102,241)' }}>Fit</span>AI
            </span>
          </div>
          <nav className="hidden md:flex items-center gap-1">
            {[['#pricing','Pricing'],['#faq','FAQ'],['#compare','Compare']].map(([href, label]) => (
              <a key={href} href={href}
                className="h-8 px-3 text-[13px] font-medium rounded-lg transition-colors flex items-center"
                style={{ color: 'rgb(107,114,128)' }}
                onMouseEnter={e => { e.currentTarget.style.color='rgb(15,15,20)'; e.currentTarget.style.background='rgba(0,0,0,0.04)' }}
                onMouseLeave={e => { e.currentTarget.style.color='rgb(107,114,128)'; e.currentTarget.style.background='transparent' }}>
                {label}
              </a>
            ))}
            <Link to="/about"
              className="h-8 px-3 text-[13px] font-medium rounded-lg transition-colors flex items-center"
              style={{ color: 'rgb(107,114,128)' }}
              onMouseEnter={e => { e.currentTarget.style.color='rgb(15,15,20)'; e.currentTarget.style.background='rgba(0,0,0,0.04)' }}
              onMouseLeave={e => { e.currentTarget.style.color='rgb(107,114,128)'; e.currentTarget.style.background='transparent' }}>
              About
            </Link>
          </nav>
          <div className="flex items-center gap-1.5">
            <Link to="/login"
              className="h-8 px-4 text-[13px] font-medium rounded-lg transition-colors flex items-center"
              style={{ color: 'rgb(107,114,128)' }}
              onMouseEnter={e => e.currentTarget.style.color='rgb(15,15,20)'}
              onMouseLeave={e => e.currentTarget.style.color='rgb(107,114,128)'}>
              Sign in
            </Link>
            <Link to="/login"
              className="h-8 px-4 text-[13px] font-semibold text-white rounded-lg transition-all flex items-center"
              style={{ background: 'rgb(99,102,241)' }}
              onMouseEnter={e => e.currentTarget.style.background='rgb(79,70,229)'}
              onMouseLeave={e => e.currentTarget.style.background='rgb(99,102,241)'}>
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[12px] font-semibold mb-6 border"
              style={{ background: 'rgba(99,102,241,0.08)', borderColor: 'rgba(99,102,241,0.2)', color: 'rgb(99,102,241)' }}>
              <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'rgb(99,102,241)' }}/>
              Built for job seekers in Germany
            </motion.div>
            <motion.h1 initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, delay: 0.1 }}
              className="text-[clamp(36px,5vw,60px)] font-black leading-[1.08] mb-5"
              style={{ letterSpacing: '-2px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
              Know your <em className="not-italic" style={{ color: 'rgb(99,102,241)' }}>fit</em>
              <br/>before you apply
            </motion.h1>
            <motion.p initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}
              className="text-[17px] leading-relaxed mb-8 max-w-md" style={{ color: 'rgb(107,114,128)' }}>
              Upload your resume, paste a job description, and get an AI-powered match score
              with keyword gaps, ATS check, and live job listings from Adzuna, Arbeitnow, and
              the Bundesagentur - all in one place.
            </motion.p>
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.28 }}
              className="flex flex-wrap items-center gap-3 mb-5">
              <Link to="/login"
                className="inline-flex items-center gap-2 h-12 px-7 text-white rounded-xl font-semibold text-[15px] transition-all hover:-translate-y-0.5"
                style={{ background: 'rgb(99,102,241)', boxShadow: '0 4px 20px rgba(99,102,241,0.4)' }}
                onMouseEnter={e => e.currentTarget.style.background='rgb(79,70,229)'}
                onMouseLeave={e => e.currentTarget.style.background='rgb(99,102,241)'}>
                Start for free
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 8h10M9 4l4 4-4 4"/></svg>
              </Link>
              <Link to="/login"
                className="inline-flex items-center h-12 px-6 rounded-xl font-medium text-[15px] border transition-colors"
                style={{ color: 'rgb(55,65,81)', borderColor: 'rgba(0,0,0,0.1)', background: 'rgba(255,255,255,0.8)' }}
                onMouseEnter={e => e.currentTarget.style.background='white'}
                onMouseLeave={e => e.currentTarget.style.background='rgba(255,255,255,0.8)'}>
                Sign in
              </Link>
            </motion.div>
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
              className="text-[12px]" style={{ color: 'rgb(156,163,175)' }}>
              Free to use. No credit card required.
            </motion.p>
          </div>
          <div className="relative flex justify-center lg:justify-end pt-6 pb-16 pr-10">
            <AppMockup/>
          </div>
        </div>
      </section>

      {/* Ticker */}
      <div className="border-y border-black/[0.06] py-5" style={{ background: 'rgba(255,255,255,0.6)' }}>
        <div className="text-center text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: 'rgb(156,163,175)' }}>
          Matching candidates to roles across Germany
        </div>
        <Ticker/>
      </div>

      {/* Stats */}
      <section className="max-w-4xl mx-auto px-6 py-16">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
          {[
            { to: 3,   suffix: '',    label: 'German job boards connected' },
            { to: 200, suffix: '+',   label: 'Jobs fetched per run' },
            { to: 6,   suffix: '',    label: 'Resume dimensions scored' },
            { to: 100, suffix: '',    label: 'Point match scale' },
          ].map((s, i) => (
            <FadeIn key={s.label} delay={i * 0.08}>
              <div className="text-[clamp(28px,4vw,42px)] font-black mb-1"
                style={{ color: 'rgb(99,102,241)', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif", letterSpacing: '-1px' }}>
                <Counter to={s.to} suffix={s.suffix}/>
              </div>
              <div className="text-[12.5px]" style={{ color: 'rgb(107,114,128)' }}>{s.label}</div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="border-y border-black/[0.06] py-20" style={{ background: 'white' }}>
        <div className="max-w-5xl mx-auto px-6">
          <FadeIn className="text-center mb-14">
            <div className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: 'rgb(99,102,241)' }}>How it works</div>
            <h2 className="text-[clamp(26px,4vw,38px)] font-black tracking-tight"
              style={{ letterSpacing: '-1px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
              From resume to interview-ready in minutes
            </h2>
            <p className="mt-3 text-[15px] max-w-lg mx-auto" style={{ color: 'rgb(107,114,128)' }}>
              Stop guessing whether your resume fits. Get a precise score and know exactly what to fix.
            </p>
          </FadeIn>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              { n:'1', title:'Upload your resume', desc:'Drop a PDF or DOCX. We extract the text and store up to 3 versions in your vault - one base resume and tailored copies for different roles.' },
              { n:'2', title:'Paste a job description', desc:'Copy any German or English job posting. Our AI extracts the required skills, experience level, and keywords from the full text.' },
              { n:'3', title:'Get your score and fix it', desc:'See your 0-100 match score, section breakdown, matched and missing keywords, strengths, and gaps - then tailor your resume accordingly.' },
            ].map((s, i) => (
              <FadeIn key={s.n} delay={i * 0.12}>
                <div className="rounded-2xl p-6 h-full border border-black/[0.06] hover:shadow-md transition-shadow"
                  style={{ background: 'rgb(248,248,250)' }}>
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center font-black text-[15px] text-white mb-4"
                    style={{ background: 'rgb(99,102,241)', boxShadow: '0 4px 14px rgba(99,102,241,0.35)' }}>{s.n}</div>
                  <div className="text-[15px] font-bold mb-2" style={{ color: 'rgb(15,15,20)' }}>{s.title}</div>
                  <p className="text-[13.5px] leading-relaxed" style={{ color: 'rgb(107,114,128)' }}>{s.desc}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <FadeIn className="text-center mb-12">
          <div className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: 'rgb(156,163,175)' }}>Features</div>
          <h2 className="text-[clamp(24px,3.5vw,36px)] font-black tracking-tight"
            style={{ letterSpacing: '-1px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
            Everything you need for your job search in Germany
          </h2>
        </FadeIn>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { color:'#6366f1', bg:'rgba(99,102,241,0.09)',  title:'AI match score', desc:'Get a 0-100 score broken down across skills, experience, education, and keywords - not just a vague percentage.',
              icon:<><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></> },
            { color:'#0ea5e9', bg:'rgba(14,165,233,0.09)',  title:'Keyword gap analysis', desc:'See exactly which skills and terms the employer wants and which ones are missing from your resume right now.',
              icon:<><path d="M4 6h16M4 12h10M4 18h7"/></> },
            { color:'#8b5cf6', bg:'rgba(139,92,246,0.09)',  title:'Live German job listings', desc:'Automatically pull fresh listings from Adzuna Germany, Arbeitnow, and the Bundesagentur fur Arbeit - all scored against your resume.',
              icon:<><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></> },
            { color:'#16a34a', bg:'rgba(22,163,74,0.09)',   title:'ATS compatibility check', desc:'Check if your resume will pass automated applicant tracking systems before you submit. Section completeness and formatting warnings included.',
              icon:<><path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-5M9 21H5a2 2 0 01-2-2v-5m0 0h18"/></> },
            { color:'#f59e0b', bg:'rgba(245,158,11,0.09)',  title:'3 resume slots', desc:'Store a base resume and up to two tailored versions. Switch between them instantly when applying for different roles or companies.',
              icon:<><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h4"/></> },
            { color:'#ec4899', bg:'rgba(236,72,153,0.09)',  title:'AI strengths and gaps', desc:'Get a plain-language summary of your profile strengths, the gaps you need to close, and a recommended focus area for each application.',
              icon:<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/> },
          ].map((f, i) => (
            <FadeIn key={f.title} delay={i * 0.07}>
              <div className="rounded-2xl p-5 h-full border border-black/[0.06] hover:shadow-lg hover:-translate-y-0.5 transition-all"
                style={{ background: 'white' }}>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4"
                  style={{ background: f.bg, color: f.color }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    {f.icon}
                  </svg>
                </div>
                <div className="text-[14px] font-bold mb-1.5" style={{ color: 'rgb(15,15,20)' }}>{f.title}</div>
                <p className="text-[13px] leading-relaxed" style={{ color: 'rgb(107,114,128)' }}>{f.desc}</p>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* Comparison */}
      <section id="compare" className="border-y border-black/[0.06] py-20" style={{ background: 'white' }}>
        <div className="max-w-4xl mx-auto px-6">
          <FadeIn className="text-center mb-12">
            <div className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: 'rgb(156,163,175)' }}>Compare</div>
            <h2 className="text-[clamp(24px,3.5vw,36px)] font-black tracking-tight"
              style={{ letterSpacing: '-1px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
              Why JobsFitAI?
            </h2>
            <p className="mt-3 text-[14px] max-w-md mx-auto" style={{ color: 'rgb(107,114,128)' }}>
              Most tools score your resume but don't connect to German job boards or let you control the AI model.
            </p>
          </FadeIn>
          <FadeIn>
            <div className="rounded-2xl overflow-hidden border border-black/[0.08] shadow-sm">
              <table className="w-full text-[13.5px]">
                <thead>
                  <tr style={{ background: 'rgb(248,248,250)', borderBottom: '1px solid rgba(0,0,0,0.07)' }}>
                    <th className="px-5 py-3.5 text-left font-semibold" style={{ color: 'rgb(107,114,128)' }}>Feature</th>
                    <th className="px-4 py-3.5 text-center font-bold" style={{ color: 'rgb(99,102,241)' }}>JobsFitAI</th>
                    <th className="px-4 py-3.5 text-center font-semibold" style={{ color: 'rgb(107,114,128)' }}>Jobscan</th>
                    <th className="px-4 py-3.5 text-center font-semibold" style={{ color: 'rgb(107,114,128)' }}>Manual</th>
                  </tr>
                </thead>
                <tbody>
                  {COMPARE_ROWS.map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(0,0,0,0.05)', background: i % 2 === 0 ? 'white' : 'rgb(250,250,252)' }}>
                      <td className="px-5 py-3 font-medium" style={{ color: 'rgb(55,65,81)' }}>{row.feature}</td>
                      <td className="px-4 py-3 text-center"><Check val={row.us}/></td>
                      <td className="px-4 py-3 text-center"><Check val={row.jobscan}/></td>
                      <td className="px-4 py-3 text-center"><Check val={row.manual}/></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="max-w-4xl mx-auto px-6 py-20">
        <FadeIn className="text-center mb-12">
          <div className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: 'rgb(156,163,175)' }}>Pricing</div>
          <h2 className="text-[clamp(24px,3.5vw,36px)] font-black tracking-tight"
            style={{ letterSpacing: '-1px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
            Simple, transparent pricing
          </h2>
          <p className="mt-3 text-[14px] max-w-md mx-auto" style={{ color: 'rgb(107,114,128)' }}>
            Start free. Upgrade when you need scheduled job fetching and priority analysis.
          </p>
          <div className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-full text-[13px] font-medium"
            style={{ background: 'rgba(99,102,241,0.08)', color: 'rgb(99,102,241)' }}>
            <span className="w-2 h-2 rounded-full" style={{ background: 'rgb(99,102,241)' }} />
            Currently in beta: all features are free for invited users
          </div>
        </FadeIn>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Free */}
          <FadeIn delay={0.05}>
            <div className="rounded-2xl border p-7 h-full flex flex-col border-black/[0.08]"
              style={{ background: 'white' }}>
              <div className="mb-5">
                <div className="text-[13px] font-bold uppercase tracking-wide mb-1" style={{ color: 'rgb(107,114,128)' }}>Free</div>
                <div className="text-[42px] font-black leading-none mb-1" style={{ fontFamily: "'Plus Jakarta Sans',Inter,sans-serif", letterSpacing: '-2px' }}>
                  0 <span className="text-[18px] font-semibold" style={{ color: 'rgb(107,114,128)' }}>EUR/mo</span>
                </div>
                <p className="text-[13px]" style={{ color: 'rgb(107,114,128)' }}>Full analyzer access, forever free.</p>
              </div>
              <ul className="space-y-2.5 flex-1 mb-7">
                {FREE_FEATURES.map(f => (
                  <li key={f} className="flex items-start gap-2.5 text-[13.5px]" style={{ color: 'rgb(55,65,81)' }}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="#16a34a" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0 mt-0.5">
                      <path d="M2.5 8l3.5 3.5 7.5-7"/>
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
              <Link to="/login"
                className="w-full h-11 flex items-center justify-center rounded-xl font-semibold text-[14px] border transition-colors"
                style={{ color: 'rgb(99,102,241)', borderColor: 'rgba(99,102,241,0.3)', background: 'rgba(99,102,241,0.05)' }}
                onMouseEnter={e => e.currentTarget.style.background='rgba(99,102,241,0.1)'}
                onMouseLeave={e => e.currentTarget.style.background='rgba(99,102,241,0.05)'}>
                Get started free
              </Link>
            </div>
          </FadeIn>
          {/* Pro */}
          <FadeIn delay={0.1}>
            <div className="rounded-2xl p-7 h-full flex flex-col relative overflow-hidden"
              style={{ background: 'linear-gradient(145deg, rgb(99,102,241), rgb(124,58,237))', boxShadow: '0 8px 40px rgba(99,102,241,0.4)' }}>
              <div className="absolute top-4 right-4 px-2.5 py-1 rounded-full text-[11px] font-bold"
                style={{ background: 'rgba(255,255,255,0.2)', color: 'white' }}>Popular</div>
              <div className="mb-5">
                <div className="text-[13px] font-bold uppercase tracking-wide mb-1" style={{ color: 'rgba(255,255,255,0.7)' }}>Pro</div>
                <div className="text-[42px] font-black leading-none mb-1 text-white" style={{ fontFamily: "'Plus Jakarta Sans',Inter,sans-serif", letterSpacing: '-2px' }}>
                  9 <span className="text-[18px] font-semibold" style={{ color: 'rgba(255,255,255,0.7)' }}>EUR/mo</span>
                </div>
                <p className="text-[13px]" style={{ color: 'rgba(255,255,255,0.7)' }}>Automated job hunting on autopilot.</p>
              </div>
              <ul className="space-y-2.5 flex-1 mb-7">
                {PRO_FEATURES.map(f => (
                  <li key={f} className="flex items-start gap-2.5 text-[13.5px] text-white">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="rgba(255,255,255,0.9)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="flex-shrink-0 mt-0.5">
                      <path d="M2.5 8l3.5 3.5 7.5-7"/>
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
              <Link to="/login"
                className="w-full h-11 flex items-center justify-center rounded-xl font-bold text-[14px] transition-all hover:-translate-y-0.5"
                style={{ background: 'white', color: 'rgb(99,102,241)' }}
                onMouseEnter={e => e.currentTarget.style.boxShadow='0 4px 20px rgba(0,0,0,0.2)'}
                onMouseLeave={e => e.currentTarget.style.boxShadow='none'}>
                Start Pro trial
              </Link>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="border-t border-black/[0.06] py-20" style={{ background: 'white' }}>
        <div className="max-w-3xl mx-auto px-6">
          <FadeIn className="text-center mb-12">
            <div className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: 'rgb(156,163,175)' }}>FAQ</div>
            <h2 className="text-[clamp(24px,3.5vw,36px)] font-black tracking-tight"
              style={{ letterSpacing: '-1px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
              Common questions
            </h2>
          </FadeIn>
          <FAQ/>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-20">
        <FadeIn>
          <div className="max-w-4xl mx-auto rounded-3xl p-12 text-center relative overflow-hidden"
            style={{ background: 'linear-gradient(135deg, rgb(99,102,241), rgb(139,92,246))' }}>
            <div className="absolute top-0 right-0 w-64 h-64 rounded-full opacity-20 blur-3xl pointer-events-none"
              style={{ background: 'white', transform: 'translate(30%,-30%)' }}/>
            <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full opacity-15 blur-3xl pointer-events-none"
              style={{ background: 'white', transform: 'translate(-30%,30%)' }}/>
            <div className="relative">
              <h2 className="text-[clamp(24px,4vw,38px)] font-black text-white mb-3 tracking-tight"
                style={{ letterSpacing: '-1px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
                Ready to land your next role in Germany?
              </h2>
              <p className="text-[15px] mb-8 max-w-md mx-auto" style={{ color: 'rgba(255,255,255,0.8)' }}>
                Free to start. No credit card. Your first analysis takes under a minute.
              </p>
              <Link to="/login"
                className="inline-flex items-center gap-2 h-12 px-8 rounded-xl font-bold text-[15px] transition-all hover:-translate-y-0.5"
                style={{ background: 'white', color: 'rgb(99,102,241)' }}
                onMouseEnter={e => e.currentTarget.style.boxShadow='0 8px 30px rgba(0,0,0,0.25)'}
                onMouseLeave={e => e.currentTarget.style.boxShadow='none'}>
                Get started free
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 8h10M9 4l4 4-4 4"/></svg>
              </Link>
            </div>
          </div>
        </FadeIn>
      </section>

      {/* Footer */}
      <footer className="border-t border-black/[0.06] py-8" style={{ background: 'white' }}>
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md flex items-center justify-center" style={{ background: 'rgb(99,102,241)' }}>
              <svg width="11" height="11" viewBox="0 0 16 16" fill="white"><path d="M8 1L1 4.5v4c0 3.5 2.8 6.2 7 7.5 4.2-1.3 7-4 7-7.5v-4L8 1z"/></svg>
            </div>
            <span className="text-[13px] font-semibold">Jobs<span style={{ color: 'rgb(99,102,241)' }}>Fit</span>AI</span>
          </div>
          <div className="flex items-center gap-5 text-[12.5px]" style={{ color: 'rgb(107,114,128)' }}>
            <Link to="/about" className="hover:text-gray-900 transition-colors">About</Link>
            <Link to="/pricing" className="hover:text-gray-900 transition-colors">Pricing</Link>
            <Link to="/privacy" className="hover:text-gray-900 transition-colors">Privacy</Link>
          </div>
          <div className="text-[12px]" style={{ color: 'rgb(156,163,175)' }}>
            Built for job seekers in Germany
          </div>
        </div>
      </footer>
    </div>
  )
}
