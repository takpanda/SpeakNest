## 背景

Phase 1の核心機能を実装する。MVPの要件はissue BEE-43に記載。

## 実装内容

### ディレクトリ構成

```
backend/
  app/
    main.py          # FastAPI アプリ本体
    config.py        # 設定（環境変数）
    schemas.py       # リクエスト/レスポンスモデル
    routers/
      health.py      # ヘルスチェック
      chat.py        # 会話エンドポイント
      audio.py       # 音声アップロード
    services/
      stt_service.py     # STT（whisper.cpp）抽象化
      ollama_service.py  # Ollama 抽象化
    prompts/
      conversation.md    # 会話相手プロンプト
      feedback.md        # 添削プロンプト
  tests/
    conftest.py      # テスト共通設定
    test_health.py   # ヘルスチェックテスト
    test_chat.py     # 会話エンドポイント tests
    test_audio.py    # 音声アップロード tests
  pyproject.toml
  .env.example
  README.md
```

### 環境変数

| 変数名 | 初期値 | 説明 |
|--------|--------|------|
| SPEAKNEST_OLLAMA_BASE_URL | http://localhost:11434 | Ollama API エンドポイント |
| SPEAKNEST_OLLAMA_MODEL | llama3.2 | 使用するOllamaモデル |
| SPEAKNEST_STT_BASE_URL | http://localhost:8080 | STTサービスエンドポイント |
| SPEAKNEST_STT_MODEL | base.en | STTモデル |
| SPEAKNEST_UPLOAD_DIR | data/recordings | 音声ファイル保存先 |
| SPEAKNEST_CORS_ORIGINS | * | CORS許可オリジン |
| SPEAKNEST_DEBUG | false | デバッグモード |

### API仕様

#### GET /api/health

ヘルスチェック。STTとOllamaの接続状態を返す。

##### レスポンス例

```json
{
  "status": "ok",
  "ollama": "ok",
  "stt": "not_available",
  "upload_dir": "data/recordings"
}
```

`ollama` / `stt` が `"ok"` の場合は接続成功、`"not_available"` の場合は接続不可。

#### POST /api/chat

会話処理。音声ファイルのアップロードは separate endpoint にて行う。
本エンドポイントは transcript の受け取りとLLMへの処理を担う。

##### リクエスト例

```json
{
  "level": "A2",
  "scenario": "カフェで注文する",
  "transcript": "I would like a coffee please."
}
```

##### レスポンス例（成功）

```json
{
  "transcript": "I would like a coffee please.",
  "reply_en": "Sure! Would you like it hot or iced?",
  "reply_ja": "はい！ホットアイスどちらにしますか？",
  "feedback_ja": "「I would like」の使い方が正確です。丁寧で自然な表現です。",
  "next_practice": "Could I have a latte, please?"
}
```

##### エラーケース

- `400`: transcript が空、または入力パラメータ不正
- `503`: STTまたはOllamaが接続不可

#### POST /api/audio/upload

音声ファイルをアップロードしてローカルに保存。

##### リクエスト

- Content-Type: multipart/form-data
- Form field: `file` (audio file)
- 許可される MIME タイプ: audio/webm, audio/wav, audio/mp4, audio/mpeg, audio/x-wav
- 最大ファイルサイズ: 30MB

##### レスポンス例

```json
{
  "file_id": "abc123def456.wav",
  "file_path": "data/recordings/abc123def456.wav",
  "size": 245760,
  "mime_type": "audio/wav"
}
```

#### GET /api/audio/uploads/{file_id}

アップロードした音声ファイルを取得する。

#### GET /

アプリ情報と `/docs` へのリンクを返す。

## 参照

- Issue: BEE-43
- プロジェクト設計: BEE-41
