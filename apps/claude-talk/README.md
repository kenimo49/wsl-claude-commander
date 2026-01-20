# claude-talk

Claude Codeとの双方向音声インターフェース。音声でClaudeに指示を送り、Claudeの回答を読み上げます。

## 機能

- **音声入力（STT）**: "Hey Claude" で起動し、音声でClaudeに指示
- **音声読み上げ（TTS）**: Claudeの回答を自動で読み上げ
- **2つの読み上げモード**:
  - `full`: 全文読み上げ（デフォルト）
  - `notify`: 状態通知のみ（長い出力時向け）

## インストール

```bash
cd apps/claude-talk
pip install -e .
```

### WSL2での音声入力設定

WSL2では音声入力にPulseAudioの設定が必要です。詳細は [docs/knowledge/wsl-audio.md](docs/knowledge/wsl-audio.md) を参照。

## 使い方

### 初期設定

```bash
# 設定ファイルを初期化
claude-talk init

# 音声デバイスを確認
claude-talk devices
```

### デーモン起動

```bash
# バックグラウンドで起動
claude-talk start

# 状態確認
claude-talk status

# 停止
claude-talk stop
```

### テスト

```bash
# 音声認識テスト
claude-talk test-stt --duration 10

# 読み上げテスト
claude-talk test-tts "こんにちは、テストです"

# 通知モードテスト
claude-talk test-tts --mode notify --type completed
```

## 設定

`config.yaml` で設定を変更できます。

### 認識モード

```yaml
stt:
  mode: "free"  # "free" (Vosk) or "paid" (OpenAI Whisper)
```

### 読み上げモード

```yaml
tts:
  mode: "full"   # "full" or "notify"
  voice: "ja-JP-NanamiNeural"
```

### デバイス指定

```yaml
audio:
  input_device: 0   # マイク番号
  output_device: 1  # スピーカー番号
```

## ライセンス

MIT
