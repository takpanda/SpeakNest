import { useState, useEffect } from 'react'
import './App.css'
import ConversationScreen from './pages/ConversationScreen.jsx'
import ShadowingScreen from './pages/ShadowingScreen.jsx'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function App() {
  const [apiStatus, setApiStatus] = useState('checking')
  const [page, setPage] = useState('home') // 'home', 'conversation', 'shadowing'

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(res => res.ok ? setApiStatus('connected') : setApiStatus('disconnected'))
      .catch(() => setApiStatus('disconnected'))
  }, [])

  if (page === 'shadowing') {
    return <div><button className="nav-back" onClick={() => setPage('home')}>← ホームに戻る</button><ShadowingScreen /></div>
  }

  if (page === 'conversation') {
    return (
      <div>
        <button className="nav-back" onClick={() => setPage('home')}>← ホームに戻る</button>
        <ConversationScreen initialScene="cafe_order" initialLevel="A2" />
      </div>
    )
  }

  return (
    <div className="app">
      <h1>SpeakNest - ローカル英語学習アプリ</h1>
      <div className="status">
        API: <span className={apiStatus}>{apiStatus === 'connected' ? 'connected' : apiStatus === 'disconnected' ? 'disconnected' : 'checking...'}</span>
      </div>
      <p>起動にはバックエンドサーバーが必要です。</p>
      <div className="action-buttons">
        <button className="btn-primary" onClick={() => setPage('conversation')}>
          AI英会話練習を始める
        </button>
        <button className="btn-primary" onClick={() => setPage('shadowing')}>
          シャドーイング練習を始める
        </button>
      </div>
      <p className="instructions">
        {'1. CD backend && uvicorn main:app --reload'}
        {'2. こちらで npm run dev を実行'}
        {'3. Docker Compose: docker-compose up --build'}
      </p>
    </div>
  )
}

export default App
