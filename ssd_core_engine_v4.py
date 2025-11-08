"""
SSD Core Engine v4.0: 四層構造エネルギー・整合慣性分離版

v3.5からv4.0への理論的跳躍:
================================

v3.5の限界:
----------
- E_indirect（間接エネルギー）が単一プール
  → BASE層の「本能的不満」とUPPER層の「理念的不満」を区別できない
- kappa（整合慣性）が単一スカラ値
  → 本能的学習と理念的学習を区別できない

v4.0の革新:
----------
1. エネルギーの層別分離:
   E_indirect → E_base + E_core + E_upper
   - E_base: 本能的不満（恐怖、飢餓、生存圧の未処理残渣）
   - E_core: 規範的不満（役割不全、疎外、システムへの不適合）
   - E_upper: 理念的不満（戦略破綻、意味喪失、物語の崩壊）

2. 整合慣性の層別分離:
   kappa → kappa_base + kappa_core + kappa_upper
   - kappa_base: 本能的学習（速く学習、強固、動かしにくい）
   - kappa_core: 規範的学習（中速学習、中強度）
   - kappa_upper: 理念的学習（遅く学習、柔軟、動かしやすい）

3. 層別跳躍閾値:
   各層が独立した臨界値を持つ
   - E_base > Theta_base → 衝動的跳躍（パニック、逃走、攻撃）
   - E_upper > Theta_upper → 計画的跳躍（革命、メタ戦略、ルールブレイク）

4. R値（動かしにくさ）との対応:
   kappa × R = 構造的抵抗
   - BASE: kappa_base(大) × R(100.0) = 最も動かしにくい
   - UPPER: kappa_upper(小) × R(1.0) = 最も動かしやすい

理論的意義:
----------
- 「恐怖は忘れにくく、理念は変わりやすい」を再現
- 異なるタイプの跳躍を区別可能
- 層間葛藤の解決を、E×κ×Rの多次元パワーバランスで決定可能
"""

import numpy as np
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, List, Tuple


class SSDDomain(Enum):
    """動作ドメイン"""
    DIRECT_ONLY = auto()     # 直接作用のみ
    INDIRECT_ONLY = auto()   # 間接作用のみ
    COUPLED = auto()         # 連成系（v3.5+）


class SSDLayer(Enum):
    """SSD人間モジュールの四層構造"""
    PHYSICAL = auto()  # 物理層（R→∞）
    BASE = auto()      # 基層（R=large）
    CORE = auto()      # 中核層（R=medium）
    UPPER = auto()     # 上層（R=small）


@dataclass
class SSDStateV4:
    """
    SSD状態ベクトル v4.0（層別E, κ対応）
    
    [v4新機能] 層別エネルギー:
    - E_direct: 直接作用エネルギー（物理的行動）
    - E_base: BASE層の未処理圧（本能的不満）
    - E_core: CORE層の未処理圧（規範的不満）
    - E_upper: UPPER層の未処理圧（理念的不満）
    
    [v4新機能] 層別整合慣性:
    - kappa_base: 本能的学習の強度（速く学習、強固）
    - kappa_core: 規範的学習の強度（中速学習）
    - kappa_upper: 理念的学習の強度（遅く学習、柔軟）
    """
    # エネルギー（層別）
    E_direct: float = 0.0       # 直接作用エネルギー
    E_base: float = 0.0         # BASE層エネルギー
    E_core: float = 0.0         # CORE層エネルギー
    E_upper: float = 0.0        # UPPER層エネルギー
    
    # 整合慣性（層別）
    kappa_base: float = 1.0     # BASE層整合慣性
    kappa_core: float = 1.0     # CORE層整合慣性
    kappa_upper: float = 1.0    # UPPER層整合慣性
    
    # 直接作用・間接作用の力
    F_direct: np.ndarray = field(default_factory=lambda: np.zeros(3))
    p_base: np.ndarray = field(default_factory=lambda: np.zeros(3))
    p_core: np.ndarray = field(default_factory=lambda: np.zeros(3))
    p_upper: np.ndarray = field(default_factory=lambda: np.zeros(3))
    
    # 反力（整合作用）
    j_direct: np.ndarray = field(default_factory=lambda: np.zeros(3))
    j_base: np.ndarray = field(default_factory=lambda: np.zeros(3))
    j_core: np.ndarray = field(default_factory=lambda: np.zeros(3))
    j_upper: np.ndarray = field(default_factory=lambda: np.zeros(3))
    
    # [v4] 層別の臨界フラグ
    is_critical_base: bool = False
    is_critical_core: bool = False
    is_critical_upper: bool = False
    
    # [v4] 層別のエネルギーフロー（診断用）
    E_base_flow: float = 0.0
    E_core_flow: float = 0.0
    E_upper_flow: float = 0.0
    E_direct_flow: float = 0.0
    
    # [v4] 層別の変換量（診断用）
    conversion_base2d: float = 0.0  # BASE→direct変換
    conversion_core2d: float = 0.0  # CORE→direct変換
    conversion_upper2d: float = 0.0 # UPPER→direct変換
    conversion_d2base: float = 0.0  # direct→BASE変換
    conversion_d2core: float = 0.0  # direct→CORE変換
    conversion_d2upper: float = 0.0 # direct→UPPER変換


