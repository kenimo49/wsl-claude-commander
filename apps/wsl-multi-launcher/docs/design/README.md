---
title: Design
category: index
tags: [design, architecture, decisions]
---

# Design

設計判断、アーキテクチャ、トレードオフの記録。

## ドキュメント一覧

| ドキュメント | 説明 | 優先度 |
|-------------|------|--------|
| [window-tracking-strategy.md](./window-tracking-strategy.md) | ウィンドウ追跡戦略の設計判断 | ⭐⭐⭐ |

### 今後追加予定

- `architecture.md` - 全体アーキテクチャ
- `hybrid-approach.md` - WSL+PowerShellハイブリッド設計

## このディレクトリの目的

- システムの設計判断と「なぜそう設計したか」を説明
- アーキテクチャの背景を記録
- トレードオフと代替案を文書化

## ドキュメント追加時のテンプレート

```markdown
---
title: [タイトル]
category: design
tags: [tag1, tag2, tag3]
related:
  - ../references/related-spec.md
---

# タイトル

## 設計の背景
## アーキテクチャ概要
## 設計判断
## トレードオフ
## 代替案
```

## 関連ドキュメント

- [../flows/](../flows/) - 処理フロー
- [../references/](../references/) - 外部仕様
