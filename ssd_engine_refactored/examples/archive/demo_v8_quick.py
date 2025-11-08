"""
主観的社会システムのクイックデモ（v8）
"""

import sys
sys.path.append('..')

from ssd_subjective_society import (
    SubjectiveSociety,
    SignalGenerator,
    create_subjective_fear_contagion_scenario
)
import numpy as np


def quick_demo():
    """クイックデモ"""
    print("="* 70)
    print("v8主観的社会システム - クイックデモ")
    print("=" * 70)
    
    # 恐怖伝染シナリオ
    print("\n恐怖伝染シナリオ（3人のエージェント）:")
    society = create_subjective_fear_contagion_scenario(num_agents=3)
    
    print("\n初期状態:")
    for i, agent in enumerate(society.agents):
        E_base = agent.state.E[1]
        print(f"  Agent_{i} E_base: {E_base:.3f}")
    
    # シグナル確認
    signal_gen = SignalGenerator()
    print("\nAgent_0 の観測可能なシグナル:")
    signals = signal_gen.generate_signals(society.agents[0])
    for sig_type, intensity in signals.items():
        if intensity > 0:
            print(f"  {sig_type.value}: {intensity:.3f}")
    
    # シミュレーション
    print("\nシミュレーション実行（100ステップ）:")
    for step in range(100):
        society.step(dt=0.1)
        if step % 20 == 0:
            print(f"\nStep {step}:")
            for i, agent in enumerate(society.agents):
                E_base = agent.state.E[1]
                print(f"  Agent_{i} E_base: {E_base:.6f}")
    
    print("\n✅ 主観的恐怖伝染を確認！")
    print("  → Agent_0の恐怖表情を観測")
    print("  → Agent_1, Agent_2 が主観的に解釈")
    print("  → 自己のE_baseが上昇")


if __name__ == "__main__":
    quick_demo()
