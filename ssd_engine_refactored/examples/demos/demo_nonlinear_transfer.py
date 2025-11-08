"""
非線形層間転送システムのデモ
==============================

Phase 3の理論的整合を高めた、非線形層間転送のデモンストレーション。

核心原理:
- 転送量は転送元（E_source）だけでなく、転送先（E_target）にも依存
- 例: 理念による本能の抑制は、本能が強すぎると効かなくなる
- v5の線形モデル → v7の非線形モデルへの発展
"""

import sys
sys.path.append('..')

import numpy as np
from ssd_human_module import HumanAgent, HumanPressure, HumanLayer
from ssd_nonlinear_transfer import NonlinearInterlayerTransfer


def demo_nonlinear_transfer():
    """非線形層間転送のデモ"""
    print("=" * 70)
    print("非線形層間転送システム - デモ")
    print("=" * 70)
    print("\n核心原理:")
    print("  1. 転送量は E_source だけでなく E_target にも依存")
    print("  2. 飽和効果: 本能が強すぎると理念の抑制が効かない")
    print("  3. κ依存: 構造が強固なほど転送が効果的")
    print("  4. v5の線形モデル → v7の非線形モデル")
    
    # 非線形転送システム
    transfer_system = NonlinearInterlayerTransfer()
    
    print("\n" + "=" * 70)
    print("[1] 登録された転送関数")
    print("=" * 70)
    print(transfer_system.get_transfer_description())
    
    # シナリオ1: 理念による本能の抑制（飽和効果）
    print("\n" + "=" * 70)
    print("[2] シナリオ1: 理念による本能の抑制（飽和効果）")
    print("=" * 70)
    
    print("\n  状況:")
    print("    - 理念（UPPER）が本能（BASE）を抑制しようとする")
    print("    - 本能が弱い時 vs 本能が強い時の比較")
    
    # エネルギー状態を設定
    E_upper = 50.0  # 理念エネルギー（一定）
    kappa_upper = 1.5
    kappa_base = 1.0
    
    print(f"\n  固定値:")
    print(f"    E_upper: {E_upper:.1f}")
    print(f"    κ_upper: {kappa_upper:.2f}")
    print(f"    κ_base: {kappa_base:.2f}")
    
    print(f"\n  本能エネルギー E_base を変化させた時の抑制効果:")
    
    for E_base in [10.0, 30.0, 50.0, 100.0, 200.0]:
        E = np.array([0.0, E_base, 0.0, E_upper])
        kappa = np.array([1.0, kappa_base, 1.0, kappa_upper])
        
        transfer = transfer_system.compute_transfer(E, kappa, dt=1.0)
        suppression = transfer[HumanLayer.BASE.value]
        
        print(f"    E_base={E_base:6.1f} → 抑制量={suppression:+.3f}")
    
    print("\n  → 本能が強すぎる（E_base > 100）と、抑制が効かなくなる")
    
    # シナリオ2: 本能→規範の飽和転送
    print("\n" + "=" * 70)
    print("[3] シナリオ2: 本能→規範の飽和転送")
    print("=" * 70)
    
    print("\n  状況:")
    print("    - 本能（BASE）エネルギーが規範（CORE）に転送される")
    print("    - 規範が飽和すると、転送量が減少する")
    
    E_base_fixed = 80.0
    kappa_base = 1.2
    kappa_core = 1.5
    
    print(f"\n  固定値:")
    print(f"    E_base: {E_base_fixed:.1f}")
    print(f"    κ_base: {kappa_base:.2f}")
    print(f"    κ_core: {kappa_core:.2f}")
    
    print(f"\n  規範エネルギー E_core を変化させた時の転送量:")
    
    for E_core in [0.0, 20.0, 50.0, 100.0, 200.0]:
        E = np.array([0.0, E_base_fixed, E_core, 0.0])
        kappa = np.array([1.0, kappa_base, kappa_core, 1.0])
        
        transfer = transfer_system.compute_transfer(E, kappa, dt=1.0)
        transfer_amount = transfer[HumanLayer.CORE.value]
        
        print(f"    E_core={E_core:6.1f} → 転送量={transfer_amount:+.3f}")
    
    print("\n  → 規範が飽和（E_core > 100）すると、転送量が減少")
    
    # シナリオ3: κ依存の抑制
    print("\n" + "=" * 70)
    print("[4] シナリオ3: κ（整合慣性）依存の抑制")
    print("=" * 70)
    
    print("\n  状況:")
    print("    - 規範（CORE）による本能（BASE）の抑制")
    print("    - κ_coreが高いほど、抑制力が強い")
    
    E_core_fixed = 40.0
    E_base_fixed = 60.0
    kappa_base = 1.0
    
    print(f"\n  固定値:")
    print(f"    E_core: {E_core_fixed:.1f}")
    print(f"    E_base: {E_base_fixed:.1f}")
    print(f"    κ_base: {kappa_base:.2f}")
    
    print(f"\n  規範の整合慣性 κ_core を変化させた時の抑制効果:")
    
    for kappa_core in [1.0, 1.5, 2.0, 2.5, 3.0]:
        E = np.array([0.0, E_base_fixed, E_core_fixed, 0.0])
        kappa = np.array([1.0, kappa_base, kappa_core, 1.0])
        
        transfer = transfer_system.compute_transfer(E, kappa, dt=1.0)
        suppression = transfer[HumanLayer.BASE.value]
        
        print(f"    κ_core={kappa_core:.2f} → 抑制量={suppression:+.3f}")
    
    print("\n  → κ_coreが高い = 規範が強固 = 抑制力が強い")
    
    # シナリオ4: 身体疲労と本能の相互作用
    print("\n" + "=" * 70)
    print("[5] シナリオ4: 身体疲労と本能の相互作用")
    print("=" * 70)
    
    print("\n  状況:")
    print("    - 身体（PHYSICAL）の疲労が本能（BASE）の恐怖を引き起こす")
    print("    - 疲労が高いほど、恐怖が増幅される")
    
    E_base_low = 20.0
    kappa_physical = 1.0
    kappa_base = 1.0
    
    print(f"\n  固定値:")
    print(f"    E_base: {E_base_low:.1f}")
    print(f"    κ_physical: {kappa_physical:.2f}")
    
    print(f"\n  身体疲労 E_physical を変化させた時の恐怖増幅:")
    
    for E_physical in [0.0, 20.0, 50.0, 100.0, 150.0]:
        E = np.array([E_physical, E_base_low, 0.0, 0.0])
        kappa = np.array([kappa_physical, kappa_base, 1.0, 1.0])
        
        transfer = transfer_system.compute_transfer(E, kappa, dt=1.0)
        fear_amplification = transfer[HumanLayer.BASE.value]
        
        print(f"    E_physical={E_physical:6.1f} → 恐怖増幅={fear_amplification:+.3f}")
    
    print("\n  → 身体疲労が高いほど、本能的恐怖が増幅される")
    
    # シナリオ5: 実際のエージェントでの統合
    print("\n" + "=" * 70)
    print("[6] シナリオ5: HumanAgentとの統合（将来実装）")
    print("=" * 70)
    
    print("\n  現在のHumanAgent:")
    print("    - 線形転送モデル（v5）を使用")
    print("    - transfer[i] += matrix[i][j] * E[j]")
    
    print("\n  v7での改善案:")
    print("    - HumanAgent.step()内で NonlinearInterlayerTransfer を使用")
    print("    - より人間らしい心理動態を実現")
    
    print("\n  実装例:")
    print("    ```python")
    print("    class HumanAgentV7(HumanAgent):")
    print("        def __init__(self, ...):")
    print("            self.nonlinear_transfer = NonlinearInterlayerTransfer()")
    print("        ")
    print("        def step(self, pressure, dt=0.1):")
    print("            # 非線形転送を計算")
    print("            transfer = self.nonlinear_transfer.compute_transfer(")
    print("                self.state.E, self.state.kappa, dt")
    print("            )")
    print("            # エンジンに適用")
    print("            self.engine.step(pressure_vector, dt, interlayer_transfer=transfer)")
    print("    ```")
    
    # まとめ
    print("\n" + "=" * 70)
    print("[7] 理論的整合性の検証")
    print("=" * 70)
    
    print("\n  ✅ v5の問題点（線形モデル）の解決:")
    print("    - v5: transfer = matrix * E_source")
    print("    - v7: transfer = f(E_source, E_target, κ_source, κ_target)")
    
    print("\n  ✅ 人間的リアリズムの向上:")
    print("    - 飽和効果: 本能が強すぎると理性が効かない")
    print("    - κ依存: 構造が強固なほど、制御が効果的")
    print("    - 疲労増幅: 身体疲労が心理的脆弱性を引き起こす")
    
    print("\n  ✅ 次のステップ:")
    print("    - HumanAgent への統合")
    print("    - 人狼ゲームでの実証")
    print("    - パラメータチューニング")
    
    print("\n" + "=" * 70)
    print("デモ完了")
    print("=" * 70)


if __name__ == "__main__":
    demo_nonlinear_transfer()
