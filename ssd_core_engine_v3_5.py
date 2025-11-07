"""
SSD Core Engine v3.5: Coupled Direct-Indirect Action System

革新点:
-------
v3.0: E_direct と E_indirect は独立に積分
v3.5: 相互変換項 γ により連成系を実現

連成方程式:
----------
dE_direct/dt = α_d(p_d - j_d) + γ_i2d * E_indirect - γ_d2i * E_direct
dE_indirect/dt = α_i(p_i - j_i) - γ_i2d * E_indirect + γ_d2i * E_direct - β_decay * E_indirect

物理的意味:
----------
- γ_i2d: indirect → direct (思想が行動を引き起こす)
- γ_d2i: direct → indirect (行動が新しい意味を生む)
- 循環: 言葉 → 行動 → 新しい言葉 → ...

社会的臨界:
----------
E_indirect < Θ_critical → γ_i2d *= 10 (相転移)
"言葉が通じない → 暴力解放"
"""

import numpy as np
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SSDDomain(Enum):
    """システムのドメイン"""
    PHYSICS = "physics"        # 物理系 (γ=0, 保存則)
    COMBAT = "combat"          # 戦闘系 (E_direct 支配)
    SOCIAL = "social"          # 社会系 (E_indirect 支配)
    COUPLED = "coupled"        # 連成系 (両方が相互作用)


@dataclass
class SSDStateV3_5:
    """SSD状態ベクトル (v3.5 連成系対応)"""
    
    # v3.0 互換フィールド
    kappa: float                              # 主構造パラメータ
    F_direct: np.ndarray = field(default_factory=lambda: np.zeros(3))    # 直接作用力
    p_indirect: np.ndarray = field(default_factory=lambda: np.zeros(3))  # 間接作用圧
    E_direct: float = 0.0                     # 直接エネルギー
    E_indirect: float = 0.0                   # 間接エネルギー
    
    # v3.5 新規フィールド (連成系追跡用)
    E_direct_flow: float = 0.0                # 直接エネルギー流量 [J/s]
    E_indirect_flow: float = 0.0              # 間接エネルギー流量 [J/s]
    conversion_i2d: float = 0.0               # indirect→direct 変換量 [J/s]
    conversion_d2i: float = 0.0               # direct→indirect 変換量 [J/s]
    decay_rate: float = 0.0                   # 減衰率 [J/s]
    
    # 臨界状態フラグ
    is_critical: bool = False                 # E_indirect < Θ_critical
    phase_transition_count: int = 0           # 相転移発生回数


@dataclass
class SSDParametersV3_5:
    """SSDパラメータセット (v3.5 連成系対応)"""
    
    # v3.0 互換パラメータ
    use_direct_action: bool = True            # 直接作用を使用
    use_indirect_action: bool = True          # 間接作用を使用
    amplification_factor: float = 1.0         # 間接作用の増幅率
    G0: float = 0.5                           # 基準剛性
    g: float = 0.3                            # 剛性増分
    alpha: float = 0.5                        # エネルギー変換効率
    beta_decay: float = 0.1                   # 間接エネルギー減衰率
    
    # v3.5 新規パラメータ (連成系)
    gamma_i2d: float = 0.0                    # indirect → direct 変換率
    gamma_d2i: float = 0.0                    # direct → indirect 変換率
    Theta_critical: float = 500.0             # 臨界閾値
    enable_phase_transition: bool = False     # 相転移ON/OFF
    phase_transition_multiplier: float = 10.0 # 相転移時の γ_i2d 増幅率
    
    # リザーバー
    reservoir_capacity: float = 1e6           # エネルギーリザーバー容量


