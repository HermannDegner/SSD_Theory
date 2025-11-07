"""
SSD v3.5 拡張: 多次元意味圧モジュール (Multi-Dimensional Semantic Pressure)

概念:
----
意味圧（p_external）を単一のベクトルではなく、
複数の次元（ディメンション）から構成されるものとして扱う。

各次元は独立した圧力源を表し、重み付けで統合される。

例: AIの意思決定（APEX SURVIVOR風）
- 順位圧 (Rank Pressure): 競争における順位からの圧力
- スコア圧 (Score Pressure): 目標との差からの圧力
- 時間圧 (Time Pressure): 締め切りや経過時間からの圧力
- 生存圧 (Survival Pressure): 生存状況や危機感からの圧力
- リスク圧 (Risk Pressure): リスク評価からの圧力

拡張性:
------
新しい次元を簡単に追加できる設計:
- カスタム圧力計算関数を登録
- 重みパラメータで影響度を調整
- 動的に次元を追加・削除可能
"""

import numpy as np
from typing import Dict, Callable, Optional, List
from dataclasses import dataclass, field


@dataclass
class PressureDimension:
    """意味圧の1つの次元"""
    name: str                           # 次元名
    weight: float                       # 重み（影響度）
    calculator: Callable                # 計算関数
    enabled: bool = True                # 有効/無効
    description: str = ""               # 説明
    history: List[float] = field(default_factory=list)  # 履歴


class MultiDimensionalPressure:
    """多次元意味圧計算システム"""
    
    def __init__(self):
        self.dimensions: Dict[str, PressureDimension] = {}
        self.total_pressure_history = []
        
    def register_dimension(
        self, 
        name: str, 
        calculator: Callable,
        weight: float = 1.0,
        description: str = "",
        enabled: bool = True
    ):
        """
        新しい圧力次元を登録
        
        Parameters:
        -----------
        name: str
            次元の名前
        calculator: Callable[[dict], float]
            圧力を計算する関数。contextを受け取り、圧力値を返す
        weight: float
            重み（影響度）
        description: str
            次元の説明
        enabled: bool
            有効/無効
        """
        dimension = PressureDimension(
            name=name,
            weight=weight,
            calculator=calculator,
            enabled=enabled,
            description=description
        )
        self.dimensions[name] = dimension
        
    def remove_dimension(self, name: str):
        """圧力次元を削除"""
        if name in self.dimensions:
            del self.dimensions[name]
    
    def set_weight(self, name: str, weight: float):
        """次元の重みを変更"""
        if name in self.dimensions:
            self.dimensions[name].weight = weight
    
    def enable_dimension(self, name: str, enabled: bool = True):
        """次元の有効/無効を切り替え"""
        if name in self.dimensions:
            self.dimensions[name].enabled = enabled
    
    def calculate(self, context: dict) -> np.ndarray:
        """
        多次元意味圧を計算
        
        Parameters:
        -----------
        context: dict
            計算に必要なコンテキスト情報
            
        Returns:
        --------
        pressure: np.ndarray
            3次元ベクトルとしての総合圧力
        """
        total_pressure = 0.0
        total_weight = 0.0
        
        for name, dim in self.dimensions.items():
            if not dim.enabled:
                continue
                
            try:
                # 各次元の圧力を計算
                pressure_value = dim.calculator(context)
                
                # 履歴に記録
                dim.history.append(pressure_value)
                
                # 重み付き和
                total_pressure += dim.weight * pressure_value
                total_weight += dim.weight
                
            except Exception as e:
                print(f"Warning: Failed to calculate pressure for {name}: {e}")
                continue
        
        # 正規化（重みの合計で割る）
        if total_weight > 0:
            normalized_pressure = total_pressure / total_weight
        else:
            normalized_pressure = 0.0
        
        # 履歴に記録
        self.total_pressure_history.append(normalized_pressure)
        
        # 3次元ベクトルとして返す（x成分のみに圧力、y, zは0）
        return np.array([normalized_pressure, 0.0, 0.0])
    
    def get_dimension_info(self) -> Dict[str, dict]:
        """全次元の情報を取得"""
        info = {}
        for name, dim in self.dimensions.items():
            info[name] = {
                'weight': dim.weight,
                'enabled': dim.enabled,
                'description': dim.description,
                'last_value': dim.history[-1] if dim.history else None,
                'history_length': len(dim.history)
            }
        return info
    
    def get_statistics(self) -> dict:
        """統計情報を取得"""
        return {
            'num_dimensions': len(self.dimensions),
            'num_enabled': sum(1 for d in self.dimensions.values() if d.enabled),
            'total_weight': sum(d.weight for d in self.dimensions.values() if d.enabled),
            'dimension_names': list(self.dimensions.keys()),
            'last_total_pressure': self.total_pressure_history[-1] if self.total_pressure_history else None
        }


