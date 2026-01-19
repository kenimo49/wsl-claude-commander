---
title: Knowledge
category: index
tags: [knowledge, implementation, best-practices]
---

# Knowledge

実装時の注意点、ベストプラクティス、トラブルシューティング。

## ドキュメント一覧

| ドキュメント | 説明 | 優先度 |
|-------------|------|--------|
| [window-handle-tracking.md](./window-handle-tracking.md) | ウィンドウハンドル追跡の実装ノウハウ | ⭐⭐⭐ |

## このディレクトリの目的

- 実装時に「知らないとハマる」情報を蓄積
- ベストプラクティスとアンチパターンを文書化
- トラブルシューティングガイドを提供

## ドキュメント追加時のテンプレート

```markdown
---
title: [タイトル]
category: knowledge
tags: [tag1, tag2, tag3]
related:
  - ../design/related-doc.md
---

# タイトル

## なぜ必要か
## 内容
## ベストプラクティス
## アンチパターン
## トラブルシューティング
```

## 関連ドキュメント

- [../flows/](../flows/) - 処理フロー
- [../design/](../design/) - 設計ドキュメント