@dataclass
class SSDParametersV4:
    """
    SSD Engine v4.0 パラメータ
    
    [v4新機能] 層別パラメータ:
    - 各層が独立した変換係数、減衰率、臨界値を持つ
    """
    # 層別変換係数（間接→直接）
    gamma_base2d: float = 0.08   # BASE→direct（本能は強く変換）
    gamma_core2d: float = 0.05   # CORE→direct
    gamma_upper2d: float = 0.03  # UPPER→direct（理念は弱く変換）
    
    # 層別変換係数（直接→間接）
    gamma_d2base: float = 0.03   # direct→BASE（本能は影響を受けにくい）
    gamma_d2core: float = 0.02   # direct→CORE
    gamma_d2upper: float = 0.04  # direct→UPPER（理念は影響を受けやすい）
    
    # 層別臨界閾値
    Theta_base: float = 150.0    # BASE層臨界（高い：本能は我慢できる）
    Theta_core: float = 100.0    # CORE層臨界（中程度）
    Theta_upper: float = 80.0    # UPPER層臨界（低い：理念は脆い）
    
    # 層別減衰率
    beta_base: float = 0.005     # BASE層減衰（遅い：本能は忘れにくい）
    beta_core: float = 0.01      # CORE層減衰（中程度）
    beta_upper: float = 0.02     # UPPER層減衰（速い：理念は忘れやすい）
    
    # 層別整合慣性学習速度
    eta_base: float = 0.8        # BASE層学習速度（速い）
    eta_core: float = 0.5        # CORE層学習速度（中程度）
    eta_upper: float = 0.3       # UPPER層学習速度（遅い）
    
    # 共通パラメータ
    alpha_d: float = 1.0         # 直接行動の生産係数
    alpha_base: float = 1.0      # BASE層生産係数
    alpha_core: float = 1.0      # CORE層生産係数
    alpha_upper: float = 1.0     # UPPER層生産係数
    
    rho_d: float = 0.1           # 直接反力の減衰
    rho_base: float = 0.1        # BASE層反力減衰
    rho_core: float = 0.1        # CORE層反力減衰
    rho_upper: float = 0.1       # UPPER層反力減衰
    
    lambda_base: float = 0.05    # BASE層κ減衰
    lambda_core: float = 0.05    # CORE層κ減衰
    lambda_upper: float = 0.05   # UPPER層κ減衰
    
    kappa_min_base: float = 0.8  # BASE層κ最小値（高い：本能は強固）
    kappa_min_core: float = 0.5  # CORE層κ最小値（中程度）
    kappa_min_upper: float = 0.3 # UPPER層κ最小値（低い：理念は柔軟）
    
    # 相転移制御
    enable_phase_transition: bool = True
    phase_transition_multiplier_base: float = 15.0   # BASE層相転移強度（強い）
    phase_transition_multiplier_core: float = 10.0   # CORE層相転移強度
    phase_transition_multiplier_upper: float = 8.0   # UPPER層相転移強度（弱い）
    
    # エネルギーリザーバ
    reservoir_capacity: float = 1000.0
    
    # 動作モード
    use_direct_action: bool = True
    use_indirect_action: bool = True


