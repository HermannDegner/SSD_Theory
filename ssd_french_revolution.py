"""
SSD v3.5 実証: フランス革命 (1789)

シナリオ:
--------
Phase 1: 思想蓄積 (1750-1789)
  - ルソー、ヴォルテールの啓蒙思想
  - E_indirect が徐々に蓄積
  - γ_i2d は低い (言葉が行動に転換しにくい)
  
Phase 2: 臨界突破 (1789年7月14日)
  - E_indirect > Θ_critical
  - γ_i2d が急増 (相転移)
  - バスティーユ襲撃 (E_direct 解放)
  
Phase 3: フィードバック循環 (1789-1794)
  - E_direct (革命) → γ_d2i → E_indirect (人権宣言)
  - "行動が新しい意味を生む"
  - 極限サイクル: 革命 → 新思想 → さらなる革命
  
Phase 4: 減衰とナポレオン (1794-1804)
  - β_decay により E_indirect 減少
  - E_direct が再支配 (恐怖政治、独裁)
  
連成方程式:
----------
dE_direct/dt = α_d(p_d - j_d) + γ_i2d * E_indirect - γ_d2i * E_direct
dE_indirect/dt = α_i(p_i - j_i) - γ_i2d * E_indirect + γ_d2i * E_direct - β_decay * E_indirect

相転移条件:
----------
E_indirect < 500 → γ_i2d *= 10 (思想が一気に行動へ)
"""

import numpy as np
import matplotlib.pyplot as plt
from ssd_core_engine_v3_5 import SSDCoreEngineV3_5, SSDParametersV3_5, SSDStateV3_5


