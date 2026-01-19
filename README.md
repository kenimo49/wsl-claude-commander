# WSL Claude Commander

WSL2上のClaudeを音声入出力とマルチウィンドウで操作するツール

## 機能

- **音声入力**: 指定したマイクから音声認識でClaudeにテキスト入力
- **音声出力**: Claudeの出力を指定したスピーカーで読み上げ
- **マルチウィンドウ**: WSLウィンドウを複数起動し、指定ディスプレイに8分割表示

## プロジェクト構造

このリポジトリはモノレポ構成で、複数のアプリケーションを管理しています。

```
wsl-claude-commander/
├── apps/                     # アプリケーション
│   ├── voice-input/          # 音声入力アプリ（準備中）
│   ├── voice-output/         # 音声出力アプリ（準備中）
│   └── window-manager/       # ウィンドウ管理アプリ（準備中）
├── packages/                 # 共有パッケージ
│   ├── shared/               # 共有ライブラリ（準備中）
│   └── config/               # 共通設定（準備中）
├── docs/                     # ドキュメント
│   ├── README.md             # ドキュメントインデックス
│   ├── ARCHITECTURE.md       # システムアーキテクチャ
│   ├── guide/                # 開発ガイドライン
│   ├── knowledge/            # 実践的知識
│   ├── design/               # 設計思想
│   ├── references/           # 外部仕様
│   ├── flows/                # 処理フロー
│   └── testing/              # テストガイド
├── CLAUDE.md                 # Claude Code用ガイドライン
└── README.md                 # このファイル
```

## アプリケーション一覧

| アプリ | 説明 | 状態 |
|-------|------|------|
| [voice-input](apps/voice-input/) | 音声認識でClaudeにテキスト入力 | 準備中 |
| [voice-output](apps/voice-output/) | Claudeの応答を音声で読み上げ | 準備中 |
| [window-manager](apps/window-manager/) | WSLウィンドウの配置管理 | 準備中 |

## 必要環境

- Windows 10/11
- WSL2
- Claude Code (CLI)

## インストール

```bash
git clone https://github.com/kenimo49/wsl-claude-commander.git
cd wsl-claude-commander
```

## 使い方

(準備中)

## ドキュメント

詳細なドキュメントは [docs/](docs/) を参照してください。

- [docs/README.md](docs/README.md) - ドキュメント全体のインデックス
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - システムアーキテクチャ
- [docs/guide/documentation.md](docs/guide/documentation.md) - ドキュメント作成ガイド

## 開発者向け情報

Claude Codeで開発する場合は [CLAUDE.md](CLAUDE.md) を参照してください。

## ライセンス

MIT
