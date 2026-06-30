import { useState } from 'react'
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
  matches:  JobMatches,
  resumes:  Resumes,
  ats:      ATS,
  history:  History,
  settings: Settings,
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
          <div className="max-w-5xl mx-auto px-6 py-8">
            <TabContent />
          </div>
        </main>
      </div>
    </ToastProvider>
  )
}
