"""
SSD v3.5 拡張: 多層社会モデル (Multi-Layer Society)

概念:
----
社会は単一の塊ではなく、複数の層（階級）から構成される。
各層は独自の E_direct, E_indirect を持ち、層間で相互作用する。

例: フランス革命前夜 (1789)
- 貴族層 (Nobility): 高 E_direct, 低 E_indirect (暴力支配)
- 市民層 (Bourgeoisie): 低 E_direct, 高 E_indirect (啓蒙思想)
- 農民層 (Peasants): 中 E_direct, 低 E_indirect (不満蓄積)

層間連成:
-------
γ_ij: 層 i から層 j への影響
- γ_市民→農民: 啓蒙思想が農民に伝播
- γ_貴族→市民: 弾圧が市民の怒りを増幅
- γ_農民→貴族: 一揆が貴族を脅かす

多相転移:
-------
1つの層が E_indirect < Θ_critical を越えると、
他の層にも連鎖的に相転移が伝播。
→ 全体崩壊 (革命)
"""

import numpy as np
import matplotlib.pyplot as plt
from ssd_core_engine_v3_5 import SSDCoreEngineV3_5, SSDParametersV3_5, SSDStateV3_5
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class SocialLayer:
    """社会の1つの層"""
    name: str
    population: int  # 人口
    engine: SSDCoreEngineV3_5
    state: SSDStateV3_5
    gamma_to: Dict[str, float]  # 他層への影響係数


