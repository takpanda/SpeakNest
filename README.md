# SpeakNest - 英語学習アプリ

SpeakNestは、Ollama（LLM）、whisper.cpp（音声認識）、piper（音声合成）を自前でホストし、
インターネット接続なしで英語の発音練習、フィードバック、音声対話を提供します。

## アーキテクチャ

```
┌─────────────┐       http://backend:8000        ┌──────────────┐
│   Frontend   │ ────────────────────────────►  │   Backend    │
│  (Vite +     │                                  │  (FastAPI)   │
│   React)     │ ◄──────────────────────────────  │              │
│ :3000        │       CORS / API calls           │ :8000        │
└─────────────┘                                  └───┬──────┘
                                                          │
       http://whisper:8000                    http://192.168.1.103:11434
                                                          │
                                                   ┌──────▼───────┐
                                                   │    Ollama    │
                                                   │ (remote)     │
                                                   └──────────────┘
    ┌────────────────┐
    │  Whisper STT   │
    │    :8001       │
    │(faster-whipser)│
    └────────────────┘
```

## 要件

- **Docker & Docker Compose** (推奨)
- **Node.js** 18+ (ローカル開発用)
- **Python** 3.12+ (ローカル開発用)
- **Ollama** (モデル: gemma4:e4b, リモートサーバー 192.168.1.103)

## クイックスタート

### Docker Compose (推奨)

```bash
# Ollama モデルを事前に pull しておく (192.168.1.103 の Ollama 上で)
bash scripts/setup-ollama-model.sh

# 全てのサービスを起動
docker-compose up --build

# バックグラウンドで起動
docker-compose up --build -d
```

サービスが起動したら:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Whisper STT: http://localhost:8001
- Ollama: http://192.168.1.103:11434 (リモート)

### ローカル開発 (Docker なし)

```bash
# Ollama の起動 (192.168.1.103 上に Ollama がインストールされている前提)
# gemma4:e4b モデルを pull: https://ollama.com/library/gemma4

# Backend 起動
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Whisper STT 起動
cd ../services/whisper
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8001

# Frontend 起動（別ターミナル）
cd frontend
npm install
npm run dev
```

## 環境変数

| 変数 | 説明 | デフォルト |
|--|----|------------|
| `SPEAKNEST_OLLAMA_BASE_URL` | Ollama サーバーのアドレス | `http://192.168.1.103:11434` |
| `SPEAKNEST_OLLAMA_MODEL` | 使用するLLMモデル | `gemma4:e4b` |
| `SPEAKNEST_STT_BASE_URL` | STT サービスのアドレス | `http://whisper:8000` |
| `SPEAKNEST_STT_MODEL` | STTモデル | `medium` |
| `SPEAKNEST_UPLOAD_DIR` | 学習データ保存先 | `./data/recordings` |
| `SPEAKNEST_CORS_ORIGINS` | CORS 許可オリジン | `*` |
| `SPEAKNEST_DEBUG` | デバッグモード | `false` |

## Backend 検証

### ヘルスチェック

```bash
curl http://localhost:8000/api/health
```

正常応答:
```json
{
  "status": "ok",
  "ollama": "ok",
  "stt": "ok",
  "upload_dir": "data/recordings"
}
```

ollama が未接続の場合は:
```json
{
  "status": "degraded",
  "ollama": "not_available",
  "stt": "ok",
  "upload_dir": "data/recordings"
}
```

### Whisper STT

```bash
curl -X POST http://localhost:8001/health
curl -X POST -F "file=@sample.wav" http://localhost:8001/transcribe
```

## Frontend-Backend 接続設定

Frontend から Backend への API 接続先は環境変数で設定できます。

### Docker 環境
Frontend の Dockerfile で `VITE_API_BASE_URL=http://backend:8000` をビルド時に設定。
Docker ネットワーク内で `backend` ホスト名で Backend サービスにアクセス可能。

### ローカル開発
`frontend/.env` に以下を記載:
```
VITE_API_BASE_URL=http://localhost:8000
```

## プロジェクト構造

```
SpeakNest/
├── docker-compose.yml
├── README.md
├── scripts/
│   └── setup-ollama-model.sh
├── services/
│   ├── whisper/
│   │   ├── Dockerfile
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── README.md
│   └── piper/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── services/
│   │   ├── db/
│   │   └── prompts/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   ├── Dockerfile
│   ├── vite.config.js
│   ├── package.json
│   └── .env.example
└── tests/
    └── test_health.py
```

## Tech stack

| レイヤー | 技術 |
|------|----|
| Frontend | Vite + React + TypeScript |
| Backend | FastAPI + Python 3.12 |
| LLM | Ollama (gemma4:e4b) |
| 音声認識 | whisper.cpp (faster-whisper, medium) |
| 音声合成 | Piper (予定) |
| デプロイ | Docker Compose |
| データベース | SQLite (ローカル) |

## TODO

### Phase 1 - 基盤（実装中）
- [x] Docker Compose 構成の作成
- [x] Backend/Frontend の Dockerfile 作成
- [x] 環境変数テンプレートの整備
- [x] whisper.cpp サービスの追加
- [x] Ollama リモートサーバーへの接続変更
- [ ] Ollama モデル (gemma4:e4b) の動作確認

### Phase 2 - 音声合成（piper）
- [ ] Piper TTS の Docker サービス追加
- [ ] 復唱練習機能の実装
- [ ] 音声フィードバック機能

### Phase 3 - 学習機能
- [ ] 会話シナリオエンジン
- [ ] 進捗追跡・履歴機能
- [ ] レポート/ダッシュボード

### Phase 4 - 改善
- [ ] モデル微調整 pipeline
- [ ] 発音詳細分析モデル
- [ ] カスタムシナリオ作成ツール

---

**外部 Ollama サーバー経由の学習スタック。**
