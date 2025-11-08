# Archive - 開発履歴ドキュメント

このフォルダには開発過程で作成された設計書・結果報告を保管しています。

## アーカイブ日時
2025年11月8日

## ファイル一覧

### **ARCHITECTURE.md** (13.1KB)
Phase 2時点のアーキテクチャ設計書

- システム全体構成
- モジュール間依存関係
- 初期設計思想

**状態:** Phase 2完了時点、現在は core/ と extensions/ に実装済み

### **COMPLETION_SUMMARY.md** (8.9KB)
Phase完了時のサマリー

- 各Phaseの達成内容
- 実装済み機能一覧
- 次フェーズへの課題

**状態:** Phase 8時点、現在はv1.0.0として安定化

### **PHASE_10_2_2_DESIGN.md** (8.6KB)
Phase 10.2.2の詳細設計

- 記憶システムの設計
- 実装計画
- 検証項目

**状態:** 実装済み（extensions/ssd_memory_structure.py）

### **PHASE6_7_THEORETICAL_INTEGRATION.md** (12.8KB)
Phase 6-7の理論統合ドキュメント

- 非線形伝達の統合
- 圧力システムの拡張
- 理論的整合性の確認

**状態:** 実装済み（core/モジュール群）

### **V10_WEREWOLF_GAME_RESULTS.md** (13.0KB)
V10人狼ゲーム実験結果

- 実験データ
- 性能評価
- 改善点の分析

**状態:** 参考資料、現在は examples/werewolf/ に実装

### **WEREWOLF_VERSION_COMPARISON.md** (9.9KB)
人狼ゲームバージョン比較

- v8.5 vs v9 vs v10
- 各バージョンの特徴
- 性能差の分析

**状態:** 参考資料、最新版は werewolf_ultimate_demo.py

## 現在の状態

これらのドキュメントで設計された機能は、以下に実装されています：

### コア機能
- **core/** - 基本エンジン、人間モデル、圧力システム
- **extensions/** - 社会システム、記憶構造、動的解釈

### 実装例
- **examples/werewolf/** - 人狼ゲーム最新実装
- **examples/apex_survivor_ssd_pure_v3.py** - 純粋E/κ創発

## 理論的進化

### Phase 2-8の成果
初期設計 → モジュール化 → 理論統合

### V9-V10の提案
- **V9**: 動的解釈（実装済み）
- **V10**: 記憶構造（実装済み）

詳細は `../V9_*.md`, `../V10_*.md` 参照

## 使用方法

### 開発履歴の理解
```
ARCHITECTURE.md → 初期構想
PHASE6_7_THEORETICAL_INTEGRATION.md → 理論統合
COMPLETION_SUMMARY.md → 実装完了
```

### 実験結果の参照
```
V10_WEREWOLF_GAME_RESULTS.md → 性能データ
WEREWOLF_VERSION_COMPARISON.md → バージョン比較
```

## 最新ドキュメント

開発履歴ではなく、現在の使用方法は以下を参照：

- **../../README.md** - プロジェクト全体
- **../../core/README.md** - コアモジュール
- **../../extensions/README.md** - 拡張機能
- **../../examples/README.md** - 実装例

---

*Note: これらは歴史的文書です。最新情報は上記の現行ドキュメントを参照してください。*