# ========================================
# プリセット圧力計算関数
# ========================================

def rank_pressure_calculator(context: dict) -> float:
    """
    順位圧力の計算
    
    Context Keys:
    - rank: int - 現在の順位（1位が最高）
    - total_players: int - 総プレイヤー数
    """
    rank = context.get('rank', 1)
    total = context.get('total_players', 1)
    
    # 順位が低いほど圧力が高い
    return (total - rank) / total


def score_pressure_calculator(context: dict) -> float:
    """
    スコア差圧力の計算
    
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
    時間圧力の計算
    
    Context Keys:
    - elapsed: float - 経過時間
    - total: float - 総時間
    """
    elapsed = context.get('elapsed', 0.0)
    total = context.get('total', 1.0)
    
    # 締め切りに近づくほど圧力が高い
    return elapsed / total


def survival_pressure_calculator(context: dict) -> float:
    """
    生存圧力の計算
    
    Context Keys:
    - alive_count: int - 生存者数
    - initial_count: int - 初期人数
    """
    alive = context.get('alive_count', 1)
    initial = context.get('initial_count', 1)
    
    # 生存者が少ないほど圧力が高い
    return 1.0 - (alive / initial)


def risk_pressure_calculator(context: dict) -> float:
    """
    リスク圧力の計算
    
    Context Keys:
    - risk_level: float - リスクレベル（0-1）
    - risk_tolerance: float - リスク許容度（0-1）
    """
    risk = context.get('risk_level', 0.0)
    tolerance = context.get('risk_tolerance', 0.5)
    
    # リスクが許容度を超えるほど圧力が高い
    return max(0.0, risk - tolerance) / (1.0 - tolerance) if tolerance < 1.0 else 0.0


def resource_pressure_calculator(context: dict) -> float:
    """
    リソース圧力の計算
    
    Context Keys:
    - current_resource: float - 現在のリソース量
    - required_resource: float - 必要なリソース量
    """
    current = context.get('current_resource', 0.0)
    required = context.get('required_resource', 1.0)
    
    # リソース不足が大きいほど圧力が高い
    if current >= required:
        return 0.0
    return (required - current) / required


def competition_pressure_calculator(context: dict) -> float:
    """
    競争圧力の計算
    
    Context Keys:
    - my_performance: float - 自分のパフォーマンス
    - competitor_performance: float - 競争相手のパフォーマンス
    """
    my_perf = context.get('my_performance', 0.0)
    comp_perf = context.get('competitor_performance', 0.0)
    
    # 競争相手が優位なほど圧力が高い
    if comp_perf <= my_perf:
        return 0.0
    return (comp_perf - my_perf) / comp_perf if comp_perf > 0 else 0.0


# ========================================
# プリセット構成
# ========================================

def create_apex_survivor_pressure() -> MultiDimensionalPressure:
    """APEX SURVIVOR風の多次元意味圧システム"""
    mdp = MultiDimensionalPressure()
    
    mdp.register_dimension(
        "rank",
        rank_pressure_calculator,
        weight=0.3,
        description="順位からの圧力（低順位ほど高圧力）"
    )
    
    mdp.register_dimension(
        "score",
        score_pressure_calculator,
        weight=0.25,
        description="スコア差からの圧力（目標に届かないほど高圧力）"
    )
    
    mdp.register_dimension(
        "time",
        time_pressure_calculator,
        weight=0.2,
        description="時間経過からの圧力（締め切りに近いほど高圧力）"
    )
    
    mdp.register_dimension(
        "survival",
        survival_pressure_calculator,
        weight=0.25,
        description="生存状況からの圧力（生存者が少ないほど高圧力）"
    )
    
    return mdp