class MultiLayerSociety:
    """多層社会シミュレーター"""
    
    def __init__(self):
        # 貴族層: 暴力で支配、思想は弱い
        params_nobility = SSDParametersV3_5(
            use_direct_action=True,
            use_indirect_action=False,
            amplification_factor=5.0,
            gamma_i2d=0.01,
            gamma_d2i=0.01,
            beta_decay=0.1,
            Theta_critical=300.0,  # 低め (すぐ暴力に訴える)
            enable_phase_transition=True,
            phase_transition_multiplier=5.0,
        )
        
        # 市民層: 啓蒙思想を持つ、暴力は弱い
        params_bourgeoisie = SSDParametersV3_5(
            use_direct_action=False,
            use_indirect_action=True,
            amplification_factor=50.0,
            gamma_i2d=0.05,
            gamma_d2i=0.5,  # 行動→思想が強い
            beta_decay=0.01,  # 思想は残る
            Theta_critical=500.0,
            enable_phase_transition=True,
            phase_transition_multiplier=20.0,
        )
        
        # 農民層: 潜在的暴力、思想は受動的
        params_peasants = SSDParametersV3_5(
            use_direct_action=True,
            use_indirect_action=True,
            amplification_factor=10.0,
            gamma_i2d=0.1,  # 思想→行動は速い
            gamma_d2i=0.05,
            beta_decay=0.05,
            Theta_critical=400.0,
            enable_phase_transition=True,
            phase_transition_multiplier=15.0,
        )
        
        # 層の初期化
        self.layers = {
            'nobility': SocialLayer(
                name='貴族',
                population=100000,
                engine=SSDCoreEngineV3_5(params_nobility),
                state=SSDStateV3_5(kappa=1.0, E_direct=500.0, E_indirect=50.0),
                gamma_to={'bourgeoisie': 0.5, 'peasants': 0.3}  # 弾圧
            ),
            'bourgeoisie': SocialLayer(
                name='市民',
                population=500000,
                engine=SSDCoreEngineV3_5(params_bourgeoisie),
                state=SSDStateV3_5(kappa=0.7, E_direct=10.0, E_indirect=400.0),
                gamma_to={'nobility': 0.1, 'peasants': 0.8}  # 啓蒙
            ),
            'peasants': SocialLayer(
                name='農民',
                population=2000000,
                engine=SSDCoreEngineV3_5(params_peasants),
                state=SSDStateV3_5(kappa=0.8, E_direct=100.0, E_indirect=200.0),
                gamma_to={'nobility': 0.2, 'bourgeoisie': 0.1}  # 一揆
            ),
        }
        
    def simulate(self, duration: float = 10.0, dt: float = 0.01):
        """多層社会の時間発展"""
        
        print("="*70)
        print("SSD v3.5: 多層社会モデル - フランス革命前夜")
        print("="*70)
        
        steps = int(duration / dt)
        
        # データ記録
        history = {
            'time': [],
            'nobility_E_direct': [],
            'nobility_E_indirect': [],
            'bourgeoisie_E_direct': [],
            'bourgeoisie_E_indirect': [],
            'peasants_E_direct': [],
            'peasants_E_indirect': [],
            'total_E_direct': [],
            'total_E_indirect': [],
        }
        
        print("\n[初期状態]")
        for name, layer in self.layers.items():
            print(f"  {layer.name}:")
            print(f"    人口: {layer.population:,}人")
            print(f"    E_direct: {layer.state.E_direct:.1f}J")
            print(f"    E_indirect: {layer.state.E_indirect:.1f}J")
        
        phase_transitions = []
        
        for step in range(steps):
            t = step * dt
            
            # 1. 層間相互作用の計算
            layer_influences = {}
            for name, layer in self.layers.items():
                influence = np.zeros(3)
                for target_name, gamma in layer.gamma_to.items():
                    target_layer = self.layers[target_name]
                    # E_indirect を意味圧として伝播
                    influence += gamma * target_layer.state.E_indirect * np.array([1.0, 0, 0])
                layer_influences[name] = influence
            
            # 2. 各層を更新
            for name, layer in self.layers.items():
                # 外部からの影響 + 内部生成
                p_external = layer_influences[name] / layer.population * 1000
                
                # 直接作用 (弾圧、一揆)
                if name == 'nobility':
                    contact = np.array([10.0, 0, 0])  # 弾圧
                elif name == 'peasants' and layer.state.is_critical:
                    contact = np.array([50.0, 0, 0])  # 一揆
                else:
                    contact = None
                
                layer.engine.step(layer.state, p_external, dt, contact_pressure=contact)
                
                # 相転移検出
                if layer.state.is_critical and layer.state.phase_transition_count == 1:
                    phase_transitions.append((t, name, layer.name))
                    print(f"\n[相転移] t={t:.2f}年: {layer.name}層が臨界突破!")
                    print(f"  E_indirect: {layer.state.E_indirect:.1f} < Θ")
            
            # 3. 記録
            if step % 10 == 0:
                history['time'].append(t)
                history['nobility_E_direct'].append(self.layers['nobility'].state.E_direct)
                history['nobility_E_indirect'].append(self.layers['nobility'].state.E_indirect)
                history['bourgeoisie_E_direct'].append(self.layers['bourgeoisie'].state.E_direct)
                history['bourgeoisie_E_indirect'].append(self.layers['bourgeoisie'].state.E_indirect)
                history['peasants_E_direct'].append(self.layers['peasants'].state.E_direct)
                history['peasants_E_indirect'].append(self.layers['peasants'].state.E_indirect)
                
                total_direct = sum(l.state.E_direct for l in self.layers.values())
                total_indirect = sum(l.state.E_indirect for l in self.layers.values())
                history['total_E_direct'].append(total_direct)
                history['total_E_indirect'].append(total_indirect)
        
        print("\n[最終状態]")
        for name, layer in self.layers.items():
            print(f"  {layer.name}:")
            print(f"    E_direct: {layer.state.E_direct:.1f}J")
            print(f"    E_indirect: {layer.state.E_indirect:.1f}J")
            print(f"    相転移回数: {layer.state.phase_transition_count}")
        
        # 可視化
        self.visualize(history, phase_transitions)
        
        return history
    
    def visualize(self, history, phase_transitions):
        """結果の可視化"""
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        time = np.array(history['time'])
        
        # 1. 各層の E_direct
        ax1 = axes[0, 0]
        ax1.plot(time, history['nobility_E_direct'], 'r-', linewidth=2, label='Nobility', alpha=0.8)
        ax1.plot(time, history['bourgeoisie_E_direct'], 'b-', linewidth=2, label='Bourgeoisie', alpha=0.8)
        ax1.plot(time, history['peasants_E_direct'], 'g-', linewidth=2, label='Peasants', alpha=0.8)
        
        for t, name, label in phase_transitions:
            ax1.axvline(x=t, color='orange', linestyle='--', alpha=0.5)
        
        ax1.set_xlabel('Time (years)', fontsize=12)
        ax1.set_ylabel('E_direct (Violence)', fontsize=12)
        ax1.set_title('Physical Violence by Social Layer', fontsize=13, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # 2. 各層の E_indirect
        ax2 = axes[0, 1]
        ax2.plot(time, history['nobility_E_indirect'], 'r-', linewidth=2, label='Nobility', alpha=0.8)
        ax2.plot(time, history['bourgeoisie_E_indirect'], 'b-', linewidth=2, label='Bourgeoisie', alpha=0.8)
        ax2.plot(time, history['peasants_E_indirect'], 'g-', linewidth=2, label='Peasants', alpha=0.8)
        
        # 臨界線
        ax2.axhline(y=300, color='red', linestyle=':', alpha=0.5, label='Θ_nobility')
        ax2.axhline(y=400, color='green', linestyle=':', alpha=0.5, label='Θ_peasants')
        ax2.axhline(y=500, color='blue', linestyle=':', alpha=0.5, label='Θ_bourgeoisie')
        
        for t, name, label in phase_transitions:
            ax2.axvline(x=t, color='orange', linestyle='--', alpha=0.5)
            ax2.text(t, ax2.get_ylim()[1]*0.9, label, rotation=90, fontsize=8)
        
        ax2.set_xlabel('Time (years)', fontsize=12)
        ax2.set_ylabel('E_indirect (Ideas)', fontsize=12)
        ax2.set_title('Ideological Energy by Social Layer', fontsize=13, fontweight='bold')
        ax2.legend(loc='best', fontsize=9)
        ax2.grid(True, alpha=0.3)
        
        # 3. 全体のエネルギー
        ax3 = axes[1, 0]
        ax3.plot(time, history['total_E_direct'], 'r-', linewidth=2.5, label='Total E_direct', alpha=0.8)
        ax3.plot(time, history['total_E_indirect'], 'b-', linewidth=2.5, label='Total E_indirect', alpha=0.8)
        
        for t, name, label in phase_transitions:
            ax3.axvline(x=t, color='orange', linestyle='--', alpha=0.5)
        
        ax3.set_xlabel('Time (years)', fontsize=12)
        ax3.set_ylabel('Total Energy', fontsize=12)
        ax3.set_title('Society-Wide Energy Balance', fontsize=13, fontweight='bold')
        ax3.legend(loc='best')
        ax3.grid(True, alpha=0.3)
        
        # 4. エネルギー比率 (対数)
        ax4 = axes[1, 1]
        
        ratio_nobility = np.array(history['nobility_E_indirect']) / (np.array(history['nobility_E_direct']) + 1)
        ratio_bourgeoisie = np.array(history['bourgeoisie_E_indirect']) / (np.array(history['bourgeoisie_E_direct']) + 1)
        ratio_peasants = np.array(history['peasants_E_indirect']) / (np.array(history['peasants_E_direct']) + 1)
        
        ax4.semilogy(time, ratio_nobility, 'r-', linewidth=2, label='Nobility', alpha=0.8)
        ax4.semilogy(time, ratio_bourgeoisie, 'b-', linewidth=2, label='Bourgeoisie', alpha=0.8)
        ax4.semilogy(time, ratio_peasants, 'g-', linewidth=2, label='Peasants', alpha=0.8)
        
        ax4.axhline(y=1.0, color='black', linestyle='-', linewidth=1.5, alpha=0.5)
        
        for t, name, label in phase_transitions:
            ax4.axvline(x=t, color='orange', linestyle='--', alpha=0.5)
        
        ax4.set_xlabel('Time (years)', fontsize=12)
        ax4.set_ylabel('E_indirect / E_direct (log)', fontsize=12)
        ax4.set_title('Power Balance: Ideas vs Violence', fontsize=13, fontweight='bold')
        ax4.legend(loc='best')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('ssd_multilayer_society.png', dpi=150, bbox_inches='tight')
        print("\n💾 Plot saved: ssd_multilayer_society.png")
        plt.show()


if __name__ == "__main__":
    sim = MultiLayerSociety()
    history = sim.simulate(duration=10.0, dt=0.01)
    
    print("\n" + "="*70)
    print("📊 分析")
    print("="*70)
    
    print("\n🔬 多層社会の洞察:")
    print("  1. 各層は独自の E_direct, E_indirect を持つ")
    print("  2. γ_ij により層間で相互作用")
    print("  3. 1層の相転移が他層に連鎖")
    print("  4. 全体崩壊 = 多相転移")
    
    print("\n🎯 フランス革命への応用:")
    print("  - 市民層: 高 E_indirect (啓蒙思想)")
    print("  - 農民層: γ_市民→農民 により思想伝播")
    print("  - 農民層が臨界突破 → 一揆 (E_direct)")
    print("  - 貴族層の弾圧 → さらなる怒り")
    print("  - 結果: 全層が相転移 → 革命")
    
    print("\n" + "="*70)
    print("✅ SSD v3.5: 多層社会モデル 完了")
    print("="*70)
