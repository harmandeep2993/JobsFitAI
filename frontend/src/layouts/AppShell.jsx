import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { ToastProvider } from '../components/Toast.jsx'
import TopBar from '../components/TopBar.jsx'
import Sidebar from '../components/Sidebar.jsx'
import Analyzer from '../components/tabs/Analyzer.jsx'
import JobMatches from '../components/tabs/JobMatches.jsx'
import Resumes from '../components/tabs/Resumes.jsx'
import ATS from '../components/tabs/ATS.jsx'
import History from '../components/tabs/History.jsx'
import Settings from '../components/tabs/Settings.jsx'

const TABS = {
  analyzer: Analyzer,
  ats:      ATS,
  matches:  JobMatches,
  resumes:  Resumes,
  history:  History,
  settings: Settings,
}

const pageVariants = {
  initial: { opacity: 0, y: 10 },
  enter:   { opacity: 1, y: 0, transition: { duration: 0.18, ease: [0.25, 0.1, 0.25, 1] } },
  exit:    { opacity: 0, y: -6, transition: { duration: 0.12 } },
}

export default function AppShell() {
  const [tab, setTab] = useState('analyzer')
  const TabContent = TABS[tab] || Analyzer

  return (
    <ToastProvider>
      <div className="min-h-screen bg-bg text-t1">
        <TopBar />
        <Sidebar active={tab} onChange={setTab} />
        <main
          style={{
            paddingTop: 'var(--topbar-h)',
            paddingLeft: 'var(--sidebar-w)',
            minHeight: '100vh',
          }}
        >
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={tab}
              variants={pageVariants}
              initial="initial"
              animate="enter"
              exit="exit"
              className="max-w-5xl mx-auto px-6 py-8"
            >
              <TabContent />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </ToastProvider>
  )
}
