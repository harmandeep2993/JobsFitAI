/**
 * Privacy policy page - plain-language GDPR-aligned privacy information.
 */
import { Link } from 'react-router-dom'

function Section({ title, children }) {
  return (
    <section className="mb-10">
      <h2 className="text-[18px] font-bold mb-3"
        style={{ color: 'rgb(15,15,20)', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
        {title}
      </h2>
      <div className="space-y-3 text-[14px] leading-relaxed" style={{ color: 'rgb(107,114,128)' }}>
        {children}
      </div>
    </section>
  )
}

export default function Privacy() {
  return (
    <div className="min-h-screen" style={{ background: 'rgb(248,248,250)', color: 'rgb(15,15,20)' }}>

      {/* Navbar */}
      <header className="sticky top-0 z-50 border-b border-black/[0.07]"
        style={{ background: 'rgba(255,255,255,0.88)', backdropFilter: 'blur(16px)' }}>
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'rgb(99,102,241)' }}>
              <svg width="13" height="13" viewBox="0 0 16 16" fill="white"><path d="M8 1L1 4.5v4c0 3.5 2.8 6.2 7 7.5 4.2-1.3 7-4 7-7.5v-4L8 1z"/></svg>
            </div>
            <span className="text-[15px] font-bold tracking-tight" style={{ fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
              Jobs<span style={{ color: 'rgb(99,102,241)' }}>Fit</span>AI
            </span>
          </Link>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-14">
        <div className="mb-10">
          <div className="text-[11px] font-bold uppercase tracking-widest mb-3" style={{ color: 'rgb(156,163,175)' }}>Legal</div>
          <h1 className="text-[clamp(28px,4vw,40px)] font-black mb-3"
            style={{ letterSpacing: '-1px', fontFamily: "'Plus Jakarta Sans',Inter,sans-serif" }}>
            Privacy Policy
          </h1>
          <p className="text-[13.5px]" style={{ color: 'rgb(156,163,175)' }}>
            Last updated: July 2026
          </p>
        </div>

        <div className="rounded-2xl p-6 mb-10 border border-black/[0.06]"
          style={{ background: 'rgba(99,102,241,0.05)', borderColor: 'rgba(99,102,241,0.15)' }}>
          <p className="text-[14px] leading-relaxed" style={{ color: 'rgb(55,65,81)' }}>
            <strong style={{ color: 'rgb(15,15,20)' }}>Short version:</strong> We store only what is
            necessary to provide the service. We never sell your data. We never share it with third parties
            beyond what is needed to call the AI providers you configure. You can delete everything at any time.
          </p>
        </div>

        <Section title="Who we are">
          <p>JobsFitAI is an AI-powered resume analysis tool for job seekers, focused on the German job market.
            References to "we", "us", or "our" in this policy refer to the JobsFitAI service and its operator.</p>
        </Section>

        <Section title="What data we collect">
          <p>We collect and store the following data when you create an account and use the service:</p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li>Your email address and a hashed (bcrypt) version of your password - used to authenticate you.</li>
            <li>Resume files you upload (PDF or DOCX), stored under your account only.</li>
            <li>Extracted text and structured data derived from your resume by the AI pipeline.</li>
            <li>Job descriptions you paste into the analyzer, stored as part of your analysis history.</li>
            <li>Analysis results: match scores, keyword breakdowns, and AI summaries.</li>
            <li>Job listings fetched from Adzuna, Arbeitnow, and the Bundesagentur and scored against your resume.</li>
            <li>Your settings (target job titles, location, LLM provider preference, scheduler state).</li>
          </ul>
          <p>We do not collect payment card data directly. Payments are handled by our payment processor (Stripe),
            which has its own privacy policy.</p>
        </Section>

        <Section title="How we use your data">
          <p>We use the data listed above exclusively to provide the JobsFitAI service to you:</p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li>To authenticate your account and keep your session secure.</li>
            <li>To run the resume extraction and match scoring pipeline against job descriptions you provide.</li>
            <li>To fetch and score live job listings against your current resume.</li>
            <li>To store your history so you can review past analyses.</li>
          </ul>
          <p>We do not use your resume or analysis data to train any AI model. We do not use it for advertising.
            We do not profile you for any purpose other than delivering the features you actively use.</p>
        </Section>

        <Section title="AI providers and third-party APIs">
          <p>To perform resume extraction and scoring, your resume text and job description text are sent to the
            AI provider you have selected in Settings. The available providers are:</p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li><strong style={{ color: 'rgb(55,65,81)' }}>OpenAI</strong> - governed by OpenAI's privacy policy and data processing addendum.</li>
            <li><strong style={{ color: 'rgb(55,65,81)' }}>Groq</strong> - governed by Groq's privacy policy.</li>
            <li><strong style={{ color: 'rgb(55,65,81)' }}>Ollama (local)</strong> - runs entirely on your machine. No data leaves your server.</li>
          </ul>
          <p>Job listings are fetched from Adzuna, Arbeitnow, and the Bundesagentur fur Arbeit via their public
            APIs. We only retrieve publicly available job posting data. Your resume data is never sent to these APIs.</p>
        </Section>

        <Section title="Data storage and security">
          <p>Your data is stored in a SQLite database on the server running the JobsFitAI backend. Resume files
            are stored on the same server filesystem under your user ID.</p>
          <p>Passwords are hashed with bcrypt before storage. We never store plain-text passwords.
            API sessions are authenticated with short-lived JWT tokens (30-day expiry).</p>
          <p>We take reasonable technical precautions to protect your data, but no internet service can guarantee
            absolute security. We recommend using a strong, unique password for your account.</p>
        </Section>

        <Section title="Data retention and deletion">
          <p>Your data is retained for as long as your account exists. You can delete individual resumes,
            analyses, and job matches from within the app at any time.</p>
          <p>To delete your entire account and all associated data, send a deletion request from your registered
            email address. We will process the request within 7 days and confirm by email.</p>
        </Section>

        <Section title="Your rights under GDPR">
          <p>If you are based in the EU or Germany, you have the following rights under the General Data
            Protection Regulation (GDPR):</p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li><strong style={{ color: 'rgb(55,65,81)' }}>Right of access</strong> - you can request a copy of the personal data we hold about you.</li>
            <li><strong style={{ color: 'rgb(55,65,81)' }}>Right to rectification</strong> - you can ask us to correct inaccurate data.</li>
            <li><strong style={{ color: 'rgb(55,65,81)' }}>Right to erasure</strong> - you can ask us to delete your data (see Data retention above).</li>
            <li><strong style={{ color: 'rgb(55,65,81)' }}>Right to data portability</strong> - you can request your analysis history as a CSV export.</li>
            <li><strong style={{ color: 'rgb(55,65,81)' }}>Right to object</strong> - you can object to any processing that is not strictly necessary for the service.</li>
          </ul>
          <p>To exercise any of these rights, contact us at the email address on the About page.</p>
        </Section>

        <Section title="Cookies and tracking">
          <p>JobsFitAI does not use advertising cookies or third-party tracking pixels. We do not integrate
            Google Analytics, Facebook Pixel, or any similar tracking service.</p>
          <p>The only browser storage we use is localStorage to keep your authentication token between sessions.
            This is deleted when you sign out.</p>
        </Section>

        <Section title="Changes to this policy">
          <p>We may update this policy as the service evolves. If we make a material change - such as a new
            category of data collection or a new third-party sharing arrangement - we will notify you by email
            at least 14 days before the change takes effect.</p>
          <p>Continued use of the service after a notified change constitutes acceptance of the updated policy.</p>
        </Section>

        <Section title="Contact">
          <p>If you have questions about this privacy policy or want to exercise your data rights, email us at
            the address listed on the <Link to="/about" className="underline" style={{ color: 'rgb(99,102,241)' }}>About page</Link>.
            We aim to respond within 5 working days.</p>
        </Section>
      </main>

      {/* Footer */}
      <footer className="border-t border-black/[0.06] py-6 text-center" style={{ background: 'white' }}>
        <div className="flex items-center justify-center gap-5 text-[12.5px]" style={{ color: 'rgb(156,163,175)' }}>
          <Link to="/" className="hover:text-gray-700 transition-colors">Home</Link>
          <Link to="/about" className="hover:text-gray-700 transition-colors">About</Link>
          <Link to="/pricing" className="hover:text-gray-700 transition-colors">Pricing</Link>
        </div>
      </footer>
    </div>
  )
}
