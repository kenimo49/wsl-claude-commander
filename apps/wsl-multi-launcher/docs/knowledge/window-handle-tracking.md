---
title: ウィンドウハンドル追跡
category: knowledge
tags: [window-management, powershell, windows-api, handle-tracking]
related:
  - ../design/window-tracking-strategy.md
  - ../flows/launch-flow.md
---

# ウィンドウハンドル追跡

## なぜ必要か

Windows Terminalのウィンドウを配置するには、ウィンドウを一意に識別する必要がある。
当初はウィンドウタイトルで検索する方式を採用したが、以下の問題があった：

1. Windows Terminalの `--title` オプションが期待通りに動作しない
2. bashのエスケープシーケンスでタイトル設定すると、cmd.exe経由で文字化けする
3. タイトルが「Ubuntu-24.04」など、ディストリビューション名で固定される

## 内容

### ウィンドウハンドルとは

ウィンドウハンドル（HWND）は、Windowsがウィンドウを識別するための一意な整数値。
プロセスIDとは異なり、同一プロセスの複数ウィンドウも区別できる。

### 追跡方式

1. ウィンドウ起動前に既存のWindows Terminalウィンドウハンドル一覧を取得
2. ウィンドウを起動
3. 起動後にウィンドウハンドル一覧を再取得
4. 差分を計算して新しいウィンドウを特定

```rust
// 起動前のハンドル一覧
let handles_before: HashSet<i64> = get_wt_window_handles()?.into_iter().collect();

// ウィンドウ起動
launch_window(window)?;
std::thread::sleep(Duration::from_millis(1000));

// 起動後のハンドル一覧
let handles_after: HashSet<i64> = get_wt_window_handles()?.into_iter().collect();

// 新しいウィンドウを特定
let new_handles: Vec<i64> = handles_after.difference(&handles_before).copied().collect();
```

### PowerShellでのハンドル取得

Windows APIの `EnumWindows` を使用して、Windows Terminalのウィンドウを列挙：

```powershell
# CASCADIA_HOSTING_WINDOW_CLASSクラスを持つウィンドウを検索
[WindowHelper]::EnumWindows($callback, [IntPtr]::Zero)
```

## ベストプラクティス

1. **十分な待機時間**: ウィンドウ起動後、1000ms程度待機してからハンドルを取得
2. **ハンドルの即時使用**: ハンドルは時間経過で無効になる可能性があるため、取得後すぐに配置を実行
3. **エラーハンドリング**: ハンドルが見つからない場合も処理を継続

## アンチパターン

### タイトルベースの検索

```rust
// NG: タイトルが期待通りに設定されない
move_window("window-1", &rect)?;
```

### 長時間のハンドル保持

```rust
// NG: ハンドルを配列に保存して後で使用
let handles = collect_all_handles();
// ... 時間経過 ...
for handle in handles {
    move_window_by_handle(handle, &rect)?;  // 失敗する可能性
}
```

## トラブルシューティング

### ハンドルが見つからない

**原因**: ウィンドウの起動が遅い、または失敗している

**解決策**: 待機時間を増やす、またはリトライ機構を追加

### 配置が失敗する

**原因**: ハンドルが無効になっている（ウィンドウが閉じられた等）

**解決策**: 配置直前にハンドルの有効性を確認

## 関連ドキュメント

- [設計: ウィンドウ追跡戦略](../design/window-tracking-strategy.md)
- [フロー: Launch処理フロー](../flows/launch-flow.md)