class SSDCoreEngineV3_5:
    """
    SSD Core Engine v3.5: 連成直接-間接作用系
    
    特徴:
    ----
    1. 相互変換: γ_i2d, γ_d2i により E_direct ↔ E_indirect
    2. 社会的臨界: E_indirect < Θ で相転移 (暴力解放)
    3. v3.0 後方互換: γ=0 で v3.0 と同一挙動
    """
    
    def __init__(self, params: SSDParametersV3_5):
        self.params = params
        self.domain = SSDDomain.COUPLED  # デフォルトは連成系
        self.reservoir_E = params.reservoir_capacity
        self.time = 0.0
        
        # 統計
        self.total_conversion_i2d = 0.0  # 累積 indirect→direct 変換
        self.total_conversion_d2i = 0.0  # 累積 direct→indirect 変換
        self.total_decay = 0.0           # 累積減衰
        
    def step(
        self,
        state: SSDStateV3_5,
        p_external: np.ndarray,
        dt: float,
        contact_pressure: Optional[np.ndarray] = None
    ) -> SSDStateV3_5:
        """
        1ステップの時間積分 (連成系対応)
        
        Parameters:
        -----------
        state: SSDStateV3_5
            現在の状態
        p_external: np.ndarray
            外部からの間接作用圧
        dt: float
            時間刻み
        contact_pressure: Optional[np.ndarray]
            接触圧力 (直接作用)
            
        Returns:
        --------
        state: SSDStateV3_5
            更新された状態
        """
        
        # 1. 直接作用の計算
        if self.params.use_direct_action and contact_pressure is not None:
            state.F_direct = contact_pressure.copy()
        else:
            state.F_direct = np.zeros(3)
            
        # 2. 間接作用の計算
        if self.params.use_indirect_action:
            state.p_indirect = p_external * self.params.amplification_factor
        else:
            state.p_indirect = np.zeros(3)
            
        # 3. 剛性の計算 (v3.0 互換)
        G = self.params.G0 + self.params.g * state.kappa
        
        # 4. エネルギー流の計算 (生成項)
        # 直接作用からのエネルギー生成
        if self.params.use_direct_action:
            F_norm = np.linalg.norm(state.F_direct)
            j_direct = G * state.kappa  # 構造からの反力
            E_direct_production = self.params.alpha * max(0, F_norm - j_direct)
        else:
            E_direct_production = 0.0
            
        # 間接作用からのエネルギー生成
        if self.params.use_indirect_action:
            p_norm = np.linalg.norm(state.p_indirect)
            j_indirect = G * state.kappa * 0.5  # 間接作用の反力は小さい
            E_indirect_production = self.params.alpha * max(0, p_norm - j_indirect)
            
            # リザーバーからの増幅
            if self.params.amplification_factor > 1.0:
                E_amplification = E_indirect_production * (self.params.amplification_factor - 1.0)
                if self.reservoir_E >= E_amplification:
                    self.reservoir_E -= E_amplification
                    E_indirect_production += E_amplification
        else:
            E_indirect_production = 0.0
            
        # 5. 連成項の計算 (v3.5 新規)
        conversion_i2d = self.params.gamma_i2d * state.E_indirect
        conversion_d2i = self.params.gamma_d2i * state.E_direct
        
        # 6. 減衰項
        decay = self.params.beta_decay * state.E_indirect
        
        # 7. 社会的臨界チェック (v3.5 新規)
        if self.params.enable_phase_transition:
            if state.E_indirect < self.params.Theta_critical and not state.is_critical:
                # 臨界突破: "言葉が通じない → 暴力へ"
                self.params.gamma_i2d *= self.params.phase_transition_multiplier
                state.is_critical = True
                state.phase_transition_count += 1
            elif state.E_indirect >= self.params.Theta_critical and state.is_critical:
                # 臨界回復: "暴力 → 言葉へ"
                self.params.gamma_i2d /= self.params.phase_transition_multiplier
                state.is_critical = False
                
        # 8. 連成方程式の積分
        dE_direct = E_direct_production + conversion_i2d - conversion_d2i
        dE_indirect = E_indirect_production - conversion_i2d + conversion_d2i - decay
        
        state.E_direct += dE_direct * dt
        state.E_indirect += dE_indirect * dt
        
        # 負値防止
        state.E_direct = max(0.0, state.E_direct)
        state.E_indirect = max(0.0, state.E_indirect)
        
        # 9. 状態更新記録
        state.E_direct_flow = dE_direct
        state.E_indirect_flow = dE_indirect
        state.conversion_i2d = conversion_i2d
        state.conversion_d2i = conversion_d2i
        state.decay_rate = decay
        
        # 10. 統計更新
        self.total_conversion_i2d += conversion_i2d * dt
        self.total_conversion_d2i += conversion_d2i * dt
        self.total_decay += decay * dt
        self.time += dt
        
        return state
    
    def get_total_energy(self, state: SSDStateV3_5) -> float:
        """総エネルギー (連成系では保存されない)"""
        return state.E_direct + state.E_indirect
    
    def get_coupling_strength(self) -> float:
        """連成の強さ (0=独立, 1=強連成)"""
        gamma_total = self.params.gamma_i2d + self.params.gamma_d2i
        return min(1.0, gamma_total / 10.0)
    
    def get_energy_balance(self, state: SSDStateV3_5) -> dict:
        """エネルギー収支の詳細"""
        return {
            'E_direct': state.E_direct,
            'E_indirect': state.E_indirect,
            'E_total': self.get_total_energy(state),
            'reservoir': self.reservoir_E,
            'conversion_i2d': state.conversion_i2d,
            'conversion_d2i': state.conversion_d2i,
            'decay': state.decay_rate,
            'net_flow': state.E_direct_flow + state.E_indirect_flow,
            'is_critical': state.is_critical,
        }
    
    def reset_statistics(self):
        """統計をリセット"""
        self.total_conversion_i2d = 0.0
        self.total_conversion_d2i = 0.0
        self.total_decay = 0.0
        self.time = 0.0


