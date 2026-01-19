---
title: 設定ガイド
category: guide
tags: [configuration, yaml, grid, layout, windows]
related:
  - ./setup.md
  - ./build.md
  - ../flows/launch-flow.md
---

# 設定ガイド

wsl-multi-launcherの設定ファイル（config.yaml）の書き方。

## 設定ファイルの場所

デフォルトの設定ファイルは `config.yaml` です。

```bash
# カレントディレクトリの config.yaml を使用
cargo run -- launch

# 別のファイルを指定
cargo run -- -c my-config.yaml launch
```

## 設定ファイルの生成

### initコマンドで生成

```bash
# デフォルト設定（2x2グリッド、4ウィンドウ）
cargo run -- init

# カスタム設定
cargo run -- init --grid 2x4 --windows 8 --display 1

# 既存ファイルを上書き
cargo run -- init --force
```

### 手動で作成

`config.example.yaml` をコピーして編集:

```bash
cp config.example.yaml config.yaml
vim config.yaml
```

## 設定ファイルの構造

```yaml
# WSLディストリビューション名
wsl_distribution: Ubuntu-24.04

# ターゲットディスプレイ（0=プライマリ）
target_display: 1

# レイアウト設定
layout:
  grid: "2x4"

# ウィンドウ設定
windows:
  - name: "claude-1"
    command: "claude"
    working_dir: "~/workspace/project1"
```

## 設定項目の詳細

### wsl_distribution

**必須**: はい

WSLディストリビューション名を指定します。

```yaml
wsl_distribution: Ubuntu-24.04
```

利用可能なディストリビューションを確認:

```bash
wsl -l -v
```

### target_display

**必須**: いいえ（デフォルト: 0）

ウィンドウを配置するディスプレイのインデックス。

| 値 | 説明 |
|----|------|
| 0 | プライマリディスプレイ |
| 1 | セカンダリディスプレイ |
| 2+ | 3台目以降のディスプレイ |

```yaml
target_display: 1
```

利用可能なディスプレイを確認:

```bash
cargo run -- displays
```

### layout.grid

**必須**: はい

グリッドの形式を `列x行` で指定します。

```yaml
layout:
  grid: "2x4"  # 2列4行 = 8ウィンドウ
```

**よく使うグリッド**:

| グリッド | ウィンドウ数 | レイアウト |
|---------|------------|----------|
| `1x1` | 1 | フルスクリーン |
| `2x2` | 4 | 4分割 |
| `2x4` | 8 | 縦長8分割 |
| `3x3` | 9 | 9分割 |
| `4x2` | 8 | 横長8分割 |

### windows

**必須**: はい（最低1つ）

起動するウィンドウの設定リスト。

```yaml
windows:
  - name: "claude-1"
    command: "claude"
    working_dir: "~/workspace/project1"

  - name: "shell"
    command: "bash"
```

#### name

**必須**: はい

ウィンドウの識別名。重複不可。

```yaml
name: "claude-1"
```

#### command

**必須**: いいえ（デフォルト: `bash`）

ウィンドウで実行するコマンド。

```yaml
command: "claude"
command: "htop"
command: "tail -f /var/log/syslog"
```

#### working_dir

**必須**: いいえ

作業ディレクトリ。`~` はホームディレクトリに展開されます。

```yaml
working_dir: "~/workspace/project1"
working_dir: "/tmp"
```

## 設定例

### 開発用（Claude 4ウィンドウ）

```yaml
wsl_distribution: Ubuntu-24.04
target_display: 1
layout:
  grid: "2x2"
windows:
  - name: "claude-1"
    command: "claude"
    working_dir: "~/workspace/frontend"
  - name: "claude-2"
    command: "claude"
    working_dir: "~/workspace/backend"
  - name: "claude-3"
    command: "claude"
    working_dir: "~/workspace/infra"
  - name: "claude-4"
    command: "claude"
    working_dir: "~/workspace/docs"
```

### モニタリング用

```yaml
wsl_distribution: Ubuntu-24.04
target_display: 0
layout:
  grid: "2x2"
windows:
  - name: "htop"
    command: "htop"
  - name: "logs"
    command: "tail -f /var/log/syslog"
  - name: "docker"
    command: "docker stats"
  - name: "shell"
    command: "bash"
    working_dir: "~"
```

### 混合用（8ウィンドウ）

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
  - name: "claude-3"
    command: "claude"
    working_dir: "~/workspace/project3"
  - name: "claude-4"
    command: "claude"
    working_dir: "~/workspace/project4"
  - name: "shell-1"
    command: "bash"
    working_dir: "~"
  - name: "shell-2"
    command: "bash"
    working_dir: "~"
  - name: "htop"
    command: "htop"
  - name: "logs"
    command: "tail -f /var/log/syslog"
```

## バリデーション

### 設定ファイルの検証

```bash
cargo run -- validate
```

**チェック項目**:
- YAML構文
- 必須フィールドの存在
- グリッド形式（`列x行`）
- ウィンドウ数がグリッドに収まるか
- ウィンドウ名の重複

### エラー例と対処

#### グリッド形式エラー

```
Error: Invalid grid format: abc. Expected format: 'COLSxROWS' (e.g., '2x4')
```

**対処**: `grid` を `2x4` のような形式に修正

#### ウィンドウ数超過

```
Error: Too many windows configured: 10 windows for 2x4 grid (max: 8)
```

**対処**: ウィンドウ数を減らすか、グリッドを大きくする

#### 重複名

```
Error: Duplicate window name: claude-1
```

**対処**: ウィンドウ名をユニークにする

## ウィンドウ配置順序

ウィンドウは設定ファイルの順番で、左上から右下へ配置されます。

**2x4グリッドの場合**:

```
┌─────────┬─────────┐
│ window1 │ window2 │
├─────────┼─────────┤
│ window3 │ window4 │
├─────────┼─────────┤
│ window5 │ window6 │
├─────────┼─────────┤
│ window7 │ window8 │
└─────────┴─────────┘
```

## 関連ドキュメント

- [環境構築ガイド](./setup.md) - 開発環境のセットアップ
- [ビルドガイド](./build.md) - ビルドとテスト実行
