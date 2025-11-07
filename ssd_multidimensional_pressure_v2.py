"""
SSD v3.5 拡張: 多次元意味圧モジュール v2.0 (Four-Layer Structure)

概念:
----
意味圧（p_external）を、SSDの「人間モジュール四層構造」に基づいて
階層別に計算・集計するシステム。

四層構造 (Four-Layer Human Module):
- PHYSICAL層 (R→∞): 物理的制約（疲労、損傷、物理法則）
- BASE層 (R=large): 基層構造（生存本能、恐怖、リスク回避）
- CORE層 (R=medium): 中核構造（ルール、規範、社会システム、スコア）
- UPPER層 (R=small): 上層構造（理念、物語、意味、時間的文脈）

理論的意義:
----------
v1.0では全ての意味圧を単一のプールに集約していたが、
これでは「どの構造層が悲鳴を上げているか」を区別できない。

v2.0では、各圧力が作用する層を明示的に定義し、
層ごとに集計された圧力の辞書を返すことで:
  1. 内的葛藤（整合不能）のモデル化が可能に
     例: BASE圧高（危険）× CORE圧低（1位）→ 葛藤
  2. 層ごとに異なる反応ロジックを実装可能
     BASE圧高 → 生存優先の衝動的跳躍（逃走）
     CORE圧高 → ルール遵守の効率的整合（スコア稼ぎ）
     UPPER圧高 → 長期的戦略の自己犠牲的跳躍（特攻）
  3. 「動かしにくさ」の再現
     BASE層は最も動かしにくい（本能）
     UPPER層は最も動かしやすい（理念）

拡張性:
------
v1.0の全機能を維持しつつ、SSD理論に基づく構造的拡張:
- 各次元が作用する層（SSDLayer）を指定
- 層ごとに重み付け平均された圧力を返す
- 層間の葛藤を定量化する統計関数を追加
"""

import numpy as np
from typing import Dict, Callable, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto


class SSDLayer(Enum):
    """SSD人間モジュールの四層構造
    
    R値（動かしにくさ）: PHYSICAL→∞ > BASE > CORE > UPPER
    """
    PHYSICAL = auto()  # 物理層: 疲労、損傷、物理的制約 (R→∞)
    BASE = auto()      # 基層:   生存圧、恐怖、リスク圧 (本能, R=large)
    CORE = auto()      # 中核層: ルール、スコア、順位、リソース (社会/システム, R=medium)
    UPPER = auto()     # 上層:   理念、物語、時間圧 (意味/文脈, R=small)


@dataclass
class PressureDimension:
    """意味圧の1つの次元 (四層構造対応)"""
    name: str                           # 次元名
    weight: float                       # 重み（影響度）
    calculator: Callable                # 計算関数
    layer: SSDLayer                     # [v2追加] 作用する構造層
    enabled: bool = True                # 有効/無効
    description: str = ""               # 説明
    history: List[float] = field(default_factory=list)  # 履歴