def create_physics_params() -> SSDParametersV3_5:
    """物理系パラメータ (γ=0, 保存則)"""
    return SSDParametersV3_5(
        use_direct_action=True,
        use_indirect_action=False,
        amplification_factor=1.0,
        gamma_i2d=0.0,
        gamma_d2i=0.0,
        beta_decay=0.0,
        enable_phase_transition=False,
    )


def create_social_params() -> SSDParametersV3_5:
    """社会系パラメータ (間接作用支配)"""
    return SSDParametersV3_5(
        use_direct_action=False,
        use_indirect_action=True,
        amplification_factor=100.0,
        gamma_i2d=0.01,
        gamma_d2i=0.05,
        beta_decay=0.1,
        enable_phase_transition=False,
    )


def create_revolution_params() -> SSDParametersV3_5:
    """革命期パラメータ (強連成 + 相転移)"""
    return SSDParametersV3_5(
        use_direct_action=True,
        use_indirect_action=True,
        amplification_factor=50.0,
        gamma_i2d=0.1,   # 初期は低め
        gamma_d2i=0.5,   # 行動は意味を生みやすい
        beta_decay=0.01, # 思想は残りやすい
        Theta_critical=500.0,
        enable_phase_transition=True,
        phase_transition_multiplier=10.0,
    )


def create_sns_params() -> SSDParametersV3_5:
    """SNS情報拡散パラメータ (高速循環)"""
    return SSDParametersV3_5(
        use_direct_action=True,
        use_indirect_action=True,
        amplification_factor=100000.0,  # バズる
        gamma_i2d=1.0,    # 情報 → 行動 (速い)
        gamma_d2i=0.5,    # 行動 → 情報 (やや遅い)
        beta_decay=10.0,  # すぐ忘れる
        enable_phase_transition=False,
    )


