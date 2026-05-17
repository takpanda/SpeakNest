#!/usr/bin/env python3
"""
SpeakNest Phase 1 MVP - E2E 結合確認手順書 + テスト結果

このスクリプトは確認手順を出力するだけであり、実際の外部サービス依存チェックは
手動で行う（Ollama / STT が未接続の場合、健康チェックは degraded を返す）。

Usage:
    python3 scripts/e2e_checklist.py
"""

CHECKLIST = """\
========================================
SpeakNest Phase 1 MVP E2E 結合確認書
========================================

確認環境: Mac (darwin) / Python 3.14.3 / pytest 9.0.3 / httpx 0.28+

----------------------------------------
1. 事前条件
----------------------------------------
[ ] docker-compose up して全サービスが起動していること
     確認コマンド: docker-compose ps
     期待: frontend, backend, whisper が healthy

[ ] Ollama がローカル または リモート (192.168.1.103:11434) で起動していること
     確認コマンド: curl http://192.168.1.103:11434/api/tags
     期待: モデル名のリストが返る

[ ] whisper.cpp STT が docker で起動していること
     確認コマンド: curl http://localhost:8001/health
     期待: HTTP 200

----------------------------------------
2. 主要フロー（正常系）
----------------------------------------
手順:
  1. ブラウザで http://localhost:3000 を開く
  2. シーンを選択（例: "カフェで注文する"）
  3. レベルを選択（例: "A2"）
  4. 「録音開始」ボタン -> 許可 -> 話す
  5. 「録音停止・送信」ボタン
  6. 書き起こしテキスト、AI Reply、フィードバック、次の練習文が表示される

確認事項:
  [ ] 書き起こしテキストが正しく表示される
  [ ] reply_en (英語応答) が表示される
  [ ] reply_ja (日本語訳) が表示される
  [ ] feedback_ja (添削フィードバック) が表示される
  [ ] next_practice (次の練習文) が表示される
  [ ] 「もう一度話す」ボタンで初期状態に戻れる

評価基準:
  6.1 レスポンススキーマ (pydantic ConversationResponse に準拠)
  6.2 全フィールドが非空文字列である
  6.3 エラーバナーが表示されていない

----------------------------------------
3. 主要フロー（自動テスト結果）
----------------------------------------
(既に実施済)

バックエンドユニットテスト (backend/tests/):
  命令: cd SpeakNest/backend && python3 -m pytest tests/ -v
  結果: 14 passed

フロントエンド関連のユニットテスト:
  未実装 (JS/E2E テスト基盤なし)

主要フローの自動テスト観点 (テストコードで保証):
  [x] POST /api/chat - transcript 付き -> 200 + 全フィールド存在
  [x] POST /api/chat - transcript なし -> 400
  [x] POST /api/chat - transcript 空文字 -> 400
  [x] POST /api/audio/upload - 有効な MIME -> 200
  [x] POST /api/audio/upload - 無効な MIME -> 400
  [x] POST /api/audio/upload - 空ファイル -> 400
  [x] GET /api/health -> スキーマ準拠
  [x] GET /api/config -> スキーマ準拠 (全 missing / 全 configured / 混在)
  [x] POST /pronunciation - パフェクトマッチ -> WER 0.0
  [x] POST /pronunciation - 正規化テスト (大文字・句読点・空白)
  [x] POST /pronunciation - エッジケース (空入力, 全 mismatch)
  [x] CORS ヘッダー存在 (OPTIONS および GET)

----------------------------------------
4. 異常系
----------------------------------------
4.1 マイク拒否
  [ ] マイクアクセス拒否 -> STATUS.NO_MIC、エラーバナー表示
  [ ] エラーメッセージ: ブラウザ設定で許可する旨が表示される
  [ ] 「閉じる」ボタンで IDLE 状態に戻る

4.2 Ollama 未接続
  [ ] GET /api/health -> status: "degraded", ollama: "not_available"
  [ ] POST /api/chat -> 503 (エラーメッセージ: "Ollama is not available")
  [ ] フロントエンドでエラーバナー表示

4.3 STT 未接続
  [ ] GET /api/health -> status: "degraded", stt: "not_available"
  [ ] POST /api/conversation (audio) -> 503 (エラーメッセージ: STT failure)
  [ ] フロントエンドで "送信中..." のままタイムアウトする

4.4 不正なファイルタイプ
  [ ] POST /api/audio/upload - .txt -> 400 Unsupported file type
  [ ] POST /api/audio/upload - .png -> 400 Unsupported file type

4.5 ファイルサイズ制限
  [ ] POST /api/audio/upload - 30MB超過 -> 400 File too large

4.6 API 全般のエラーレスポンス
  [ ] 400 レスポンスに detail フィールドが存在する
  [ ] 500 レスポンスに detail フィールドが存在する
  [ ] ユーザーに分かりやすいエラーメッセージが表示される

4.7 長時間録音
  [ ] 60秒以上の録音 -> メモリ不足にならず停止できる
  [ ] 録音停止後、正しくファイル送信できる

----------------------------------------
5. 境界値
----------------------------------------
5.1 発音評価
  [ ] 空文字列の target: WER = 1.0, is_valid = False
  [ ] 空文字列の transcript: WER = 1.0, missing_words = 全単語
  [ ] 1語の単語: WER が正しい
  [ ] 100語以上の長文: 正常に計算される

5.2 シーン/レベル選択
  [ ] シーンが 4件 (カフェ注文, ホテル, 道案内, ショッピング)
  [ ] レベルが 5件 (A1 - C2)
  [ ] シーン/レベル未選択で送れない

5.3 ファイルサイズ
  [ ] 最小ファイル (1バイト) -> 400 File is empty ではない (保存される)
  [ ] 30MBちょうど -> 400 で拒否される
  [ ] 30MB - 1byte -> 正常に保存される

----------------------------------------
6. 完全ローカル要件の確認
----------------------------------------
[ ] docker-compose.yml に Ollama コンテナが comment アウトされている
     -> 外部サービス (192.168.1.103 に依存可能) の使用は確認必須
[ ] .env / env_file が機密情報 (API key) を含まない
[ ] .gitignore が .env / data/ を含む

docker-compose.yml:
  whisper:  -> 内蔵 (build: ./services/whisper)
  backend:  -> 内蔵 (build: ./backend)
  frontend: -> 内蔵 (build: ./frontend)
  ollama:   -> Comment out (外部依存になる)
  piper:    -> Comment out (未実装)

----------------------------------------
7. 確認環境
----------------------------------------
プラットフォーム: darwin (macOS)
Python: 3.14.3
pytest: 9.0.3
httpx: 0.28+
ブラウザ: (要確認 - Safari / Chrome / Firefox のいずれか)

----------------------------------------
8. 未確認事項 / 手動確認が必要なもの
----------------------------------------
[ ] 実際のブラウザでフルフローの確認 (Chrome / Safari / Firefox)
[ ] 実際の音声入力での STT 精度
    -> 本タスク対象外: アジェンダで「音声認識精度そのものの品質保証」は外されている
[ ] Ollama の応答品質 (フィードバックの有用性)
    -> 本タスク対象外: 品質保証は含まれない
[ ] パフォーマンス (応答時間, ストレージ容量)
[ ] 複数同時接続テスト
[ ] docker-compose の再現性 (他環境での動作)
[ ] ブラウザ対応一覧の確認 (Safari, Chrome, Firefox, Edge)

========================================
確認実施日: YYYY-MM-DD
確認者:
========================================
"""

print(CHECKLIST)