class MultiDimensionalPressure:
    """多次元意味圧計算システム v2.0 (四層構造対応)
    
    v1.0との違い:
    - calculate()の戻り値が Dict[SSDLayer, float] に変更
    - 各次元にSSDLayerを指定必須
    - 層間葛藤を分析する新機能追加
    """
    
    def __init__(self):
        self.dimensions: Dict[str, PressureDimension] = {}
        self.total_pressure_history = []
        self.layer_pressure_history: Dict[SSDLayer, List[float]] = {
            layer: [] for layer in SSDLayer
        }
        
    def register_dimension(
        self, 
        name: str, 
        calculator: Callable,
        layer: SSDLayer,  # [v2追加] 必須パラメータに
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
        layer: SSDLayer
            この圧力が作用する構造層 (PHYSICAL/BASE/CORE/UPPER)
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
            layer=layer,  # [v2追加] 層を登録
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
    
    def calculate(self, context: dict) -> Dict[SSDLayer, float]:
        """
        多次元意味圧を「四層構造」別に集計して計算
        
        v1.0との違い:
        - 戻り値が np.ndarray から Dict[SSDLayer, float] に変更
        - 各層ごとに重み付け平均された圧力を返す
        - 層間の葛藤を定量化可能に
        
        Parameters:
        -----------
        context: dict
            計算に必要なコンテキスト情報
            
        Returns:
        --------
        pressures: Dict[SSDLayer, float]
            各層ごとに重み付け平均された圧力値の辞書
            例: {SSDLayer.BASE: 0.8, SSDLayer.CORE: 0.3, SSDLayer.UPPER: 0.5}
        """
        
        # 各層ごとに圧力の合計と重みの合計を格納する
        layer_pressures: Dict[SSDLayer, float] = {layer: 0.0 for layer in SSDLayer}
        layer_weights: Dict[SSDLayer, float] = {layer: 0.0 for layer in SSDLayer}
        
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
        final_pressures: Dict[SSDLayer, float] = {}
        for layer in SSDLayer:
            total_w = layer_weights[layer]
            if total_w > 0:
                final_pressures[layer] = layer_pressures[layer] / total_w
            else:
                final_pressures[layer] = 0.0
        
        # 層ごとの履歴に記録
        for layer in SSDLayer:
            self.layer_pressure_history[layer].append(final_pressures[layer])
        
        # 総合圧（参考値）も計算
        # SSD理論的には「層ごとに異なる反応」が本質だが、
        # 全体の圧力レベルも参考情報として保持
        total_pressure_all = sum(final_pressures.values())
        self.total_pressure_history.append(total_pressure_all)
        
        return final_pressures
    
    def get_dimension_info(self) -> Dict[str, dict]:
        """全次元の情報を取得 (層情報を含む)"""
        info = {}
        for name, dim in self.dimensions.items():
            info[name] = {
                'weight': dim.weight,
                'layer': dim.layer.name,  # [v2追加] 層名を含む
                'enabled': dim.enabled,
                'description': dim.description,
                'last_value': dim.history[-1] if dim.history else None,
                'history_length': len(dim.history)
            }
        return info
    
    def get_statistics(self) -> dict:
        """統計情報を取得 (層別統計を含む)"""
        # 層別の次元数と総重みを計算
        layer_stats = {}
        for layer in SSDLayer:
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
            'layer_stats': layer_stats  # [v2追加] 層別統計
        }
    
    def get_layer_conflict_index(self) -> Dict[str, float]:
        """
        [v2新機能] 層間葛藤指数を計算
        
        理論的意義:
        - BASE層とUPPER層の圧力が同時に高い場合、強い内的葛藤が生じる
        - 例: BASE圧高（危険）× UPPER圧高（理念）→ 「逃げるべきか、理念を貫くか」
        
        Returns:
        --------
        conflict_indices: Dict[str, float]
            各層ペアの葛藤指数
            例: 'BASE-UPPER': 0.64 (両方とも0.8の圧力)
        """
        if not self.layer_pressure_history[SSDLayer.BASE]:
            return {}
        
        # 最新の各層圧力を取得
        current_pressures = {
            layer: self.layer_pressure_history[layer][-1] 
            for layer in SSDLayer
        }
        
        conflicts = {}
        
        # BASE-UPPER葛藤（本能 vs 理念）
        conflicts['BASE-UPPER'] = current_pressures[SSDLayer.BASE] * current_pressures[SSDLayer.UPPER]
        
        # BASE-CORE葛藤（本能 vs 規範）
        conflicts['BASE-CORE'] = current_pressures[SSDLayer.BASE] * current_pressures[SSDLayer.CORE]
        
        # CORE-UPPER葛藤（規範 vs 理念）
        conflicts['CORE-UPPER'] = current_pressures[SSDLayer.CORE] * current_pressures[SSDLayer.UPPER]
        
        # PHYSICAL圧が高い場合は全ての葛藤が無意味（物理制約が支配的）
        physical_suppression = 1.0 - current_pressures[SSDLayer.PHYSICAL]
        conflicts = {k: v * physical_suppression for k, v in conflicts.items()}
        
        return conflicts
    
    def get_dominant_layer(self) -> Tuple[SSDLayer, float]:
        """
        [v2新機能] 現在最も圧力が高い層を返す
        
        Returns:
        --------
        (layer, pressure): Tuple[SSDLayer, float]
            最高圧力の層とその値
        """
        if not self.layer_pressure_history[SSDLayer.BASE]:
            return (SSDLayer.BASE, 0.0)
        
        current_pressures = {
            layer: self.layer_pressure_history[layer][-1] 
            for layer in SSDLayer
        }
        
        dominant_layer = max(current_pressures.items(), key=lambda x: x[1])
        return dominant_layer
    
    def should_trigger_leap(self, threshold: float = 0.7) -> Optional[SSDLayer]:
        """
        [v2新機能] 跳躍（Leap）をトリガーすべき層を判定
        
        理論的意義:
        - 各層には「動かしにくさ」(R値)がある
        - BASE層が閾値を超えた場合、最も強い跳躍（本能的行動）
        - UPPER層が閾値を超えた場合、最も弱い跳躍（理念的行動）
        
        Parameters:
        -----------
        threshold: float
            跳躍トリガーの閾値（デフォルト0.7）
            
        Returns:
        --------
        layer: Optional[SSDLayer]
            跳躍すべき層。複数の層が閾値を超えた場合、R値が最大の層を返す
        """
        if not self.layer_pressure_history[SSDLayer.BASE]:
            return None
        
        current_pressures = {
            layer: self.layer_pressure_history[layer][-1] 
            for layer in SSDLayer
        }
        
        # R値の定義（動かしにくさ）: PHYSICAL→∞ > BASE > CORE > UPPER
        R_values = {
            SSDLayer.PHYSICAL: 1000.0,  # 物理制約は絶対的
            SSDLayer.BASE: 100.0,       # 本能は非常に強い
            SSDLayer.CORE: 10.0,        # 規範は中程度
            SSDLayer.UPPER: 1.0         # 理念は最も弱い
        }
        
        # 閾値を超えた層を抽出
        triggered_layers = [
            layer for layer, pressure in current_pressures.items() 
            if pressure > threshold
        ]
        
        if not triggered_layers:
            return None
        
        # 最もR値が高い（動かしにくい）層を返す
        # → 最も強い跳躍をトリガーする層
        dominant_layer = max(triggered_layers, key=lambda l: R_values[l])
        return dominant_layer


