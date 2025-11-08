"""
非線形層間転送システム (Nonlinear Interlayer Transfer)
======================================================

Phase 3の理論的整合を高めるための、非線形層間転送実装。

核心原理:
- 転送量は転送元（E_source）だけでなく、転送先（E_target）にも依存
- 例: 理念による本能の抑制は、本能が強すぎると効かなくなる
- 例: 本能から規範への転送は、規範エネルギーが飽和すると減少

v5/v6との違い:
- v5: transfer = matrix[i][j] * E[j] (線形)
- v7: transfer = f(E_source, E_target, κ_source, κ_target) (非線形)
"""

from dataclasses import dataclass
from typing import Callable, Optional
import numpy as np

from ssd_human_module import HumanLayer


@dataclass
class NonlinearTransferFunction:
    """非線形転送関数の定義
    
    Args:
        source_layer: 転送元の層
        target_layer: 転送先の層
        base_coefficient: 基本係数（v5のmatrix[i][j]相当）
        transfer_function: 転送量計算関数
        description: 説明
    """
    source_layer: HumanLayer
    target_layer: HumanLayer
    base_coefficient: float
    transfer_function: Callable[[float, float, float, float], float]
    description: str


class NonlinearInterlayerTransfer:
    """非線形層間転送システム
    
    v5の線形モデルを拡張し、転送元・転送先の両方のエネルギーと
    整合慣性（κ）に依存する非線形モデルを実装
    """
    
    def __init__(self):
        """初期化"""
        self.transfer_functions: list[NonlinearTransferFunction] = []
        
        # デフォルトの非線形転送関数を登録
        self._register_default_functions()
    
    def _register_default_functions(self):
        """デフォルトの非線形転送関数を登録"""
        
        # 1. UPPER → BASE: 理念による本能の抑制（飽和抑制）
        self.transfer_functions.append(
            NonlinearTransferFunction(
                source_layer=HumanLayer.UPPER,
                target_layer=HumanLayer.BASE,
                base_coefficient=-0.15,  # 負 = 抑制
                transfer_function=self._saturating_suppression,
                description="理念による本能の抑制（本能が強すぎると効かない）"
            )
        )
        
        # 2. BASE → CORE: 本能から規範への転送（飽和転送）
        self.transfer_functions.append(
            NonlinearTransferFunction(
                source_layer=HumanLayer.BASE,
                target_layer=HumanLayer.CORE,
                base_coefficient=0.1,
                transfer_function=self._saturating_transfer,
                description="本能→規範（規範が飽和すると転送量減少）"
            )
        )
        
        # 3. CORE → BASE: 規範による本能の抑制（κ依存）
        self.transfer_functions.append(
            NonlinearTransferFunction(
                source_layer=HumanLayer.CORE,
                target_layer=HumanLayer.BASE,
                base_coefficient=-0.1,
                transfer_function=self._kappa_weighted_suppression,
                description="規範による本能の抑制（κ_coreが高いほど効果的）"
            )
        )
        
        # 4. CORE → UPPER: 規範から理念への転送（促進転送）
        self.transfer_functions.append(
            NonlinearTransferFunction(
                source_layer=HumanLayer.CORE,
                target_layer=HumanLayer.UPPER,
                base_coefficient=0.08,
                transfer_function=self._facilitative_transfer,
                description="規範→理念（両方のκが高いほど促進）"
            )
        )
        
        # 5. UPPER → CORE: 理念から規範への転送（強化転送）
        self.transfer_functions.append(
            NonlinearTransferFunction(
                source_layer=HumanLayer.UPPER,
                target_layer=HumanLayer.CORE,
                base_coefficient=0.05,
                transfer_function=self._reinforcement_transfer,
                description="理念→規範（理念が強いほど規範を強化）"
            )
        )
        
        # 6. BASE → PHYSICAL: 本能から身体への転送（疲労依存）
        self.transfer_functions.append(
            NonlinearTransferFunction(
                source_layer=HumanLayer.BASE,
                target_layer=HumanLayer.PHYSICAL,
                base_coefficient=0.05,
                transfer_function=self._fatigue_dependent_transfer,
                description="本能→身体（身体が疲労すると転送量増加）"
            )
        )
        
        # 7. PHYSICAL → BASE: 身体から本能への転送（痛覚転送）
        self.transfer_functions.append(
            NonlinearTransferFunction(
                source_layer=HumanLayer.PHYSICAL,
                target_layer=HumanLayer.BASE,
                base_coefficient=0.2,
                transfer_function=self._pain_transfer,
                description="身体→本能（身体的苦痛が本能的恐怖を引き起こす）"
            )
        )
        
        # 8. UPPER → UPPER: 自己反省（自己抑制）
        self.transfer_functions.append(
            NonlinearTransferFunction(
                source_layer=HumanLayer.UPPER,
                target_layer=HumanLayer.UPPER,
                base_coefficient=-0.03,
                transfer_function=self._self_reflection,
                description="自己反省（理念が高まると自己抑制が働く）"
            )
        )
    
    def compute_transfer(
        self,
        E: np.ndarray,
        kappa: np.ndarray,
        dt: float = 0.1
    ) -> np.ndarray:
        """非線形層間転送を計算
        
        Args:
            E: エネルギーベクトル [E_physical, E_base, E_core, E_upper]
            kappa: 整合慣性ベクトル [κ_physical, κ_base, κ_core, κ_upper]
            dt: 時間刻み
            
        Returns:
            転送量ベクトル [transfer_physical, transfer_base, transfer_core, transfer_upper]
        """
        transfer = np.zeros(4)
        
        for func_def in self.transfer_functions:
            src_idx = func_def.source_layer.value
            tgt_idx = func_def.target_layer.value
            
            E_source = E[src_idx]
            E_target = E[tgt_idx]
            kappa_source = kappa[src_idx]
            kappa_target = kappa[tgt_idx]
            
            # 非線形転送量を計算
            transfer_amount = func_def.transfer_function(
                E_source, E_target, kappa_source, kappa_target
            )
            
            # 基本係数とdtを適用
            transfer[tgt_idx] += func_def.base_coefficient * transfer_amount * dt
        
        return transfer
    
    # ========================================
    # 非線形転送関数群
    # ========================================
    
    def _saturating_suppression(
        self,
        E_source: float,
        E_target: float,
        kappa_source: float,
        kappa_target: float
    ) -> float:
        """飽和抑制関数
        
        E_sourceが高いほど抑制力が強いが、E_targetが極端に高いと
        抑制が効かなくなる（飽和）
        
        例: 理念（UPPER）による本能（BASE）の抑制
        """
        # 抑制力: E_source に比例
        suppression_power = E_source * kappa_source
        
        # 抵抗力: E_target が高いほど抑制が効きにくい
        resistance = 1.0 + E_target / 10.0
        
        # 飽和抑制
        effective_suppression = suppression_power / resistance
        
        return effective_suppression
    
    def _saturating_transfer(
        self,
        E_source: float,
        E_target: float,
        kappa_source: float,
        kappa_target: float
    ) -> float:
        """飽和転送関数
        
        E_targetが飽和すると、転送量が減少する
        
        例: 本能（BASE）→ 規範（CORE）の転送
        """
        # 転送力: E_source に比例
        transfer_power = E_source
        
        # 飽和度: E_target が高いほど受け入れにくい
        saturation_factor = 1.0 / (1.0 + E_target / 50.0)
        
        # 受容性: κ_target が高いほど受け入れやすい
        receptivity = kappa_target / 2.0
        
        return transfer_power * saturation_factor * receptivity
    
    def _kappa_weighted_suppression(
        self,
        E_source: float,
        E_target: float,
        kappa_source: float,
        kappa_target: float
    ) -> float:
        """κ重み付き抑制関数
        
        κ_sourceが高いほど抑制力が強い
        
        例: 規範（CORE）による本能（BASE）の抑制
        """
        # κが高い = 構造が強固 = 抑制力が強い
        suppression_strength = E_source * (kappa_source / 2.0)
        
        # 本能の強さによる抵抗
        resistance = 1.0 + E_target / 20.0
        
        return suppression_strength / resistance
    
    def _facilitative_transfer(
        self,
        E_source: float,
        E_target: float,
        kappa_source: float,
        kappa_target: float
    ) -> float:
        """促進転送関数
        
        両方のκが高いほど転送が促進される
        
        例: 規範（CORE）→ 理念（UPPER）の転送
        """
        # 両方の構造が強固なほど、転送が促進される
        facilitation = (kappa_source * kappa_target) / 4.0
        
        return E_source * facilitation
    
    def _reinforcement_transfer(
        self,
        E_source: float,
        E_target: float,
        kappa_source: float,
        kappa_target: float
    ) -> float:
        """強化転送関数
        
        E_sourceが高いほど、E_targetを強化する
        
        例: 理念（UPPER）→ 規範（CORE）の強化
        """
        # 理念が強いほど、規範を強化する
        reinforcement = E_source * kappa_source / 5.0
        
        # ただし、規範が既に強い場合は効果が弱まる
        saturation = 1.0 / (1.0 + E_target / 30.0)
        
        return reinforcement * saturation
    
    def _fatigue_dependent_transfer(
        self,
        E_source: float,
        E_target: float,
        kappa_source: float,
        kappa_target: float
    ) -> float:
        """疲労依存転送関数
        
        E_target（身体疲労）が高いほど、転送量が増加
        
        例: 本能（BASE）→ 身体（PHYSICAL）
        """
        # 身体が疲労しているほど、本能的エネルギーが身体に流れ込む
        fatigue_amplification = 1.0 + E_target / 10.0
        
        return E_source * fatigue_amplification / 10.0
    
    def _pain_transfer(
        self,
        E_source: float,
        E_target: float,
        kappa_source: float,
        kappa_target: float
    ) -> float:
        """痛覚転送関数
        
        身体的苦痛が本能的恐怖を引き起こす
        
        例: 身体（PHYSICAL）→ 本能（BASE）
        """
        # 身体的エネルギーが高い = 痛み/疲労
        # これが本能的恐怖（生存への脅威）を引き起こす
        pain_intensity = E_source
        
        # κ_physicalが低い = 身体が弱い = 痛みに敏感
        pain_sensitivity = 2.0 / (kappa_source + 1.0)
        
        return pain_intensity * pain_sensitivity
    
    def _self_reflection(
        self,
        E_source: float,
        E_target: float,
        kappa_source: float,
        kappa_target: float
    ) -> float:
        """自己反省関数
        
        理念エネルギーが高まると、自己抑制が働く
        
        例: 理念（UPPER）→ 理念（UPPER）の自己抑制
        """
        # 理念が高まりすぎると、自己批判・自己抑制が働く
        # これは「独善」を防ぐメカニズム
        
        if E_source > 10.0:  # 閾値を超えた場合のみ
            excess = E_source - 10.0
            self_criticism = excess * kappa_source / 20.0
            return self_criticism
        else:
            return 0.0
    
    def get_transfer_description(self) -> str:
        """転送関数の説明を取得"""
        desc = "非線形層間転送関数:\n"
        for i, func in enumerate(self.transfer_functions, 1):
            desc += f"  {i}. {func.source_layer.name} → {func.target_layer.name}\n"
            desc += f"     係数: {func.base_coefficient:+.3f}\n"
            desc += f"     説明: {func.description}\n"
        return desc
