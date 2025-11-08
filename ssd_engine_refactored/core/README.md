# SSD Theory - Core Modules

SSD理論の基本構成要素

## 📦 モジュール一覧

### **ssd_core_engine.py** (11.0KB)
SSDエンジンの中核

**主要クラス:**
- `SSDAgent` - 基本エージェント
- `SSDState` - 内部状態管理

**機能:**
- E（未処理圧）の管理
- κ（慣性）の成長
- β（減衰）の適用
- 状態更新ループ

### **ssd_human_module.py** (15.1KB)
人間心理の三層モデル

**主要クラス:**
- `HumanAgent` - 人間エージェント
- `HumanLayer` - 三層構造（BASE/CORE/UPPER）
- `HumanPressure` - 層別圧力

**機能:**
- 三層構造の実装
- 層間相互作用
- 意味圧の処理
- 行動決定メカニズム

### **ssd_pressure_system.py** (16.3KB)
意味圧システム

**主要クラス:**
- `PressureType` - 圧力の種類
- `PressureSource` - 圧力の源泉

**機能:**
- 圧力の生成
- 圧力の伝播
- 圧力の合成
- 時間的減衰

### **ssd_nonlinear_transfer.py** (12.9KB)
非線形伝達関数

**主要クラス:**
- `TransferFunction` - 伝達関数
- `TransferType` - 関数の種類

**機能:**
- E → action の変換
- 非線形性の実装
- パラメータ調整
- 飽和特性

## 🧠 理論的基盤

### SSD理論の核心

**E/κダイナミクス:**
```
dE/dt = -β·E + Input
dκ/dt = f(E, κ)
action = g(E - κ)
```

**三層構造:**
- **BASE**: 本能的・生存的価値
- **CORE**: 中核的・自我的価値
- **UPPER**: 戦略的・理性的価値

## 📚 使用例

### 基本的な使用

```python
from ssd_engine_refactored.core import HumanAgent, HumanPressure

# エージェント作成
agent = HumanAgent()

# 圧力設定
pressure = HumanPressure()
pressure.base = 10.0
pressure.core = 5.0
pressure.upper = 3.0

# 状態更新
agent.step(pressure)

# 行動取得
action = agent.get_action()
```

### ゲームAIへの適用

```python
# 状況を意味圧に変換
def situation_to_pressure(game_state):
    pressure = HumanPressure()
    
    # HP低下 → 生存圧（BASE）
    if hp == 1:
        pressure.base = 400.0
    
    # 勝利可能性 → 勝利欲（CORE）
    if can_win:
        pressure.core = 200.0
    
    # 戦略的判断 → 分析圧（UPPER）
    pressure.upper = analyze_situation()
    
    return pressure

# E/κから行動が創発
agent.step(situation_to_pressure(state))
action = agent.get_action()
```

## 🔑 設計原則

### κ初期値の設計

**本能的価値（高κ）:**
- 死の恐怖: κ_BASE = 10-15
- 生存本能: κ_BASE = 8-12

**後天的価値（低κ）:**
- 勝利欲求: κ_CORE = 0.3-0.9
- 戦略思考: κ_UPPER = 0.4-0.8

### 創発的行動

外部ロジックを避け、E/κバランスから行動を創発させる：

**❌ 悪い例:**
```python
if危険:
    return 安全行動  # 外部制御
```

**✅ 良い例:**
```python
pressure.base = 危険度 × 100
agent.step(pressure)
return agent.get_action()  # 創発
```

## 🔗 依存関係

```
ssd_core_engine.py
    ↓
ssd_human_module.py (extends SSDAgent)
    ↓
ssd_pressure_system.py (defines HumanPressure)
    ↓
ssd_nonlinear_transfer.py (converts E to action)
```

## 📖 関連ドキュメント

- `../examples/demos/` - 基本デモ集
- `../examples/README.md` - 応用例
- `../docs/` - 理論的提案書

---

*Note: これらは全SSD実装の基礎となる必須モジュールです*
