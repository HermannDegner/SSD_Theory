"""
SSD Multidimensional Pressure - 多次元意味圧モジュール
=========================================================

構造主観力学の「意味圧」を多次元的に計算し、四層構造別に集計するシステム。

核心概念:
- 意味圧は単一ではなく、複数の次元から構成される
- 各次元は特定の構造層（PHYSICAL/BASE/CORE/UPPER）に作用する
- 層ごとに集計された圧力が、その層の「未処理圧（E）」の生成源となる

理論的意義:
----------
1. 内的葛藤のモデル化
   - BASE圧高（危険） × UPPER圧高（理念） → 「逃げるべきか、理念を貫くか」
   - 層間の葛藤を定量化可能

2. 層別反応ロジック
   - BASE層圧力 → 本能的・衝動的跳躍
   - CORE層圧力 → 規範的・効率的整合
   - UPPER層圧力 → 理念的・自己犠牲的跳躍

3. 動かしにくさの再現
   - R値階層（PHYSICAL > BASE > CORE > UPPER）に基づく支配構造

原典理論:
https://github.com/HermannDegner/Structural-Subjectivity-Dynamics
→ 意味圧とは？.md
"""

import numpy as np
from typing import Dict, Callable, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 人間モジュールからHumanLayerをインポート
try:
    from ssd_human_module import HumanLayer
except ImportError:
    # スタンドアロン使用時のフォールバック
    class HumanLayer(Enum):
        PHYSICAL = 0
        BASE = 1
        CORE = 2
        UPPER = 3


@dataclass
class PressureDimension:
    """
    意味圧の1つの次元
    
    各次元は:
    - 特定の構造層に作用する
    - 独自の計算ロジックを持つ
    - 重み付けされて集計される
    """
    name: str                           # 次元名（例: "rank_pressure"）
    weight: float                       # 影響度の重み
    calculator: Callable                # 圧力計算関数
    layer: HumanLayer                   # 作用する構造層
    enabled: bool = True                # 有効/無効フラグ
    description: str = ""               # 次元の説明
    history: List[float] = field(default_factory=list)  # 計算履歴


