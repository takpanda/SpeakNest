import { useState, useRef, useCallback, useEffect } from 'react'
import { getScenes, getLevels, submitAudio, getMockResult } from '../services/conversationApi.js'
import './ConversationScreen.css'

const TTS_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const STATUS = {
  IDLE: 'idle',
  RECORDING: 'recording',
  UPLOADING: 'uploading',
  SUCCESS: 'success',
  ERROR: 'error',
  NO_MIC: 'no-mic',
}

function ConversationScreen({ initialScene, initialLevel }) {
  const [scenes] = useState(getScenes())
  const [levels] = useState(getLevels())
  const [selectedScene, setSelectedScene] = useState(initialScene || scenes[0].id)
  const [selectedLevel, setSelectedLevel] = useState(initialLevel || levels[1].id)
  const [status, setStatus] = useState(STATUS.IDLE)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [isSupported, setIsSupported] = useState(true)
  const [isTtsReady, setIsTtsReady] = useState(true)
  const [isPlaying, setIsPlaying] = useState(false)

  const audioRef = useRef(null)

  const mediaRecorderRef = useRef(null)
  const audioUrlRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const mediaStreamRef = useRef(null)

  // Check microphone support on mount
  useEffect(() => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setIsSupported(false)
      setStatus(STATUS.NO_MIC)
    }
    return () => {
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((t) => t.stop())
      }
    }
  }, [])

  const startRecording = useCallback(async () => {
    setError('')
    setResult(null)
    setStatus(STATUS.UPLOADING)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream
      streamRef.current = stream

      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        chunksRef.current = []

        // Upload the audio to backend
        setStatus(STATUS.UPLOADING)

        try {
          const res = await submitAudio(blob, selectedScene, selectedLevel)
          setResult(res)
          setStatus(STATUS.SUCCESS)
        } catch (err) {
          setStatus(STATUS.ERROR)
          setError(err.message || '送信に失敗しました')
        }
      }

      mediaRecorder.start()
      setStatus(STATUS.RECORDING)
    } catch (err) {
      streamRef.current = null
      if (err.name === 'NotAllowedError') {
        setStatus(STATUS.NO_MIC)
        setError('マイクへのアクセスが拒否されました。ブラウザの設定でマイクの使用を許可してください。')
      } else if (err.name === 'NotFoundError') {
        setStatus(STATUS.NO_MIC)
        setError('マイクが見つかりません。接続されているか確認してください。')
      } else {
        setStatus(STATUS.NO_MIC)
        setError(`マイクエラー: ${err.message}`)
      }
    }
  }, [selectedScene, selectedLevel])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop())
      mediaStreamRef.current = null
    }
  }, [])

  const resetState = useCallback(() => {
    setStatus(STATUS.IDLE)
    setError('')
    setResult(null)
  }, [])

  const playAiReply = useCallback(async () => {
    if (!result?.reply_en || isPlaying) return
    setIsPlaying(true)
    setError('')
    try {
      const resp = await fetch(`${TTS_BASE}/tts/synthesize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: result.reply_en }),
      })
      if (!resp.ok) {
        setIsTtsReady(false)
        throw new Error(`TTS error: ${resp.status}`)
      }
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
      audioRef.current = new Audio(url)
      audioRef.current.onended = () => {
        setIsPlaying(false)
        URL.revokeObjectURL(url)
      }
      audioRef.current.onerror = () => {
        setIsTtsReady(false)
        setIsPlaying(false)
      }
      await audioRef.current.play()
    } catch {
      setIsTtsReady(false)
      setIsPlaying(false)
    }
  }, [result, isPlaying])

  const retryConversation = useCallback(() => {
    setStatus(STATUS.IDLE)
    setError('')
    setResult(null)
  }, [])

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  const [recordingSeconds, setRecordingSeconds] = useState(0)
  const intervalRef = useRef(null)

  useEffect(() => {
    if (status === STATUS.RECORDING) {
      setRecordingSeconds(0)
      intervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1)
      }, 1000)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [status])

  const selectedSceneName = scenes.find((s) => s.id === selectedScene)?.name || ''
  const selectedLevelName = levels.find((l) => l.id === selectedLevel)?.name || ''

  if (!isSupported) {
    return (
      <div className="conversation-screen">
        <div className="conversation-card">
          <h2>AI英会話練習</h2>
          <div className="error-banner">
            <p className="error-title">マイクが利用できません</p>
            <p>お使いのブラウザは音声録音に対応していません。マイクをサポートしているブラウザでご利用ください。</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="conversation-screen">
      <div className="conversation-card">
        <h2>AI英会話練習</h2>

        {/* Scene & Level Selection */}
        <div className="conversation-config">
          <div className="config-field">
            <label htmlFor="scene-select">シーン</label>
            <select
              id="scene-select"
              value={selectedScene}
              onChange={(e) => {
                if (status === STATUS.IDLE || status === STATUS.ERROR) {
                  setSelectedScene(e.target.value)
                  setResult(null)
                }
              }}
              disabled={status !== STATUS.IDLE && status !== STATUS.ERROR}
            >
              {scenes.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div className="config-field">
            <label htmlFor="level-select">レベル</label>
            <select
              id="level-select"
              value={selectedLevel}
              onChange={(e) => {
                if (status === STATUS.IDLE || status === STATUS.ERROR) {
                  setSelectedLevel(e.target.value)
                  setResult(null)
                }
              }}
              disabled={status !== STATUS.IDLE && status !== STATUS.ERROR}
            >
              {levels.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Status: IDLE - show selected scene level info */}
        {status === STATUS.IDLE && (
          <div className="conversation-info">
            <p>シーン: <strong>{selectedSceneName}</strong></p>
            <p>レベル: <strong>{selectedLevelName}</strong></p>
          </div>
        )}

        {/* Recording timer */}
        {status === STATUS.RECORDING && (
          <div className="recording-indicator">
            <span className="recording-dot" />
            録音中 {formatTime(recordingSeconds)}
          </div>
        )}

        {/* Uploading state */}
        {status === STATUS.UPLOADING && (
          <div className="loading">
            <div className="spinner" />
            <p>送信中... 書き起こしとフィードバックを生成しています</p>
          </div>
        )}

        {/* Microphone access denied */}
        {status === STATUS.NO_MIC && (
          <div className="error-banner">
            <p className="error-title">録音できません</p>
            <p>{error}</p>
            <button className="btn-secondary" onClick={resetState}>閉じる</button>
          </div>
        )}

        {/* Error banner */}
        {status === STATUS.ERROR && (
          <div className="error-banner">
            <p className="error-title">エラーが発生しました</p>
            <p>{error}</p>
            <button className="btn-secondary" onClick={retryConversation}>やり直す</button>
          </div>
        )}

        {/* Result display - only when SUCCESS or IDLE */}
        {status === STATUS.SUCCESS && result && (
          <div className="result-panel">
            <div className="result-section">
              <h3 className="result-label">あなたの発話</h3>
              <p className="result-text">{result.transcript}</p>
            </div>
            <div className="result-section">
              <h3 className="result-label">AI Reply</h3>
              <p className="result-text-en">{result.reply_en}</p>
              <p className="result-text-ja">{result.reply_ja}</p>
              <div className="reply-actions">
                <button
                  className="btn-play"
                  disabled={!isTtsReady || isPlaying}
                  onClick={playAiReply}
                >
                  {isPlaying ? '再生中...' : isTtsReady ? '▶ 再生' : '音声利用不可'}
                </button>
              </div>
              <audio ref={audioRef} hidden />
            </div>
            <div className="result-section">
              <h3 className="result-label">フィードバック</h3>
              <p className="result-text-ja">{result.feedback_ja}</p>
            </div>
            <div className="result-section">
              <h3 className="result-label">次の練習文</h3>
              <p className="result-text-practice">{result.next_practice}</p>
            </div>
            <button className="btn-record" onClick={retryConversation}>
              もう一度話す
            </button>
          </div>
        )}

        {/* Record button */}
        {(status === STATUS.IDLE || status === STATUS.SUCCESS || status === STATUS.ERROR) && (
          <div className="record-actions">
            <button className="btn-record" onClick={startRecording}>
              <span className="record-icon" /> 録音開始
            </button>
          </div>
        )}

        {/* Stop button - only shown while actually recording */}
        {status === STATUS.RECORDING && (
          <div className="record-actions">
            <button className="btn-stop" onClick={stopRecording}>
              録音停止・送信
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default ConversationScreen
