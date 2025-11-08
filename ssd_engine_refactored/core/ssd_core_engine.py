"""
SSD Core Engine - 汎用計算エンジン
=====================================

構造主観力学（SSD）の基本数理を実装した、ドメイン非依存の計算エンジン。

核心概念:
- 意味圧 (p): 構造に作用する外部/内部エネルギー
- 整合慣性 (κ): 経路の使いやすさ（学習痕跡）
- 未処理圧 (E): 処理しきれなかった圧力の蓄積
- 抵抗 (R): 構造の動かしにくさ
- 臨界閾値 (Theta): 跳躍を引き起こす閾値

理論的基盤:
- Ohm's law analogy: j = (G0 + g·κ)·p
- Energy accumulation: E蓄積 = 意味圧 - 処理能力
- Leap trigger: E ≥ Theta → 構造的跳躍

参考: https://github.com/HermannDegner/Structural-Subjectivity-Dynamics
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from enum import Enum, auto


class LeapType(Enum):
    """跳躍タイプ（ドメイン非依存）"""
    NO_LEAP = auto()
    LEAP_LAYER_1 = auto()
    LEAP_LAYER_2 = auto()
    LEAP_LAYER_3 = auto()
    LEAP_LAYER_4 = auto()
    # 必要に応じて追加可能


@dataclass
class SSDCoreParams:
    """
    SSD汎用パラメータ
    
    レイヤー数やドメインに依存しない基本パラメータセット
    """
    # レイヤー構成
    num_layers: int = 4
    
    # 各レイヤーのパラメータ（配列として指定）
    R_values: List[float] = field(default_factory=lambda: [1000.0, 100.0, 10.0, 1.0])
    
    # エネルギー生成パラメータ（各レイヤー）
    gamma_values: List[float] = field(default_factory=lambda: [0.15, 0.10, 0.08, 0.05])
    
    # エネルギー減衰パラメータ（各レイヤー）
    beta_values: List[float] = field(default_factory=lambda: [0.001, 0.01, 0.05, 0.1])
    
    # κ学習率（各レイヤー）
    eta_values: List[float] = field(default_factory=lambda: [0.9, 0.5, 0.3, 0.2])
    
    # κ減衰率（各レイヤー）
    lambda_values: List[float] = field(default_factory=lambda: [0.001, 0.01, 0.02, 0.05])
    
    # κ最小値（各レイヤー）
    kappa_min_values: List[float] = field(default_factory=lambda: [0.9, 0.8, 0.5, 0.3])
    
    # Theta閾値（各レイヤー）
    Theta_values: List[float] = field(default_factory=lambda: [200.0, 100.0, 50.0, 30.0])
    
    # Dynamic Theta パラメータ
    enable_dynamic_theta: bool = True
    theta_sensitivity: float = 0.3
    
    # Ohm's law パラメータ
    G0: float = 0.5  # ベース導電率
    g: float = 0.7   # 慣性ゲイン
    
    # ノイズ
    epsilon_noise: float = 0.01
    
    def __post_init__(self):
        """パラメータ配列の長さを検証"""
        arrays = [
            self.R_values, self.gamma_values, self.beta_values,
            self.eta_values, self.lambda_values, self.kappa_min_values,
            self.Theta_values
        ]
        for arr in arrays:
            if len(arr) != self.num_layers:
                raise ValueError(f"パラメータ配列の長さがnum_layers={self.num_layers}と一致しません")


@dataclass
class SSDCoreState:
    """
    SSD汎用状態ベクトル
    
    レイヤー数に応じて動的にサイズが決まる
    """
    # 各レイヤーのエネルギー
    E: np.ndarray = field(default_factory=lambda: np.zeros(4))
    
    # 各レイヤーのκ
    kappa: np.ndarray = field(default_factory=lambda: np.ones(4))
    
    # 時間
    t: float = 0.0
    
    # 跳躍履歴
    leap_history: List[Tuple[float, LeapType]] = field(default_factory=list)
    
    def __post_init__(self):
        """NumPy配列に変換"""
        if not isinstance(self.E, np.ndarray):
            self.E = np.array(self.E)
        if not isinstance(self.kappa, np.ndarray):
            self.kappa = np.array(self.kappa)


class SSDCoreEngine:
    """
    SSD汎用計算エンジン
    
    任意のレイヤー数・パラメータセットで動作する計算エンジン。
    ドメイン固有の解釈は上位モジュール（HumanModule等）が担当。
    """
    
    def __init__(self, params: SSDCoreParams):
        self.params = params
        self.num_layers = params.num_layers
        
    def compute_structural_power(
        self,
        state: SSDCoreState,
        pressure: np.ndarray
    ) -> np.ndarray:
        """
        構造的影響力の計算
        
        Power[i] = P[i] × E[i] × κ[i] × R[i]
        
        Returns:
            各レイヤーの構造的影響力
        """
        if len(pressure) != self.num_layers:
            raise ValueError(f"圧力ベクトルの長さが{self.num_layers}ではありません")
        
        R_array = np.array(self.params.R_values)
        power = pressure * state.E * state.kappa * R_array
        return power
    
    def compute_dynamic_theta(
        self,
        state: SSDCoreState,
        pressure: np.ndarray,
        layer_index: int
    ) -> float:
        """
        [Phase 2] 動的閾値の計算
        
        Theta_dynamic = Theta_base × (1 - sensitivity × structural_influence)
        
        structural_influence = (P × E × κ × R) / (κ × R)
        """
        if not self.params.enable_dynamic_theta:
            return self.params.Theta_values[layer_index]
        
        # 構造的影響力
        power = self.compute_structural_power(state, pressure)
        total_power = np.sum(power)
        
        # 正規化された影響
        R_array = np.array(self.params.R_values)
        denominator = np.sum(state.kappa * R_array)
        
        if denominator > 0:
            structural_influence = total_power / denominator
        else:
            structural_influence = 0.0
        
        # 動的Theta
        base_theta = self.params.Theta_values[layer_index]
        dynamic_theta = base_theta * (1.0 - self.params.theta_sensitivity * structural_influence)
        
        return max(1.0, dynamic_theta)  # 最小値1.0
    
    def detect_leap(
        self,
        state: SSDCoreState,
        pressure: np.ndarray
    ) -> Tuple[bool, Optional[int]]:
        """
        跳躍検出（統合版）
        
        Returns:
            (跳躍発生フラグ, 跳躍したレイヤーのインデックス)
        """
        for i in range(self.num_layers):
            theta_i = self.compute_dynamic_theta(state, pressure, i)
            
            if state.E[i] >= theta_i:
                # 確率的跳躍判定
                leap_prob = min(1.0, (state.E[i] - theta_i) / theta_i)
                if np.random.random() < leap_prob:
                    return True, i
        
        return False, None
    
    def execute_leap(
        self,
        state: SSDCoreState,
        layer_index: int
    ) -> SSDCoreState:
        """
        跳躍の実行
        
        - エネルギーをリセット
        - κを微増（跳躍による学習）
        """
        new_state = SSDCoreState(
            E=state.E.copy(),
            kappa=state.kappa.copy(),
            t=state.t,
            leap_history=state.leap_history.copy()
        )
        
        # エネルギーリセット
        new_state.E[layer_index] *= 0.1
        
        # κ微増（跳躍による学習）
        new_state.kappa[layer_index] += 0.1
        
        # 跳躍履歴記録
        leap_type = LeapType(layer_index + 2)  # NO_LEAPを除いて2から開始
        new_state.leap_history.append((state.t, leap_type))
        
        return new_state
    
    def step(
        self,
        state: SSDCoreState,
        pressure: np.ndarray,
        dt: float = 0.1,
        interlayer_transfer: Optional[np.ndarray] = None
    ) -> SSDCoreState:
        """
        1ステップ実行
        
        Args:
            state: 現在の状態
            pressure: 意味圧ベクトル（各レイヤー）
            dt: 時間刻み
            interlayer_transfer: 層間転送行列（オプション、上位モジュールが提供）
        
        Returns:
            更新後の状態
        """
        # 跳躍検出
        leap_occurred, leap_layer = self.detect_leap(state, pressure)
        
        if leap_occurred:
            state = self.execute_leap(state, leap_layer)
        
        # 新しい状態
        new_state = SSDCoreState(
            E=state.E.copy(),
            kappa=state.kappa.copy(),
            t=state.t + dt,
            leap_history=state.leap_history.copy()
        )
        
        # 各レイヤーの更新
        R_array = np.array(self.params.R_values)
        gamma_array = np.array(self.params.gamma_values)
        beta_array = np.array(self.params.beta_values)
        eta_array = np.array(self.params.eta_values)
        lambda_array = np.array(self.params.lambda_values)
        kappa_min_array = np.array(self.params.kappa_min_values)
        
        # Ohm's law: j = (G0 + g·κ)·p
        conductance = self.params.G0 + self.params.g * state.kappa
        j = conductance * pressure
        
        # エネルギー生成（処理しきれない分）
        energy_generation = gamma_array * np.abs(pressure) / R_array
        
        # エネルギー減衰
        energy_decay = beta_array * state.E
        
        # エネルギー更新
        dE = energy_generation - energy_decay
        
        # 層間転送があれば加算
        if interlayer_transfer is not None:
            dE += interlayer_transfer
        
        new_state.E = np.maximum(0.0, state.E + dE * dt)
        
        # κ更新（使用による強化と未使用減衰）
        usage_factor = np.abs(j) / (np.abs(j) + 1.0)  # 正規化された使用度
        dkappa = eta_array * usage_factor - lambda_array * state.kappa
        new_state.kappa = np.maximum(kappa_min_array, state.kappa + dkappa * dt)
        
        return new_state
    
    def get_dominant_layer(self, state: SSDCoreState, pressure: np.ndarray) -> int:
        """
        最も影響力の高いレイヤーを返す
        
        Returns:
            最大構造的影響力を持つレイヤーのインデックス
        """
        power = self.compute_structural_power(state, pressure)
        return int(np.argmax(power))


# ============================================================================
# ユーティリティ関数
# ============================================================================

def create_default_state(num_layers: int = 4) -> SSDCoreState:
    """デフォルト状態の生成"""
    return SSDCoreState(
        E=np.zeros(num_layers),
        kappa=np.ones(num_layers),
        t=0.0
    )


def create_custom_params(
    num_layers: int,
    R_values: List[float],
    **kwargs
) -> SSDCoreParams:
    """カスタムパラメータの生成ヘルパー"""
    return SSDCoreParams(
        num_layers=num_layers,
        R_values=R_values,
        **kwargs
    )
