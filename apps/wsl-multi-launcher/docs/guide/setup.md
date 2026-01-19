---
title: 環境構築ガイド
category: guide
tags: [setup, environment, wsl, rust, windows-terminal]
related:
  - ./build.md
  - ./configuration.md
---

# 環境構築ガイド

wsl-multi-launcherの開発・実行に必要な環境を構築する手順。

## 前提条件

| 項目 | 要件 |
|------|------|
| OS | Windows 10/11 + WSL2 |
| WSL | Ubuntu 24.04 推奨 |
| ターミナル | Windows Terminal |

## 必要なツール

### 1. WSL2のセットアップ

WSL2がインストールされていない場合:

```powershell
# PowerShell（管理者権限）で実行
wsl --install -d Ubuntu-24.04
```

インストール済みのディストリビューションを確認:

```bash
wsl -l -v
```

出力例:
```
  NAME            STATE           VERSION
* Ubuntu-24.04    Running         2
```

### 2. Windows Terminalのインストール

Microsoft Storeからインストール、または:

```powershell
winget install Microsoft.WindowsTerminal
```

### 3. Rustのインストール（WSL内）

WSL内でRustをインストール:

```bash
# rustupをインストール
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# デフォルト設定でインストール
# プロンプトで 1) Proceed with standard installation を選択

# パスを反映
source $HOME/.cargo/env

# バージョン確認
rustc --version
cargo --version
```

**期待される出力**:
```
rustc 1.XX.0 (XXXXXXXX YYYY-MM-DD)
cargo 1.XX.0 (XXXXXXXX YYYY-MM-DD)
```

## ディレクトリ構造

```
apps/wsl-multi-launcher/
├── Cargo.toml          # Rustプロジェクト設定
├── Cargo.lock          # 依存関係ロックファイル
├── src/
│   ├── main.rs         # エントリーポイント
│   ├── config.rs       # 設定管理
│   ├── wsl.rs          # WSL起動
│   ├── layout.rs       # グリッドレイアウト計算
│   └── windows.rs      # Windows操作（PowerShell連携）
├── scripts/
│   ├── get-displays.ps1    # ディスプレイ情報取得
│   └── move-window.ps1     # ウィンドウ移動
├── config.example.yaml # 設定ファイルサンプル
└── docs/               # ドキュメント
```

## 環境変数

特別な環境変数の設定は不要です。

## トラブルシューティング

### WSLが見つからない

```
エラー: wsl.exe: command not found
```

**原因**: WSLがインストールされていない、またはパスが通っていない

**解決策**:
1. WindowsでWSLをインストール
2. WSLを再起動

### Rustがインストールできない

```
エラー: curl: command not found
```

**解決策**:
```bash
sudo apt update && sudo apt install -y curl
```

### Windows Terminalが起動しない

```
エラー: 'wt.exe' is not recognized
```

**原因**: Windows Terminalがインストールされていない

**解決策**: Microsoft StoreからWindows Terminalをインストール

## 確認チェックリスト

- [ ] WSL2が動作している（`wsl -l -v`で確認）
- [ ] Ubuntu 24.04がインストールされている
- [ ] Windows Terminalがインストールされている
- [ ] Rustがインストールされている（`rustc --version`で確認）
- [ ] プロジェクトディレクトリにアクセスできる

## 次のステップ

環境構築が完了したら、[ビルドガイド](./build.md)に進んでください。

## 関連ドキュメント

- [ビルドガイド](./build.md) - ビルドとテスト実行
- [設定ガイド](./configuration.md) - 設定ファイルの書き方
