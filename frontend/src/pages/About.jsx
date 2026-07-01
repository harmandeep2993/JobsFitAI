/**
 * About page - mission, what the tool does, tech stack, Germany focus.
 */
import { useRef } from 'react'
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

const STACK = [
  { name: 'FastAPI', role: 'Backend API and job pipeline' },
  { name: 'SQLite', role: 'Lightweight local storage' },
  { name: 'React + Vite', role: 'Single-page frontend' },
  { name: 'Tailwind CSS', role: 'Utility-first styling' },
  { name: 'Framer Motion', role: 'Animations' },
  { name: 'OpenAI / Groq', role: 'LLM extraction and scoring' },
  { name: 'Ollama', role: 'Local offline LLM option' },
  { name: 'Adzuna API', role: 'German job listings' },
  { name: 'Arbeitnow', role: 'Tech-focused German listings' },
  { name: 'Bundesagentur', role: 'Official German job board' },
]

const NAV_BG = 'rgba(255,255,255,0.88)'

export default function About() {
  return (
    <div className="min-h-screen" style={{ background: 'rgb(248,248,250)', color: 'rgb(15,15,20)' }}>

      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-black/[0.07]"
        style={{ background: NAV_BG, backdropFilter: 'blur(16px)' }}>
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2.5 flex-1 group">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'rgb(99,102,241)' }}>
              <svg width="13" height="13" viewBox="0 0 16 16" fill="white"><path d="M8 1L1 4.5v4c0 3.5 2.8 6.2 7 7.5 4.2-1.3 7-4 7-7.5v-4L8 1z"/></svg>
            </div>
            <span className="text-[15px] font-bold tracking-tight" style={{ fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
              Jobs<span style={{ color: 'rgb(99,102,241)' }}>Fit</span>AI
            </span>
          </Link>
          <div className="flex items-center gap-1.5">
            <Link to="/login"
              className="h-8 px-4 text-[13px] font-semibold text-white rounded-lg flex items-center"
              style={{ background: 'rgb(99,102,241)' }}
              onMouseEnter={e => e.currentTarget.style.background='rgb(79,70,229)'}
              onMouseLeave={e => e.currentTarget.style.background='rgb(99,102,241)'}>
              Get started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-6 pt-20 pb-16 text-center">
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[12px] font-semibold mb-6 border"
            style={{ background: 'rgba(99,102,241,0.08)', borderColor: 'rgba(99,102,241,0.2)', color: 'rgb(99,102,241)' }}>
            About the project
          </div>
          <h1 className="text-[clamp(32px,5vw,52px)] font-black leading-tight mb-5"
            style={{ letterSpacing: '-1.5px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
            Built for people navigating<br/>the German job market
          </h1>
          <p className="text-[17px] leading-relaxed" style={{ color: 'rgb(107,114,128)' }}>
            JobsFitAI started as a personal tool to figure out why some job applications got responses and others did not.
            The answer was almost always the same: keyword mismatch and a resume that was not tailored to the role.
          </p>
        </motion.div>
      </section>

      {/* Mission */}
      <section className="border-y border-black/[0.06] py-16" style={{ background: 'white' }}>
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
          <FadeIn>
            <h2 className="text-[24px] font-black mb-4"
              style={{ letterSpacing: '-0.5px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
              The problem we solve
            </h2>
            <div className="space-y-4 text-[14px] leading-relaxed" style={{ color: 'rgb(107,114,128)' }}>
              <p>
                Applying for jobs in Germany is competitive. Companies use ATS software to filter resumes before a human
                ever reads them. If your resume does not contain the right keywords, it gets rejected automatically -
                regardless of how qualified you actually are.
              </p>
              <p>
                Most people do not know which keywords are missing, or how closely their experience matches what the
                employer actually wants. They apply broadly and wonder why they hear nothing back.
              </p>
              <p>
                JobsFitAI gives you precise, actionable feedback before you apply - so you can spend less time
                sending applications into the void and more time tailoring the ones that matter.
              </p>
            </div>
          </FadeIn>
          <FadeIn delay={0.1}>
            <h2 className="text-[24px] font-black mb-4"
              style={{ letterSpacing: '-0.5px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
              Why Germany specifically?
            </h2>
            <div className="space-y-4 text-[14px] leading-relaxed" style={{ color: 'rgb(107,114,128)' }}>
              <p>
                We built the job fetching layer around three sources that cover the German market well: Adzuna Germany,
                Arbeitnow (strong on tech roles), and the Bundesagentur fur Arbeit - Germany's official federal
                employment agency with hundreds of thousands of listings.
              </p>
              <p>
                Whether you are looking for roles in Berlin, Munich, Hamburg, or remote positions for Germany-based
                companies, we pull and score listings automatically so you always have a fresh list ranked by
                how well they match your current resume.
              </p>
              <p>
                Both German and English job postings are supported. Language detection flags the posting language
                so you always know what you are applying to.
              </p>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* Tech stack */}
      <section className="max-w-4xl mx-auto px-6 py-16">
        <FadeIn className="mb-10">
          <div className="text-[11px] font-bold uppercase tracking-widest mb-2" style={{ color: 'rgb(156,163,175)' }}>Tech stack</div>
          <h2 className="text-[24px] font-black"
            style={{ letterSpacing: '-0.5px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
            What it is built with
          </h2>
        </FadeIn>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {STACK.map((s, i) => (
            <FadeIn key={s.name} delay={i * 0.04}>
              <div className="rounded-xl p-4 border border-black/[0.07] hover:shadow-sm transition-shadow"
                style={{ background: 'white' }}>
                <div className="text-[13.5px] font-bold mb-1" style={{ color: 'rgb(15,15,20)' }}>{s.name}</div>
                <div className="text-[11.5px]" style={{ color: 'rgb(156,163,175)' }}>{s.role}</div>
              </div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* Privacy note */}
      <section className="border-t border-black/[0.06] py-16" style={{ background: 'white' }}>
        <div className="max-w-3xl mx-auto px-6 text-center">
          <FadeIn>
            <div className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-5"
              style={{ background: 'rgba(99,102,241,0.1)', color: 'rgb(99,102,241)' }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            <h2 className="text-[22px] font-black mb-3"
              style={{ letterSpacing: '-0.5px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
              Your data stays yours
            </h2>
            <p className="text-[14px] leading-relaxed max-w-lg mx-auto mb-5" style={{ color: 'rgb(107,114,128)' }}>
              Your resume and analysis results are stored only in your account. We do not sell data, share it with
              third parties, or use it to train any AI model. You can delete your account and all associated data
              at any time.
            </p>
            <Link to="/privacy"
              className="inline-flex items-center gap-1.5 text-[13px] font-semibold"
              style={{ color: 'rgb(99,102,241)' }}>
              Read the full privacy policy
              <svg width="12" height="12" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7h8M7 3l4 4-4 4"/></svg>
            </Link>
          </FadeIn>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-3xl mx-auto px-6 py-16 text-center">
        <FadeIn>
          <h2 className="text-[26px] font-black mb-3"
            style={{ letterSpacing: '-0.5px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
            Try it for free
          </h2>
          <p className="text-[14px] mb-7" style={{ color: 'rgb(107,114,128)' }}>
            No credit card needed. Your first analysis is ready in under a minute.
          </p>
          <Link to="/login"
            className="inline-flex items-center gap-2 h-11 px-7 text-white rounded-xl font-semibold text-[14px] transition-all hover:-translate-y-0.5"
            style={{ background: 'rgb(99,102,241)', boxShadow: '0 4px 18px rgba(99,102,241,0.35)' }}
            onMouseEnter={e => e.currentTarget.style.background='rgb(79,70,229)'}
            onMouseLeave={e => e.currentTarget.style.background='rgb(99,102,241)'}>
            Get started
            <svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 8h10M9 4l4 4-4 4"/></svg>
          </Link>
        </FadeIn>
      </section>

      {/* Footer */}
      <footer className="border-t border-black/[0.06] py-6 text-center" style={{ background: 'white' }}>
        <div className="flex items-center justify-center gap-5 text-[12.5px]" style={{ color: 'rgb(156,163,175)' }}>
          <Link to="/" className="hover:text-gray-700 transition-colors">Home</Link>
          <Link to="/pricing" className="hover:text-gray-700 transition-colors">Pricing</Link>
          <Link to="/privacy" className="hover:text-gray-700 transition-colors">Privacy</Link>
        </div>
      </footer>
    </div>
  )
}
