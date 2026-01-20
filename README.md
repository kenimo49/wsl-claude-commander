# WSL Claude Commander

WSL2上のClaudeを音声入出力とマルチウィンドウで操作するツール

## 機能

- **音声インターフェース**: "Hey Claude"で起動、音声入力と読み上げ
- **マルチウィンドウ**: WSLウィンドウを複数起動し、グリッド配置

## プロジェクト構造

このリポジトリはモノレポ構成で、複数のアプリケーションを管理しています。

```
wsl-claude-commander/
├── apps/                     # アプリケーション
│   ├── wsl-multi-launcher/   # WSLマルチウィンドウランチャー ✅
│   └── claude-talk/          # 音声インターフェース ✅
├── packages/                 # 共有パッケージ（準備中）
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
| [claude-talk](apps/claude-talk/) | Claude Codeとの双方向音声インターフェース | ✅ 完成 |

---

## wsl-multi-launcher

WSLウィンドウを複数起動し、グリッド配置するCLIツール。

### クイックスタート

```bash
cd apps/wsl-multi-launcher
cargo build --release
cargo run -- init --grid 2x4 --windows 8
cargo run -- launch
```

詳細は [apps/wsl-multi-launcher/README.md](apps/wsl-multi-launcher/README.md) を参照。

---

## claude-talk

Claude Codeとの双方向音声インターフェース。

### クイックスタート

```bash
cd apps/claude-talk
pip install -e .
claude-talk init
claude-talk start
```

詳細は [apps/claude-talk/README.md](apps/claude-talk/README.md) を参照。

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
