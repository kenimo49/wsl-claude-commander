# CLAUDE.md

このファイルはClaude Codeがwsl-multi-launcherで作業する際のガイドラインです。

## 言語設定

- **回答**: 日本語で返答すること
- **コード内コメント**: 英語のまま
- **技術用語**: 英語のまま（無理に翻訳しない）

## プロジェクト概要

WSL (Ubuntu 24.04) を指定して、特定のディスプレイに複数のウィンドウをグリッド配置するツール。

### 主な機能

- 指定したWSLディストリビューションでWindows Terminalを起動
- 特定のディスプレイを指定して配置
- グリッド分割（2x4, 3x3など）で自動配置
- 各ウィンドウで異なるコマンド・作業ディレクトリを指定可能

## ソースコード構造

```
src/
├── main.rs       # CLIエントリーポイント（clap）
├── config.rs     # YAML設定ファイルの読み込み・検証
├── wsl.rs        # WSLディストリビューション操作
├── layout.rs     # グリッドレイアウト計算
└── windows.rs    # ウィンドウ配置（PowerShell連携）
```

### モジュール責務

| モジュール | 責務 |
|-----------|------|
| `main.rs` | CLI引数パース、サブコマンド実行 |
| `config.rs` | 設定ファイルの読み書き、バリデーション |
| `wsl.rs` | WSLディストリビューション一覧取得、起動 |
| `layout.rs` | グリッド座標計算、ウィンドウサイズ算出 |
| `windows.rs` | ディスプレイ取得、ウィンドウ移動 |

## 開発コマンド

```bash
# ビルド
cargo build

# リリースビルド
cargo build --release

# テスト
cargo test

# 実行
cargo run -- <command>

# 例: ディスプレイ確認
cargo run -- displays

# 例: 設定生成
cargo run -- init --grid 2x4 --windows 8
```

## ドキュメント構成

```
docs/
├── README.md           # ドキュメントインデックス
├── guide/              # セットアップ・ビルド・設定ガイド
├── knowledge/          # 実践的知識
├── flows/              # 処理フロー
├── design/             # 設計思想
└── references/         # 外部仕様
```

## コーディングガイドライン

### Rust スタイル

- `cargo fmt` でフォーマット
- `cargo clippy` で静的解析
- エラーハンドリングは `anyhow::Result` を使用
- カスタムエラーは `thiserror` で定義

### 依存クレート

| クレート | 用途 |
|---------|------|
| `clap` | CLI引数パース |
| `serde` / `serde_yaml` | YAML設定ファイル |
| `anyhow` / `thiserror` | エラーハンドリング |
| `tracing` | ロギング |

## 関連ドキュメント

- [README.md](./README.md) - プロジェクト概要・使い方
- [ROADMAP.md](./ROADMAP.md) - 開発ロードマップ
- [docs/README.md](./docs/README.md) - ドキュメントインデックス
