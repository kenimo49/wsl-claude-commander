# wsl-multi-launcher

WSL (Ubuntu 24.04) を指定して、特定のディスプレイに複数のウィンドウをグリッド配置するツール。

## 機能

- 指定したWSLディストリビューションでWindows Terminalを起動
- 特定のディスプレイを指定して配置
- グリッド分割（2x4, 3x3など）で自動配置
- 各ウィンドウで異なるコマンド・作業ディレクトリを指定可能

## クイックスタート

```bash
# 1. ビルド
cargo build --release

# 2. 設定ファイルを生成
cargo run -- init --grid 2x4 --windows 8

# 3. ディスプレイを確認
cargo run -- displays

# 4. 設定を編集（必要に応じて）
vim config.yaml

# 5. 起動！
cargo run -- launch
```

## インストール

### 必要環境

- WSL2 (Ubuntu 24.04 推奨)
- Windows Terminal
- Rust 1.70+

### ビルド

```bash
cd apps/wsl-multi-launcher
cargo build --release
```

バイナリは `target/release/wsl-multi-launcher` に生成されます。

## 使い方

### コマンド一覧

| コマンド | 説明 |
|---------|------|
| `init` | 設定ファイルを生成 |
| `status` | システム状態を表示（WSL、ディスプレイ、設定） |
| `displays` | 利用可能なディスプレイを表示 |
| `validate` | 設定ファイルを検証 |
| `launch` | ウィンドウを起動して配置 |
| `arrange` | 既存ウィンドウを再配置 |

### 設定ファイルの生成

```bash
# デフォルト（2x2グリッド、4ウィンドウ）
wsl-multi-launcher init

# カスタム設定
wsl-multi-launcher init --grid 2x4 --windows 8 --display 1

# 既存ファイルを上書き
wsl-multi-launcher init --force
```

### ディスプレイの確認

```bash
wsl-multi-launcher displays
```

出力例：
```
Found 2 display(s):

  Display 0
    Device:       \\.\DISPLAY1
    Resolution:   1920x1080
    Position:     (1920, 0)
    Working Area: 1920x1032 at (1920, 0)

  Display 1 (Primary)
    Device:       \\.\DISPLAY2
    Resolution:   1920x1080
    Position:     (0, 0)
    Working Area: 1920x1032 at (0, 0)
```

### ウィンドウの起動

```bash
# 設定ファイルを読み込んで起動
wsl-multi-launcher launch

# 配置をスキップ（起動のみ）
wsl-multi-launcher launch --no-arrange

# 別の設定ファイルを使用
wsl-multi-launcher -c my-config.yaml launch
```

### ウィンドウの再配置

```bash
# 既存ウィンドウを設定に従って再配置
wsl-multi-launcher arrange
```

## 設定ファイル

### 基本構造

```yaml
# WSLディストリビューション名
wsl_distribution: Ubuntu-24.04

# ターゲットディスプレイ（0=プライマリ）
target_display: 0

# レイアウト設定
layout:
  grid: "2x4"  # 2列4行 = 8ウィンドウ

# ウィンドウ設定
windows:
  - name: "claude-1"
    command: "claude"
    working_dir: "~/workspace/project1"
```

### ウィンドウ設定オプション

| フィールド | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| `name` | ○ | - | ウィンドウの識別名 |
| `command` | - | `bash` | 実行するコマンド |
| `working_dir` | - | - | 作業ディレクトリ（`~`対応） |

### グリッドレイアウト

グリッドは `列x行` の形式で指定します：

| グリッド | ウィンドウ数 | 配置 |
|---------|------------|------|
| `2x2` | 4 | □□ / □□ |
| `2x4` | 8 | □□ / □□ / □□ / □□ |
| `3x3` | 9 | □□□ / □□□ / □□□ |
| `4x2` | 8 | □□□□ / □□□□ |

ウィンドウは左上から右下へ順番に配置されます。

## アーキテクチャ

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

## トラブルシューティング

### ウィンドウが配置されない

ウィンドウの `name` がWindows Terminalのタイトルと一致している必要があります。
`arrange` コマンドで再配置を試してください。

### ディスプレイが見つからない

`displays` コマンドで利用可能なディスプレイを確認し、
`target_display` の値を適切なインデックスに設定してください。

### WSLディストリビューションが見つからない

`status` コマンドで利用可能なディストリビューションを確認し、
`wsl_distribution` の値を正しい名前に設定してください。

```bash
# WSLディストリビューション一覧
wsl -l -v
```

## 開発

### ビルド

```bash
cargo build
```

### テスト

```bash
cargo test
```

### リリースビルド

```bash
cargo build --release
```

## ライセンス

MIT

## 関連ドキュメント

- [ROADMAP.md](./ROADMAP.md) - 開発ロードマップ
