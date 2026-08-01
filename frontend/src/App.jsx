import { useState } from 'react'
import './App.css'
import CSVUpload from './components/CSVUpload'
import ManualTransactionForm from './components/ManualTransactionForm'
import Dashboard from './components/Dashboard'
import ChartsReports from './components/ChartsReports'

function App() {
  const [currentView, setCurrentView] = useState('upload')

  return (
    <div className="App">
      <header className="app-header">
        <h1>Personal Expense Tracker</h1>
        <nav className="app-nav">
          <button 
            onClick={() => setCurrentView('upload')}
            className={currentView === 'upload' ? 'active' : ''}
          >
            Upload Data
          </button>
          <button 
            onClick={() => setCurrentView('manual')}
            className={currentView === 'manual' ? 'active' : ''}
          >
            Add Transaction
          </button>
          <button 
            onClick={() => setCurrentView('dashboard')}
            className={currentView === 'dashboard' ? 'active' : ''}
          >
            Dashboard
          </button>
          <button 
            onClick={() => setCurrentView('charts')}
            className={currentView === 'charts' ? 'active' : ''}
          >
            Charts & Reports
          </button>
        </nav>
      </header>

      <main className="app-main">
        <div style={{ display: currentView === 'upload' ? 'block' : 'none' }}>
          <CSVUpload />
        </div>
        <div style={{ display: currentView === 'manual' ? 'block' : 'none' }}>
          <ManualTransactionForm />
        </div>
        <div style={{ display: currentView === 'dashboard' ? 'block' : 'none' }}>
          <Dashboard />
        </div>
        <div style={{ display: currentView === 'charts' ? 'block' : 'none' }}>
          <ChartsReports />
        </div>
      </main>
    </div>
  )
}

export default App