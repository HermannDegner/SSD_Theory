# Phase 10.2.2: 圧力システム統合の設計

## 目的
v10.1の構造化記憶解釈を、SSDの主観的圧力システムと完全統合する。

## 現在の問題点（v10.1）

```python
# v10.1: 構造化記憶の解釈結果を直接使用
pressure_interpretation = self.structured_memory.interpret_with_structure(
    signal=target_signals,
    kappa=kappa,
    use_concepts=True
)

# 疑惑レベル = BASE層圧力（直接計算）
suspicion = pressure_interpretation[1]  # BASE層
suspicion += 0.3 * pressure_interpretation[2]  # CORE層
```

**問題**: 
- 構造化記憶の出力を直接使用
- SSDの圧力システム（`ssd_pressure_system.py`、`ssd_subjective_social_pressure.py`）を迂回
- 主観的解釈の多様性が表現できない

## 改善方針（v10.2: Phase 10.2.2）

### アーキテクチャ

```
観測シグナル
  ↓
構造化記憶（概念マッチング）
  ↓
意味圧（MultiDimensionalPressure）← NEW!
  ↓
主観的圧力システム（SubjectiveSocialPressure）← NEW!
  ↓
HumanAgent.step()（E蓄積）
  ↓
疑惑レベル（E_BASEを参照）
```

### 実装ステップ

#### 1. 概念から意味圧への変換

```python
class PlayerV10Full:
    def observe_player(self, target_id, target_signals, current_time):
        # 1. 構造化記憶で概念マッチング
        pressure_interpretation = self.structured_memory.interpret_with_structure(
            signal=target_signals,
            kappa=self.agent.state.kappa,
            use_concepts=True
        )
        
        # 2. 概念解釈を意味圧に変換 ← NEW!
        meaning_pressure = self._interpretation_to_pressure(
            pressure_interpretation,
            target_signals
        )
        
        # 3. 主観的圧力システムで処理 ← NEW!
        subjective_pressure = self.subjective_pressure_system.process(
            meaning_pressure,
            observer_state=self.agent.state,
            context={'target_id': target_id}
        )
        
        # 4. HumanAgentに圧力を入力
        self.agent.step(subjective_pressure, dt=0.1)
        
        # 5. 疑惑レベルはE_BASEから取得
        suspicion = self.agent.state.E[HumanLayer.BASE.value]
        
        return suspicion
```

#### 2. 意味圧変換ロジック

```python
def _interpretation_to_pressure(
    self,
    pressure_interpretation: np.ndarray,
    target_signals: np.ndarray
) -> HumanPressure:
    """
    構造化記憶の解釈結果を意味圧に変換
    
    Args:
        pressure_interpretation: [4] 層別圧力
        target_signals: [7] 観測されたシグナル
    
    Returns:
        HumanPressure: 四層への意味圧
    """
    # BASE層の圧力 = 生存脅威
    # aggressive, defensive シグナルが高い → 脅威
    threat_level = pressure_interpretation[1]
    
    # CORE層の圧力 = 規範的違和感
    # cooperative が低い、norm_violation が高い → 違和感
    normative_conflict = pressure_interpretation[2]
    
    # UPPER層の圧力 = 理念的不一致
    # ideological シグナルとの齟齬
    ideological_dissonance = pressure_interpretation[3]
    
    return HumanPressure(
        physical=0.0,  # 観測では物理圧力なし
        base=threat_level,
        core=normative_conflict,
        upper=ideological_dissonance
    )
```

#### 3. 主観的圧力システムの活用

```python
from ssd_subjective_social_pressure import SubjectiveSocialPressure

class PlayerV10Full:
    def __init__(self, ...):
        # ...
        
        # 主観的圧力システム ← NEW!
        self.subjective_pressure_system = SubjectiveSocialPressure(
            agent_state=self.agent.state
        )
```

**利点**:
- エージェントごとに異なる主観的解釈
- κに基づく解釈の変化
- 過去の経験（E履歴）が解釈に影響

## 期待される効果

### 1. 主観的多様性の表現

```python
# 同じシグナルでも、エージェントの状態で解釈が変わる

# Player A（過去に攻撃された経験あり、E_BASE高い）
# → 攻撃的シグナルに過敏に反応
suspicion_A = 0.9

# Player B（平和な経験のみ、E_BASE低い）
# → 同じシグナルを軽微と解釈
suspicion_B = 0.3
```

