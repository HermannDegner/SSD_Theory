"""
人間心理モジュールのデモ
========================

四層構造の人間エージェントの動作確認
"""

import sys
sys.path.append('..')

from ssd_human_module import (
    HumanAgent, HumanParams, HumanPressure, HumanLayer,
    NeurotransmitterMapper
)


def demo_human_psychology():
    """人間心理モジュールのデモ"""
    print("=" * 60)
    print("SSD Human Module - 人間心理デモ")
    print("=" * 60)
    
    # エージェント作成
    print("\n[1] エージェント初期化")
    agent = HumanAgent(agent_id="TestPerson")
    
    state = agent.get_psychological_state()
    print(f"  Agent: {state['agent_id']}")
    print(f"  Dominant Layer: {state['dominant_layer']}")
    print(f"  Energies: {state['energies']}")
    
    # シナリオ1: 物理的疲労の蓄積
    print("\n" + "=" * 60)
    print("[2] シナリオ1: 物理的疲労の蓄積")
    print("=" * 60)
    
    pressure_fatigue = HumanPressure(physical=100.0)
    
    print("\n  継続的な物理的圧力を加える...")
    for step in range(30):
        agent.step(pressure_fatigue, dt=0.1)
        
        if step % 10 == 0:
            state = agent.get_psychological_state()
            print(f"\n  Step {step}:")
            print(f"    E_physical: {state['energies']['PHYSICAL']:.1f}")
            print(f"    状態: {state['interpretations'][HumanLayer.PHYSICAL]}")
            
            # 神経物質推定
            cortisol = NeurotransmitterMapper.estimate_cortisol(agent)
            serotonin = NeurotransmitterMapper.estimate_serotonin(agent)
            print(f"    Cortisol (stress): {cortisol:.2f}")
            print(f"    Serotonin (wellbeing): {serotonin:.2f}")
    
    # シナリオ2: 本能的不満の爆発
    print("\n" + "=" * 60)
    print("[3] シナリオ2: 本能的不満の爆発")
    print("=" * 60)
    
    agent2 = HumanAgent(agent_id="FrustratedPerson")
    pressure_instinct = HumanPressure(base=80.0)
    
    print("\n  継続的な本能的圧力を加える...")
    for step in range(50):
        agent2.step(pressure_instinct, dt=0.1)
        
        if step % 10 == 0:
            state = agent2.get_psychological_state()
            print(f"\n  Step {step}:")
            print(f"    E_base: {state['energies']['BASE']:.1f}")
            print(f"    状態: {state['interpretations'][HumanLayer.BASE]}")
            
            # Dopamine（跳躍可能性）
            dopamine = NeurotransmitterMapper.estimate_dopamine(agent2)
            print(f"    Dopamine (leap potential): {dopamine:.2f}")
        
        # 跳躍発生チェック
        if len(state['leap_history']) > 0:
            last_leap = state['leap_history'][-1]
            print(f"\n  *** 跳躍発生！***")
            print(f"    Time: {last_leap[0]:.1f}")
            print(f"    Type: {last_leap[1]}")
            break
    
    # シナリオ3: 層間転送（理念が本能を抑圧）
    print("\n" + "=" * 60)
    print("[4] シナリオ3: 層間転送（理念が本能を抑圧）")
    print("=" * 60)
    
    agent3 = HumanAgent(agent_id="IdealistPerson")
    
    # 高い本能的エネルギー
    agent3.state.E[HumanLayer.BASE.value] = 80.0
    # 高い理念的エネルギー
    agent3.state.E[HumanLayer.UPPER.value] = 40.0
    
    print("\n  初期状態:")
    print(f"    E_base: {agent3.state.E[HumanLayer.BASE.value]:.1f}")
    print(f"    E_upper: {agent3.state.E[HumanLayer.UPPER.value]:.1f}")
    
    # 圧力なしで層間転送のみ観察
    pressure_none = HumanPressure()
    
    print("\n  層間転送の観察...")
    for step in range(20):
        agent3.step(pressure_none, dt=0.1)
        
        if step % 5 == 0:
            print(f"\n  Step {step}:")
            print(f"    E_base: {agent3.state.E[HumanLayer.BASE.value]:.1f}")
            print(f"    E_upper: {agent3.state.E[HumanLayer.UPPER.value]:.1f}")
            print(f"    → 理念が本能を抑圧中...")
    
    print("\n" + "=" * 60)
    print("デモ完了")
    print("=" * 60)


if __name__ == "__main__":
    demo_human_psychology()
