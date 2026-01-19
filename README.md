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
│   ├── wsl-multi-launcher/   # WSLマルチウィンドウランチャー ✅
│   ├── voice-input/          # 音声入力アプリ（準備中）
│   └── voice-output/         # 音声出力アプリ（準備中）
├── packages/                 # 共有パッケージ
│   └── (準備中)
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
| [wsl-multi-launcher](apps/wsl-multi-launcher/) | WSLウィンドウを複数起動しグリッド配置 | ✅ 完成 |
| voice-input | 音声認識でClaudeにテキスト入力 | 準備中 |
| voice-output | Claudeの応答を音声で読み上げ | 準備中 |

---

## wsl-multi-launcher

WSL (Ubuntu 24.04) を指定して、特定のディスプレイに複数のウィンドウをグリッド配置するCLIツール。

### 主な機能

- 指定したWSLディストリビューションでWindows Terminalを起動
- 特定のディスプレイを指定して配置
- グリッド分割（2x4, 3x3など）で自動配置
- 各ウィンドウで異なるコマンド・作業ディレクトリを指定可能

### クイックスタート

```bash
cd apps/wsl-multi-launcher

# ビルド
cargo build --release

# 設定ファイルを生成（2x4グリッド、8ウィンドウ）
cargo run -- init --grid 2x4 --windows 8

# ディスプレイを確認
cargo run -- displays

# 起動
cargo run -- launch
```

### アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│                    WSL (Ubuntu 24.04)               │
│  ┌───────────────────────────────────────────────┐  │
│  │           wsl-multi-launcher (Rust)           │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────────┐  │  │
│  │  │ config  │ │   wsl   │ │     layout      │  │  │
│  │  │ (YAML)  │ │ launcher│ │ (grid calc)     │  │  │
│  │  └─────────┘ └─────────┘ └─────────────────┘  │  │
│  └───────────────────┬───────────────────────────┘  │
│                      │ PowerShell呼び出し            │
└──────────────────────┼──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│                    Windows Host                      │
│  ┌───────────────────────────────────────────────┐  │
│  │              PowerShell Scripts               │  │
│  │  ┌─────────────────┐ ┌─────────────────────┐  │  │
│  │  │  get-displays   │ │    move-window      │  │  │
│  │  └─────────────────┘ └─────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                   │
│  │ WSL │ │ WSL │ │ WSL │ │ WSL │  ← Windows Terminal │
│  │ Win │ │ Win │ │ Win │ │ Win │                     │
│  └─────┘ └─────┘ └─────┘ └─────┘                   │
└─────────────────────────────────────────────────────┘
```

### 設定例

```yaml
wsl_distribution: Ubuntu-24.04
target_display: 1
layout:
  grid: "2x4"
windows:
  - name: "claude-1"
    command: "claude"
    working_dir: "~/workspace/project1"
  - name: "claude-2"
    command: "claude"
    working_dir: "~/workspace/project2"
  # ... 最大8ウィンドウ
```

詳細は [apps/wsl-multi-launcher/README.md](apps/wsl-multi-launcher/README.md) を参照してください。

---

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