### 2. 理論的完全性

```
✅ 構造化記憶（v10の利点）
✅ SSDコア力学（E/κ）
✅ 主観的圧力システム ← NEW!
✅ 創発的シグナル
✅ 正確な因果学習

→ SSD理論の完全実装
```

### 3. 説明可能性の向上

```python
def explain_suspicion(self, target_id):
    # v10.1
    "疑惑 0.75: 'dangerous_aggressive_BASE' (E_BASE=0.00)"
    
    # v10.2（Phase 10.2.2）
    "疑惑 0.75: 'dangerous_aggressive_BASE' 概念活性 → " \
    "意味圧(BASE=0.6) → 主観的解釈(+0.15) → E_BASE=0.75蓄積"
    
    # 主観的解釈の内訳も説明可能！
```

## 実装の優先順位

### Phase 10.2.2a（最小実装）
- `_interpretation_to_pressure()` メソッド
- `HumanPressure` による `agent.step()` 呼び出し
- 疑惑レベルを `E_BASE` から取得

### Phase 10.2.2b（完全実装）
- `SubjectiveSocialPressure` の統合
- エージェント間の主観的差異の表現
- 圧力の時系列追跡

### Phase 10.2.2c（高度化）
- 圧力の可視化
- 主観的解釈の学習（κによる変化）
- 集団的圧力の創発

## コード例（Phase 10.2.2a）

```python
class PlayerV10PressureIntegrated(PlayerV10Simplified):
    """
    v10.2: 圧力システム統合版
    """
    
    def observe_player(self, target_id, target_signals, current_time):
        # 1. 構造化記憶で解釈
        pressure_interpretation = self.structured_memory.interpret_with_structure(
            signal=target_signals,
            kappa=self.agent.state.kappa,
            use_concepts=True
        )
        
        # 2. 意味圧に変換 ← NEW!
        meaning_pressure = HumanPressure(
            physical=0.0,
            base=pressure_interpretation[1],      # BASE層
            core=pressure_interpretation[2],      # CORE層
            upper=pressure_interpretation[3]      # UPPER層
        )
        
        # 3. HumanAgentに圧力を入力 ← CHANGED!
        self.agent.step(meaning_pressure, dt=0.1)
        
        # 4. 疑惑レベルはE_BASEから ← CHANGED!
        suspicion = self.agent.state.E[HumanLayer.BASE.value]
        
        # 観測履歴に記録
        if target_id not in self.observation_history:
            self.observation_history[target_id] = []
        self.observation_history[target_id].append(target_signals.copy())
        
        # 説明用に記録（意味圧も含める）
        activated_concepts = [
            c for c in self.learned_concepts
            if c.matches(target_signals)
        ]
        
        self.last_decision_explanation[target_id] = {
            'suspicion': suspicion,
            'E_state': self.agent.state.E.copy(),
            'meaning_pressure': meaning_pressure,  # ← NEW!
            'primary_concept': activated_concepts[0].name if activated_concepts else None
        }
        
        return suspicion
    
    def explain_suspicion(self, target_id):
        """説明可能性（圧力情報も含む）"""
        if target_id not in self.last_decision_explanation:
            return "観測データなし"
        
        info = self.last_decision_explanation[target_id]
        suspicion = info['suspicion']
        primary_concept = info['primary_concept']
        E = info['E_state']
        pressure = info['meaning_pressure']
        
        if primary_concept:
            explanation = f"疑惑 {suspicion:.2f}: '{primary_concept}' → " \
                         f"意味圧(BASE={pressure.base:.2f}, CORE={pressure.core:.2f}) → " \
                         f"E_BASE={E[1]:.2f}"
        else:
            explanation = f"疑惑 {suspicion:.2f}: 新規パターン → " \
                         f"意味圧(BASE={pressure.base:.2f}) → E_BASE={E[1]:.2f}"
        
        return explanation
```

## 次のステップ

1. **Phase 10.2.2a実装**: 最小限の圧力システム統合
2. **検証**: v10.1と比較して主観的多様性が表現されるか
3. **Phase 10.2.2b**: `SubjectiveSocialPressure` の完全統合
4. **Phase 10.3**: Nano最適化（並列化）
5. **Phase 10.4**: 可視化（圧力の流れ、概念ネットワーク）

---

**作成日**: 2025年11月7日  
**Phase**: 10.2.2 設計  
**目的**: SSD理論の完全統合
