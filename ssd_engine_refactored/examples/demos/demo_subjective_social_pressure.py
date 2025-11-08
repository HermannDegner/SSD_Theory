"""
主観的社会圧力システムのデモ
=============================

Phase 4の理論的整合を達成した、主観的な社会的意味圧のデモンストレーション。

核心原理:
- エージェントは他者の内部状態（E, κ）を直接観測できない
- 他者の「シグナル」を観測→解釈→自己変化
- 「神の視点」から「主観視点」への移行
"""

import sys
sys.path.append('..')

from ssd_human_module import HumanAgent, HumanPressure, HumanLayer
from ssd_subjective_social_pressure import (
    SubjectiveSocialPressureCalculator,
    ObservableSignal,
    ObservationContext,
    create_fear_observation,
    create_ideology_observation
)


def demo_subjective_social_pressure():
    """主観的社会圧力のデモ"""
    print("=" * 70)
    print("主観的社会圧力システム - デモ")
    print("=" * 70)
    print("\n核心原理:")
    print("  1. エージェントは他者の内部状態（E, κ）を直接観測できない")
    print("  2. 他者の「シグナル（表情・行動）」を観測する")
    print("  3. 自己の構造で「解釈」し、自己の内部状態が変化する")
    print("  4. v5の「神の視点」→ v6の「主観視点」への移行")
    
    # エージェント作成
    print("\n" + "=" * 70)
    print("[1] エージェント初期化")
    print("=" * 70)
    
    agent_A = HumanAgent(agent_id="Alice")
    agent_B = HumanAgent(agent_id="Bob")
    agent_C = HumanAgent(agent_id="Charlie")
    
    # Aliceの初期状態を表示
    print("\n  Alice初期状態:")
    print(f"    E_base: {agent_A.state.E[HumanLayer.BASE.value]:.3f}")
    print(f"    E_core: {agent_A.state.E[HumanLayer.CORE.value]:.3f}")
    print(f"    E_upper: {agent_A.state.E[HumanLayer.UPPER.value]:.3f}")
    
    # 圧力計算器
    calculator = SubjectiveSocialPressureCalculator()
    
    # シナリオ1: 恐怖表情の伝染（親密な関係）
    print("\n" + "=" * 70)
    print("[2] シナリオ1: 恐怖伝染（親しい友人の恐怖を観測）")
    print("=" * 70)
    
    print("\n  状況:")
    print("    - Bob（親しい友人）が強い恐怖を表している")
    print("    - Alice は Bob の恐怖表情を観測")
    
    # Bobの恐怖表情を観測
    observation = create_fear_observation(
        observer_id="Alice",
        target_id="Bob",
        fear_level=0.8,      # 強い恐怖
        relationship=0.9,    # 親密な関係
        distance=0.0         # 近距離
    )
    
    print(f"\n  観測データ:")
    print(f"    シグナル: {observation.signal_type.value}")
    print(f"    強度: {observation.signal_intensity}")
    print(f"    関係性: {observation.relationship} (親密)")
    print(f"    距離: {observation.distance}")
    
    # 主観的解釈
    social_pressure = calculator.calculate_pressure(agent_A, observation)
    
    print(f"\n  Alice の主観的解釈結果（意味圧）:")
    for layer, pressure in social_pressure.items():
        print(f"    {layer.name}: {pressure:+.3f}")
    
    print("\n  → 親しい相手の恐怖 → 共感的恐怖（BASE層）")
    
    # Aliceに圧力を適用
    human_pressure = HumanPressure(
        physical=social_pressure[HumanLayer.PHYSICAL],
        base=social_pressure[HumanLayer.BASE],
        core=social_pressure[HumanLayer.CORE],
        upper=social_pressure[HumanLayer.UPPER]
    )
    
    agent_A.step(human_pressure)
    
    print(f"\n  Alice の内部状態変化:")
    print(f"    E_base: {agent_A.state.E[HumanLayer.BASE.value]:.3f} ↑ (恐怖が伝染)")
    
    # シナリオ2: 敵の恐怖（敵対的関係）
    print("\n" + "=" * 70)
    print("[3] シナリオ2: 敵の恐怖（敵対的相手の恐怖を観測）")
    print("=" * 70)
    
    agent_A2 = HumanAgent(agent_id="Alice2")
    
    print("\n  状況:")
    print("    - Charlie（敵対的相手）が恐怖を表している")
    print("    - Alice は Charlie の恐怖表情を観測")
    
    observation2 = create_fear_observation(
        observer_id="Alice2",
        target_id="Charlie",
        fear_level=0.8,
        relationship=-0.9,   # 敵対的関係
        distance=0.1
    )
    
    social_pressure2 = calculator.calculate_pressure(agent_A2, observation2)
    
    print(f"\n  Alice の主観的解釈結果（意味圧）:")
    for layer, pressure in social_pressure2.items():
        print(f"    {layer.name}: {pressure:+.3f}")
    
    print("\n  → 敵の恐怖 → 優越感（負の圧力 = 安心感）")
    
    # シナリオ3: イデオロギー対立
    print("\n" + "=" * 70)
    print("[4] シナリオ3: イデオロギー対立（信念の衝突）")
    print("=" * 70)
    
    agent_A3 = HumanAgent(agent_id="Alice3")
    
    print("\n  状況:")
    print("    - Bob が強いイデオロギーを表明")
    print("    - Alice の信念と対立（alignment = -0.8）")
    
    observation3 = create_ideology_observation(
        observer_id="Alice3",
        target_id="Bob",
        ideology_strength=0.9,
        alignment=-0.8,      # 強い対立
        relationship=0.3,
        distance=0.2
    )
    
    social_pressure3 = calculator.calculate_pressure(agent_A3, observation3)
    
    print(f"\n  Alice の主観的解釈結果（意味圧）:")
    for layer, pressure in social_pressure3.items():
        print(f"    {layer.name}: {pressure:+.3f}")
    
    print("\n  → 対立するイデオロギー → UPPER層の葛藤")
    
    # 圧力適用
    human_pressure3 = HumanPressure(
        physical=social_pressure3[HumanLayer.PHYSICAL],
        base=social_pressure3[HumanLayer.BASE],
        core=social_pressure3[HumanLayer.CORE],
        upper=social_pressure3[HumanLayer.UPPER]
    )
    
    agent_A3.step(human_pressure3)
    
    print(f"\n  Alice の内部状態変化:")
    print(f"    E_upper: {agent_A3.state.E[HumanLayer.UPPER.value]:.3f} ↑ (イデオロギー葛藤)")
    
    # シナリオ4: 距離による減衰
    print("\n" + "=" * 70)
    print("[5] シナリオ4: 距離による影響の減衰")
    print("=" * 70)
    
    print("\n  同じ恐怖表情でも、距離が遠いほど影響が減衰:")
    
    for distance in [0.0, 0.3, 0.6, 0.9]:
        obs = create_fear_observation(
            observer_id="Alice",
            target_id="Bob",
            fear_level=0.8,
            relationship=0.9,
            distance=distance
        )
        
        pressure = calculator.calculate_pressure(agent_A, obs)
        base_pressure = pressure[HumanLayer.BASE]
        
        print(f"    距離={distance:.1f} → BASE圧力={base_pressure:+.3f}")
    
    # シナリオ5: 協力行動（信頼 vs 疑念）
    print("\n" + "=" * 70)
    print("[6] シナリオ5: 協力行動の解釈（信頼 vs 疑念）")
    print("=" * 70)
    
    print("\n  親しい相手の協力 → 信頼（負の圧力）:")
    
    obs_coop_friend = ObservationContext(
        observer_id="Alice",
        target_id="Bob",
        signal_type=ObservableSignal.COOPERATIVE_ACT,
        signal_intensity=0.7,
        relationship=0.8,
        distance=0.0
    )
    
    pressure_friend = calculator.calculate_pressure(agent_A, obs_coop_friend)
    
    print(f"    BASE圧力: {pressure_friend[HumanLayer.BASE]:+.3f} (安心感)")
    print(f"    CORE圧力: {pressure_friend[HumanLayer.CORE]:+.3f} (信頼)")
    
    print("\n  敵対的相手の協力 → 疑念（正の圧力）:")
    
    obs_coop_enemy = ObservationContext(
        observer_id="Alice",
        target_id="Charlie",
        signal_type=ObservableSignal.COOPERATIVE_ACT,
        signal_intensity=0.7,
        relationship=-0.8,
        distance=0.0
    )
    
    pressure_enemy = calculator.calculate_pressure(agent_A, obs_coop_enemy)
    
    print(f"    BASE圧力: {pressure_enemy[HumanLayer.BASE]:+.3f} (警戒)")
    print(f"    CORE圧力: {pressure_enemy[HumanLayer.CORE]:+.3f} (裏を読む)")
    print(f"    UPPER圧力: {pressure_enemy[HumanLayer.UPPER]:+.3f} (動機の解釈)")
    
    # まとめ
    print("\n" + "=" * 70)
    print("[7] 理論的整合性の検証")
    print("=" * 70)
    
    print("\n  ✅ v5の問題点（神の視点）の解決:")
    print("    - v5: Society が E を直接操作")
    print("    - v6: エージェントが観測→解釈→自己変化")
    
    print("\n  ✅ 主観的解釈の実装:")
    print("    - 同じシグナルでも、関係性で解釈が変わる")
    print("    - 観測者の内部状態（κ）に依存する解釈")
    print("    - 距離・文脈による減衰")
    
    print("\n  ✅ 次のステップ:")
    print("    - Society クラスの再設計")
    print("    - エージェント間の「シグナル生成」ロジック")
    print("    - 多エージェントシミュレーションへの統合")
    
    print("\n" + "=" * 70)
    print("デモ完了")
    print("=" * 70)


if __name__ == "__main__":
    demo_subjective_social_pressure()