class SSDCoreEngineV4:
    """
    SSD Core Engine v4.0: 四層構造エネルギー・整合慣性分離版
    
    主要機能:
    1. E_base, E_core, E_upper の独立管理
    2. kappa_base, kappa_core, kappa_upper の独立学習
    3. 層別の臨界判定と相転移
    4. 層別の変換係数による異なる跳躍ダイナミクス
    """
    
    def __init__(self, params: SSDParametersV4):
        self.params = params
        self.domain = SSDDomain.COUPLED
        self.reservoir_E = params.reservoir_capacity
        self.time = 0.0
        
        # 統計（層別）
        self.total_conversion_base2d = 0.0
        self.total_conversion_core2d = 0.0
        self.total_conversion_upper2d = 0.0
        self.total_conversion_d2base = 0.0
        self.total_conversion_d2core = 0.0
        self.total_conversion_d2upper = 0.0
        self.total_decay_base = 0.0
        self.total_decay_core = 0.0
        self.total_decay_upper = 0.0
        
    def step(
        self,
        state: SSDStateV4,
        p_external_base: np.ndarray,
        p_external_core: np.ndarray,
        p_external_upper: np.ndarray,
        dt: float,
        contact_pressure: Optional[np.ndarray] = None
    ) -> SSDStateV4:
        """
        1ステップの時間積分（層別エネルギー・整合慣性対応）
        
        Parameters:
        -----------
        state: SSDStateV4
            現在の状態
        p_external_base: np.ndarray
            BASE層への外部圧力
        p_external_core: np.ndarray
            CORE層への外部圧力
        p_external_upper: np.ndarray
            UPPER層への外部圧力
        dt: float
            時間刻み
        contact_pressure: Optional[np.ndarray]
            直接接触圧力
            
        Returns:
        --------
        state: SSDStateV4
            更新された状態
        """
        
        # 1. 直接作用の計算
        if self.params.use_direct_action and contact_pressure is not None:
            state.F_direct = contact_pressure.copy()
        else:
            state.F_direct = np.zeros(3)
        
        # 2. 層別間接作用の設定
        state.p_base = p_external_base.copy()
        state.p_core = p_external_core.copy()
        state.p_upper = p_external_upper.copy()
        
        # 3. 層別反力の計算（整合作用）
        state.j_direct = state.kappa_base * state.F_direct  # 物理は主にBASE層が反応
        state.j_base = state.kappa_base * state.p_base
        state.j_core = state.kappa_core * state.p_core
        state.j_upper = state.kappa_upper * state.p_upper
        
        # 4. 層別エネルギー生産（圧力 - 反力の正部分）
        p_d_mag = np.linalg.norm(state.F_direct)
        j_d_mag = np.linalg.norm(state.j_direct)
        E_direct_production = self.params.alpha_d * max(0, p_d_mag - j_d_mag)
        
        p_base_mag = np.linalg.norm(state.p_base)
        j_base_mag = np.linalg.norm(state.j_base)
        E_base_production = self.params.alpha_base * max(0, p_base_mag - j_base_mag)
        
        p_core_mag = np.linalg.norm(state.p_core)
        j_core_mag = np.linalg.norm(state.j_core)
        E_core_production = self.params.alpha_core * max(0, p_core_mag - j_core_mag)
        
        p_upper_mag = np.linalg.norm(state.p_upper)
        j_upper_mag = np.linalg.norm(state.j_upper)
        E_upper_production = self.params.alpha_upper * max(0, p_upper_mag - j_upper_mag)
        
        # 5. 層別整合慣性の更新
        dkappa_base = (self.params.eta_base * (p_base_mag * j_base_mag - self.params.rho_base * j_base_mag**2) -
                       self.params.lambda_base * (state.kappa_base - self.params.kappa_min_base))
        state.kappa_base += dkappa_base * dt
        state.kappa_base = max(self.params.kappa_min_base, state.kappa_base)
        
        dkappa_core = (self.params.eta_core * (p_core_mag * j_core_mag - self.params.rho_core * j_core_mag**2) -
                       self.params.lambda_core * (state.kappa_core - self.params.kappa_min_core))
        state.kappa_core += dkappa_core * dt
        state.kappa_core = max(self.params.kappa_min_core, state.kappa_core)
        
        dkappa_upper = (self.params.eta_upper * (p_upper_mag * j_upper_mag - self.params.rho_upper * j_upper_mag**2) -
                        self.params.lambda_upper * (state.kappa_upper - self.params.kappa_min_upper))
        state.kappa_upper += dkappa_upper * dt
        state.kappa_upper = max(self.params.kappa_min_upper, state.kappa_upper)
        
        # 6. [v4核心機能] 層別の相転移判定
        gamma_base2d = self.params.gamma_base2d
        gamma_core2d = self.params.gamma_core2d
        gamma_upper2d = self.params.gamma_upper2d
        
        state.is_critical_base = False
        state.is_critical_core = False
        state.is_critical_upper = False
        
        if self.params.enable_phase_transition:
            # BASE層臨界判定
            if state.E_base < self.params.Theta_base:
                gamma_base2d *= self.params.phase_transition_multiplier_base
                state.is_critical_base = True
            
            # CORE層臨界判定
            if state.E_core < self.params.Theta_core:
                gamma_core2d *= self.params.phase_transition_multiplier_core
                state.is_critical_core = True
            
            # UPPER層臨界判定
            if state.E_upper < self.params.Theta_upper:
                gamma_upper2d *= self.params.phase_transition_multiplier_upper
                state.is_critical_upper = True
        
        # 7. [v4核心機能] 層別の連成変換
        # 間接→直接変換（各層から物理行動へ）
        conversion_base2d = gamma_base2d * state.E_base
        conversion_core2d = gamma_core2d * state.E_core
        conversion_upper2d = gamma_upper2d * state.E_upper
        
        # 直接→間接変換（物理行動から各層へのフィードバック）
        conversion_d2base = self.params.gamma_d2base * state.E_direct
        conversion_d2core = self.params.gamma_d2core * state.E_direct
        conversion_d2upper = self.params.gamma_d2upper * state.E_direct
        
        # 8. 層別減衰
        decay_base = self.params.beta_base * state.E_base
        decay_core = self.params.beta_core * state.E_core
        decay_upper = self.params.beta_upper * state.E_upper
        
        # 9. [v4核心機能] 層別エネルギー微分方程式
        # dE_base: 本能的不満の変化
        dE_base = E_base_production - conversion_base2d + conversion_d2base - decay_base
        
        # dE_core: 規範的不満の変化
        dE_core = E_core_production - conversion_core2d + conversion_d2core - decay_core
        
        # dE_upper: 理念的不満の変化
        dE_upper = E_upper_production - conversion_upper2d + conversion_d2upper - decay_upper
        
        # dE_direct: 直接行動エネルギーの変化
        dE_direct = (E_direct_production + 
                     conversion_base2d + conversion_core2d + conversion_upper2d -
                     conversion_d2base - conversion_d2core - conversion_d2upper)
        
        # 10. エネルギー更新
        state.E_base += dE_base * dt
        state.E_core += dE_core * dt
        state.E_upper += dE_upper * dt
        state.E_direct += dE_direct * dt
        
        # 負値防止
        state.E_base = max(0.0, state.E_base)
        state.E_core = max(0.0, state.E_core)
        state.E_upper = max(0.0, state.E_upper)
        state.E_direct = max(0.0, state.E_direct)
        
        # 11. 診断情報の記録
        state.E_base_flow = dE_base
        state.E_core_flow = dE_core
        state.E_upper_flow = dE_upper
        state.E_direct_flow = dE_direct
        
        state.conversion_base2d = conversion_base2d
        state.conversion_core2d = conversion_core2d
        state.conversion_upper2d = conversion_upper2d
        state.conversion_d2base = conversion_d2base
        state.conversion_d2core = conversion_d2core
        state.conversion_d2upper = conversion_d2upper
        
        # 12. 統計更新
        self.total_conversion_base2d += conversion_base2d * dt
        self.total_conversion_core2d += conversion_core2d * dt
        self.total_conversion_upper2d += conversion_upper2d * dt
        self.total_conversion_d2base += conversion_d2base * dt
        self.total_conversion_d2core += conversion_d2core * dt
        self.total_conversion_d2upper += conversion_d2upper * dt
        self.total_decay_base += decay_base * dt
        self.total_decay_core += decay_core * dt
        self.total_decay_upper += decay_upper * dt
        self.time += dt
        
        return state
    
    def get_total_energy(self, state: SSDStateV4) -> float:
        """総エネルギー"""
        return state.E_direct + state.E_base + state.E_core + state.E_upper
    
    def get_layer_energy_distribution(self, state: SSDStateV4) -> Dict[str, float]:
        """層別エネルギー分布"""
        total = self.get_total_energy(state)
        if total == 0:
            return {
                'BASE': 0.0,
                'CORE': 0.0,
                'UPPER': 0.0,
                'DIRECT': 0.0
            }
        return {
            'BASE': state.E_base / total,
            'CORE': state.E_core / total,
            'UPPER': state.E_upper / total,
            'DIRECT': state.E_direct / total
        }
    
    def get_dominant_frustration_layer(self, state: SSDStateV4) -> Tuple[str, float]:
        """最も不満が蓄積している層を返す"""
        layers = {
            'BASE': state.E_base,
            'CORE': state.E_core,
            'UPPER': state.E_upper
        }
        dominant = max(layers.items(), key=lambda x: x[1])
        return dominant
    
    def get_structural_resistance(self, state: SSDStateV4) -> Dict[str, float]:
        """
        構造的抵抗 = kappa × R
        
        理論的意義:
        この値が高いほど、その層は「動かしにくい」
        """
        R_values = {
            'BASE': 100.0,
            'CORE': 10.0,
            'UPPER': 1.0
        }
        
        return {
            'BASE': state.kappa_base * R_values['BASE'],
            'CORE': state.kappa_core * R_values['CORE'],
            'UPPER': state.kappa_upper * R_values['UPPER']
        }


