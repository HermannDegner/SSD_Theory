# SSD Theory Demos - 基本デモ集

SSD理論の各要素を個別に実証するデモプログラム集

## ファイル一覧

### 基礎デモ

#### **demo_basic_engine.py** (2.8KB)
SSDエンジンの基本動作

- 最もシンプルな実装例
- E/κの基本的な振る舞い
- 入門用デモ

**学習内容:** SSDエンジンの最小構成

#### **demo_human_psychology.py** (4.1KB)
HumanAgentの心理モデル

- 三層構造（BASE/CORE/UPPER）
- 層間の相互作用
- 行動決定メカニズム

**学習内容:** 人間心理の多層的モデリング

### 圧力システム

#### **demo_pressure_system.py** (9.2KB)
意味圧システムの詳細

- 圧力の生成と伝播
- 層別の圧力処理
- 圧力の減衰と蓄積

**学習内容:** HumanPressureの動作原理

#### **demo_nonlinear_transfer.py** (8.3KB)
非線形伝達関数

- 伝達関数の種類
- パラメータの影響
- 非線形性の効果

**学習内容:** 圧力→行動の変換メカニズム

### 社会相互作用

#### **demo_social_dynamics.py** (5.0KB)
社会的力学の基礎

- エージェント間相互作用
- 集団行動の創発
- 社会的圧力の伝播

**学習内容:** マルチエージェント系の基本

#### **demo_subjective_social_pressure.py** (9.1KB)
主観的社会圧モデル

- 個人視点の社会認識
- 他者からの圧力の主観的評価
- 社会的文脈の影響

**学習内容:** 主観性の実装方法

#### **demo_subjective_society.py** (7.4KB)
主観的社会システム

- 社会全体の主観的構築
- 複数視点の統合
- 集合的主観の創発

**学習内容:** 社会システムのSSD的記述

## 推奨学習順序

1. **demo_basic_engine.py** - まずはここから
2. **demo_human_psychology.py** - 人間モデルの理解
3. **demo_pressure_system.py** - 圧力システムの詳細
4. **demo_nonlinear_transfer.py** - 変換メカニズム
5. **demo_social_dynamics.py** - 社会相互作用の基礎
6. **demo_subjective_social_pressure.py** - 主観的圧力
7. **demo_subjective_society.py** - 統合システム

## クイックスタート

```powershell
# 基本エンジンデモ
python demo_basic_engine.py

# 人間心理デモ
python demo_human_psychology.py

# 圧力システムデモ
python demo_pressure_system.py
```

## 各デモの主要概念

### E/κダイナミクス
- **E（未処理圧）**: 状況的・一時的な圧力
- **κ（慣性）**: 確立された価値・抵抗
- **β（減衰）**: 圧力の自然減衰

### 三層構造
- **BASE**: 本能的・生存的価値
- **CORE**: 中核的・自我的価値
- **UPPER**: 戦略的・理性的価値

### 創発原理
外部制御なしで行動が内部力学から創発

## 理論学習リソース

各デモにはコメントで理論的背景を記載:

- SSD理論の基本原理
- 実装上の設計判断
- パラメータの意味
- 期待される動作

## 応用例へ

基本理解後は以下の応用実装へ:

- **../apex_survivor_ssd_pure_v3.py** - ゲームAI
- **../werewolf/** - 社会的推論
- **../newtons_cradle/** - 物理シミュレーション
- **../*_ssd_pure.py** - 各種ゲーム実装

---

*Note: これらは教育・実証用の簡略化された実装です*
