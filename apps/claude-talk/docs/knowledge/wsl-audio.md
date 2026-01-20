# WSL2での音声入出力設定

Windows 11のWSLgを使用して、WSL2から音声入出力を行います。

## WSLg（推奨）

Windows 11ではWSLgがPulseAudioサーバーを自動で提供するため、**追加設定は基本的に不要**です。

### 動作確認

```bash
# PulseAudioサーバーへの接続確認
pactl info

# 期待される出力例:
# Server Name: PulseAudio (on PipeWire 0.3.xx)
```

### 必要なパッケージ

```bash
sudo apt-get update
sudo apt-get install -y pulseaudio-utils libportaudio2 portaudio19-dev libasound2-plugins ffmpeg
```

### ALSA→PulseAudioブリッジ設定

PortAudioがPulseAudioを認識するために、`~/.asoundrc`を作成：

```bash
cat > ~/.asoundrc << 'EOF'
pcm.!default {
    type pulse
}
ctl.!default {
    type pulse
}
EOF
```

### 音声デバイスの確認

```bash
# 利用可能なソース（マイク）を確認
pactl list sources short

# 利用可能なシンク（スピーカー）を確認
pactl list sinks short
```

### claude-talkの動作確認

```bash
cd ~/workspace/wsl-claude-commander/apps/claude-talk
source .venv/bin/activate

# デバイス一覧
claude-talk devices

# TTSテスト（音声出力）
claude-talk test-tts "こんにちは、テストです"

# STTテスト（音声入力）
claude-talk test-stt --duration 5
```

## WSLgのデバイス制限

### 制限事項

WSLgは個別のオーディオデバイス（Bluetoothマイク等）を直接公開しません。
WSL2から見えるのは以下の仮想デバイスのみです：

| デバイス | 説明 |
|----------|------|
| RDPSource | Windowsの**デフォルト**マイク |
| RDPSink | Windowsの**デフォルト**スピーカー |

```bash
# 確認コマンド
pactl list sources short
# 出力例:
# 1  RDPSink.monitor  module-rdp-sink.c    s16le 2ch 44100Hz  IDLE
# 2  RDPSource        module-rdp-source.c  s16le 1ch 44100Hz  SUSPENDED
```

### 特定のマイク（Bluetooth等）を使いたい場合

**方法1: Windowsでデフォルトを変更（推奨）**

Windows側で使いたいマイクをデフォルトに設定すれば、WSLgは自動的にそれを使います。

```
Windows設定 → システム → サウンド → 入力 → 使いたいマイクを選択
```

**方法2: PowerShellで切り替え**

AudioDeviceCmdletsモジュールを使って切り替えスクリプトを作成できます：

```powershell
# モジュールのインストール（管理者権限で1回だけ）
Install-Module -Name AudioDeviceCmdlets

# デバイス一覧
Get-AudioDevice -List

# デフォルトマイクを変更
Set-AudioDevice -ID "{デバイスID}"
```

**方法3: PulseAudioサーバー方式（上級者向け）**

WSLgの代わりにWindows上でPulseAudioサーバーを動かせば、個別デバイスを公開できます。
ただし設定が複雑になるため、通常は方法1で十分です。

## トラブルシューティング

### Windowsでマイクを変更したのに反映されない

**原因**: WSLgはWindowsのオーディオ設定をWSL起動時に読み込むため、起動後の変更は反映されません。

**解決策**: WSLを完全に再起動する

```powershell
# PowerShellで実行（全WSLウィンドウが閉じます）
wsl --shutdown
```

その後、WSLを再度開いてください。

**注意**:
- 新しいWSLターミナルを開くだけでは不十分です（同じインスタンスを共有するため）
- `wsl --shutdown` は全WSLウィンドウを閉じるので、作業中のものは保存してください

### Windowsの「既定のデバイス」が2種類ある

Windowsには2種類のデフォルト設定があります：

| 種類 | 用途 |
|------|------|
| 既定のデバイス | 一般的な録音/再生 |
| 既定の通信デバイス | 通話アプリ等 |

**WSLgは「既定のデバイス」を使用します。**

設定方法：
```
コントロールパネル → サウンド → 録音タブ
→ 使いたいマイクを右クリック
→ 「既定のデバイスとして設定」を選択
```

### 「Connection refused」エラー

**原因**: WSLgのPulseAudioサーバーに接続できない

**解決策**:
```bash
# WSLを再起動
wsl --shutdown
# その後、WSLを再度開く
```

### 「PortAudio library not found」エラー

**原因**: libportaudio2がインストールされていない

**解決策**:
```bash
sudo apt-get install -y libportaudio2 portaudio19-dev
```

### 音が出ない/録音できない

**確認事項**:
1. Windowsの音声設定でマイク/スピーカーが有効か確認
2. WSLgが有効か確認:
   ```bash
   # /mnt/wslg が存在するか確認
   ls /mnt/wslg
   ```

### WSLgが無効の場合

WSLgを有効にする:
```powershell
# PowerShell（管理者）で実行
wsl --update
wsl --shutdown
```

`.wslconfig` で無効化されていないか確認（`C:\Users\<username>\.wslconfig`）:
```ini
[wsl2]
guiApplications=true  # falseになっていたらtrueに変更
```

## 参考リンク

- [WSLg GitHub](https://github.com/microsoft/wslg)
- [Microsoft WSL Documentation](https://docs.microsoft.com/en-us/windows/wsl/)