# ========================================
# プリセット圧力計算関数 (v1.0から継承)
# ========================================

def rank_pressure_calculator(context: dict) -> float:
    """
    順位圧力の計算 (CORE層に作用)
    
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
    スコア差圧力の計算 (CORE層に作用)
    
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
    時間圧力の計算 (UPPER層に作用)
    
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
    生存圧力の計算 (BASE層に作用)
    
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
    リスク圧力の計算 (BASE層に作用)
    
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
    リソース圧力の計算 (CORE層に作用)
    
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
    競争圧力の計算 (UPPER層に作用)
    
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


def fatigue_pressure_calculator(context: dict) -> float:
    """
    疲労圧力の計算 (PHYSICAL層に作用)
    
    Context Keys:
    - fatigue_level: float - 疲労度（0-1）
    - fatigue_threshold: float - 疲労限界（0-1）
    """
    fatigue = context.get('fatigue_level', 0.0)
    threshold = context.get('fatigue_threshold', 0.8)
    
    # 疲労が閾値を超えるほど圧力が高い
    return max(0.0, fatigue - threshold) / (1.0 - threshold) if threshold < 1.0 else 0.0


def damage_pressure_calculator(context: dict) -> float:
    """
    ダメージ圧力の計算 (PHYSICAL層に作用)
    
    Context Keys:
    - current_hp: float - 現在のHP
    - max_hp: float - 最大HP
    """
    current_hp = context.get('current_hp', 100.0)
    max_hp = context.get('max_hp', 100.0)
    
    # HPが低いほど圧力が高い
    return 1.0 - (current_hp / max_hp) if max_hp > 0 else 0.0


# ========================================
# プリセット構成 (四層構造対応版)
# ========================================

def create_apex_survivor_pressure_v2() -> MultiDimensionalPressure:
    """APEX SURVIVOR風の多次元意味圧システム v2.0 (四層構造対応版)"""
    mdp = MultiDimensionalPressure()
    
    # --- PHYSICAL層: 物理的制約 ---
    mdp.register_dimension(
        "damage",
        damage_pressure_calculator,
        layer=SSDLayer.PHYSICAL,
        weight=0.5,
        description="ダメージ圧力（物理層）- HP低下による物理的制約"
    )
    
    # --- BASE層: 本能・生存・恐怖 ---
    mdp.register_dimension(
        "survival",
        survival_pressure_calculator,
        layer=SSDLayer.BASE,
        weight=0.4,
        description="生存圧力（基層）- 生存者減少による本能的恐怖"
    )
    mdp.register_dimension(
        "risk",
        risk_pressure_calculator,
        layer=SSDLayer.BASE,
        weight=0.3,
        description="リスク圧力（基層）- 危険状況への本能的回避"
    )
    
    # --- CORE層: ルール・社会・スコア ---
    mdp.register_dimension(
        "rank",
        rank_pressure_calculator,
        layer=SSDLayer.CORE,
        weight=0.3,
        description="順位圧力（中核層）- 社会的競争における順位プレッシャー"
    )
    mdp.register_dimension(
        "score",
        score_pressure_calculator,
        layer=SSDLayer.CORE,
        weight=0.15,
        description="スコア圧力（中核層）- 目標達成のシステム的要求"
    )
    
    # --- UPPER層: 意味・文脈・理念 ---
    mdp.register_dimension(
        "time",
        time_pressure_calculator,
        layer=SSDLayer.UPPER,
        weight=0.15,
        description="時間圧力（上層）- 締切という意味的文脈からの圧力"
    )
    
    return mdp


def create_business_pressure_v2() -> MultiDimensionalPressure:
    """ビジネス・経営判断用の多次元意味圧システム v2.0 (四層構造対応版)"""
    mdp = MultiDimensionalPressure()
    
    # --- PHYSICAL層: 物理的制約 ---
    mdp.register_dimension(
        "fatigue",
        fatigue_pressure_calculator,
        layer=SSDLayer.PHYSICAL,
        weight=0.3,
        description="疲労圧力（物理層）- 身体的限界"
    )
    
    # --- BASE層: 本能・生存 ---
    mdp.register_dimension(
        "survival",
        survival_pressure_calculator,  # 企業の生存率として解釈
        layer=SSDLayer.BASE,
        weight=0.4,
        description="生存圧力（基層）- 倒産危機からの本能的反応"
    )
    
    # --- CORE層: ルール・社会・スコア ---
    mdp.register_dimension(
        "score",
        score_pressure_calculator,  # 売上・目標
        layer=SSDLayer.CORE,
        weight=0.35,
        description="業績圧力（中核層）- 売上・目標達成の社会的要求"
    )
    mdp.register_dimension(
        "resource",
        resource_pressure_calculator,
        layer=SSDLayer.CORE,
        weight=0.2,
        description="リソース圧力（中核層）- 予算・人員の制約"
    )
    
    # --- UPPER層: 意味・文脈・理念 ---
    mdp.register_dimension(
        "time",
        time_pressure_calculator,
        layer=SSDLayer.UPPER,
        weight=0.25,
        description="期限圧力（上層）- 納期という時間的意味からの圧力"
    )
    mdp.register_dimension(
        "competition",
        competition_pressure_calculator,
        layer=SSDLayer.UPPER,
        weight=0.2,
        description="競争圧力（上層）- 競合との物語的関係性"
    )
    
    return mdp


def create_simple_pressure_v2() -> MultiDimensionalPressure:
    """シンプルな2次元意味圧システム v2.0 (BASE + UPPER)"""
    mdp = MultiDimensionalPressure()
    
    # --- BASE層: 本能 ---
    mdp.register_dimension(
        "survival",
        survival_pressure_calculator,
        layer=SSDLayer.BASE,
        weight=0.6,
        description="生存圧力（基層）- 本能的反応"
    )
    
    # --- UPPER層: 意味 ---
    mdp.register_dimension(
        "urgency",
        time_pressure_calculator,
        layer=SSDLayer.UPPER,
        weight=0.4,
        description="緊急性圧力（上層）- 時間的意味"
    )
    
    return mdp


# ========================================
# デモ・テスト
# ========================================

if __name__ == "__main__":
    print("="*70)
    print("多次元意味圧モジュール v2.0 - 四層構造対応版デモ")
    print("="*70)
    
    # APEX SURVIVOR風のシステム v2.0
    print("\n[1] APEX SURVIVOR風の四層構造意味圧 v2.0")
    mdp_apex = create_apex_survivor_pressure_v2()
    
    # コンテキスト例
    context = {
        # PHYSICAL層
        'current_hp': 30,
        'max_hp': 100,
        # BASE層
        'alive_count': 3,
        'initial_count': 7,
        'risk_level': 0.7,
        'risk_tolerance': 0.4,
        # CORE層
        'rank': 5,
        'total_players': 7,
        'score': 120,
        'target_score': 200,
        'threshold': 100,
        # UPPER層
        'elapsed': 3.5,
        'total': 5.0
    }
    
    pressures = mdp_apex.calculate(context)
    print(f"\n層別圧力:")
    for layer, pressure in pressures.items():
        print(f"  {layer.name:10s}: {pressure:.4f}")
    
    print(f"\n総合圧力（参考）: {sum(pressures.values()):.4f}")
    
    # 支配的な層を判定
    dominant_layer, dominant_pressure = mdp_apex.get_dominant_layer()
    print(f"\n支配的な層: {dominant_layer.name} (圧力={dominant_pressure:.4f})")
    
    # 葛藤指数を計算
    conflicts = mdp_apex.get_layer_conflict_index()
    print(f"\n層間葛藤指数:")
    for conflict_pair, index in conflicts.items():
        print(f"  {conflict_pair}: {index:.4f}")
    
    # 跳躍判定
    leap_layer = mdp_apex.should_trigger_leap(threshold=0.5)
    if leap_layer:
        print(f"\n⚠️ 跳躍トリガー: {leap_layer.name}層が閾値を超えました")
        if leap_layer == SSDLayer.BASE:
            print("   → 本能的な生存行動（逃走・攻撃）を推奨")
        elif leap_layer == SSDLayer.PHYSICAL:
            print("   → 物理的制約による強制的行動変更")
    else:
        print(f"\n✅ 跳躍なし（全層が閾値0.5以下）")
    
    # 各次元の情報
    print("\n各次元の情報:")
    for name, info in mdp_apex.get_dimension_info().items():
        print(f"  {name}: 層={info['layer']}, 重み={info['weight']:.2f}, 最終値={info['last_value']:.4f}")
    
    # 統計情報
    print("\n[2] 統計情報 (層別)")
    stats = mdp_apex.get_statistics()
    print(f"総次元数: {stats['num_dimensions']}")
    print(f"有効次元数: {stats['num_enabled']}")
    print(f"\n層別統計:")
    for layer_name, layer_stat in stats['layer_stats'].items():
        last_p = layer_stat['last_pressure'] if layer_stat['last_pressure'] is not None else 0.0
        print(f"  {layer_name:10s}: 次元数={layer_stat['num_dimensions']}, "
              f"総重み={layer_stat['total_weight']:.2f}, "
              f"最終圧力={last_p:.4f}")
    
    # シナリオテスト: 内的葛藤のケース
    print("\n[3] シナリオテスト: 内的葛藤（BASE高 × UPPER高）")
    context_conflict = {
        # PHYSICAL層: 正常
        'current_hp': 80,
        'max_hp': 100,
        # BASE層: 高圧力（危険！）
        'alive_count': 2,
        'initial_count': 7,
        'risk_level': 0.9,
        'risk_tolerance': 0.3,
        # CORE層: 低圧力（順位は良好）
        'rank': 2,
        'total_players': 7,
        'score': 180,
        'target_score': 200,
        'threshold': 100,
        # UPPER層: 高圧力（時間切れ間近！）
        'elapsed': 4.8,
        'total': 5.0
    }
    
    pressures_conflict = mdp_apex.calculate(context_conflict)
    print(f"\n層別圧力:")
    for layer, pressure in pressures_conflict.items():
        print(f"  {layer.name:10s}: {pressure:.4f}")
    
    conflicts_conflict = mdp_apex.get_layer_conflict_index()
    print(f"\n層間葛藤指数:")
    for conflict_pair, index in conflicts_conflict.items():
        print(f"  {conflict_pair}: {index:.4f}")
    
    print(f"\n解釈:")
    if conflicts_conflict['BASE-UPPER'] > 0.5:
        print("  ⚠️ BASE-UPPER葛藤が高い！")
        print("  → 「逃げるべきか（BASE: 生存本能）、理念を貫くべきか（UPPER: 時間圧）」")
        print("  → AIは内的整合不能状態 → 構造的跳躍の可能性")
    
    leap_layer_conflict = mdp_apex.should_trigger_leap(threshold=0.6)
    if leap_layer_conflict:
        print(f"\n⚠️ 跳躍トリガー: {leap_layer_conflict.name}層")
        print(f"   → R値が高い{leap_layer_conflict.name}層が支配的")
    
    print("\n" + "="*70)
    print("✅ v2.0デモ完了")
    print("="*70)
    
    print("\n💡 v2.0の理論的意義:")
    print("  1. 層別の圧力集計 → 「どの構造が悲鳴を上げているか」を区別可能")
    print("  2. 内的葛藤の定量化 → BASE×UPPER高 = 本能と理念の対立")
    print("  3. 跳躍のR値判定 → 最も動かしにくい層が最優先で跳躍")
    print("  4. AIの人間らしさ → 単なる最適化ではなく、構造的葛藤を抱える主体へ")