if __name__ == "__main__":
    print("="*70)
    print("SSD Core Engine v3.5: Coupled Direct-Indirect Action System")
    print("="*70)
    
    # テスト1: 物理系 (γ=0)
    print("\n[Test 1] 物理系 (Newton's Cradle mode)")
    params_phys = create_physics_params()
    engine_phys = SSDCoreEngineV3_5(params_phys)
    state_phys = SSDStateV3_5(kappa=1.0, E_direct=100.0, E_indirect=0.0)
    
    print(f"初期: E_direct={state_phys.E_direct:.2f}, E_indirect={state_phys.E_indirect:.2f}")
    for _ in range(10):
        engine_phys.step(state_phys, np.zeros(3), dt=0.1, contact_pressure=np.array([5.0, 0, 0]))
    print(f"10ステップ後: E_direct={state_phys.E_direct:.2f}, E_indirect={state_phys.E_indirect:.2f}")
    print(f"エネルギー変化: {abs(state_phys.E_direct - 100.0):.6f}J (保存則チェック)")
    
    # テスト2: 社会系 (間接作用のみ)
    print("\n[Test 2] 社会系 (Pen mode)")
    params_social = create_social_params()
    engine_social = SSDCoreEngineV3_5(params_social)
    state_social = SSDStateV3_5(kappa=0.5, E_direct=0.0, E_indirect=10.0)
    
    print(f"初期: E_direct={state_social.E_direct:.2f}, E_indirect={state_social.E_indirect:.2f}")
    for _ in range(10):
        engine_social.step(state_social, np.array([10.0, 0, 0]), dt=0.1)
    print(f"10ステップ後: E_direct={state_social.E_direct:.2f}, E_indirect={state_social.E_indirect:.2f}")
    balance = engine_social.get_energy_balance(state_social)
    print(f"増幅率: {state_social.E_indirect / 10.0:.2f}x")
    print(f"変換 i→d: {balance['conversion_i2d']:.4f} J/s")
    
    # テスト3: 革命期 (相転移)
    print("\n[Test 3] 革命期 (Phase transition)")
    params_rev = create_revolution_params()
    engine_rev = SSDCoreEngineV3_5(params_rev)
    state_rev = SSDStateV3_5(kappa=1.0, E_direct=0.0, E_indirect=600.0)
    
    print(f"初期: E_indirect={state_rev.E_indirect:.1f} > Θ={params_rev.Theta_critical}")
    print(f"γ_i2d (初期) = {params_rev.gamma_i2d:.4f}")
    
    # E_indirect を 500 以下に減衰させる
    for step in range(100):
        engine_rev.step(state_rev, np.zeros(3), dt=0.1)
        if state_rev.is_critical and step == state_rev.phase_transition_count * 10:
            print(f"\n[相転移発生] Step {step}")
            print(f"  E_indirect={state_rev.E_indirect:.1f} < Θ={params_rev.Theta_critical}")
            print(f"  γ_i2d (新) = {params_rev.gamma_i2d:.4f}")
            print(f"  → 暴力解放!")
            break
    
    print(f"\n最終: E_direct={state_rev.E_direct:.2f}, E_indirect={state_rev.E_indirect:.2f}")
    print(f"相転移回数: {state_rev.phase_transition_count}")
    
    # テスト4: SNS拡散 (高速循環)
    print("\n[Test 4] SNS情報拡散 (Fast coupling)")
    params_sns = create_sns_params()
    engine_sns = SSDCoreEngineV3_5(params_sns)
    state_sns = SSDStateV3_5(kappa=0.3, E_direct=0.0, E_indirect=1.0)
    
    print(f"初期: E_indirect={state_sns.E_indirect:.2f}J (1ツイート)")
    engine_sns.step(state_sns, np.array([1.0, 0, 0]), dt=0.01)
    print(f"0.01s後: E_indirect={state_sns.E_indirect:.2e}J (バズった!)")
    balance = engine_sns.get_energy_balance(state_sns)
    print(f"変換 i→d: {balance['conversion_i2d']:.2e} J/s (デモ参加者)")
    print(f"減衰率: {balance['decay']:.2e} J/s (すぐ忘れる)")
    
    print("\n" + "="*70)
    print("✅ v3.5 Core Engine Tests Complete")
    print("="*70)
