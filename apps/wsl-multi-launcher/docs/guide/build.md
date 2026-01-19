---
title: ビルドガイド
category: guide
tags: [build, cargo, test, release]
related:
  - ./setup.md
  - ./configuration.md
---

# ビルドガイド

wsl-multi-launcherのビルド、テスト、リリースビルドの手順。

## 前提条件

[環境構築ガイド](./setup.md)が完了していること。

## ビルド

### 開発ビルド

```bash
cd apps/wsl-multi-launcher
cargo build
```

**出力先**: `target/debug/wsl-multi-launcher`

### リリースビルド

```bash
cargo build --release
```

**出力先**: `target/release/wsl-multi-launcher`

リリースビルドは最適化が有効になり、実行速度が向上します。

## テスト

### 全テスト実行

```bash
cargo test
```

**期待される出力**:
```
running 17 tests
test config::tests::test_parse_grid ... ok
test config::tests::test_parse_grid_invalid ... ok
test config::tests::test_parse_yaml_config ... ok
...
test result: ok. 17 passed; 0 failed; 0 ignored
```

### 特定のテストを実行

```bash
# モジュール単位
cargo test config::tests

# テスト名でフィルタ
cargo test test_parse_grid
```

### テスト出力を表示

```bash
cargo test -- --nocapture
```

## CLIコマンド

### ヘルプ表示

```bash
cargo run -- --help
```

### 利用可能なコマンド

| コマンド | 説明 | 例 |
|---------|------|-----|
| `init` | 設定ファイル生成 | `cargo run -- init` |
| `status` | システム状態表示 | `cargo run -- status` |
| `displays` | ディスプレイ一覧 | `cargo run -- displays` |
| `validate` | 設定ファイル検証 | `cargo run -- validate` |
| `launch` | ウィンドウ起動 | `cargo run -- launch` |
| `arrange` | ウィンドウ再配置 | `cargo run -- arrange` |

### コマンド例

```bash
# 設定ファイルを生成（2x4グリッド、8ウィンドウ）
cargo run -- init --grid 2x4 --windows 8

# ディスプレイを確認
cargo run -- displays

# 設定を検証
cargo run -- validate

# ウィンドウを起動
cargo run -- launch

# 別の設定ファイルを使用
cargo run -- -c my-config.yaml launch
```

## 依存関係

### Cargo.tomlの依存関係

| クレート | バージョン | 用途 |
|---------|-----------|------|
| clap | 4.x | CLI引数解析 |
| serde | 1.x | シリアライズ/デシリアライズ |
| serde_yaml | 0.9.x | YAML解析 |
| serde_json | 1.x | JSON解析（PowerShell連携） |
| anyhow | 1.x | エラーハンドリング |
| thiserror | 2.x | カスタムエラー定義 |
| tracing | 0.1.x | ログ出力 |
| tracing-subscriber | 0.3.x | ログ設定 |

### 依存関係の更新

```bash
cargo update
```

## ビルドエラーのトラブルシューティング

### コンパイルエラー

```
error[E0433]: failed to resolve: use of undeclared crate or module
```

**解決策**:
```bash
cargo clean
cargo build
```

### 依存関係エラー

```
error: failed to select a version for the requirement
```

**解決策**:
```bash
rm Cargo.lock
cargo build
```

### リンクエラー

```
error: linker `cc` not found
```

**解決策**:
```bash
sudo apt update && sudo apt install -y build-essential
```

## パフォーマンス

### ビルド時間の目安

| ビルド | 初回 | 増分 |
|--------|------|------|
| Debug | ~30秒 | ~5秒 |
| Release | ~60秒 | ~10秒 |

### キャッシュのクリア

```bash
cargo clean
```

## CI/CD

### 推奨するCIステップ

```yaml
# .github/workflows/ci.yml の例
- name: Build
  run: cargo build --release

- name: Test
  run: cargo test

- name: Clippy
  run: cargo clippy -- -D warnings

- name: Format check
  run: cargo fmt -- --check
```

## 次のステップ

ビルドが完了したら、[設定ガイド](./configuration.md)で設定ファイルをカスタマイズしてください。

## 関連ドキュメント

- [環境構築ガイド](./setup.md) - 開発環境のセットアップ
- [設定ガイド](./configuration.md) - 設定ファイルの書き方
