import { useState } from 'react'
import './App.css'
import CSVUpload from './components/CSVUpload'
import ManualTransactionForm from './components/ManualTransactionForm'
import Dashboard from './components/Dashboard'

function App() {
  const [currentView, setCurrentView] = useState('upload')

  return (
    <div className="App">
      <header className="app-header">
        <h1>Personal Finance Tracker</h1>
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
        </nav>
      </header>

      <main className="app-main">
        {currentView === 'upload' && <CSVUpload />}
        {currentView === 'manual' && <ManualTransactionForm />}
        {currentView === 'dashboard' && <Dashboard />}
      </main>
    </div>
  )
}

export default App