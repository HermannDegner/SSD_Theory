"""
SSD Human Module - 人間心理特化モジュール
=========================================

構造主観力学の人間モジュール（四層構造）を実装。
汎用エンジン（ssd_core_engine.py）をラップし、人間心理に特化した解釈を提供。

四層構造:
- PHYSICAL層 (R=1000): 物理的制約（疲労、損傷、飢餓）
- BASE層 (R=100): 本能的不満（生存、繁殖、快楽）
- CORE層 (R=10): 規範的不満（法、習慣、道徳）
- UPPER層 (R=1): 理念的不満（価値観、信念、物語）

原典理論:
https://github.com/HermannDegner/Structural-Subjectivity-Dynamics
→ Human_Module/人間モジュール　コア.md
"""

import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple

from ssd_core_engine import (
    SSDCoreEngine, SSDCoreParams, SSDCoreState,
    LeapType, create_default_state
)


class HumanLayer(Enum):
    """人間モジュールの四層構造"""
    PHYSICAL = 0  # 物理層（最も動かしにくい）
    BASE = 1      # 基層（本能的）
    CORE = 2      # 中核層（規範的）
    UPPER = 3     # 上層（理念的、最も動かしやすい）


class HumanLeapType(Enum):
    """人間特化の跳躍タイプ"""
    NO_LEAP = 0
    LEAP_PHYSICAL = 1  # 物理的限界突破（条件反射、パニック）
    LEAP_BASE = 2      # 本能的跳躍（怒り爆発、性衝動）
    LEAP_CORE = 3      # 規範的跳躍（習慣変更、ルール破り）
    LEAP_UPPER = 4     # 理念的跳躍（価値観転換、信念崩壊）


@dataclass
class HumanParams:
    """
    人間モジュール特化パラメータ
    
    原典の人間モジュール仕様に基づくデフォルト値
    """
    # 四層のR値（動かしにくさ）
    R_physical: float = 1000.0  # 極めて動かしにくい
    R_base: float = 100.0       # 動かしにくい
    R_core: float = 10.0        # やや動きやすい
    R_upper: float = 1.0        # 最も動きやすい
    
    # エネルギー生成率（gamma）
    gamma_physical: float = 0.15  # 物理的疲労は急速に蓄積
    gamma_base: float = 0.10      # 本能的不満も蓄積しやすい
    gamma_core: float = 0.08      # 規範的不満は中程度
    gamma_upper: float = 0.05     # 理念的不満は緩やか
    
    # エネルギー減衰率（beta）
    beta_physical: float = 0.001  # 疲労は回復が遅い
    beta_base: float = 0.01       # 本能も遅い
    beta_core: float = 0.05       # 規範は中速
    beta_upper: float = 0.1       # 理念は速い（忘れやすい）
    
    # κ学習率（eta）
    eta_physical: float = 0.9     # 条件反射は速い
    eta_base: float = 0.5         # 本能的学習も速い
    eta_core: float = 0.3         # 規範的学習は中速
    eta_upper: float = 0.2        # 理念的学習は遅い
    
    # κ減衰率（lambda）
    lambda_physical: float = 0.001  # 身体記憶は忘れにくい
    lambda_base: float = 0.01       # 本能も忘れにくい
    lambda_core: float = 0.02       # 規範は中程度
    lambda_upper: float = 0.05      # 理念は忘れやすい
    
    # κ最小値
    kappa_min_physical: float = 0.9  # 極めて強固
    kappa_min_base: float = 0.8      # 強固
    kappa_min_core: float = 0.5      # 中程度
    kappa_min_upper: float = 0.3     # 柔軟
    
    # Theta閾値
    Theta_physical: float = 200.0  # 極めて高い
    Theta_base: float = 100.0      # 高い
    Theta_core: float = 50.0       # 中程度
    Theta_upper: float = 30.0      # 低い
    
    # Dynamic Theta
    enable_dynamic_theta: bool = True
    theta_sensitivity: float = 0.3
    
    # [Phase 3] 層間転送係数（8パス）
    transfer_upper_to_base: float = 0.08   # 理念が本能を抑圧
    transfer_upper_to_core: float = 0.06   # 理念が規範を変更
    transfer_base_to_upper: float = 0.15   # 本能が理念を破壊
    transfer_base_to_core: float = 0.10    # 本能が規範を侵食
    transfer_core_to_upper: float = 0.05   # 規範が理念を制約
    transfer_core_to_base: float = 0.03    # 規範が本能を抑制
    transfer_physical_to_base: float = 0.20   # 疲労が本能を減衰
    transfer_physical_to_upper: float = 0.12  # 疲労が思考を鈍化
    
    def to_core_params(self) -> SSDCoreParams:
        """汎用エンジンパラメータに変換"""
        return SSDCoreParams(
            num_layers=4,
            R_values=[self.R_physical, self.R_base, self.R_core, self.R_upper],
            gamma_values=[self.gamma_physical, self.gamma_base, self.gamma_core, self.gamma_upper],
            beta_values=[self.beta_physical, self.beta_base, self.beta_core, self.beta_upper],
            eta_values=[self.eta_physical, self.eta_base, self.eta_core, self.eta_upper],
            lambda_values=[self.lambda_physical, self.lambda_base, self.lambda_core, self.lambda_upper],
            kappa_min_values=[self.kappa_min_physical, self.kappa_min_base, self.kappa_min_core, self.kappa_min_upper],
            Theta_values=[self.Theta_physical, self.Theta_base, self.Theta_core, self.Theta_upper],
            enable_dynamic_theta=self.enable_dynamic_theta,
            theta_sensitivity=self.theta_sensitivity
        )


