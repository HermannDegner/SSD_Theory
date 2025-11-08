# SSD Engine Refactored - 構造的再設計

## 📁 ディレクトリ構成

```
ssd_engine_refactored/
├── README.md                    # このファイル
├── ssd_core_engine.py          # 汎用計算エンジン（ドメイン非依存）
├── ssd_human_module.py         # 人間モジュール（四層構造特化）
├── ssd_social_dynamics.py      # 社会的相互作用
├── ssd_pressure_system.py      # 多次元意味圧システム
└── examples/
    ├── demo_basic_engine.py       # エンジン基本デモ
    ├── demo_human_psychology.py   # 人間心理デモ
    ├── demo_social_dynamics.py    # 社会ダイナミクスデモ
    └── demo_pressure_system.py    # 意味圧システムデモ
```

## 🎯 設計思想

### **分離の原則**

1. **ssd_core_engine.py** - 計算エンジン
   - 意味圧 (p)、整合慣性 (κ)、未処理圧 (E)、抵抗 (R) の基本数理
   - 整合・跳躍の汎用アルゴリズム
   - レイヤー数・パラメータに依存しない設計
   - **目的**: 高速化、他ドメインへの適用可能性

2. **ssd_human_module.py** - 人間モジュール
   - 四層構造（PHYSICAL/BASE/CORE/UPPER）の定義
   - R値階層（1000/100/10/1）
   - 神経物質マッピング（Dopamine/Serotonin等）
   - 層間転送行列（8パス）
   - **目的**: 心理学的妥当性、人間行動の再現

3. **ssd_social_dynamics.py** - 社会ダイナミクス
   - エージェント間のE/κ伝播
   - 関係性マトリクス（協力/競争）
   - 集団レベルの創発現象
   - **目的**: 多エージェントシミュレーション

4. **ssd_pressure_system.py** - 多次元意味圧システム
   - 層別の圧力入力管理
   - 重み付き集約計算
   - 層間葛藤分析
   - HumanAgentとの統合ブリッジ
   - **目的**: 複雑な外部圧力のモデリング、内的葛藤の可視化

## 🔄 v5.0からの変更点

### **計算効率の向上**
- 汎用エンジン: NumPy最適化、ベクトル演算
- 人間モジュール: エンジンをラップ、心理解釈を追加

### **拡張性の向上**
- 新しいドメイン（動物、AI、組織）への適用が容易
- 層の数や特性を柔軟に変更可能
- 多次元圧力システムによる入力の柔軟な構成

### **保守性の向上**
- 各モジュールの責務が明確
- テストが容易
- ドキュメントの整理

## 🚀 使用例

### 基本エンジンのみ使用
```python
from ssd_core_engine import SSDEngine, SSDParams

# 2層システムの例
engine = SSDEngine(num_layers=2)
params = SSDParams(R_values=[100, 1])
state = engine.step(state, pressure, params, dt=0.1)
```

### 人間モジュール使用
```python
from ssd_human_module import HumanAgent, HumanParams

# 四層構造の人間エージェント
agent = HumanAgent()
agent.step(pressure_input, dt=0.1)
print(agent.get_dominant_layer())  # 最も影響力の高い層
```

### 社会シミュレーション

```python
from ssd_social_dynamics import Society

society = Society(num_agents=10)
society.step(dt=0.1)
society.visualize_network()
```

### 多次元意味圧システム

```python
from ssd_pressure_system import (
    MultiDimensionalPressure,
    rank_pressure_calculator,
    HumanLayer
)

# 圧力システム構築
pressure_system = MultiDimensionalPressure()
pressure_system.register_dimension(
    name="rank_pressure",
    calculator=rank_pressure_calculator,
    layer=HumanLayer.CORE,
    weight=1.5
)

# 圧力計算と統合
context = {'rank': 3, 'total_players': 10}
layer_pressures = pressure_system.calculate(context)
human_pressure = pressure_system.to_human_pressure()

# HumanAgentに入力
agent = HumanAgent()
agent.step(human_pressure)

# 葛藤分析
conflicts = pressure_system.get_layer_conflict_index()
print(f"BASE-UPPER葛藤: {conflicts['BASE-UPPER']:.3f}")
```

## 📚 理論的背景

原典リポジトリ: <https://github.com/HermannDegner/Structural-Subjectivity-Dynamics>

- 構造主観力学（SSD）の核心概念を実装
- 整合跳躍数理モデルに基づく
- 人間モジュールの四層構造を再現

## 🔬 Phase 1-4の統合

- **Phase 1**: PHYSICAL層の実装 → `ssd_human_module.py`
- **Phase 2**: Dynamic Theta → `ssd_core_engine.py`
- **Phase 3**: 層間転送 → `ssd_human_module.py`
- **Phase 4**: Social Coupling → `ssd_social_dynamics.py`
- **多次元意味圧**: 層別入力管理 → `ssd_pressure_system.py`

---

**開発状況**: ✅ 完成
**最終更新**: 2025年11月7日