class MultiDimensionalPressure:
    """
    多次元意味圧計算システム
    
    使用例:
    -------
    ```python
    pressure_system = MultiDimensionalPressure()
    
    # 次元登録
    pressure_system.register_dimension(
        name="rank_pressure",
        calculator=lambda ctx: (ctx['total'] - ctx['rank']) / ctx['total'],
        layer=HumanLayer.CORE,
        weight=1.5,
        description="順位による圧力"
    )
    
    # 計算
    context = {'rank': 5, 'total': 10}
    pressures = pressure_system.calculate(context)
    # → {HumanLayer.CORE: 0.5, HumanLayer.BASE: 0.0, ...}
    ```
    """
    
    def __init__(self):
        self.dimensions: Dict[str, PressureDimension] = {}
        self.total_pressure_history: List[float] = []
        self.layer_pressure_history: Dict[HumanLayer, List[float]] = {
            layer: [] for layer in HumanLayer
        }
        
    def register_dimension(
        self, 
        name: str, 
        calculator: Callable[[dict], float],
        layer: HumanLayer,
        weight: float = 1.0,
        description: str = "",
        enabled: bool = True
    ) -> None:
        """
        新しい圧力次元を登録
        
        Args:
            name: 次元の一意な名前
            calculator: context辞書を受け取り、圧力値[0,1]を返す関数
            layer: この圧力が作用する構造層
            weight: 重み（影響度）
            description: 次元の説明文
            enabled: 有効/無効フラグ
        """
        dimension = PressureDimension(
            name=name,
            weight=weight,
            calculator=calculator,
            layer=layer,
            enabled=enabled,
            description=description
        )
        self.dimensions[name] = dimension
        
    def remove_dimension(self, name: str) -> None:
        """圧力次元を削除"""
        if name in self.dimensions:
            del self.dimensions[name]
    
    def set_weight(self, name: str, weight: float) -> None:
        """次元の重みを変更"""
        if name in self.dimensions:
            self.dimensions[name].weight = weight
    
    def enable_dimension(self, name: str, enabled: bool = True) -> None:
        """次元の有効/無効を切り替え"""
        if name in self.dimensions:
            self.dimensions[name].enabled = enabled
    
    def calculate(self, context: dict) -> Dict[HumanLayer, float]:
        """
        多次元意味圧を四層構造別に集計して計算
        
        Args:
            context: 計算に必要なコンテキスト情報の辞書
        
        Returns:
            各層ごとに重み付け平均された圧力値の辞書
            例: {HumanLayer.BASE: 0.8, HumanLayer.CORE: 0.3, ...}
        """
        # 各層ごとに圧力の合計と重みの合計を格納
        layer_pressures: Dict[HumanLayer, float] = {layer: 0.0 for layer in HumanLayer}
        layer_weights: Dict[HumanLayer, float] = {layer: 0.0 for layer in HumanLayer}
        
        for name, dim in self.dimensions.items():
            if not dim.enabled:
                continue
                
            try:
                # 各次元の圧力を計算
                pressure_value = dim.calculator(context)
                
                # 履歴に記録
                dim.history.append(pressure_value)
                
                # 該当する層に、重み付けされた圧力と重みを加算
                layer_pressures[dim.layer] += dim.weight * pressure_value
                layer_weights[dim.layer] += dim.weight
                
            except Exception as e:
                print(f"Warning: Failed to calculate pressure for {name}: {e}")
                continue
        
        # 各層の最終的な圧力（重み付き平均）を計算
        final_pressures: Dict[HumanLayer, float] = {}
        for layer in HumanLayer:
            total_w = layer_weights[layer]
            if total_w > 0:
                final_pressures[layer] = layer_pressures[layer] / total_w
            else:
                final_pressures[layer] = 0.0
        
        # 層ごとの履歴に記録
        for layer in HumanLayer:
            self.layer_pressure_history[layer].append(final_pressures[layer])
        
        # 総合圧（参考値）
        total_pressure_all = sum(final_pressures.values())
        self.total_pressure_history.append(total_pressure_all)
        
        return final_pressures
    
    def get_dimension_info(self) -> Dict[str, dict]:
        """全次元の情報を取得"""
        info = {}
        for name, dim in self.dimensions.items():
            info[name] = {
                'weight': dim.weight,
                'layer': dim.layer.name,
                'enabled': dim.enabled,
                'description': dim.description,
                'last_value': dim.history[-1] if dim.history else None,
                'history_length': len(dim.history)
            }
        return info
    
    def get_statistics(self) -> dict:
        """統計情報を取得（層別統計を含む）"""
        layer_stats = {}
        for layer in HumanLayer:
            dims_in_layer = [d for d in self.dimensions.values() if d.layer == layer and d.enabled]
            layer_stats[layer.name] = {
                'num_dimensions': len(dims_in_layer),
                'total_weight': sum(d.weight for d in dims_in_layer),
                'last_pressure': self.layer_pressure_history[layer][-1] if self.layer_pressure_history[layer] else None
            }
        
        return {
            'num_dimensions': len(self.dimensions),
            'num_enabled': sum(1 for d in self.dimensions.values() if d.enabled),
            'total_weight': sum(d.weight for d in self.dimensions.values() if d.enabled),
            'dimension_names': list(self.dimensions.keys()),
            'last_total_pressure': self.total_pressure_history[-1] if self.total_pressure_history else None,
            'layer_stats': layer_stats
        }
    
    def get_layer_conflict_index(self) -> Dict[str, float]:
        """
        層間葛藤指数を計算
        
        理論的意義:
        - BASE層とUPPER層の圧力が同時に高い場合、強い内的葛藤
        - 例: BASE高（危険）× UPPER高（理念）→「逃げるか、理念を貫くか」
        
        Returns:
            各層ペアの葛藤指数
            例: {'BASE-UPPER': 0.64, 'BASE-CORE': 0.48, ...}
        """
        if not self.layer_pressure_history[HumanLayer.BASE]:
            return {}
        
        # 最新の各層圧力を取得
        current_pressures = {
            layer: self.layer_pressure_history[layer][-1] 
            for layer in HumanLayer
        }
        
        conflicts = {}
        
        # BASE-UPPER葛藤（本能 vs 理念）
        conflicts['BASE-UPPER'] = current_pressures[HumanLayer.BASE] * current_pressures[HumanLayer.UPPER]
        
        # BASE-CORE葛藤（本能 vs 規範）
        conflicts['BASE-CORE'] = current_pressures[HumanLayer.BASE] * current_pressures[HumanLayer.CORE]
        
        # CORE-UPPER葛藤（規範 vs 理念）
        conflicts['CORE-UPPER'] = current_pressures[HumanLayer.CORE] * current_pressures[HumanLayer.UPPER]
        
        # PHYSICAL圧が高い場合は全ての葛藤が無意味（物理制約が支配的）
        physical_suppression = 1.0 - current_pressures[HumanLayer.PHYSICAL]
        conflicts = {k: v * physical_suppression for k, v in conflicts.items()}
        
        return conflicts
    
    def get_dominant_layer(self) -> Tuple[HumanLayer, float]:
        """
        現在最も圧力が高い層を返す
        
        Returns:
            (layer, pressure): 最高圧力の層とその値
        """
        if not self.layer_pressure_history[HumanLayer.BASE]:
            return (HumanLayer.BASE, 0.0)
        
        current_pressures = {
            layer: self.layer_pressure_history[layer][-1] 
            for layer in HumanLayer
        }
        
        dominant_layer = max(current_pressures.items(), key=lambda x: x[1])
        return dominant_layer
    
    def should_trigger_leap(self, threshold: float = 0.7) -> Optional[HumanLayer]:
        """
        跳躍（Leap）をトリガーすべき層を判定
        
        理論的意義:
        - 各層には「動かしにくさ」(R値)がある
        - 複数層が閾値を超えた場合、R値が最大の層が支配的
        
        Args:
            threshold: 跳躍トリガーの閾値（デフォルト0.7）
        
        Returns:
            跳躍すべき層（複数超過時はR値最大の層）
        """
        if not self.layer_pressure_history[HumanLayer.BASE]:
            return None
        
        current_pressures = {
            layer: self.layer_pressure_history[layer][-1] 
            for layer in HumanLayer
        }
        
        # R値の定義（動かしにくさ）
        R_values = {
            HumanLayer.PHYSICAL: 1000.0,
            HumanLayer.BASE: 100.0,
            HumanLayer.CORE: 10.0,
            HumanLayer.UPPER: 1.0
        }
        
        # 閾値を超えた層を抽出
        triggered_layers = [
            layer for layer, pressure in current_pressures.items() 
            if pressure > threshold
        ]
        
        if not triggered_layers:
            return None
        
        # 最もR値が高い層を返す（最も強い跳躍）
        dominant_layer = max(triggered_layers, key=lambda l: R_values[l])
        return dominant_layer
    
    def to_human_pressure(self):
        """
        HumanPressure形式に変換
        
        Returns:
            HumanPressure インスタンス（ssd_human_module使用時）
        """
        try:
            from ssd_human_module import HumanPressure
            
            if not self.layer_pressure_history[HumanLayer.BASE]:
                return HumanPressure()
            
            current_pressures = {
                layer: self.layer_pressure_history[layer][-1] 
                for layer in HumanLayer
            }
            
            return HumanPressure(
                physical=current_pressures[HumanLayer.PHYSICAL],
                base=current_pressures[HumanLayer.BASE],
                core=current_pressures[HumanLayer.CORE],
                upper=current_pressures[HumanLayer.UPPER]
            )
        except ImportError:
            raise RuntimeError("ssd_human_module not available")