def create_business_pressure() -> MultiDimensionalPressure:
    """ビジネス・経営判断用の多次元意味圧システム"""
    mdp = MultiDimensionalPressure()
    
    mdp.register_dimension(
        "score",
        score_pressure_calculator,
        weight=0.35,
        description="売上・目標達成からの圧力"
    )
    
    mdp.register_dimension(
        "time",
        time_pressure_calculator,
        weight=0.25,
        description="期限・納期からの圧力"
    )
    
    mdp.register_dimension(
        "resource",
        resource_pressure_calculator,
        weight=0.2,
        description="予算・人員などリソースからの圧力"
    )
    
    mdp.register_dimension(
        "competition",
        competition_pressure_calculator,
        weight=0.2,
        description="競合他社からの圧力"
    )
    
    return mdp


def create_simple_pressure() -> MultiDimensionalPressure:
    """シンプルな2次元意味圧システム"""
    mdp = MultiDimensionalPressure()
    
    mdp.register_dimension(
        "performance",
        score_pressure_calculator,
        weight=0.6,
        description="パフォーマンスギャップからの圧力"
    )
    
    mdp.register_dimension(
        "urgency",
        time_pressure_calculator,
        weight=0.4,
        description="緊急性からの圧力"
    )
    
    return mdp


# ========================================
# デモ・テスト
# ========================================

if __name__ == "__main__":
    print("="*70)
    print("多次元意味圧モジュール - デモ")
    print("="*70)
    
    # APEX SURVIVOR風のシステム
    print("\n[1] APEX SURVIVOR風の4次元意味圧")
    mdp_apex = create_apex_survivor_pressure()
    
    # コンテキスト例
    context = {
        'rank': 5,
        'total_players': 7,
        'score': 120,
        'target_score': 200,
        'threshold': 100,
        'elapsed': 3.5,
        'total': 5.0,
        'alive_count': 4,
        'initial_count': 7
    }
    
    pressure = mdp_apex.calculate(context)
    print(f"総合圧力: {pressure[0]:.4f}")
    
    print("\n各次元の情報:")
    for name, info in mdp_apex.get_dimension_info().items():
        print(f"  {name}: 重み={info['weight']:.2f}, 最終値={info['last_value']:.4f}")
    
    # ビジネス用のシステム
    print("\n[2] ビジネス判断用の4次元意味圧")
    mdp_business = create_business_pressure()
    
    context_business = {
        'score': 8000,
        'target_score': 10000,
        'threshold': 5000,
        'elapsed': 8,
        'total': 12,
        'current_resource': 50000,
        'required_resource': 80000,
        'my_performance': 7.5,
        'competitor_performance': 8.2
    }
    
    pressure_business = mdp_business.calculate(context_business)
    print(f"総合圧力: {pressure_business[0]:.4f}")
    
    print("\n各次元の情報:")
    for name, info in mdp_business.get_dimension_info().items():
        print(f"  {name}: 重み={info['weight']:.2f}, 最終値={info['last_value']:.4f}")
    
    # カスタム次元の追加例
    print("\n[3] カスタム次元の追加")
    
    def custom_stress_calculator(context: dict) -> float:
        """カスタム: ストレスレベル計算"""
        stress = context.get('stress_level', 0.0)
        return min(1.0, stress / 10.0)
    
    mdp_apex.register_dimension(
        "stress",
        custom_stress_calculator,
        weight=0.15,
        description="心理的ストレスからの圧力"
    )
    
    context['stress_level'] = 7.5
    pressure_with_stress = mdp_apex.calculate(context)
    print(f"ストレス次元追加後の総合圧力: {pressure_with_stress[0]:.4f}")
    
    # 統計情報
    print("\n[4] 統計情報")
    stats = mdp_apex.get_statistics()
    print(f"次元数: {stats['num_dimensions']}")
    print(f"有効次元数: {stats['num_enabled']}")
    print(f"総重み: {stats['total_weight']:.2f}")
    print(f"次元名: {', '.join(stats['dimension_names'])}")
    
    print("\n" + "="*70)
    print("✅ デモ完了")
    print("="*70)
    
    print("\n💡 使い方:")
    print("  1. create_apex_survivor_pressure() などでプリセットを取得")
    print("  2. register_dimension() でカスタム次元を追加")
    print("  3. calculate(context) で総合圧力を計算")
    print("  4. set_weight() や enable_dimension() で動的に調整")