@dataclass
class HumanPressure:
    """
    人間特化の意味圧入力
    
    各層に対する圧力を心理的意味で表現
    """
    physical: float = 0.0   # 物理的圧力（疲労、痛み、飢餓）
    base: float = 0.0       # 本能的圧力（恐怖、欲求、快楽）
    core: float = 0.0       # 規範的圧力（義務、責任、同調圧力）
    upper: float = 0.0      # 理念的圧力（価値観衝突、信念の揺らぎ）
    
    def to_vector(self) -> np.ndarray:
        """ベクトルに変換"""
        return np.array([self.physical, self.base, self.core, self.upper])


class HumanAgent:
    """
    人間エージェント
    
    汎用SSDエンジンを内包し、人間心理に特化した解釈を提供。
    """
    
    def __init__(self, params: Optional[HumanParams] = None, agent_id: str = "Human"):
        self.params = params or HumanParams()
        self.agent_id = agent_id
        
        # 汎用エンジン初期化
        core_params = self.params.to_core_params()
        self.engine = SSDCoreEngine(core_params)
        
        # 状態初期化
        self.state = create_default_state(num_layers=4)
        
        # 層間転送行列（4x4）
        self.interlayer_matrix = self._build_interlayer_matrix()
    
    def _build_interlayer_matrix(self) -> np.ndarray:
        """
        [Phase 3] 層間転送行列の構築
        
        matrix[i][j]: j層からi層へのエネルギー転送係数
        """
        p = self.params
        matrix = np.zeros((4, 4))
        
        # UPPER → BASE (理念が本能を抑圧)
        matrix[HumanLayer.BASE.value][HumanLayer.UPPER.value] = -p.transfer_upper_to_base
        
        # UPPER → CORE (理念が規範を変更)
        matrix[HumanLayer.CORE.value][HumanLayer.UPPER.value] = -p.transfer_upper_to_core
        
        # BASE → UPPER (本能が理念を破壊)
        matrix[HumanLayer.UPPER.value][HumanLayer.BASE.value] = -p.transfer_base_to_upper
        
        # BASE → CORE (本能が規範を侵食)
        matrix[HumanLayer.CORE.value][HumanLayer.BASE.value] = -p.transfer_base_to_core
        
        # CORE → UPPER (規範が理念を制約)
        matrix[HumanLayer.UPPER.value][HumanLayer.CORE.value] = -p.transfer_core_to_upper
        
        # CORE → BASE (規範が本能を抑制)
        matrix[HumanLayer.BASE.value][HumanLayer.CORE.value] = -p.transfer_core_to_base
        
        # PHYSICAL → BASE (疲労が本能を減衰)
        matrix[HumanLayer.BASE.value][HumanLayer.PHYSICAL.value] = -p.transfer_physical_to_base
        
        # PHYSICAL → UPPER (疲労が思考を鈍化)
        matrix[HumanLayer.UPPER.value][HumanLayer.PHYSICAL.value] = -p.transfer_physical_to_upper
        
        return matrix
    
    def _compute_interlayer_transfer(self) -> np.ndarray:
        """
        [Phase 3] 層間転送の計算
        
        Returns:
            各層へのエネルギー転送量（4次元ベクトル）
        """
        transfer = np.zeros(4)
        
        for i in range(4):
            for j in range(4):
                if i != j:
                    # j層からi層への転送
                    transfer[i] += self.interlayer_matrix[i][j] * self.state.E[j]
        
        return transfer
    
    def step(self, pressure: HumanPressure, dt: float = 0.1) -> None:
        """
        1ステップ実行
        
        Args:
            pressure: 人間特化の意味圧入力
            dt: 時間刻み
        """
        # 圧力をベクトルに変換
        p_vector = pressure.to_vector()
        
        # 層間転送計算
        interlayer_transfer = self._compute_interlayer_transfer()
        
        # エンジンで状態更新
        self.state = self.engine.step(
            self.state,
            p_vector,
            dt=dt,
            interlayer_transfer=interlayer_transfer
        )
    
    def get_dominant_layer(self) -> HumanLayer:
        """最も影響力の高い層を返す"""
        # ダミー圧力（構造的影響力計算のため）
        p_dummy = np.ones(4)
        dominant_idx = self.engine.get_dominant_layer(self.state, p_dummy)
        return HumanLayer(dominant_idx)
    
    def get_psychological_state(self) -> Dict[str, any]:
        """
        心理状態の人間可読な解釈を返す
        
        Returns:
            各層のエネルギー・κ・解釈を含む辞書
        """
        dominant = self.get_dominant_layer()
        
        # 各層の解釈
        interpretations = {
            HumanLayer.PHYSICAL: self._interpret_physical(),
            HumanLayer.BASE: self._interpret_base(),
            HumanLayer.CORE: self._interpret_core(),
            HumanLayer.UPPER: self._interpret_upper()
        }
        
        return {
            "agent_id": self.agent_id,
            "time": self.state.t,
            "dominant_layer": dominant.name,
            "energies": {
                "PHYSICAL": self.state.E[0],
                "BASE": self.state.E[1],
                "CORE": self.state.E[2],
                "UPPER": self.state.E[3]
            },
            "kappas": {
                "PHYSICAL": self.state.kappa[0],
                "BASE": self.state.kappa[1],
                "CORE": self.state.kappa[2],
                "UPPER": self.state.kappa[3]
            },
            "interpretations": interpretations,
            "leap_history": [(t, self._convert_leap_type(lt)) for t, lt in self.state.leap_history]
        }
    
    def _interpret_physical(self) -> str:
        """PHYSICAL層の心理的解釈"""
        E = self.state.E[0]
        if E > 150:
            return "極度の疲労・物理的限界"
        elif E > 80:
            return "かなりの疲労感"
        elif E > 40:
            return "軽い疲れ"
        else:
            return "良好な体調"
    
    def _interpret_base(self) -> str:
        """BASE層の心理的解釈"""
        E = self.state.E[1]
        if E > 80:
            return "本能的不満が爆発寸前"
        elif E > 50:
            return "強い欲求・不安"
        elif E > 25:
            return "軽い不満"
        else:
            return "本能的に満たされている"
    
    def _interpret_core(self) -> str:
        """CORE層の心理的解釈"""
        E = self.state.E[2]
        if E > 40:
            return "規範との激しい葛藤"
        elif E > 25:
            return "義務感によるストレス"
        elif E > 15:
            return "軽い罪悪感"
        else:
            return "規範に整合している"
    
    def _interpret_upper(self) -> str:
        """UPPER層の心理的解釈"""
        E = self.state.E[3]
        if E > 25:
            return "価値観の崩壊寸前"
        elif E > 18:
            return "信念の揺らぎ"
        elif E > 10:
            return "軽い違和感"
        else:
            return "理念に整合している"
    
    def _convert_leap_type(self, leap_type: LeapType) -> HumanLeapType:
        """汎用LeapTypeを人間特化LeapTypeに変換"""
        mapping = {
            LeapType.NO_LEAP: HumanLeapType.NO_LEAP,
            LeapType.LEAP_LAYER_1: HumanLeapType.LEAP_PHYSICAL,
            LeapType.LEAP_LAYER_2: HumanLeapType.LEAP_BASE,
            LeapType.LEAP_LAYER_3: HumanLeapType.LEAP_CORE,
            LeapType.LEAP_LAYER_4: HumanLeapType.LEAP_UPPER
        }
        return mapping.get(leap_type, HumanLeapType.NO_LEAP)
    
    def __repr__(self):
        state = self.get_psychological_state()
        return (f"HumanAgent({self.agent_id})\n"
                f"  Dominant: {state['dominant_layer']}\n"
                f"  E_physical={state['energies']['PHYSICAL']:.1f}, "
                f"E_base={state['energies']['BASE']:.1f}, "
                f"E_core={state['energies']['CORE']:.1f}, "
                f"E_upper={state['energies']['UPPER']:.1f}")