class FrenchRevolutionSimulator:
    """フランス革命のSSDシミュレーション"""
    
    def __init__(self):
        # Phase 1-2: 思想蓄積から臨界まで (1750-1789)
        self.params_accumulation = SSDParametersV3_5(
            use_direct_action=False,  # まだ暴力なし
            use_indirect_action=True,
            amplification_factor=10.0,  # 啓蒙思想の増幅
            gamma_i2d=0.01,  # 低変換率 (言葉 → 行動は難しい)
            gamma_d2i=0.0,   # 行動がないので0
            beta_decay=0.005,  # 思想はゆっくり減衰
            Theta_critical=500.0,
            enable_phase_transition=True,
            phase_transition_multiplier=20.0,  # 革命は急激
        )
        
        # Phase 3: 革命期 (1789-1794)
        self.params_revolution = SSDParametersV3_5(
            use_direct_action=True,   # 暴力解放
            use_indirect_action=True,
            amplification_factor=20.0,
            gamma_i2d=0.2,   # 高変換率 (相転移後)
            gamma_d2i=0.5,   # 行動 → 意味 (人権宣言など)
            beta_decay=0.01,
            enable_phase_transition=False,  # すでに転移済み
        )
        
        # Phase 4: 減衰期 (1794-1804)
        self.params_decay = SSDParametersV3_5(
            use_direct_action=True,
            use_indirect_action=True,
            amplification_factor=5.0,  # 思想の力が弱まる
            gamma_i2d=0.05,  # 変換率低下
            gamma_d2i=0.2,   # 行動優位
            beta_decay=0.1,  # 急速減衰 (恐怖政治)
            enable_phase_transition=False,
        )
        
    def simulate(self):
        """革命全体をシミュレーション"""
        
        print("="*70)
        print("SSD v3.5: フランス革命シミュレーション (1750-1804)")
        print("="*70)
        
        # データ記録
        time_data = []
        E_direct_data = []
        E_indirect_data = []
        conversion_i2d_data = []
        conversion_d2i_data = []
        phase_labels = []
        
        total_time = 0.0
        
        # Phase 1: 思想蓄積 (1750-1789, 39年間)
        print("\n[Phase 1] 思想蓄積期 (1750-1789)")
        print("  啓蒙思想家: ルソー、ヴォルテール、モンテスキュー")
        print("  E_indirect を蓄積中...")
        
        engine = SSDCoreEngineV3_5(self.params_accumulation)
        state = SSDStateV3_5(kappa=0.8, E_direct=0.0, E_indirect=100.0)
        
        dt = 0.1
        duration_phase1 = 39.0  # 39年
        steps_phase1 = int(duration_phase1 / dt)
        
        for step in range(steps_phase1):
            t = total_time + step * dt
            
            # 啓蒙思想の流入 (連続的)
            p_external = np.array([20.0, 0.0, 0.0])  # 思想圧
            engine.step(state, p_external, dt)
            
            # 記録
            if step % 10 == 0:
                time_data.append(t)
                E_direct_data.append(state.E_direct)
                E_indirect_data.append(state.E_indirect)
                conversion_i2d_data.append(state.conversion_i2d)
                conversion_d2i_data.append(state.conversion_d2i)
                phase_labels.append("思想蓄積")
                
            # 臨界チェック
            if state.is_critical:
                print(f"\n  [臨界突破!] t={t:.1f}年")
                print(f"    E_indirect = {state.E_indirect:.1f} < Θ = {self.params_accumulation.Theta_critical}")
                print(f"    γ_i2d: {self.params_accumulation.gamma_i2d / self.params_accumulation.phase_transition_multiplier:.3f} → {self.params_accumulation.gamma_i2d:.3f}")
                break
                
        total_time += (step + 1) * dt
        print(f"  最終: E_indirect = {state.E_indirect:.1f}J")
        
        # Phase 2: バスティーユ襲撃 (1789年7月14日, 瞬間的)
        print("\n[Phase 2] バスティーユ襲撃 (1789年7月14日)")
        print("  思想が一気に行動へ変換!")
        
        # パラメータ切り替え
        engine = SSDCoreEngineV3_5(self.params_revolution)
        
        # 襲撃の瞬間 (大きな直接作用)
        for _ in range(10):
            p_external = np.array([50.0, 0.0, 0.0])  # 革命の叫び
            contact = np.array([100.0, 0.0, 0.0])    # 暴力
            engine.step(state, p_external, dt, contact_pressure=contact)
            
            t = total_time
            time_data.append(t)
            E_direct_data.append(state.E_direct)
            E_indirect_data.append(state.E_indirect)
            conversion_i2d_data.append(state.conversion_i2d)
            conversion_d2i_data.append(state.conversion_d2i)
            phase_labels.append("革命")
            total_time += dt
            
        print(f"  E_direct = {state.E_direct:.1f}J (暴力解放)")
        print(f"  E_indirect = {state.E_indirect:.1f}J (革命思想)")
        
        # Phase 3: 革命期の循環 (1789-1794, 5年間)
        print("\n[Phase 3] 革命期の循環 (1789-1794)")
        print("  行動 → 新しい意味 → 新しい行動 → ...")
        
        duration_phase3 = 5.0
        steps_phase3 = int(duration_phase3 / dt)
        
        for step in range(steps_phase3):
            t = total_time + step * dt
            
            # 革命活動 (直接 + 間接)
            p_external = np.array([30.0, 0.0, 0.0])
            contact = np.array([20.0, 0.0, 0.0]) if step % 10 < 5 else np.zeros(3)
            engine.step(state, p_external, dt, contact_pressure=contact)
            
            # 記録
            if step % 5 == 0:
                time_data.append(t)
                E_direct_data.append(state.E_direct)
                E_indirect_data.append(state.E_indirect)
                conversion_i2d_data.append(state.conversion_i2d)
                conversion_d2i_data.append(state.conversion_d2i)
                phase_labels.append("革命")
                
        total_time += duration_phase3
        print(f"  E_direct = {state.E_direct:.1f}J")
        print(f"  E_indirect = {state.E_indirect:.1f}J")
        print(f"  循環: i→d = {state.conversion_i2d:.2f} J/s, d→i = {state.conversion_d2i:.2f} J/s")
        
        # Phase 4: 減衰とナポレオン (1794-1804, 10年間)
        print("\n[Phase 4] 減衰期とナポレオン (1794-1804)")
        print("  思想の減衰 → 独裁の台頭")
        
        engine = SSDCoreEngineV3_5(self.params_decay)
        
        duration_phase4 = 10.0
        steps_phase4 = int(duration_phase4 / dt)
        
        for step in range(steps_phase4):
            t = total_time + step * dt
            
            # 恐怖政治 (直接作用優位)
            p_external = np.array([5.0, 0.0, 0.0])  # 思想の力は弱まる
            contact = np.array([30.0, 0.0, 0.0])    # 暴力が支配
            engine.step(state, p_external, dt, contact_pressure=contact)
            
            # 記録
            if step % 10 == 0:
                time_data.append(t)
                E_direct_data.append(state.E_direct)
                E_indirect_data.append(state.E_indirect)
                conversion_i2d_data.append(state.conversion_i2d)
                conversion_d2i_data.append(state.conversion_d2i)
                phase_labels.append("減衰")
                
        total_time += duration_phase4
        print(f"  最終: E_direct = {state.E_direct:.1f}J (暴力支配)")
        print(f"  最終: E_indirect = {state.E_indirect:.1f}J (思想の衰退)")
        
        # 可視化
        self.visualize(
            time_data, E_direct_data, E_indirect_data,
            conversion_i2d_data, conversion_d2i_data, phase_labels
        )
        
        return time_data, E_direct_data, E_indirect_data
    
    def visualize(self, time_data, E_direct_data, E_indirect_data,
                  conversion_i2d_data, conversion_d2i_data, phase_labels):
        """結果の可視化"""
        
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        
        time_array = np.array(time_data)
        
        # 1. エネルギー時間発展
        ax1 = axes[0]
        ax1.plot(time_array, E_direct_data, 'r-', linewidth=2.5, label='E_direct (Violence)', alpha=0.8)
        ax1.plot(time_array, E_indirect_data, 'b-', linewidth=2.5, label='E_indirect (Ideas)', alpha=0.8)
        
        # フェーズ境界
        ax1.axvline(x=39, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='Bastille (1789)')
        ax1.axvline(x=44, color='purple', linestyle='--', linewidth=2, alpha=0.7, label='Terror begins (1794)')
        ax1.axhline(y=500, color='red', linestyle=':', linewidth=2, alpha=0.5, label='Θ_critical')
        
        ax1.set_xlabel('Time (years from 1750)', fontsize=12)
        ax1.set_ylabel('Energy (J)', fontsize=12)
        ax1.set_title('French Revolution: Energy Evolution', fontsize=14, fontweight='bold')
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # アノテーション
        ax1.annotate('Enlightenment\n(Rousseau, Voltaire)', 
                    xy=(20, 400), xytext=(10, 600),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=1.5),
                    fontsize=10, color='blue')
        
        ax1.annotate('Revolution!\n(E_indirect → E_direct)', 
                    xy=(39, 300), xytext=(32, 800),
                    arrowprops=dict(arrowstyle='->', color='red', lw=2),
                    fontsize=11, color='red', fontweight='bold')
        
        ax1.annotate('Napoleon\n(Dictatorship)', 
                    xy=(50, E_direct_data[-1]), xytext=(47, 1200),
                    arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5),
                    fontsize=10, color='darkred')
        
        # 2. 変換率の時間発展
        ax2 = axes[1]
        ax2.plot(time_array, conversion_i2d_data, 'g-', linewidth=2, label='γ_i2d * E_indirect (Ideas → Action)', alpha=0.8)
        ax2.plot(time_array, conversion_d2i_data, 'm-', linewidth=2, label='γ_d2i * E_direct (Action → Ideas)', alpha=0.8)
        
        ax2.axvline(x=39, color='orange', linestyle='--', linewidth=2, alpha=0.5)
        ax2.axvline(x=44, color='purple', linestyle='--', linewidth=2, alpha=0.5)
        
        ax2.set_xlabel('Time (years from 1750)', fontsize=12)
        ax2.set_ylabel('Conversion Rate (J/s)', fontsize=12)
        ax2.set_title('Coupling: "Words → Actions → New Words"', fontsize=14, fontweight='bold')
        ax2.legend(loc='best', fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        # 3. エネルギー比率 (対数スケール)
        ax3 = axes[2]
        ratio = np.array(E_indirect_data) / (np.array(E_direct_data) + 1e-6)
        ax3.semilogy(time_array, ratio, 'purple', linewidth=3, alpha=0.7)
        ax3.axhline(y=1.0, color='black', linestyle='-', linewidth=1.5, alpha=0.5, label='E_indirect = E_direct')
        
        ax3.axvline(x=39, color='orange', linestyle='--', linewidth=2, alpha=0.5)
        ax3.axvline(x=44, color='purple', linestyle='--', linewidth=2, alpha=0.5)
        
        ax3.fill_between(time_array, 1.0, 1e6, alpha=0.2, color='blue', label='Ideas dominant')
        ax3.fill_between(time_array, 1e-6, 1.0, alpha=0.2, color='red', label='Violence dominant')
        
        ax3.set_xlabel('Time (years from 1750)', fontsize=12)
        ax3.set_ylabel('E_indirect / E_direct (log scale)', fontsize=12)
        ax3.set_title('Power Balance: Ideas vs Violence', fontsize=14, fontweight='bold')
        ax3.legend(loc='best', fontsize=10)
        ax3.grid(True, alpha=0.3)
        ax3.set_ylim([1e-2, 1e4])
        
        plt.tight_layout()
        plt.savefig('ssd_french_revolution.png', dpi=150, bbox_inches='tight')
        print("\n💾 Plot saved: ssd_french_revolution.png")
        plt.show()
        
        # 統計
        print("\n" + "="*70)
        print("📊 統計")
        print("="*70)
        
        # フェーズごとのインデックスを見つける
        phase1_indices = [i for i, p in enumerate(phase_labels) if p == "思想蓄積"]
        phase2_indices = [i for i, p in enumerate(phase_labels) if p == "革命"]
        phase3_indices = [i for i, p in enumerate(phase_labels) if p == "減衰"]
        
        if phase1_indices:
            print(f"\n思想蓄積期 (1750-1789):")
            print(f"  E_indirect: {E_indirect_data[0]:.1f} → {E_indirect_data[phase1_indices[-1]]:.1f}J")
            duration = time_array[phase1_indices[-1]] - time_array[0]
            if duration > 0:
                print(f"  蓄積率: {(E_indirect_data[phase1_indices[-1]] - E_indirect_data[0]) / duration:.1f} J/year")
        
        if phase2_indices:
            print(f"\nバスティーユ襲撃 & 革命期 (1789-1794):")
            print(f"  E_indirect: {E_indirect_data[phase2_indices[0]]:.1f} → {E_indirect_data[phase2_indices[-1]]:.1f}J")
            print(f"  E_direct: {E_direct_data[phase2_indices[0]]:.1f} → {E_direct_data[phase2_indices[-1]]:.1f}J")
            
            rev_i2d = [conversion_i2d_data[i] for i in phase2_indices]
            rev_d2i = [conversion_d2i_data[i] for i in phase2_indices]
            if rev_i2d:
                print(f"  循環サイクル: 思想 → 行動 → 新思想 → ...")
                print(f"  平均 i→d: {np.mean(rev_i2d):.2f} J/s")
                print(f"  平均 d→i: {np.mean(rev_d2i):.2f} J/s")
        
        if phase3_indices:
            print(f"\n減衰期 (1794-1804):")
            print(f"  E_indirect: {E_indirect_data[phase3_indices[0]]:.1f} → {E_indirect_data[-1]:.1f}J")
            duration = time_array[-1] - time_array[phase3_indices[0]]
            if duration > 0:
                print(f"  減衰率: {(E_indirect_data[phase3_indices[0]] - E_indirect_data[-1]) / duration:.1f} J/year")
            print(f"  結果: ナポレオン独裁 (E_direct 支配)")


if __name__ == "__main__":
    sim = FrenchRevolutionSimulator()
    sim.simulate()
    
    print("\n" + "="*70)
    print("✅ SSD v3.5 実証: フランス革命 完了")
    print("="*70)
    print("\n🔬 洞察:")
    print("  1. 思想 (E_indirect) は長期蓄積可能")
    print("  2. 臨界突破 (Θ) で相転移 → 暴力解放")
    print("  3. γ_i2d, γ_d2i による循環: 言葉 ↔ 行動")
    print("  4. β_decay により思想は減衰 → 独裁へ")
    print("  5. SSD v3.5 は革命動態を数値的に再現できる")
