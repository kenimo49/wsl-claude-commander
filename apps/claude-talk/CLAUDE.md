# CLAUDE.md

このファイルはClaude Codeがclaude-talkアプリで作業する際のガイドラインです。

## 概要

claude-talkは、Claude Codeとの双方向音声インターフェースアプリケーションです。
- 音声入力（STT）: "Hey Claude" で起動し、音声で指示
- 音声読み上げ（TTS）: Claudeの回答を読み上げ

## ディレクトリ構造

```
apps/claude-talk/
├── src/claude_talk/
│   ├── cli.py           # CLIエントリポイント
│   ├── config.py        # 設定読み込み・検証
│   ├── daemon.py        # デーモン管理
│   ├── audio/           # 音声入出力
│   ├── stt/             # Speech-to-Text
│   ├── tts/             # Text-to-Speech
│   ├── hotword/         # ホットワード検出
│   ├── claude/          # Claude連携
│   └── windows/         # Windows操作
├── scripts/             # PowerShellスクリプト
└── tests/               # テスト
```

## 技術スタック

- **言語**: Python 3.10+
- **CLI**: click
- **設定**: pydantic + PyYAML
- **STT**: Vosk (無料) / OpenAI Whisper API (有料)
- **TTS**: edge-tts
- **ホットワード**: OpenWakeWord
- **ロギング**: structlog

## コーディングガイドライン

1. **型ヒント**: すべての関数に型ヒントを付ける
2. **docstring**: Google styleでdocstringを書く
3. **エラーハンドリング**: 適切な例外を使用し、ユーザーフレンドリーなメッセージを提供
4. **ロギング**: structlogを使用

## 開発コマンド

```bash
# インストール
pip install -e ".[dev]"

# テスト
pytest

# Lint
ruff check src/
ruff format src/

# 型チェック
mypy src/
```

## 関連ドキュメント

- [README.md](README.md) - プロジェクト概要
- [config.example.yaml](config.example.yaml) - 設定例
