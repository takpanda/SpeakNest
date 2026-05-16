# SpeakNest - 完全ローカル英語学習アプリ

SpeakNestは、外部APIに依存しない完全ローカルの英語学習アプリケーションです。
Ollama（LLM）、 whisper.cpp（音声認識）、piper（音声合成）を自前でホストし、
インターネット接続なしで英語の発音練習、フィードバック、音声対話を提供します。

## アーキテクチャ

```
┌─────────────┐       http://backend:8000        ┌──────────────┐
│   Frontend   │ ──────────────────────────────►  │   Backend    │
│  (Vite +     │                                  │  (FastAPI)   │
│   React)     │ ◄──────────────────────────────  │              │
│ :3000        │       CORS / API calls           │ :8000        │
└─────────────┘                                  └──────┬───────┘
                                                         │
                                              http://ollama:11434
                                                         │
                                                  ┌──────▼───────┐
                                                  │    Ollama    │
                                                  │   (LLM API)  │
                                                  └──────────────┘
```

## 要件

- **Docker & Docker Compose** (推奨)
- **Node.js** 18+ (ローカル開発用)
- **Python** 3.12+ (ローカル開発用)
- **Ollama** (モデル: qwen2.5 推奨)

## クイックスタート

### Docker Compose (推奨)

```bash
# 全てのサービスを起動
docker-compose up --build

# バックグラウンドで起動
docker-compose up --build -d
```

サービスが起動したら:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Ollama: http://localhost:11434

### ローカル開発 (Docker なし)

```bash
# Ollama の起動 (別途インストールが必要)
# https://ollama.ai からダウンロード

# Backend 起動
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend 起動（別ターミナル）
cd frontend
npm install
npm run dev
```

## 環境変数

| 変数 | 説明 | デフォルト |
|------|------|-----------|
| `PYTHON_VERSION` | Python バージョン | `3.12` |
| `OLLAMA_BASE_URL` | Ollama サーバーのアドレス | `http://localhost:11434` |
| `OLLAMA_MODEL` | 使用するLLMモデル | `qwen2.5` |
| `OLLAMA_TEMPERATURE` | LLM のTemperature | `0.7` |
| `BACKEND_PORT` | Backend のポート | `8000` |
| `FRONTEND_PORT` | Frontend のポート | `3000` |
| `DATA_DIR` | 学習データ保存先 | `./data` |
| `RECORDINGS_DIR` | 録音ファイル保存先 | `./recordings` |
| `CORS_ALLOW_ORIGINS` | CORS 許可オリジン | `http://localhost:3000,http://frontend:3000` |
| `WHISPER_MODEL` | whispered モデルサイズ | `tiny` |
| `WHISPER_LANG` | 学習言語 | `auto` |
| `TTS_MODEL` | 音声合成モデル | `piper-en` |
| `TTS_SPEED` | 音声合成速度 | `1.0` |

## Backend 検証: コンプラントチェック

```bash
# サーバー起動後、以下の curl で健康チェックを確認
curl http://localhost:8000/health
```

正常応答:
```json
{
  "status": "healthy",
  "ollama": "connected"
}
```

ollama が未接続の場合は:
```json
{
  "status": "degraded",
  "ollama": "unreachable"
}
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

## Frontend-Backend接続テスト

1. Backend を起動
```bash
curl http://localhost:8000/docs
```
Swagger UI が表示されればOK

2. Frontend が Backend に接続できるのを確認
browser console で API エンドポイントが正しくリクエストされていることを確認。
エラーがないことを確認してください。

## プロジェクト構造

```
SpeakNest/
├── docker-compose.yml
├── .env
├── .gitignore
├── README.md
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
|----------|------|
| Frontend | Vite + React + TypeScript |
| Backend | FastAPI + Python 3.12 |
| LLM | Ollama (qwen2.5) |
| 音声認識 | whisper.cpp (予定) |
| 音声合成 | Piper (予定) |
| デプロイ | Docker Compose |
| データベース | SQLite (ローカル) |

## TODO / 次のステップ

### Phase 1 - 基盤（現在）
- [x] Docker Compose 構成の作成
- [x] Backend/Frontend の Dockerfile 作成
- [x] 環境変数テンプレートの整備
- [ ] Ollama モデルのダウンロードと動作確認: `docker-compose exec ollama ollama pull qwen2.5`
- [ ] `/health` エンドポイントでのollama接続確認

### Phase 2 - 音声認識（whisper.cpp）
- [ ] whisper.cpp の Docker サービス追加
- [ ] 音声録音 → 文字起こし ワークフローの実装
- [ ] 発音採点機能の開発

### Phase 3 - 音声合成（piper）
- [ ] Piper TTS の Docker サービス追加
- [ ] 復唱練習機能の実装
- [ ] 音声フィードバック機能

### Phase 4 - 学習機能
- [ ] 会話シナリオエンジン
- [ ] 進捗追跡・履歴機能
- [ ] レポート/ダッシュボード

### Phase 5 - 改善
- [ ] モデル微調整 pipeline
- [ ] 発音詳細分析モデル
- [ ] カスタムシナリオ作成ツール

---

**完全ローカルフリースタック。** 外部APIキー不要、インターネット接続なしで使用可能。

## BEE-42 対応完了

- MVPプロジェクト土台構築完了
- PR: https://github.com/takpanda/SpeakNest/pull/1
- 詳細は上記PRをご確認ください
