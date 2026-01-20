# ホットワード検出の設定

claude-talkでは、ホットワード（ウェイクワード）を検出して音声入力を開始します。

## 利用可能なエンジン

### 1. Simple（デフォルト）

音声エネルギーベースの簡易検出。APIキー不要で動作しますが、特定のフレーズではなく「音声があるか」を検出します。

```yaml
hotword:
  engine: "simple"
  threshold: 0.5
```

**メリット**:
- APIキー不要
- すぐに使える

**デメリット**:
- 特定のフレーズを検出できない
- ノイズで誤検出する可能性

### 2. Porcupine（推奨）

Picovoiceの高精度ホットワード検出エンジン。無料で個人利用可能。

```yaml
hotword:
  engine: "porcupine"
  word: "hey google"
  threshold: 0.5
  access_key: "${PICOVOICE_ACCESS_KEY}"
```

**メリット**:
- 高精度なホットワード検出
- 複数のビルトインキーワード
- オフラインで動作

**デメリット**:
- APIキー（無料）の取得が必要
- カスタムキーワードは有料

## Porcupineのセットアップ

### 1. APIキーの取得

1. [Picovoice Console](https://console.picovoice.ai/) にアクセス
2. アカウントを作成（無料）
3. 「AccessKey」をコピー

### 2. 環境変数の設定

```bash
# ~/.bashrcに追加
export PICOVOICE_ACCESS_KEY="your-access-key-here"
source ~/.bashrc
```

または、config.yamlに直接設定:

```yaml
hotword:
  engine: "porcupine"
  access_key: "your-access-key-here"
```

### 3. 利用可能なキーワード

Porcupineのビルトインキーワード（無料）:

| キーワード | 説明 |
|-----------|------|
| `alexa` | "Alexa" |
| `hey google` | "Hey Google" |
| `hey siri` | "Hey Siri" |
| `ok google` | "OK Google" |
| `picovoice` | "Picovoice" |
| `computer` | "Computer" |
| `jarvis` | "Jarvis" |
| `bumblebee` | "Bumblebee" |

```yaml
# 例: "Hey Google"で起動
hotword:
  engine: "porcupine"
  word: "hey google"
```

### 4. 動作確認

```bash
# 設定を確認
claude-talk config

# デーモンを起動してテスト
claude-talk start --foreground
```

## カスタムキーワード

カスタムキーワード（例: "Hey Claude"）を使用するには、Picovoice Consoleで有料プランが必要です。

1. [Picovoice Console](https://console.picovoice.ai/) にログイン
2. 「Porcupine」→「Create Keyword」
3. キーワードを入力して生成
4. 生成された.ppnファイルをダウンロード
5. config.yamlで設定

```yaml
hotword:
  engine: "porcupine"
  word: "path/to/hey_claude.ppn"  # カスタムモデルファイル
```

## トラブルシューティング

### 「Access key not provided」エラー

**原因**: PICOVOICE_ACCESS_KEYが設定されていない

**解決策**:
```bash
export PICOVOICE_ACCESS_KEY="your-key"
```

### 「Keyword not available」警告

**原因**: 指定したキーワードがビルトインリストにない

**解決策**: ビルトインキーワードを使用するか、カスタムキーワードを作成

### 検出感度が低い/高い

**解決策**: thresholdを調整
- 低い値（0.3）: 感度が高い、誤検出が増える
- 高い値（0.7）: 感度が低い、検出漏れが増える

```yaml
hotword:
  threshold: 0.4  # デフォルトは0.5
```

## 参考リンク

- [Picovoice Console](https://console.picovoice.ai/)
- [Porcupine Documentation](https://picovoice.ai/docs/porcupine/)
- [pvporcupine PyPI](https://pypi.org/project/pvporcupine/)
