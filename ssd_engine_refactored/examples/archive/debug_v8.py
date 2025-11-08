"""
v8主観的社会システムのデバッグ
"""

import sys
sys.path.append('..')

from ssd_subjective_society import create_subjective_fear_contagion_scenario

# シナリオ作成
society = create_subjective_fear_contagion_scenario(num_agents=3)

print("初期状態:")
for i, agent in enumerate(society.agents):
    print(f"  Agent_{i} E_base: {agent.state.E[1]:.4f}")

# シグナル生成確認
signals = society._generate_all_signals()
print("\n観測可能なシグナル:")
for i, agent_signals in enumerate(signals):
    if agent_signals:
        print(f"  Agent_{i}:")
        for sig_type, intensity in agent_signals.items():
            print(f"    {sig_type.value}: {intensity:.4f}")

# 1ステップ実行（デバッグ）
print("\n1ステップ実行...")

# 手動で観測プロセスをトレース
observer_idx = 1
observer = society.agents[observer_idx]

print(f"\nObserver: Agent_{observer_idx}")

# Agent_0のシグナルを観測
target_idx = 0
target_signals = signals[target_idx]

print(f"Target: Agent_{target_idx}, Signals: {list(target_signals.keys())}")

# 各シグナルに対して圧力を計算
from ssd_human_module import HumanLayer

total_pressure = {
    HumanLayer.PHYSICAL: 0.0,
    HumanLayer.BASE: 0.0,
    HumanLayer.CORE: 0.0,
    HumanLayer.UPPER: 0.0
}

for signal_type, signal_intensity in target_signals.items():
    if signal_intensity > 0.01:
        print(f"\n  シグナル: {signal_type.value}, 強度: {signal_intensity:.4f}")
        
        # 観測コンテキスト作成
        observation = society._create_observation_context(
            observer_idx,
            target_idx,
            signal_type,
            signal_intensity
        )
        
        print(f"    関係性: {observation.relationship:.2f}")
        print(f"    距離: {observation.distance:.2f}")
        
        # 圧力計算
        social_pressure = society.pressure_calculator.calculate_pressure(
            observer, observation
        )
        
        print(f"    計算された圧力:")
        for layer, pressure in social_pressure.items():
            print(f"      {layer.name}: {pressure:.4f}")
            total_pressure[layer] += pressure

print(f"\n累積圧力:")
for layer, pressure in total_pressure.items():
    print(f"  {layer.name}: {pressure:.4f}")

# 圧力を適用
from ssd_human_module import HumanPressure

human_pressure = HumanPressure(
    physical=total_pressure[HumanLayer.PHYSICAL],
    base=total_pressure[HumanLayer.BASE],
    core=total_pressure[HumanLayer.CORE],
    upper=total_pressure[HumanLayer.UPPER]
)

print(f"\nAgent_{observer_idx} 圧力適用前 E_base: {observer.state.E[1]:.4f}")
observer.step(human_pressure, dt=0.1)
print(f"Agent_{observer_idx} 圧力適用後 E_base: {observer.state.E[1]:.4f}")