# ========================================
# デモ・テスト
# ========================================

if __name__ == "__main__":
    print("="*70)
    print("SSD Core Engine v4.0 - 層別E・κ分離デモ")
    print("="*70)
    
    params = SSDParametersV4()
    engine = SSDCoreEngineV4(params)
    
    # 初期状態
    state = SSDStateV4(
        E_direct=50.0,
        E_base=120.0,   # BASE層に不満が溜まっている
        E_core=80.0,
        E_upper=60.0,
        kappa_base=1.5,
        kappa_core=1.0,
        kappa_upper=0.5
    )
    
    print(f"\n[初期状態]")
    print(f"  E_direct: {state.E_direct:.1f}")
    print(f"  E_base: {state.E_base:.1f}")
    print(f"  E_core: {state.E_core:.1f}")
    print(f"  E_upper: {state.E_upper:.1f}")
    print(f"  kappa_base: {state.kappa_base:.2f}")
    print(f"  kappa_core: {state.kappa_core:.2f}")
    print(f"  kappa_upper: {state.kappa_upper:.2f}")
    
    # 構造的抵抗
    resistance = engine.get_structural_resistance(state)
    print(f"\n[構造的抵抗] (kappa × R)")
    for layer, r in resistance.items():
        print(f"  {layer}: {r:.1f}")
    
    # 圧力を加える（BASE層に強い圧力）
    print(f"\n[シミュレーション開始]")
    print(f"  BASE層に強い恐怖圧力を印加")
    
    for i in range(5):
        p_base = np.array([8.0, 0.0, 0.0])   # 強い恐怖
        p_core = np.array([3.0, 0.0, 0.0])   # 中程度の役割圧力
        p_upper = np.array([5.0, 0.0, 0.0])  # 中程度の理念圧力
        
        state = engine.step(state, p_base, p_core, p_upper, dt=1.0)
        
        print(f"\n  Step {i+1}:")
        print(f"    E_base: {state.E_base:.1f} {'[臨界!]' if state.is_critical_base else ''}")
        print(f"    E_core: {state.E_core:.1f} {'[臨界!]' if state.is_critical_core else ''}")
        print(f"    E_upper: {state.E_upper:.1f} {'[臨界!]' if state.is_critical_upper else ''}")
        print(f"    E_direct: {state.E_direct:.1f}")
        
        # 支配的な不満層
        dominant_layer, dominant_value = engine.get_dominant_frustration_layer(state)
        print(f"    支配的不満層: {dominant_layer} ({dominant_value:.1f})")
        
        if state.is_critical_base:
            print(f"    ⚠️ BASE層相転移! 本能的跳躍（パニック、逃走）")
        if state.is_critical_core:
            print(f"    ⚠️ CORE層相転移! 規範的跳躍（ルール破壊）")
        if state.is_critical_upper:
            print(f"    ⚠️ UPPER層相転移! 理念的跳躍（革命、メタ戦略）")
    
    print(f"\n[エネルギー分布]")
    distribution = engine.get_layer_energy_distribution(state)
    for layer, ratio in distribution.items():
        print(f"  {layer}: {ratio*100:.1f}%")
    
    print(f"\n[累積統計]")
    print(f"  BASE→direct変換: {engine.total_conversion_base2d:.1f}")
    print(f"  CORE→direct変換: {engine.total_conversion_core2d:.1f}")
    print(f"  UPPER→direct変換: {engine.total_conversion_upper2d:.1f}")
    print(f"  BASE層減衰: {engine.total_decay_base:.1f}")
    print(f"  CORE層減衰: {engine.total_decay_core:.1f}")
    print(f"  UPPER層減衰: {engine.total_decay_upper:.1f}")
    
    print("\n" + "="*70)
    print("✅ v4.0デモ完了")
    print("="*70)
    
    print("\n💡 v4.0の理論的成果:")
    print("  1. E層別分離 → 本能的不満と理念的不満を区別可能")
    print("  2. κ層別分離 → 本能的学習と理念的学習を区別可能")
    print("  3. 層別相転移 → 異なるタイプの跳躍を実装")
    print("  4. 構造的抵抗 → κ×Rで動かしにくさを定量化")
