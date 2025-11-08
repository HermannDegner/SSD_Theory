"""
社会ダイナミクスのデモ
======================

Phase 4: 多エージェント社会シミュレーション
"""

import sys
sys.path.append('..')

from ssd_social_dynamics import (
    Society, RelationshipMatrix,
    create_fear_contagion_scenario,
    create_ideology_conflict_scenario,
    create_norm_propagation_scenario
)
from ssd_human_module import HumanLayer, HumanPressure


def demo_social_dynamics():
    """社会ダイナミクスのデモ"""
    print("=" * 70)
    print("SSD Social Dynamics - Phase 4デモ")
    print("=" * 70)
    
    # シナリオ1: 恐怖伝染
    print("\n" + "=" * 70)
    print("[1] シナリオ1: 恐怖伝染（協力関係での感情伝播）")
    print("=" * 70)
    
    society1 = create_fear_contagion_scenario(num_agents=5)
    
    print("\n  初期状態:")
    print(f"    Agent_0 E_base: {society1.agents[0].state.E[HumanLayer.BASE.value]:.1f} (恐怖源)")
    print(f"    Agent_1 E_base: {society1.agents[1].state.E[HumanLayer.BASE.value]:.1f}")
    print(f"    Agent_2 E_base: {society1.agents[2].state.E[HumanLayer.BASE.value]:.1f}")
    
    print("\n  シミュレーション実行...")
    for step in range(50):
        society1.step(dt=0.1)
        
        if step % 10 == 0:
            print(f"\n  Step {step}:")
            for i in range(3):  # 最初の3エージェントのみ表示
                E_base = society1.agents[i].state.E[HumanLayer.BASE.value]
                print(f"    Agent_{i} E_base: {E_base:.1f}")
    
    print("\n  結果:")
    print("    → 恐怖が協力関係を通じて伝播しました")
    
    # シナリオ2: イデオロギー対立
    print("\n" + "=" * 70)
    print("[2] シナリオ2: イデオロギー対立（競争関係での抑制）")
    print("=" * 70)
    
    society2 = create_ideology_conflict_scenario(num_agents=6)
    
    print("\n  グループ構成:")
    print("    グループA: Agent_0, 1, 2 (協力関係)")
    print("    グループB: Agent_3, 4, 5 (協力関係)")
    print("    A ⇔ B: 競争関係")
    
    print("\n  初期状態:")
    print(f"    GroupA E_upper平均: {sum(society2.agents[i].state.E[HumanLayer.UPPER.value] for i in range(3))/3:.1f}")
    print(f"    GroupB E_upper平均: {sum(society2.agents[i].state.E[HumanLayer.UPPER.value] for i in range(3,6))/3:.1f}")
    
    print("\n  シミュレーション実行...")
    for step in range(30):
        society2.step(dt=0.1)
        
        if step % 10 == 0:
            avg_A = sum(society2.agents[i].state.E[HumanLayer.UPPER.value] for i in range(3))/3
            avg_B = sum(society2.agents[i].state.E[HumanLayer.UPPER.value] for i in range(3,6))/3
            print(f"\n  Step {step}:")
            print(f"    GroupA E_upper平均: {avg_A:.1f}")
            print(f"    GroupB E_upper平均: {avg_B:.1f}")
    
    print("\n  結果:")
    print("    → 競争関係により相互抑制が発生")
    
    # シナリオ3: 規範伝播
    print("\n" + "=" * 70)
    print("[3] シナリオ3: 規範伝播（κの社会的学習）")
    print("=" * 70)
    
    society3 = create_norm_propagation_scenario(num_agents=7)
    
    print("\n  初期状態:")
    print(f"    Agent_0 κ_core: {society3.agents[0].state.kappa[HumanLayer.CORE.value]:.2f} (模範)")
    print(f"    Agent_1 κ_core: {society3.agents[1].state.kappa[HumanLayer.CORE.value]:.2f}")
    print(f"    Agent_2 κ_core: {society3.agents[2].state.kappa[HumanLayer.CORE.value]:.2f}")
    
    print("\n  シミュレーション実行...")
    for step in range(50):
        society3.step(dt=0.1)
        
        if step % 10 == 0:
            print(f"\n  Step {step}:")
            for i in range(3):
                kappa_core = society3.agents[i].state.kappa[HumanLayer.CORE.value]
                print(f"    Agent_{i} κ_core: {kappa_core:.3f}")
    
    print("\n  結果:")
    print("    → 模範エージェントの規範κが他者に伝播")
    
    # ネットワーク状態の可視化
    print("\n" + "=" * 70)
    print("[4] 社会ネットワーク状態")
    print("=" * 70)
    
    society3.visualize_network()
    
    # 支配層分布
    print("\n  全シナリオの支配層分布:")
    print("\n  シナリオ1 (恐怖伝染):")
    dist1 = society1.get_dominant_layers_distribution()
    for layer, count in dist1.items():
        print(f"    {layer}: {count} agents")
    
    print("\n  シナリオ2 (イデオロギー対立):")
    dist2 = society2.get_dominant_layers_distribution()
    for layer, count in dist2.items():
        print(f"    {layer}: {count} agents")
    
    print("\n  シナリオ3 (規範伝播):")
    dist3 = society3.get_dominant_layers_distribution()
    for layer, count in dist3.items():
        print(f"    {layer}: {count} agents")
    
    print("\n" + "=" * 70)
    print("デモ完了")
    print("=" * 70)


if __name__ == "__main__":
    demo_social_dynamics()
