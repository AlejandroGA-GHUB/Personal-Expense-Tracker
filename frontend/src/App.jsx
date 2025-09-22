import { useState } from 'react'
import './App.css'
import CSVUpload from './components/CSVUpload'

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
            onClick={() => setCurrentView('dashboard')}
            className={currentView === 'dashboard' ? 'active' : ''}
          >
            Dashboard
          </button>
        </nav>
      </header>

      <main className="app-main">
        {currentView === 'upload' && <CSVUpload />}
        {currentView === 'dashboard' && (
          <div className="dashboard-placeholder">
            <h2>Dashboard</h2>
            <p>Your financial dashboard will appear here after uploading data.</p>
          </div>
        )}
      </main>
    </div>
  )
}

export default App