# ============================================================================
# 神経物質マッピング（オプション機能）
# ============================================================================

class NeurotransmitterMapper:
    """
    神経物質力学モデル（原典より）
    
    SSD層と神経物質の対応:
    - Dopamine: 跳躍のイニシエーター
    - Serotonin: 整合のスタビライザー
    - Cortisol: 臨界の警報
    - Noradrenaline: 跳躍のアクセル
    """
    
    @staticmethod
    def estimate_dopamine(agent: HumanAgent) -> float:
        """
        Dopamine推定（跳躍可能性と相関）
        
        跳躍直前にスパイク
        """
        total_E = np.sum(agent.state.E)
        avg_theta = np.mean(agent.params.to_core_params().Theta_values)
        
        # E/Theta比率でDopamineを推定
        return min(1.0, total_E / avg_theta)
    
    @staticmethod
    def estimate_serotonin(agent: HumanAgent) -> float:
        """
        Serotonin推定（整合状態と相関）
        
        低エネルギー・高κで高値
        """
        avg_E = np.mean(agent.state.E)
        avg_kappa = np.mean(agent.state.kappa)
        
        # 整合状態: 低E、高κ
        serotonin = (1.0 - avg_E / 100.0) * avg_kappa
        return np.clip(serotonin, 0.0, 1.0)
    
    @staticmethod
    def estimate_cortisol(agent: HumanAgent) -> float:
        """
        Cortisol推定（ストレス・臨界と相関）
        
        高エネルギーで高値
        """
        total_E = np.sum(agent.state.E)
        return min(1.0, total_E / 200.0)
