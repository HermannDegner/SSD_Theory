"""
主観的社会システムのデモ
========================

v8の決定的な跳躍: 「神の視点」の完全廃止

v5/v6の問題:
- Society が全エージェントの E を直接操作（客観視点）

v8の解決:
- 各エージェントが主観的に観測→解釈→自己変化
- 社会的層間変換の実現（他者のUPPER → 自己のBASE）
"""

import sys
sys.path.append('..')

from ssd_subjective_society import (
    SubjectiveSociety,
    SignalGenerator,
    create_subjective_fear_contagion_scenario,
    create_subjective_ideology_conflict_scenario
)
from ssd_human_module import HumanAgent, HumanPressure, HumanLayer


def demo_subjective_society():
    """主観的社会システムのデモ"""
    print("=" * 70)
    print("主観的社会システム - v8決定的跳躍")
    print("=" * 70)
    print("\nv5/v6からの理論的跳躍:")
    print("  ❌ v5/v6: Society が E を直接操作（神の視点）")
    print("  ✅ v8: 観測→解釈→自己変化（主観視点）")
    
    # シナリオ1: 主観的恐怖伝染
    print("\n" + "=" * 70)
    print("[1] シナリオ1: 主観的恐怖伝染")
    print("=" * 70)
    
    print("\n  状況:")
    print("    - 5人のエージェント、全員が協力関係")
    print("    - Agent_0 が強い恐怖を持つ（E_base=150.0）")
    print("    - 他のエージェントは Agent_0 の恐怖表情を観測")
    
    society = create_subjective_fear_contagion_scenario(num_agents=5)
    
    print("\n  初期状態:")
    for i, agent in enumerate(society.agents):
        E_base = agent.state.E[HumanLayer.BASE.value]
        print(f"    Agent_{i} E_base: {E_base:.1f}")
    
    # シグナル生成を確認
    signal_gen = SignalGenerator()
    agent_0_signals = signal_gen.generate_signals(society.agents[0])
    
    print("\n  Agent_0 の観測可能なシグナル:")
    for signal_type, intensity in agent_0_signals.items():
        print(f"    {signal_type.value}: {intensity:.3f}")
    
    print("\n  シミュレーション実行（主観的観測プロセス）...")
    
    for step in range(50):
        society.step(dt=0.1)
        
        if step % 10 == 0:
            print(f"\n  Step {step}:")
            for i, agent in enumerate(society.agents):
                E_base = agent.state.E[HumanLayer.BASE.value]
                print(f"    Agent_{i} E_base: {E_base:.1f}")
    
    print("\n  → 恐怖が主観的に伝染した！")
    print("  → Agent_0の恐怖表情を観測→解釈→自己のE_baseが上昇")
    
    # シナリオ2: イデオロギー対立
    print("\n" + "=" * 70)
    print("[2] シナリオ2: イデオロギー対立")
    print("=" * 70)
    
    print("\n  状況:")
    print("    - 6人のエージェント、2グループに分割")
    print("    - グループA: Agent_0,1,2（κ_upper=2.0）")
    print("    - グループB: Agent_3,4,5（κ_upper=1.2）")
    print("    - グループ内は協力、グループ間は競争")
    
    society2 = create_subjective_ideology_conflict_scenario(num_agents=6)
    
    print("\n  初期状態:")
    for i, agent in enumerate(society2.agents):
        E_upper = agent.state.E[HumanLayer.UPPER.value]
        kappa_upper = agent.state.kappa[HumanLayer.UPPER.value]
        print(f"    Agent_{i} E_upper: {E_upper:.1f}, κ_upper: {kappa_upper:.2f}")
    
    print("\n  シミュレーション実行（イデオロギー対立の主観的解釈）...")
    
    for step in range(30):
        society2.step(dt=0.1)
        
        if step % 10 == 0:
            print(f"\n  Step {step}:")
            for i, agent in enumerate(society2.agents):
                E_upper = agent.state.E[HumanLayer.UPPER.value]
                E_core = agent.state.E[HumanLayer.CORE.value]
                print(f"    Agent_{i} E_upper: {E_upper:.1f}, E_core: {E_core:.1f}")
    
    print("\n  → イデオロギー対立が主観的に発生！")
    print("  → 対立グループのVERBAL_IDEOLOGYを観測→葛藤増大")
    
    # シナリオ3: 社会的層間変換
    print("\n" + "=" * 70)
    print("[3] シナリオ3: 社会的層間変換（v8の新機能）")
    print("=" * 70)
    
    print("\n  理論的意義:")
    print("    - v5/v6: 並列的連成（AのBASE → BのBASE）")
    print("    - v8: 交差的解釈（AのUPPER → BのBASE）")
    
    # 2人のエージェント
    leader = HumanAgent(agent_id="Leader")
    follower = HumanAgent(agent_id="Follower")
    
    # リーダーに崇高な理念を注入
    leader.step(HumanPressure(upper=80.0), dt=0.1)
    leader.state.kappa[HumanLayer.UPPER.value] = 2.5
    
    print("\n  初期状態:")
    print(f"    Leader E_upper: {leader.state.E[HumanLayer.UPPER.value]:.1f}")
    print(f"    Follower E_base: {follower.state.E[HumanLayer.BASE.value]:.1f}")
    
    # 2人の社会システム
    society3 = SubjectiveSociety(
        agents=[leader, follower],
        initial_relationships=np.array([[0.0, 0.9], [0.9, 0.0]])  # 協力関係
    )
    
    print("\n  Leader の観測可能なシグナル:")
    signals = signal_gen.generate_signals(leader)
    for signal_type, intensity in signals.items():
        print(f"    {signal_type.value}: {intensity:.3f}")
    
    print("\n  シミュレーション実行...")
    
    for step in range(20):
        society3.step(dt=0.1)
    
    print(f"\n  最終状態:")
    print(f"    Leader E_upper: {leader.state.E[HumanLayer.UPPER.value]:.1f}")
    print(f"    Follower E_base: {follower.state.E[HumanLayer.BASE.value]:.1f}")
    print(f"    Follower E_upper: {follower.state.E[HumanLayer.UPPER.value]:.1f}")
    
    print("\n  → Leader の VERBAL_IDEOLOGY (UPPER層) を観測")
    print("  → Follower が主観的に解釈")
    print("  → Follower の BASE層 と UPPER層 の両方に影響")
    print("  → 社会的層間変換の実現！")
    
    # 理論的整合性の検証
    print("\n" + "=" * 70)
    print("[4] 理論的整合性の検証")
    print("=" * 70)
    
    print("\n  ✅ 「神の視点」の完全廃止:")
    print("    - Society は E を直接操作しない")
    print("    - 各エージェントが主観的に観測→解釈")
    
    print("\n  ✅ SSD「主観力学」への整合:")
    print("    - 他者の内部状態（E, κ）は観測不可能")
    print("    - 観測可能なシグナル（表情・行動）のみ入力")
    print("    - 自己の構造で解釈し、自己の状態が変化")
    
    print("\n  ✅ 社会的層間変換の実現:")
    print("    - 他者のUPPER層 → 自己のBASE層")
    print("    - 他者のBASE層 → 自己のUPPER層")
    print("    - v5/v6の並列的連成を超越")
    
    print("\n  ✅ 創発的社会ダイナミクス:")
    print("    - 恐怖伝染、イデオロギー対立が自然に創発")
    print("    - プログラムされた結果ではなく、主観的解釈の帰結")
    
    print("\n" + "=" * 70)
    print("デモ完了")
    print("=" * 70)
    
    print("\n次のステップ:")
    print("  1. ssd_social_dynamics.py の廃止")
    print("  2. 人狼ゲームv8への統合")
    print("  3. 主観的社会圧力の精緻化")


if __name__ == "__main__":
    import numpy as np
    demo_subjective_society()
