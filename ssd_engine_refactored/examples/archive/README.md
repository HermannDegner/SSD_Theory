# Archive - 旧バージョンファイル

このフォルダには開発過程で作成された旧バージョンのファイルを保管しています。

## アーカイブ日時
2025年11月8日

## アーカイブファイル一覧

### APEX SURVIVOR系（古いバージョン）
- **apex_survivor_ssd_pure.py** - v1（初期実装）
- **apex_survivor_ssd_pure_v2.py** - v2（構造的矛盾あり：外部ロジックがE/κをバイパス）

**⭐ 最新版:** `apex_survivor_ssd_pure_v3.py` (親フォルダ)
- 純粋E/κ創発の完成版
- 本能的死の恐怖をκ初期値に反映（BASE κ=10-15）
- 外部制限なしで安全行動が創発

### Werewolf Game系（開発バージョン）
- **werewolf_game_v8_5.py** - v8.5
- **werewolf_game_v9.py** - v9
- **werewolf_game_v10.py** - v10
- **werewolf_game_v10_integrated.py** - v10統合版
- **werewolf_game_v10_2_pressure.py** - v10.2圧力版
- **werewolf_game_v10_2_1_causal.py** - v10.2.1因果版

**⭐ 最新版:** 
- `werewolf_extended_roles.py` - 拡張役職版
- `werewolf_ultimate_demo.py` - 究極デモ版
- `werewolf_narrator.py` - ナレーター版
- `werewolf_visualizer.py` - ビジュアライザー版

### Newton's Cradle系（バリエーション）
- **newtons_cradle_full.py** - 基本版
- **newtons_cradle_direct_core.py** - ダイレクトコア版

**⭐ 最新版:**
- `newtons_cradle_nano.py` - ナノ版
- `newtons_cradle_nano_animated.py` - ナノアニメーション版
- `newtons_cradle_animated.py` - アニメーション版

### Demo/Debug系（テスト版）
- **debug_v8.py** - デバッグ用
- **demo_v8_final.py** - v8最終デモ
- **demo_v8_quick.py** - v8クイックテスト

**⭐ 現行Demo:**
- `demo_basic_engine.py` - 基本エンジン
- `demo_human_psychology.py` - 人間心理
- `demo_nonlinear_transfer.py` - 非線形伝達
- `demo_pressure_system.py` - 圧力システム
- `demo_social_dynamics.py` - 社会力学
- `demo_subjective_social_pressure.py` - 主観的社会圧
- `demo_subjective_society.py` - 主観的社会

## 重要な設計変更

### APEX SURVIVOR v2→v3の根本的改善
**問題（v2）:**
- `strategic_mult`という外部ロジックが行動を直接支配
- E/κの内部力学が機能していなかった
- HP=1時の400圧力がκ成長に吸収され、E≈0になっていた

**解決（v3）:**
1. **κの再解釈**: 死の恐怖は**本能的**（初期κ）、勝利欲求は**後天的**（初期κ低く成長）
2. **BASE κ = 10-15**: 進化的に刻まれた生存本能
3. **外部制限の完全削除**: E/κから純粋に行動が創発
4. **理論的整合性**: E（状況圧）とκ（確立された価値）の正しい区別

この変更により、**外部ロジックなし**でHP=1時に安全行動が自然に出現。

## 保管理由
- 開発履歴の記録
- 設計判断の根拠保存
- 将来の参考資料
- バックアップ

---
*Note: これらのファイルは動作確認済みですが、最新の理論改善が反映されていません。*