# ============================================================================
# プリセット圧力計算関数
# ============================================================================

def rank_pressure_calculator(context: dict) -> float:
    """
    順位圧力の計算（CORE層に作用）
    
    Context Keys:
    - rank: int - 現在の順位（1が最高）
    - total_players: int - 総プレイヤー数
    """
    rank = context.get('rank', 1)
    total = context.get('total_players', 1)
    return (total - rank) / total


def score_pressure_calculator(context: dict) -> float:
    """
    スコア差圧力の計算（CORE層に作用）
    
    Context Keys:
    - score: float - 現在のスコア
    - target_score: float - 目標スコア
    - threshold: float - 正規化用閾値
    """
    score = context.get('score', 0.0)
    target = context.get('target_score', 100.0)
    threshold = context.get('threshold', 100.0)
    
    gap = max(0, target - score)
    return min(1.0, gap / threshold)


def time_pressure_calculator(context: dict) -> float:
    """
    時間圧力の計算（UPPER層に作用）
    
    Context Keys:
    - elapsed: float - 経過時間
    - total: float - 総時間
    """
    elapsed = context.get('elapsed', 0.0)
    total = context.get('total', 1.0)
    return elapsed / total


def survival_pressure_calculator(context: dict) -> float:
    """
    生存圧力の計算（BASE層に作用）
    
    Context Keys:
    - hp: float - 現在HP
    - max_hp: float - 最大HP
    """
    hp = context.get('hp', 100.0)
    max_hp = context.get('max_hp', 100.0)
    return 1.0 - (hp / max_hp)


def resource_pressure_calculator(context: dict) -> float:
    """
    リソース圧力の計算（CORE層に作用）
    
    Context Keys:
    - resource: float - 現在のリソース量
    - required: float - 必要なリソース量
    """
    resource = context.get('resource', 0.0)
    required = context.get('required', 1.0)
    return max(0.0, min(1.0, (required - resource) / required))


def social_pressure_calculator(context: dict) -> float:
    """
    社会的圧力の計算（CORE層に作用）
    
    Context Keys:
    - suspicion: float - 疑惑レベル [0, 1]
    - votes: int - 投票された数
    - total_votes: int - 総投票数
    """
    suspicion = context.get('suspicion', 0.0)
    votes = context.get('votes', 0)
    total_votes = context.get('total_votes', 1)
    
    vote_pressure = votes / total_votes if total_votes > 0 else 0.0
    return (suspicion + vote_pressure) / 2.0


def physical_fatigue_calculator(context: dict) -> float:
    """
    物理的疲労の計算（PHYSICAL層に作用）
    
    Context Keys:
    - fatigue: float - 疲労度 [0, 1]
    - damage: float - ダメージ [0, 1]
    """
    fatigue = context.get('fatigue', 0.0)
    damage = context.get('damage', 0.0)
    return max(fatigue, damage)


def ideological_pressure_calculator(context: dict) -> float:
    """
    イデオロギー圧力の計算（UPPER層に作用）
    
    Context Keys:
    - belief_conflict: float - 信念の衝突度 [0, 1]
    - moral_dilemma: float - 道徳的ジレンマ [0, 1]
    """
    conflict = context.get('belief_conflict', 0.0)
    dilemma = context.get('moral_dilemma', 0.0)
    return (conflict + dilemma) / 2.0
