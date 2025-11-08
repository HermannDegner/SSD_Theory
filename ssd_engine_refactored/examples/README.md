# SSD Theory Examples - 実装例集

Structural Subjectivity Dynamics (SSD) 理論の実装例とデモプログラム

## 📁 フォルダ構成

```
examples/
├── 📄 apex_survivor_ssd_pure_v3.py    - APEX SURVIVOR完成版 ⭐
├── 📄 blackjack_ssd_pure.py           - Blackjack実装
├── 📄 roulette_ssd_pure.py            - Roulette実装
├── 📁 werewolf/                       - 人狼ゲーム各種実装
├── 📁 newtons_cradle/                 - ニュートンのゆりかご
├── 📁 demos/                          - 基本デモ集
└── 📁 archive/                        - 旧バージョン保管
```

## 🎮 ゲーム実装（ルートレベル）

### ⭐ **apex_survivor_ssd_pure_v3.py** (35.4KB)
**APEX SURVIVOR - 純粋E/κ創発の完成版**

「1位以外全員死亡」という極限状況で、外部ロジックなしに安全行動が創発する実装。

**主な特徴:**
- 本能的死の恐怖をκ初期値に反映（BASE κ=10-15）
- 外部制限なしでHP=1時に安全選択が創発
- 純粋なE/κダイナミクスの実証

**実行:**
```powershell
python apex_survivor_ssd_pure_v3.py
```

**理論的意義:**
v2からの根本的改善により、「死の恐怖は本能的（初期κ）、勝利欲求は後天的（低初期κ）」という設計原理を確立。

### **blackjack_ssd_pure.py** (27.6KB)
Blackjack（21）の実装

- ディーラー対プレイヤー
- Hit/Stand判断の創発
- 確率的思考の実装

### **roulette_ssd_pure.py** (29.4KB)
Rouletteの実装

- ベット戦略の創発
- リスク管理の学習
- 期待値判断

## 📁 専門フォルダ

### 🐺 werewolf/
人狼ゲームの各種実装（5ファイル）

- **werewolf_ultimate_demo.py** - 究極デモ版（推奨）
- werewolf_extended_roles.py - 拡張役職版
- werewolf_narrator.py - ナレーター付き
- werewolf_visualizer.py - 可視化版
- visualize_werewolf_comparison.py - 比較分析

**詳細:** `werewolf/README.md`

### ⚙️ newtons_cradle/
ニュートンのゆりかご物理シミュレーション（3ファイル）

- **newtons_cradle_nano_animated.py** - 最新版（推奨）
- newtons_cradle_nano.py - 高精度版
- newtons_cradle_animated.py - 標準版

**詳細:** `newtons_cradle/README.md`

### 📚 demos/
基本デモプログラム集（7ファイル）

- demo_basic_engine.py - エンジン基礎
- demo_human_psychology.py - 人間心理モデル
- demo_pressure_system.py - 圧力システム
- demo_nonlinear_transfer.py - 非線形伝達
- demo_social_dynamics.py - 社会力学
- demo_subjective_social_pressure.py - 主観的社会圧
- demo_subjective_society.py - 主観的社会

**詳細:** `demos/README.md`

### 🗄️ archive/
旧バージョン保管（13ファイル）

開発過程で作成されたファイルを保管。

**詳細:** `archive/README.md`

## 🚀 クイックスタート

### 初めての方
```powershell
# 基本デモから開始
cd demos
python demo_basic_engine.py
```

### ゲームAIに興味がある方
```powershell
# APEX SURVIVOR（最も完成度が高い）
python apex_survivor_ssd_pure_v3.py
```

### 社会シミュレーションに興味がある方
```powershell
# 人狼ゲーム
cd werewolf
python werewolf_ultimate_demo.py
```

### 物理シミュレーションに興味がある方
```powershell
# Newton's Cradle
cd newtons_cradle
python newtons_cradle_nano_animated.py
```

## 🧠 SSD理論の基本概念

### 三層構造
- **BASE**: 本能的・生存的価値（死の恐怖、基本的欲求）
- **CORE**: 中核的・自我的価値（勝利欲求、自己実現）
- **UPPER**: 戦略的・理性的価値（状況分析、最適化）

### E/κダイナミクス
- **E（未処理圧）**: 状況から生じる一時的な圧力
- **κ（慣性）**: 確立された価値・変化への抵抗
- **β（減衰）**: 圧力の自然減衰係数

### 創発原理
**外部ロジックなし**で、E/κの内部力学から行動が創発する。

## 📖 推奨学習パス

1. **基礎理解** → `demos/demo_basic_engine.py`
2. **人間モデル** → `demos/demo_human_psychology.py`
3. **圧力システム** → `demos/demo_pressure_system.py`
4. **簡単なゲーム** → `blackjack_ssd_pure.py`
5. **複雑なゲーム** → `apex_survivor_ssd_pure_v3.py` ⭐
6. **社会システム** → `werewolf/werewolf_ultimate_demo.py`
7. **物理適用** → `newtons_cradle/newtons_cradle_nano_animated.py`

## 🎯 各実装の特徴比較

| 実装 | 複雑度 | 創発性 | 推奨用途 |
|------|--------|--------|----------|
| APEX SURVIVOR v3 | 高 | ⭐⭐⭐ | 理論実証 |
| Werewolf | 高 | ⭐⭐⭐ | 社会AI |
| Blackjack | 中 | ⭐⭐ | 基本ゲームAI |
| Roulette | 中 | ⭐⭐ | 確率的判断 |
| Newton's Cradle | 中 | ⭐⭐ | 物理応用 |
| Demos | 低 | ⭐ | 学習・理解 |

## 💡 開発のヒント

### 新しいゲーム実装を作る場合

1. **状況を意味圧に変換** - `_calculate_pressure()`
2. **κ初期値を設計** - 本能的 vs 後天的を区別
3. **外部ロジックを排除** - E/κから創発させる
4. **デバッグ出力を充実** - E/κ/action値を表示

### 重要な設計原則

**❌ 悪い例:**
```python
if self.hp == 1:
    choice = min(choice, 5)  # 外部制限
```

**✅ 良い例:**
```python
# HP=1時の圧力を意味圧に変換
pressure.base += 400  # 死の恐怖
# κ初期値: BASE=10-15（本能的恐怖）
# → E/κバランスから安全選択が創発
```

## 📚 関連ドキュメント

- `archive/README.md` - 設計変更の履歴
- `werewolf/README.md` - 人狼ゲーム詳細
- `newtons_cradle/README.md` - 物理シミュレーション詳細
- `demos/README.md` - デモプログラム学習ガイド

## 🔬 研究用途

これらの実装は以下の研究に使用できます:

- ゲームAIの創発的行動生成
- 社会シミュレーションの主観的モデリング
- 物理システムのSSD的記述
- 意思決定の多層的モデル化

---

**Note:** すべての実装は純粋なE/κ創発原理に基づいています。外部ロジックによる行動制御は避け、内部力学から行動が自然に生まれる設計を目指しています。
