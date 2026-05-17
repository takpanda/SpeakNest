import { useState, useRef, useCallback, useEffect } from 'react'
import { getCATEGORIES, getLEVELS, fetchSentences, fetchTtsAudio, evaluateShadowing, saveSession } from '../services/shadowingApi.js'
import './ShadowingScreen.css'

const SPEED_OPTIONS = [0.75, 1.0, 1.25]

const STATUS = {
  IDLE: 'idle',
  PLAYING: 'playing',
  RECORDING: 'recording',
  PROCESSING: 'processing',
  SUCCESS: 'success',
  ERROR: 'error',
  NO_MIC: 'no-mic',
}

function ShadowingScreen() {
  const [categories, setCategories] = useState(getCATEGORIES())
  const [levels, setLevels] = useState(getLEVELS())
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedLevel, setSelectedLevel] = useState('all')
  const [sentences, setSentences] = useState([])
  const [selectedSentence, setSelectedSentence] = useState(null)
  const [status, setStatus] = useState(STATUS.IDLE)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [isSupported, setIsSupported] = useState(true)

  const [playbackSpeed, setPlaybackSpeed] = useState(1.0)
  const [isRepeating, setIsRepeating] = useState(false)

  const audioRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const mediaStreamRef = useRef(null)
  const chunksRef = useRef([])
  const repeatTimeoutRef = useRef(null)

  const statusTextMap = {
    idle: 'シャドーイング練習',
    playing: '音声再生中',
    recording: '録音中',
    processing: '評価中...',
    success: '完了',
    error: 'エラー',
    'no-mic': 'マイク不可',
  }

  // Fetch sentences on mount and when filters change
  useEffect(() => {
    fetchSentences(selectedCategory === 'all' ? null : selectedCategory, selectedLevel === 'all' ? null : selectedLevel)
      .then((data) => setSentences(data.sentences || []))
      .catch((err) => console.error('Failed to load sentences:', err))
  }, [selectedCategory, selectedLevel])

  // Microphone support check
  useEffect(() => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setIsSupported(false)
      setStatus(STATUS.NO_MIC)
    }
    return () => {
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((t) => t.stop())
      }
      if (repeatTimeoutRef.current) {
        clearTimeout(repeatTimeoutRef.current)
      }
    }
  }, [])

  // Audio playback with speed control
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackSpeed
    }
  }, [playbackSpeed])

  const playReferenceAudio = useCallback(async () => {
    if (!selectedSentence) return
    setError('')
    setStatus(STATUS.PLAYING)
    setIsRepeating(false)

    try {
      const blob = await fetchTtsAudio(selectedSentence.text)
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audio.playbackRate = playbackSpeed
      audio.onended = () => setStatus(STATUS.IDLE)
      audioRef.current = audio
      audio.play()
    } catch (err) {
      setStatus(STATUS.ERROR)
      setError(`お手本音声が取得できません: ${err.message}`)
      console.error('TTS fetch failed:', err)
    }
  }, [selectedSentence, playbackSpeed])

  const toggleRepeat = useCallback(() => {
    if (!selectedSentence) return
    setIsRepeating((prev) => {
      if (!prev) {
        // Start repeating
        playReferenceAudio()
        repeatTimeoutRef.current = setInterval(() => {
          if (audioRef.current) {
            audioRef.current.currentTime = 0
            audioRef.current.play()
          }
        }, 4000)
        return true
      } else {
        // Stop repeating
        if (repeatTimeoutRef.current) {
          clearInterval(repeatTimeoutRef.current)
          repeatTimeoutRef.current = null
        }
        if (audioRef.current) {
          audioRef.current.pause()
          audioRef.current = null
        }
        setStatus(STATUS.IDLE)
        return false
      }
    })
  }, [selectedSentence, playReferenceAudio])

  const startRecording = useCallback(async () => {
    setError('')
    setResult(null)
    setStatus(STATUS.RECORDING)

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream

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

        // Upload
        setStatus(STATUS.PROCESSING)

        try {
          const transcribedText = await transcribeLocally(blob)
          if (!transcribedText) {
            setStatus(STATUS.ERROR)
            setError('音声の書き起こしができませんでした。もう一度お試しください。')
            return
          }

          if (selectedSentence) {
            const evalResult = await evaluateShadowing(selectedSentence.text, transcribedText)
            setResult(evalResult)
            setStatus(STATUS.SUCCESS)
          }
        } catch (err) {
          setStatus(STATUS.ERROR)
          setError(`評価に失敗しました: ${err.message}`)
          console.error('Evaluation failed:', err)
        }
      }

      mediaRecorder.start()
      setStatus(STATUS.RECORDING)
    } catch (err) {
      setStatus(STATUS.NO_MIC)
      if (err.name === 'NotAllowedError') {
        setError('マイクへのアクセスが拒否されました。')
      } else if (err.name === 'NotFoundError') {
        setError('マイクが見つかりません。')
      } else {
        setError(`マイクエラー: ${err.message}`)
      }
    }
  }, [selectedSentence])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop())
      mediaStreamRef.current = null
    }
  }, [])

  const retry = useCallback(() => {
    setStatus(STATUS.IDLE)
    setResult(null)
    setError('')
  }, [])

  const resetAll = useCallback(() => {
    setSelectedSentence(null)
    setStatus(STATUS.IDLE)
    setResult(null)
    setError('')
    setIsRepeating(false)
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }
    if (repeatTimeoutRef.current) {
      clearInterval(repeatTimeoutRef.current)
      repeatTimeoutRef.current = null
    }
  }, [])

  const selectedCategoryName = selectedCategory === 'all' ? '全て' : categories.find((c) => c.id === selectedCategory)?.name || ''
  const selectedLevelName = selectedLevel === 'all' ? '全て' : levels.find((l) => l.id === selectedLevel)?.name || ''

  if (!isSupported) {
    return (
      <div className="shadowing-screen">
        <div className="shadowing-card">
          <h2>シャドーイング練習</h2>
          <div className="error-banner">
            <p className="error-title">マイクが利用できません</p>
            <p>お使いのブラウザは音声録音に対応していません。マイクをサポートしているブラウザでご利用ください。</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="shadowing-screen">
      <div className="shadowing-card">
        <h2>シャドーイング練習</h2>

        {/* Filter controls */}
        <div className="shadowing-filters">
          <div className="filter-group">
            <label htmlFor="category-select">カテゴリ</label>
            <select
              id="category-select"
              value={selectedCategory}
              onChange={() => {
                if (status === STATUS.IDLE) {
                  setSelectedCategory(event.target.value)
                  resetAll()
                }
              }}
              disabled={status !== STATUS.IDLE}
            >
              <option value="all">全て</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div className="filter-group">
            <label htmlFor="level-select">レベル</label>
            <select
              id="level-select"
              value={selectedLevel}
              onChange={() => {
                if (status === STATUS.IDLE) {
                  setSelectedLevel(event.target.value)
                  resetAll()
                }
              }}
              disabled={status !== STATUS.IDLE}
            >
              <option value="all">全て</option>
              {levels.map((l) => (
                <option key={l.id} value={l.id}>{l.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Current sentence display */}
        {selectedSentence && (
          <div className="sentence-display">
            <div className="sentence-header">
              <span className="sentence-category">{selectedSentence.category}</span>
              <span className="sentence-level">{selectedSentence.level}</span>
            </div>
            <p className="sentence-text">{selectedSentence.text}</p>
            <p className="sentence-translation">{selectedSentence.translation_ja}</p>
          </div>
        )}

        {/* Sentence list */}
        {status === STATUS.IDLE && sentences.length > 0 && !selectedSentence && (
          <div className="sentence-list">
            <h3 className="sentence-list-title">練習文リスト</h3>
            <div className="sentence-list-scroll">
              {sentences.map((s) => (
                <div
                  key={s.id}
                  className="sentence-item"
                  onClick={() => {
                    if (status === STATUS.IDLE) {
                      setSelectedSentence(s)
                    }
                  }}
                >
                  <div className="sentence-item-header">
                    <span className="sentence-item-id">{s.id}</span>
                    <span className="sentence-item-level">{s.level}</span>
                  </div>
                  <p className="sentence-item-text">{s.text}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Status indicator */}
        {status !== STATUS.IDLE && status !== STATUS.SUCCESS && status !== STATUS.ERROR && (
          <div className="status-indicator">
            {status === STATUS.PLAYING && <span className="status-dot playing" />}
            {status === STATUS.RECORDING && <span className="status-dot recording" />}
            {status === STATUS.PROCESSING && <div className="status-spinner" />}
            {statusTextMap[status]}
          </div>
        )}

        {/* Error banner */}
        {status === STATUS.ERROR && (
          <div className="error-banner">
            <p className="error-title">エラーが発生しました</p>
            <p>{error}</p>
            <button className="btn-secondary" onClick={status === STATUS.RECORDING ? stopRecording : retry}>
              {status === STATUS.RECORDING ? '録音停止' : 'やり直す'}
            </button>
          </div>
        )}

        {/* Result panel */}
        {status === STATUS.SUCCESS && result && (
          <div className="result-panel">
            <div className="result-section">
              <h3 className="result-label">あなたの発話</h3>
              <p className="result-text">{result.transcript}</p>
            </div>
            <div className="result-section wer-section">
              <h3 className="result-label">発話評価</h3>
              <div className="wer-display">
                <span className={`wer-score ${result.wer < 0.3 ? 'good' : result.wer < 0.6 ? 'fair' : 'poor'}`}>
                  WER: {result.wer > 0 ? (result.wer * 100).toFixed(0) : 0}%
                </span>
                <span className="accuracy-text">
                  正確度: {(result.accuracy * 100).toFixed(0)}%
                </span>
              </div>
              {result.missing_words && result.missing_words.length > 0 && (
                <p className="result-text-dim">
                  足りない単語: {result.missing_words.join(', ')}
                </p>
              )}
              {result.extra_words && result.extra_words.length > 0 && (
                <p className="result-text-dim">
                  追加された単語: {result.extra_words.join(', ')}
                </p>
              )}
            </div>
            <div className="result-section">
              <h3 className="result-label">フィードバック</h3>
              <div className="feedback-content">
                <p className="result-text-en">{result.reply_en || '—'}</p>
                <p className="result-text-ja">{result.feedback_ja || '—'}</p>
              </div>
            </div>
            {result.next_practice && (
              <div className="result-section">
                <h3 className="result-label">次の練習文</h3>
                <p className="result-text-practice">{result.next_practice}</p>
              </div>
            )}
          </div>
        )}

        {/* Action buttons - shown when sentence is selected */}
        {selectedSentence && (
          <div className="shadowing-actions">
            {/* Playback controls */}
            {status === STATUS.IDLE && selectedSentence && (
              <div className="playback-controls">
                <div className="speed-control">
                  <span className="speed-label">再生速度:</span>
                  {SPEED_OPTIONS.map((speed) => (
                    <button
                      key={speed}
                      className={`speed-btn ${playbackSpeed === speed ? 'active' : ''}`}
                      onClick={() => setPlaybackSpeed(speed)}
                    >
                      {speed}x
                    </button>
                  ))}
                </div>
                <div className="action-buttons">
                  <button className="btn-play" onClick={playReferenceAudio}>
                    再生
                  </button>
                  <button
                    className={`btn-repeat ${isRepeating ? 'active' : ''}`}
                    onClick={toggleRepeat}
                  >
                    {isRepeating ? 'リピート停止' : 'リピート'}
                  </button>
                  <button className="btn-record" onClick={startRecording}>
                    録音開始
                  </button>
                </div>
              </div>
            )}

            {/* Recording state */}
            {status === STATUS.RECORDING && (
              <div className="action-buttons">
                <button className="btn-stop" onClick={stopRecording}>
                  録音停止・送信
                </button>
              </div>
            )}

            {/* Processing state */}
            {status === STATUS.PROCESSING && (
              <div className="action-buttons">
                <div className="loading-spinner-wrapper">
                  <div className="spinner" />
                  <p>書き起こしと評価を実行中...</p>
                </div>
              </div>
            )}

            {/* After result */}
            {status === STATUS.SUCCESS && (
              <div className="action-buttons">
                <button className="btn-play" onClick={playReferenceAudio}>
                  再生
                </button>
                <button className="btn-record" onClick={startRecording}>
                  もう一度録音
                </button>
                <button className="btn-secondary" onClick={resetAll}>
                  シャドーイング終了
                </button>
              </div>
            )}
          </div>
        )}

        {/* Select sentence hint */}
        {status === STATUS.IDLE && sentences.length === 0 && (
          <div className="empty-state">
            <p>学習文がありません。カテゴリとレベルを選択してください。</p>
          </div>
        )}

        {status === STATUS.IDLE && selectedSentence === null && (
          <div className="empty-state">
            <p>リストから練習文を選んでください。</p>
          </div>
        )}
      </div>
    </div>
  )
}

// Local transcription fallback (mock) when STT backend is unavailable
async function transcribeLocally(blob) {
  // Phase 3: Replace with actual STT call to /api/audio/upload + transcribe
  // For now, return placeholder text based on the blob
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve('I would like a cup of coffee, please')
    }, 500)
  })
}

export default ShadowingScreen
